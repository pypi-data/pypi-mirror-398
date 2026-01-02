"""
任务级限流器

组合QPS和并发限流，提供统一的任务级限流接口
"""

import asyncio
import logging
import time
from redis.asyncio import Redis
from typing import Dict, Optional, List, Tuple, Any, TYPE_CHECKING

from .qps_limiter import QPSRateLimiter
from .concurrency_limiter import ConcurrencyRateLimiter
from .config import RateLimitConfig, QPSLimit, ConcurrencyLimit, parse_rate_limit_config

logger = logging.getLogger('app')


class TaskRateLimiter:
    """任务级别的限流器

    根据配置类型自动选择合适的限流器实现：
    - QPSLimit: 使用本地滑动窗口 + Redis 协调配额
    - ConcurrencyLimit: 使用 Redis 分布式信号量
    """

    def __init__(
        self,
        redis_client: Redis,
        task_name: str,
        worker_id: str,
        config: RateLimitConfig,
        redis_prefix: str = "jettask",
        sync_interval: float = 5.0,
        worker_state_manager = None
    ):
        self.redis = redis_client
        self.task_name = task_name
        self.worker_id = worker_id
        self.redis_prefix = redis_prefix
        self.global_config = config
        self.sync_interval = sync_interval
        self.worker_state_manager = worker_state_manager

        self.rate_limit_key = f"{redis_prefix}:RATE_LIMIT:CONFIG:{task_name}"

        if isinstance(config, QPSLimit):
            self.limiter = QPSRateLimiter(
                qps=config.qps,
                window_size=config.window_size,
                worker_id=worker_id
            )
            self.mode = 'qps'
            self._sync_task: Optional[asyncio.Task] = None
            self._running = False
        elif isinstance(config, ConcurrencyLimit):
            self.limiter = ConcurrencyRateLimiter(
                redis_client=redis_client,
                task_name=task_name,
                worker_id=worker_id,
                max_concurrency=config.max_concurrency,
                redis_prefix=redis_prefix
            )
            self.mode = 'concurrency'
            self._sync_task = None
            self._running = False
        else:
            raise ValueError(f"Unsupported config type: {type(config)}")

        self.stats = {
            'syncs': 0,
            'last_sync_time': 0,
            'current_worker_count': 0,
        }

    async def start(self):
        if self._running:
            logger.warning(f"TaskRateLimiter for {self.task_name} already running")
            return

        logger.debug(
            f"Starting TaskRateLimiter for task={self.task_name}, "
            f"config={self.global_config}, mode={self.mode}"
        )

        await self._initialize_redis()

        if self.mode == 'qps':
            self._running = True
            self._sync_task = asyncio.create_task(self._sync_loop())

            if self.worker_state_manager:
                self.worker_state_manager.register_callback(self._on_worker_state_change)
                logger.debug(f"Registered worker state change listener for {self.task_name}")

        logger.debug(f"TaskRateLimiter started for {self.task_name}")
    def __delattr__(self, name):
        self.stop()
        
    async def stop(self):
        
        print(f'准备退出限流器 {self.task_name} {self.mode}')
        if not self._running and self.mode == 'qps':
            return

        logger.debug(f"Stopping TaskRateLimiter for {self.task_name}")

        if self.mode == 'qps':
            self._running = False

            if self.worker_state_manager:
                self.worker_state_manager.unregister_callback(self._on_worker_state_change)

            if self._sync_task:
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass
        elif self.mode == 'concurrency':
            if hasattr(self.limiter, 'stop'):
                try:
                    await self.limiter.stop()
                    logger.debug(f"Concurrency limiter stopped and locks released for {self.task_name}")
                except Exception as e:
                    logger.error(f"Error stopping concurrency limiter for {self.task_name}: {e}")

        logger.debug(f"TaskRateLimiter stopped for {self.task_name}")

    async def _initialize_redis(self):
        try:
            exists = await self.redis.exists(self.rate_limit_key)
            if not exists:
                config_dict = self.global_config.to_dict()
                await self.redis.hset(self.rate_limit_key, mapping=config_dict)
                logger.debug(
                    f"Initialized rate limit config for {self.task_name}: {self.global_config}"
                )

            index_key = f"{self.redis_prefix}:RATE_LIMIT:INDEX"
            await self.redis.sadd(index_key, self.task_name)
            logger.debug(f"Added {self.task_name} to rate limit index")

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")

    async def _on_worker_state_change(self, state_data: dict):
        if self.mode == 'qps':
            logger.debug(f"[{self.task_name}] Worker state changed: {state_data}")
            await self._sync_quota()

    async def _sync_quota(self):
        if self.mode != 'qps':
            return

        try:
            config_dict = await self.redis.hgetall(self.rate_limit_key)
            if not config_dict:
                logger.warning(f"No config found in Redis for {self.task_name}")
                return

            config_dict = {
                k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in config_dict.items()
            }

            global_config = parse_rate_limit_config(config_dict)
            if not isinstance(global_config, QPSLimit):
                logger.error(f"Invalid QPS config for {self.task_name}: {config_dict}")
                return

            worker_ids = [self.worker_id]
       
            workers = await self.worker_state_manager(self.task_name, only_alive=True)
            if workers:
                worker_ids = sorted(list(workers))
             

            worker_count = len(worker_ids)

            await self._allocate_quotas(global_config.qps, worker_ids)

            quota_key = f"quota:{self.worker_id}"
            quota_str = await self.redis.hget(self.rate_limit_key, quota_key)

            if quota_str:
                quota_value = int(quota_str)
            else:
                quota_value = global_config.qps // worker_count if worker_count > 0 else global_config.qps

            await self.limiter.update_limit(quota_value)

            self.stats['syncs'] += 1
            self.stats['last_sync_time'] = time.time()
            self.stats['current_worker_count'] = worker_count

        except Exception as e:
            logger.error(f"Quota sync error: {e}")

    async def _sync_loop(self):
        while self._running:
            try:
                await self._sync_quota()
                await asyncio.sleep(self.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(1)

    async def _allocate_quotas(self, total_qps: int, worker_ids: list):
        lock_key = f"{self.rate_limit_key}:lock"

        try:
            async with self.redis.lock(lock_key, timeout=3, blocking_timeout=2):
                worker_count = len(worker_ids)
                base_quota = total_qps // worker_count
                remainder = total_qps % worker_count

                allocations = {}
                for i, worker_id in enumerate(worker_ids):
                    quota = base_quota + (1 if i < remainder else 0)
                    allocations[f"quota:{worker_id}"] = quota

                if allocations:
                    await self.redis.hset(self.rate_limit_key, mapping=allocations)

                await self._cleanup_stale_quotas(worker_ids)

                logger.debug(f"[ALLOCATE] Allocated quotas for {worker_count} workers: {allocations}")

        except asyncio.TimeoutError:
            logger.debug(f"[ALLOCATE] Failed to acquire lock, skipping allocation")
        except Exception as e:
            logger.error(f"[ALLOCATE] Error allocating quotas: {e}")

    async def _cleanup_stale_quotas(self, active_worker_ids: list):
        try:
            all_fields = await self.redis.hkeys(self.rate_limit_key)
            active_quota_keys = {f"quota:{wid}" for wid in active_worker_ids}

            to_delete = []
            for field in all_fields:
                if isinstance(field, bytes):
                    field = field.decode('utf-8')

                if field.startswith("quota:") and field not in active_quota_keys:
                    to_delete.append(field)

            if to_delete:
                await self.redis.hdel(self.rate_limit_key, *to_delete)
                logger.debug(f"[CLEANUP] Removed {len(to_delete)} stale quotas")

        except Exception as e:
            logger.error(f"[CLEANUP] Error cleaning up quotas: {e}")

    async def acquire(self, timeout: float = 10.0) -> Optional[str]:
        result = await self.limiter.acquire(timeout=timeout)
        if self.mode == 'qps':
            return True if result else None
        else:
            return result  

    async def release(self, task_id: Optional[str] = None):
        if self.mode == 'concurrency' and task_id is None:
            raise ValueError("ConcurrencyLimit requires task_id for release")

        if self.mode == 'concurrency':
            await self.limiter.release(task_id)
        else:
            pass

    async def try_acquire(self) -> bool:
        return await self.limiter.try_acquire()

    def get_stats(self) -> dict:
        return {
            **self.stats,
            'task_name': self.task_name,
            'worker_id': self.worker_id,
            'config': str(self.global_config),
        }

    async def __aenter__(self):
        task_id = await self.acquire()
        if task_id is None:
            raise TimeoutError("Failed to acquire rate limit slot")
        self._current_task_id = task_id
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, '_current_task_id'):
            task_id = self._current_task_id
            delattr(self, '_current_task_id')
            if self.mode == 'concurrency':
                await self.release(task_id)
        return False  





__all__ = ['TaskRateLimiter']
