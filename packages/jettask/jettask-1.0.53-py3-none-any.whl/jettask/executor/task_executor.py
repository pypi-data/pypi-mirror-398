"""
任务执行器

职责：
1. 从事件队列获取消息
2. 执行任务并管理生命周期
3. 限流控制和批处理
"""

import asyncio
import logging
import time
import os
from typing import Set
from collections import deque

from .core import ExecutorCore
from ..messaging.delay_queue import AsyncDelayQueue
from ..worker.lifecycle import WorkerManager
from ..utils.rate_limit.manager import RateLimiterManager

logger = logging.getLogger('app')


class TaskExecutor:
    """
    任务执行器 - 负责单个任务类型的执行

    这是真正执行任务的核心组件，无论是在单进程还是多进程模式下。

    职责：
    1. 从 event_queue 获取消息
    2. 应用限流控制
    3. 执行任务
    4. 批处理管道优化
    """

    def __init__(self, event_queue, app, task_name: str, worker_id: str, worker_state_manager, concurrency: int = 100, local_concurrency: int = None):
        self.event_queue = event_queue
        self.app = app
        self.task_name = task_name
        self.concurrency = concurrency
        self.worker_id = worker_id
        self.worker_state_manager = worker_state_manager
        self.local_concurrency = local_concurrency

        self._local_semaphore = asyncio.Semaphore(local_concurrency) if local_concurrency else None
        if local_concurrency:
            logger.info(f"TaskExecutor[{task_name}] local concurrency limit set to {local_concurrency}")
        self.executor_core = ExecutorCore(
            app=app,
            task_name=task_name,
            concurrency=concurrency
        )

        if not hasattr(app, '_executor_core'):
            app._executor_core = self.executor_core

        task_obj = app.get_task_by_name(task_name)
        if task_obj and hasattr(task_obj, '_app') and not hasattr(task_obj._app, '_executor_core'):
            task_obj._app._executor_core = self.executor_core

        self._active_tasks: Set[asyncio.Task] = set()

        self.max_buffer_size = 5000

        self.delay_queue = AsyncDelayQueue()

        logger.debug(f"TaskExecutor initialized for task '{task_name}'")

    async def initialize(self):


        from jettask.utils.time_sync import init_time_sync
        time_sync = await init_time_sync(self.app.ep.async_redis_client)
        logger.debug(f"TimeSync initialized, offset={time_sync.get_offset():.6f}s")

        self.executor_core.rate_limiter_manager = RateLimiterManager(
            redis_client=self.app.ep.async_redis_client,
            worker_id=self.worker_id,
            redis_prefix=self.executor_core.prefix,
            worker_state_manager=self.worker_state_manager
        )
        logger.debug(f"RateLimiterManager initialized for worker {self.worker_id}")

        await self.executor_core.rate_limiter_manager.load_config_from_redis()

    async def run(self):
        logger.debug(f"TaskExecutor started for task '{self.task_name}'")

        tasks_batch = []

        try:
            while True:
                if hasattr(self.app, '_should_exit') and self.app._should_exit:
                    logger.debug(f"TaskExecutor[{self.task_name}] detected shutdown signal")
                    break

                if hasattr(os, 'getppid') and os.getppid() == 1:
                    logger.warning(f"TaskExecutor[{self.task_name}] parent died, exiting")
                    break

                current_time = time.time()

                expired_tasks = self.delay_queue.get_expired_tasks()
                for expired_task in expired_tasks:
                    event_data = expired_task.get('event_data', {})
                    event_data.pop("execute_at", None)
                    event_data.pop("is_delayed", None)

                    tasks_batch.append(expired_task)
                    logger.debug(
                        f"[{self.task_name}] Delayed task {expired_task.get('event_id', 'unknown')} "
                        f"expired and ready for execution"
                    )

                event = None
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    pass
                
                if event:
                    event_data = event.get('event_data', {})
                    execute_at = event_data.get("execute_at")

                    if execute_at is not None:
                        current_time = time.time()

                        if execute_at > current_time:
                            delay = execute_at - current_time
                            self.delay_queue.put(event, delay)
                            logger.debug(
                                f"[{self.task_name}] Delayed task {event.get('event_id', 'unknown')} "
                                f"by {delay:.3f}s (execute_at={execute_at:.3f})"
                            )
                            continue
                        else:
                            event_data.pop("execute_at", None)
                            event_data.pop("is_delayed", None)
                            logger.debug(
                                f"[{self.task_name}] Delayed task {event.get('event_id', 'unknown')} "
                                f"already expired, executing immediately"
                            )

                    tasks_batch.append(event)
                    logger.debug(
                        f"[{self.task_name}] Got event: {event.get('event_id', 'unknown')}"
                    )

                if tasks_batch:
                    await self._process_batch(tasks_batch)
                    tasks_batch.clear()

                if self._should_flush_buffers(current_time):
                    asyncio.create_task(self.executor_core._flush_all_buffers())

                await self._smart_sleep()

        except asyncio.CancelledError:
            logger.debug(f"TaskExecutor[{self.task_name}] cancelled")
        except Exception as e:
            logger.error(f"TaskExecutor[{self.task_name}] error: {e}", exc_info=True)
        finally:
            await self.cleanup()

    async def _process_batch(self, tasks_batch):
        for event in tasks_batch:
            event_data = event.get('event_data', {})
            event_task_name = event_data.get("_task_name") or event_data.get("name")

            if not event_task_name:
                logger.error(f"No task_name in event {event.get('event_id')}")
                continue

            if event_task_name != self.task_name:
                logger.error(
                    f"Task name mismatch: {event_task_name} != {self.task_name}"
                )
                continue

            logger.debug(
                f"[{self.task_name}] Acquiring rate limit, event_id={event.get('event_id')}"
            )

            rate_limit_token = await self.executor_core.rate_limiter_manager.acquire(
                task_name=self.task_name,
                timeout=None
            )

            if not rate_limit_token:
                logger.error(f"Failed to acquire token for {self.task_name}")
                continue

            logger.debug(
                f"[{self.task_name}] Acquired token={rate_limit_token}, starting execution"
            )

            self.executor_core.batch_counter += 1

            async def execute_with_release(event_data, token, semaphore=None):
                try:
                    if semaphore:
                        await semaphore.acquire()
                        logger.debug(f"[{self.task_name}] Acquired local semaphore, event_id={event_data.get('event_id')}")
                    try:
                        await self.executor_core.execute_task(**event_data)
                    finally:
                        if semaphore:
                            semaphore.release()
                            logger.debug(f"[{self.task_name}] Released local semaphore, event_id={event_data.get('event_id')}")
                finally:
                    await self.executor_core.rate_limiter_manager.release(
                        self.task_name, task_id=token
                    )

            task = asyncio.create_task(execute_with_release(event, rate_limit_token, self._local_semaphore))
            self._active_tasks.add(task)
            task.add_done_callback(self._active_tasks.discard)

    def _should_flush_buffers(self, current_time: float) -> bool:
        buffer_full = (
            len(self.executor_core.pending_acks) >= self.max_buffer_size or
            len(self.executor_core.status_updates) >= self.max_buffer_size or
            len(self.executor_core.data_updates) >= self.max_buffer_size or
            len(self.executor_core.task_info_updates) >= self.max_buffer_size
        )

        if buffer_full:
            return True

        has_pending_data = (
            self.executor_core.pending_acks or
            self.executor_core.status_updates or
            self.executor_core.data_updates or
            self.executor_core.task_info_updates
        )

        if not has_pending_data:
            return False

        for data_type, config in self.executor_core.pipeline_config.items():
            time_since_flush = current_time - self.executor_core.last_pipeline_flush[data_type]

            if data_type == 'ack' and self.executor_core.pending_acks:
                if time_since_flush >= config['max_delay']:
                    return True
            elif data_type == 'task_info' and self.executor_core.task_info_updates:
                if time_since_flush >= config['max_delay']:
                    return True
            elif data_type == 'status' and self.executor_core.status_updates:
                if time_since_flush >= config['max_delay']:
                    return True
            elif data_type == 'data' and self.executor_core.data_updates:
                if time_since_flush >= config['max_delay']:
                    return True

        return False

    async def _smart_sleep(self):
        has_events = False

        if isinstance(self.event_queue, deque):
            has_events = bool(self.event_queue)
        elif isinstance(self.event_queue, asyncio.Queue):
            has_events = not self.event_queue.empty()

        if has_events:
            await asyncio.sleep(0)
        else:
            has_pending = (
                self.executor_core.pending_acks or
                self.executor_core.status_updates or
                self.executor_core.data_updates or
                self.executor_core.task_info_updates
            )

            if has_pending:
                await self.executor_core._flush_all_buffers()

            next_expire_time = self.delay_queue.get_next_expire_time()
            if next_expire_time is not None:
                current_time = time.time()
                sleep_time = max(0.001, min(0.1, next_expire_time - current_time))
                await asyncio.sleep(sleep_time)
            else:
                await asyncio.sleep(0.001)

    async def cleanup(self):
        logger.debug(f"TaskExecutor[{self.task_name}] cleaning up")

        self.delay_queue.clear()
        logger.debug("Delay queue cleared")

        if hasattr(self.app.ep, '_stop_reading'):
            self.app.ep._stop_reading = True

        if self._active_tasks:
            logger.debug(
                f"TaskExecutor[{self.task_name}] cancelling {len(self._active_tasks)} active tasks"
            )
            for task in self._active_tasks:
                if not task.done():
                    task.cancel()

            if self._active_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self._active_tasks, return_exceptions=True),
                        timeout=0.2
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        f"TaskExecutor[{self.task_name}] some tasks did not complete in time"
                    )

        await self.executor_core.cleanup()

        logger.debug(f"TaskExecutor[{self.task_name}] stopped")


__all__ = ['TaskExecutor']
