"""
并发限流器

基于Redis锁的并发数限流实现
支持：
1. 并发锁管理
2. 自动锁超时清理
3. Worker下线时的锁释放
"""

import asyncio
import logging
import time
import traceback
import uuid
from redis.asyncio import Redis
from typing import Dict, Optional, Set, List, Tuple
from collections import defaultdict

from jettask.db.connector import get_sync_redis_client

logger = logging.getLogger('app')


class ConcurrencyRateLimiter:
    """并发限流器 - 基于 Redis 的分布式信号量

    使用 Redis 实现分布式信号量，控制全局并发数。
    所有 workers 共享同一个信号量，保证全局并发不超过限制。

    特点：
    - 分布式协调，真正的全局并发控制
    - 使用 Redis 有序集合（Sorted Set）追踪正在运行的任务
    - 自动清理超时任务
    - 支持多进程、多机器部署

    性能优化：
    - 使用 Redis Pub/Sub 代替轮询等待
    - 分离超时清理，避免每次 acquire 都清理
    - 本地缓存减少 Redis 访问
    """

    def __init__(
        self,
        redis_client: Redis,
        task_name: str,
        worker_id: str,
        max_concurrency: int,
        redis_prefix: str = "jettask",
        timeout: float = 5.0,  
        cleanup_interval: float = 1.0,  
        renewal_interval: float = 1.0  
    ):
        self.redis = redis_client
        self.task_name = task_name
        self.worker_id = worker_id
        self.max_concurrency = max_concurrency
        self.redis_prefix = redis_prefix
        self.timeout = timeout
        self.cleanup_interval = cleanup_interval
        self.renewal_interval = renewal_interval

        self.semaphore_key = f"{redis_prefix}:RATE_LIMIT:CONCURRENCY:{task_name}"
        self.release_channel = f"{redis_prefix}:RATE_LIMIT:CONCURRENCY_RELEASE:{task_name}"

        self.acquire_script = """
            local semaphore_key = KEYS[1]
            local max_concurrency = tonumber(ARGV[1])
            local current_time = tonumber(ARGV[2])
            local task_id = ARGV[3]

            -- 检查当前并发数（不做清理，由后台任务定期清理）
            local current_count = redis.call('ZCARD', semaphore_key)

            if current_count < max_concurrency then
                -- 未达到限制，添加任务
                redis.call('ZADD', semaphore_key, current_time, task_id)
                return 1
            else
                return 0
            end
        """

        self.release_script = """
            local semaphore_key = KEYS[1]
            local release_channel = KEYS[2]
            local task_id = ARGV[1]

            -- 移除任务
            local removed = redis.call('ZREM', semaphore_key, task_id)

            -- 如果成功移除，通知等待者
            if removed > 0 then
                redis.call('PUBLISH', release_channel, '1')
            end

            return removed
        """

        self.cleanup_script = """
            local semaphore_key = KEYS[1]
            local release_channel = KEYS[2]
            local timeout_threshold = tonumber(ARGV[1])

            -- 清理超时任务
            local removed = redis.call('ZREMRANGEBYSCORE', semaphore_key, '-inf', timeout_threshold)

            -- 如果清理了任务，通知等待者
            if removed > 0 then
                redis.call('PUBLISH', release_channel, tostring(removed))
            end

            return removed
        """

        self.renewal_script = """
            local semaphore_key = KEYS[1]
            local task_id = ARGV[1]
            local current_time = tonumber(ARGV[2])

            -- 检查任务是否存在
            local exists = redis.call('ZSCORE', semaphore_key, task_id)
            if exists then
                -- 更新时间戳
                redis.call('ZADD', semaphore_key, current_time, task_id)
                return 1
            else
                return 0
            end
        """

        self._local_tasks = set()  
        self._unified_heartbeat_task = None  
        self._cleanup_task = None  
        self._pubsub = None  
        self._pubsub_listener_task = None  
        self._periodic_trigger_task = None  
        self._release_event = asyncio.Event()  
        self._poll_interval = 10.0  

    def _trigger_release_signal(self):
        self._release_event.set()
        self._release_event.clear()

    async def _pubsub_listener(self):
        retry_delay = 1.0  
        max_retry_delay = 30.0  

        while True:
            try:
                logger.debug(f"[CONCURRENCY] Pub/Sub listener started for {self.release_channel}")
                async for message in self._pubsub.listen():
                    if message['type'] == 'message':
                        logger.debug(f"[CONCURRENCY] Received Pub/Sub release notification, triggering signal")
                        self._trigger_release_signal()
                    retry_delay = 1.0
            except asyncio.CancelledError:
                logger.debug(f"[CONCURRENCY] Pub/Sub listener cancelled")
                raise
            except Exception as e:
                error_msg = str(e)
                if "Buffer is closed" in error_msg or "Connection" in error_msg or "closed" in error_msg.lower():
                    logger.warning(f"[CONCURRENCY] Pub/Sub connection lost: {e}, will reconnect in {retry_delay}s")
                else:
                    logger.error(f"[CONCURRENCY] Error in Pub/Sub listener: {e}")

                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)  

                try:
                    if self._pubsub is not None:
                        try:
                            await self._pubsub.close()
                        except Exception:
                            pass

                    self._pubsub = self.redis.pubsub()
                    await self._pubsub.subscribe(self.release_channel)

                    if hasattr(self._pubsub, 'connection') and self._pubsub.connection:
                        self._pubsub.connection._is_pubsub_connection = True

                    logger.info(f"[CONCURRENCY] Pub/Sub reconnected successfully for {self.release_channel}")
                except Exception as reconnect_error:
                    logger.error(f"[CONCURRENCY] Failed to reconnect Pub/Sub: {reconnect_error}")

    async def _periodic_trigger(self):
        logger.debug(f"[CONCURRENCY] Periodic trigger started, interval={self._poll_interval}s")

        while True:
            try:
                await asyncio.sleep(self._poll_interval)
                logger.debug(f"[CONCURRENCY] Periodic trigger firing, triggering signal")
                self._trigger_release_signal()
            except asyncio.CancelledError:
                logger.debug(f"[CONCURRENCY] Periodic trigger cancelled")
                raise
            except Exception as e:
                logger.error(f"[CONCURRENCY] Error in periodic trigger: {e}")
                await asyncio.sleep(1.0)

    async def _unified_heartbeat_manager(self):
        retry_delay = 1.0  
        max_retry_delay = 10.0  
        consecutive_errors = 0  

        logger.debug(f"[CONCURRENCY] Unified heartbeat manager started, interval={self.renewal_interval}s")

        while True:
            try:
                await asyncio.sleep(self.renewal_interval)

                if not self._local_tasks:
                    consecutive_errors = 0
                    retry_delay = 1.0
                    continue

                current_time = time.time()
                tasks_snapshot = list(self._local_tasks)  

                logger.debug(f"[CONCURRENCY] Renewing heartbeat for {len(tasks_snapshot)} tasks")

                try:
                    pipe = self.redis.pipeline()
                    for task_id in tasks_snapshot:
                        pipe.eval(
                            self.renewal_script,
                            1,
                            self.semaphore_key,
                            task_id,
                            current_time
                        )

                    results = await pipe.execute()

                    for task_id, result in zip(tasks_snapshot, results):
                        if result == 0:
                            logger.warning(f"[CONCURRENCY] Task {task_id} was cleaned up, removing from local tasks")
                            self._local_tasks.discard(task_id)
                        else:
                            logger.debug(f"[CONCURRENCY] Renewed lease for task {task_id}")

                    consecutive_errors = 0
                    retry_delay = 1.0

                except Exception as e:
                    error_msg = str(e)
                    consecutive_errors += 1

                    is_connection_error = any(
                        keyword in error_msg for keyword in
                        ["Buffer is closed", "Connection", "closed", "ConnectionError"]
                    )

                    if is_connection_error:
                        if consecutive_errors <= 3:
                            logger.warning(f"[CONCURRENCY] Heartbeat connection error ({consecutive_errors}): {e}")
                        else:
                            if consecutive_errors % 10 == 0:
                                logger.warning(f"[CONCURRENCY] Heartbeat still failing after {consecutive_errors} attempts")
                    else:
                        logger.error(f"[CONCURRENCY] Error renewing leases in batch: {e}")

                    for task_id in tasks_snapshot:
                        try:
                            result = await self.redis.eval(
                                self.renewal_script,
                                1,
                                self.semaphore_key,
                                task_id,
                                current_time
                            )
                            if result == 0:
                                logger.warning(f"[CONCURRENCY] Task {task_id} was cleaned up, removing from local tasks")
                                self._local_tasks.discard(task_id)
                        except Exception as e2:
                            if consecutive_errors <= 1:
                                logger.error(f"[CONCURRENCY] Error renewing lease for {task_id}: {e2}")

                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 1.5, max_retry_delay)

            except asyncio.CancelledError:
                logger.debug(f"[CONCURRENCY] Unified heartbeat manager cancelled")
                raise
            except Exception as outer_error:
                logger.error(f"[CONCURRENCY] Unexpected error in heartbeat manager: {outer_error}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, max_retry_delay)

    async def _ensure_pubsub(self):
        if self._pubsub is None:
            self._pubsub = self.redis.pubsub()
            await self._pubsub.subscribe(self.release_channel)

            if hasattr(self._pubsub, 'connection') and self._pubsub.connection:
                self._pubsub.connection._is_pubsub_connection = True
                logger.info(f"[CONCURRENCY] Marked PubSub connection {id(self._pubsub.connection)} to prevent cleanup")

            logger.debug(f"[CONCURRENCY] Subscribed to channel {self.release_channel}")

            if self._pubsub_listener_task is None:
                self._pubsub_listener_task = asyncio.create_task(self._pubsub_listener())
                logger.debug(f"[CONCURRENCY] Pub/Sub listener task started")

            if self._periodic_trigger_task is None:
                self._periodic_trigger_task = asyncio.create_task(self._periodic_trigger())
                logger.debug(f"[CONCURRENCY] Periodic trigger task started")

            if self._unified_heartbeat_task is None:
                self._unified_heartbeat_task = asyncio.create_task(self._unified_heartbeat_manager())
                logger.debug(f"[CONCURRENCY] Unified heartbeat manager started")

            if self._cleanup_task is None:
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
                logger.debug(f"[CONCURRENCY] Periodic cleanup task started")

    async def _try_acquire_slot(self, task_id: str) -> bool:
        try:
            result = await self.redis.eval(
                self.acquire_script,
                1,
                self.semaphore_key,
                self.max_concurrency,
                time.time(),
                task_id
            )

            if result == 1:
                logger.debug(f"[CONCURRENCY] Acquired slot for task_id={task_id}")
                self._local_tasks.add(task_id)

                if self._unified_heartbeat_task is None:
                    self._unified_heartbeat_task = asyncio.create_task(self._unified_heartbeat_manager())
                    logger.debug(f"[CONCURRENCY] Unified heartbeat manager started on first acquire")

                return True
            else:
                return False

        except Exception as e:
            logger.error(f"[CONCURRENCY] Error in _try_acquire_slot: {e}")
            return False

    async def _periodic_cleanup(self):
        retry_delay = 1.0  
        max_retry_delay = 30.0  
        consecutive_errors = 0  

        logger.debug(f"[CONCURRENCY] Periodic cleanup task started, interval={self.cleanup_interval}s")

        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                current_time = time.time()
                timeout_threshold = current_time - self.timeout
                try:
                    removed = await self.redis.eval(
                        self.cleanup_script,
                        2,  
                        self.semaphore_key,
                        self.release_channel,
                        timeout_threshold
                    )
                    if removed > 0:
                        logger.info(f"[CONCURRENCY] Cleaned up {removed} timeout tasks")

                    consecutive_errors = 0
                    retry_delay = 1.0

                except Exception as e:
                    error_msg = str(e)
                    consecutive_errors += 1

                    is_connection_error = any(
                        keyword in error_msg for keyword in
                        ["Buffer is closed", "Connection", "closed", "ConnectionError"]
                    )

                    if is_connection_error:
                        if consecutive_errors <= 3:
                            logger.warning(f"[CONCURRENCY] Cleanup connection error ({consecutive_errors}): {e}")
                        else:
                            if consecutive_errors % 10 == 0:
                                logger.warning(f"[CONCURRENCY] Cleanup still failing after {consecutive_errors} attempts")
                    else:
                        logger.error(f"[CONCURRENCY] Cleanup error: {e}")

                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)

            except asyncio.CancelledError:
                logger.debug(f"[CONCURRENCY] Periodic cleanup task cancelled")
                raise
            except Exception as outer_error:
                logger.error(f"[CONCURRENCY] Unexpected error in periodic cleanup: {outer_error}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)

    async def acquire(self, timeout: float = 10.0) -> Optional[str]:
        start_time = time.time()
        task_id = f"{self.worker_id}:{uuid.uuid4().hex}"

        logger.debug(f"[CONCURRENCY] Attempting to acquire, task_id={task_id}")
        if await self._try_acquire_slot(task_id):
            logger.debug(f"[WORKER:{self.worker_id}] [CONCURRENCY] Acquired immediately, task_id={task_id}, current_concurrency={len(self._local_tasks)}")
            return task_id

        await self._ensure_pubsub()

        while True:
            logger.debug(f"[CONCURRENCY] Waiting to acquire, task_id={task_id}")
            elapsed = time.time() - start_time
            if timeout is not None and elapsed >= timeout:
                logger.warning(f"[CONCURRENCY] Acquire timeout after {timeout}s")
                return None

            try:
                if timeout is not None:
                    remaining = timeout - elapsed
                    await asyncio.wait_for(self._release_event.wait(), timeout=remaining)
                else:
                    await self._release_event.wait()

                logger.debug(f"[CONCURRENCY] Received signal, attempting acquire for task_id={task_id}")

            except asyncio.TimeoutError:
                logger.warning(f"[CONCURRENCY] Acquire timeout after {timeout}s")
                return None

            if await self._try_acquire_slot(task_id):
                logger.debug(f"[WORKER:{self.worker_id}] [CONCURRENCY] Acquired after wait, task_id={task_id}, current_concurrency={len(self._local_tasks)}")
                return task_id
            else:
                logger.debug(f"[CONCURRENCY] Acquire failed (slot taken by others), waiting for next signal")

    async def try_acquire(self) -> bool:
        task_id = f"{self.worker_id}:{uuid.uuid4().hex}"

        if await self._try_acquire_slot(task_id):
            logger.debug(f"[CONCURRENCY] Try acquired, task_id={task_id}")
            return True
        else:
            logger.debug(f"[CONCURRENCY] Try acquire failed, no available slot")
            return False

    async def release(self, task_id: str):
        self._local_tasks.discard(task_id)

        try:
            result = await self.redis.eval(
                self.release_script,
                2,  
                self.semaphore_key,
                self.release_channel,
                task_id
            )

            logger.debug(f"[WORKER:{self.worker_id}] [CONCURRENCY] Released semaphore, task_id={task_id}, remaining_concurrency={len(self._local_tasks)}")

        except Exception as e:
            logger.error(f"[CONCURRENCY] Error releasing semaphore: {e}")

    async def update_limit(self, new_limit: int):
        if self.max_concurrency != new_limit:
            old_limit = self.max_concurrency
            self.max_concurrency = new_limit
            logger.debug(
                f"[WORKER:{self.worker_id}] [CONCURRENCY] Limit changed: {old_limit} → {new_limit}"
            )

    async def get_stats(self) -> dict:
        try:
            timeout_threshold = time.time() - self.timeout
            await self.redis.zremrangebyscore(
                self.semaphore_key,
                '-inf',
                timeout_threshold
            )

            current_count = await self.redis.zcard(self.semaphore_key)

            return {
                'mode': 'concurrency',
                'concurrency_limit': self.max_concurrency,
                'current_concurrency': current_count,
                'local_tasks': len(self._local_tasks),
            }

        except Exception as e:
            logger.error(f"[CONCURRENCY] Error getting stats: {e}")
            return {
                'mode': 'concurrency',
                'concurrency_limit': self.max_concurrency,
                'current_concurrency': 0,
                'local_tasks': len(self._local_tasks),
            }

    async def stop(self):
        try:
            if self._unified_heartbeat_task is not None:
                self._unified_heartbeat_task.cancel()
                try:
                    await self._unified_heartbeat_task
                except asyncio.CancelledError:
                    pass
                self._unified_heartbeat_task = None
                logger.debug(f"[CONCURRENCY] Unified heartbeat manager cancelled")

            if self._pubsub_listener_task is not None:
                self._pubsub_listener_task.cancel()
                try:
                    await self._pubsub_listener_task
                except asyncio.CancelledError:
                    pass
                self._pubsub_listener_task = None
                logger.debug(f"[CONCURRENCY] Pub/Sub listener task cancelled")

            if self._periodic_trigger_task is not None:
                self._periodic_trigger_task.cancel()
                try:
                    await self._periodic_trigger_task
                except asyncio.CancelledError:
                    pass
                self._periodic_trigger_task = None
                logger.debug(f"[CONCURRENCY] Periodic trigger task cancelled")

            if self._pubsub is not None:
                await self._pubsub.unsubscribe(self.release_channel)
                await self._pubsub.close()
                self._pubsub = None
                logger.debug(f"[CONCURRENCY] Cleaned up pubsub for {self.task_name}")

            if self._local_tasks:
                for task_id in list(self._local_tasks):
                    try:
                        await self.redis.zrem(self.semaphore_key, task_id)
                    except Exception as e:
                        logger.error(f"[CONCURRENCY] Error removing task {task_id}: {e}")
                self._local_tasks.clear()
                logger.debug(f"[CONCURRENCY] Cleaned up local tasks for {self.task_name}")

        except Exception as e:
            logger.error(f"[CONCURRENCY] Error during stop: {e}")

    async def __aenter__(self):
        task_id = await self.acquire()
        if task_id is None:
            raise TimeoutError("Failed to acquire concurrency slot")
        self._current_task_id = task_id
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, '_current_task_id'):
            await self.release(self._current_task_id)
            delattr(self, '_current_task_id')
        return False  

    @classmethod
    def cleanup_worker_locks(cls, redis_url: str, redis_prefix: str, worker_id: str = None, task_names: list = None):
        try:
            if not task_names:
                logger.warning(f"[CONCURRENCY] No task_names provided, cannot cleanup locks. Please provide task_names.")
                return 0

            sync_redis = get_sync_redis_client(redis_url, decode_responses=False)
            try:
                total_cleaned = 0

                for task_name in task_names:
                    key = f"{redis_prefix}:RATE_LIMIT:CONCURRENCY:{task_name}"

                    if not sync_redis.exists(key):
                        continue

                    if worker_id:
                        try:
                            all_members = sync_redis.zrange(key, 0, -1)
                            to_remove = []
                            for member in all_members:
                                if isinstance(member, bytes):
                                    member_str = member.decode('utf-8')
                                else:
                                    member_str = member

                                if member_str.startswith(worker_id + ':'):
                                    to_remove.append(member)

                            if to_remove:
                                removed = sync_redis.zrem(key, *to_remove)
                                total_cleaned += removed
                                logger.debug(f"[CONCURRENCY] Cleaned up {removed} locks for worker {worker_id} from {key}")
                        except Exception as e:
                            logger.error(f"[CONCURRENCY] Error cleaning {key}: {e}")
                    else:
                        try:
                            current_time = __import__('time').time()
                            timeout_threshold = current_time - 5
                            removed = sync_redis.zremrangebyscore(key, '-inf', timeout_threshold)
                            if removed > 0:
                                total_cleaned += removed
                                logger.debug(f"[CONCURRENCY] Cleaned up {removed} stale locks from {key}")
                        except Exception as e:
                            logger.error(f"[CONCURRENCY] Error cleaning {key}: {e}")

                logger.debug(f"[CONCURRENCY] Cleanup completed, total cleaned: {total_cleaned}")
                return total_cleaned
            finally:
                sync_redis.close()

        except Exception as e:
            logger.error(f"[CONCURRENCY] Error during cleanup_worker_locks: {e}")
            return 0





__all__ = ['ConcurrencyRateLimiter']
