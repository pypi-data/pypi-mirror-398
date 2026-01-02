"""
Worker 心跳管理

提供基于协程的心跳管理功能，在主进程中运行。

HeartbeatManager 是一个异步协程管理器，负责定期向 Redis 发送心跳信号。
"""

import os
import socket
import uuid
import time
import asyncio
import logging
from typing import Optional, TYPE_CHECKING
from ..messaging.registry import QueueRegistry
if TYPE_CHECKING:
    from .lifecycle import WorkerManager
logger = logging.getLogger(__name__)

class HeartbeatManager:
    """基于协程的心跳管理器（在 CLI 主进程中运行）"""

    _global_scanner_task = None
    _global_scanner_stop_event = None
    _global_worker_manager = None  
    _scanner_interval = None  

    def __init__(self, queue_registry: QueueRegistry, worker_manager: "WorkerManager", async_redis_client=None,
                 worker_key=None, worker_id=None, redis_prefix=None, redis_url=None,
                 interval=5.0, heartbeat_timeout=15.0):
        if queue_registry is None:
            raise ValueError("queue_registry is required")
        if worker_manager is None:
            raise ValueError("worker_manager is required")

        self.queue_registry = queue_registry

        self.worker_manager = worker_manager

        self.async_redis_client = async_redis_client
        self.worker_key = worker_key
        self.worker_id = worker_id
        self.redis_prefix = redis_prefix
        self.redis_url = redis_url
        self.interval = interval
        self.consumer_id = worker_id
        self.heartbeat_interval = interval
        self.heartbeat_timeout = heartbeat_timeout
        self._last_heartbeat_time = None

        self._stop_event = asyncio.Event()
        self._heartbeat_task = None
        self.heartbeat_process = self

        self._first_heartbeat_done = asyncio.Event()

    @classmethod
    async def create_and_start(cls, queue_registry, worker_manager, async_redis_client,
                        redis_prefix: str, interval: float = 5.0, heartbeat_timeout: float = 15.0,
                        worker_state=None):

        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            prefix = hostname if hostname != 'localhost' else ip
        except:
            prefix = os.environ.get('HOSTNAME', 'unknown')

        reusable_id = None
        if worker_state:
            reusable_id = await worker_state.find_reusable_worker_id(prefix=prefix)

        if reusable_id:
            worker_id = reusable_id
            logger.debug(f"[PID {os.getpid()}] Reusing offline worker ID: {worker_id}")
        else:
            worker_id = worker_state.generate_worker_id(prefix) if worker_state else f"{prefix}-{uuid.uuid4().hex[:8]}-{os.getpid()}"
            logger.debug(f"[PID {os.getpid()}] Generated new worker ID: {worker_id}")

        worker_key = f"{redis_prefix}:WORKER:{worker_id}"

        manager = cls(
            queue_registry=queue_registry,
            worker_manager=worker_manager,
            async_redis_client=async_redis_client,
            worker_key=worker_key,
            worker_id=worker_id,
            redis_prefix=redis_prefix,
            interval=interval,
            heartbeat_timeout=heartbeat_timeout
        )

        manager.start()

        try:
            await asyncio.wait_for(manager._first_heartbeat_done.wait(), timeout=10)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for first heartbeat for worker {worker_id}")

        return manager

    def start(self):
        if self._heartbeat_task and not self._heartbeat_task.done():
            logger.warning("Heartbeat task already running")
            return

        self._stop_event.clear()

        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(),
            name=f"Heartbeat-{self.worker_id}"
        )

    async def stop(self):
        if not self._heartbeat_task:
            return

        logger.debug(f"Stopping heartbeat task for worker {self.worker_id}")
        self._stop_event.set()

        try:
            await self.worker_manager.set_worker_offline(self.worker_id, reason='heartbeat_stopped')
            logger.debug(f"Worker {self.worker_id} marked as offline")
        except Exception as e:
            logger.error(f"Error marking worker offline: {e}", exc_info=True)


    async def _heartbeat_loop(self):
        hostname = socket.gethostname()
        pid = str(os.getpid())

        logger.debug(f"Heartbeat task starting for worker {self.worker_id}")

        heartbeat_count = 0
        last_log_time = time.time()
        first_heartbeat = True

        while not self._stop_event.is_set():
            try:
                current_time = time.time()

                needs_full_init = False
                publish_online_signal = False

                old_alive = await self.async_redis_client.hget(self.worker_key, 'is_alive')
                consumer_id = await self.async_redis_client.hget(self.worker_key, 'consumer_id')

                if not consumer_id:
                    needs_full_init = True
                    publish_online_signal = True
                    logger.warning(f"Worker {self.worker_id} key missing critical fields, reinitializing...")
                elif first_heartbeat and old_alive != 'true':
                    publish_online_signal = True

                if first_heartbeat:
                    first_heartbeat = False

                if needs_full_init:
                    worker_info = {
                        'consumer_id': self.worker_id,
                        'host': hostname,
                        'pid': pid,
                        'heartbeat_timeout': str(self.heartbeat_timeout),
                    }

                    await self.worker_manager.initialize_worker(self.worker_id, worker_info)
                    await self.worker_manager.register_worker(self.worker_id)
                    logger.debug(f"Reinitialized worker {self.worker_id} with full info")

                elif publish_online_signal:
                    worker_data = {
                        'host': hostname,
                        'heartbeat_timeout': str(self.heartbeat_timeout),
                    }

                    logger.debug(f"Worker {self.worker_id} 准备调用 set_worker_online，worker_data={worker_data}")
                    await self.worker_manager.set_worker_online(self.worker_id, worker_data)
                    logger.debug(f"Worker {self.worker_id} set_worker_online 完成")
                    await self.worker_manager.register_worker(self.worker_id)
                    logger.debug(f"Worker {self.worker_id} is now ONLINE (heartbeat_timeout={self.heartbeat_timeout}s)")

                else:
                    heartbeat_data = {
                        'host': hostname
                    }
                    await self.worker_manager.update_worker_heartbeat(self.worker_id, heartbeat_data)

                self._last_heartbeat_time = current_time
                heartbeat_count += 1

                if heartbeat_count == 1:
                    self._first_heartbeat_done.set()
                    logger.debug(f"First heartbeat completed for worker {self.worker_id}, will continue every {self.interval}s")

                logger.debug(f"Heartbeat #{heartbeat_count} sent for worker {self.worker_id}, waiting {self.interval}s for next")

                if current_time - last_log_time >= 30:
                    logger.debug(f"Heartbeat task: sent {heartbeat_count} heartbeats for worker {self.worker_id} in last 30s")
                    last_log_time = current_time
                    heartbeat_count = 0

            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}", exc_info=True)
                if "Timeout connecting" in str(e) or "Connection" in str(e):
                    try:
                        await self.async_redis_client.aclose()
                    except:
                        pass
                    try:
                        if self.redis_url:
                            from jettask.db.connector import get_async_redis_client
                            self.async_redis_client = get_async_redis_client(
                                redis_url=self.redis_url,
                                decode_responses=True,
                            )
                            logger.debug(f"Reconnected to Redis for heartbeat task {self.worker_id}")
                    except Exception as reconnect_error:
                        logger.error(f"Failed to reconnect Redis: {reconnect_error}")
                await asyncio.sleep(5)

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                pass  

        logger.debug(f"Heartbeat task exiting for worker {self.worker_id}")

    def is_healthy(self) -> bool:
        if not self._heartbeat_task:
            return False

        if self._heartbeat_task.done():
            logger.error(f"Heartbeat task for worker {self.worker_id} is done")
            return False
        return True

    def get_last_heartbeat_time(self) -> Optional[float]:
        return self._last_heartbeat_time

    def is_heartbeat_timeout(self) -> bool:
        last_heartbeat = self.get_last_heartbeat_time()
        if last_heartbeat is None:
            return False

        current_time = time.time()
        return (current_time - last_heartbeat) > self.heartbeat_timeout


    @classmethod
    def start_global_timeout_scanner(cls, scan_interval: float, worker_manager: "WorkerManager"):
        cls._scanner_interval = scan_interval
        if cls._global_scanner_task and not cls._global_scanner_task.done():
            logger.warning("Global worker timeout scanner already running")
            return cls._global_scanner_task

        cls._global_worker_manager = worker_manager
        cls._global_scanner_stop_event = asyncio.Event()

        async def scanner_loop():
            logger.debug(f"Worker timeout scanner started (interval={cls._scanner_interval}s)")

            try:
                while not cls._global_scanner_stop_event.is_set():
                    try:
                        timeout_workers = await cls._global_worker_manager.scan_timeout_workers()

                        if timeout_workers:
                            logger.debug(f"Processing {len(timeout_workers)} timeout workers")

                            for worker_info in timeout_workers:
                                worker_id = worker_info['worker_id']
                                try:
                                    await cls._global_worker_manager.set_worker_offline(
                                        worker_id,
                                        reason="heartbeat_timeout"
                                    )
                                    logger.debug(f"Marked worker {worker_id} as offline due to timeout")
                                except Exception as e:
                                    logger.error(f"Error marking worker {worker_id} offline: {e}")

                        try:
                            await asyncio.wait_for(
                                cls._global_scanner_stop_event.wait(),
                                timeout=cls._scanner_interval
                            )
                        except asyncio.TimeoutError:
                            pass  

                    except Exception as e:
                        logger.error(f"Error in worker scanner loop: {e}", exc_info=True)
                        await asyncio.sleep(cls._scanner_interval)

            except asyncio.CancelledError:
                logger.debug("Worker timeout scanner cancelled")
                raise
            finally:
                logger.debug("Worker timeout scanner stopped")

        cls._global_scanner_task = asyncio.create_task(
            scanner_loop(),
            name="GlobalWorkerTimeoutScanner"
        )
        logger.debug("Global worker timeout scanner task created")
        return cls._global_scanner_task

    @classmethod
    async def stop_global_timeout_scanner(cls):
        if not cls._global_scanner_task:
            return

        logger.debug("Stopping global worker timeout scanner...")

        if cls._global_scanner_stop_event:
            cls._global_scanner_stop_event.set()

        if cls._global_scanner_task and not cls._global_scanner_task.done():
            cls._global_scanner_task.cancel()
            try:
                await cls._global_scanner_task
            except asyncio.CancelledError:
                pass

        cls._global_scanner_task = None
        cls._global_scanner_stop_event = None
        logger.debug("Global worker timeout scanner stopped")

    @classmethod
    def is_global_scanner_running(cls) -> bool:
        return cls._global_scanner_task is not None and not cls._global_scanner_task.done()


__all__ = ['HeartbeatManager']

