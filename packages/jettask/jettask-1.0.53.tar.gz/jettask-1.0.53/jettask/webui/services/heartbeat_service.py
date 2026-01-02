"""
心跳监控服务

提供 Worker 心跳检查和自动离线标记功能
"""
import asyncio
import logging
import time
from typing import Optional

from .redis_monitor_service import RedisMonitorService

logger = logging.getLogger(__name__)


class HeartbeatService:
    """心跳监控服务类"""

    def __init__(self, redis_service: RedisMonitorService, scanner_interval: int = 5, heartbeat_timeout: int = 30):
        self.redis_service = redis_service
        self.scanner_interval = scanner_interval
        self.default_heartbeat_timeout = heartbeat_timeout

        self.scanner_task: Optional[asyncio.Task] = None
        self._scanner_running = False

    @property
    def redis(self):
        return self.redis_service.redis

    @property
    def redis_prefix(self) -> str:
        return self.redis_service.redis_prefix

    @property
    def worker_state_manager(self):
        return self.redis_service.worker_state_manager

    async def start_heartbeat_scanner(self):
        if not self._scanner_running:
            self._scanner_running = True
            self.scanner_task = asyncio.create_task(self._heartbeat_scanner())
            logger.info("心跳扫描器任务已创建并启动")
        else:
            logger.warning("心跳扫描器已经在运行中")

    async def stop_heartbeat_scanner(self):
        self._scanner_running = False
        if self.scanner_task and not self.scanner_task.done():
            self.scanner_task.cancel()
            try:
                await self.scanner_task
            except asyncio.CancelledError:
                logger.info("心跳扫描器已取消")
                pass
            logger.info("心跳扫描器已停止")

    async def _heartbeat_scanner(self):
        logger.info(f"心跳扫描器启动 (扫描间隔: {self.scanner_interval}s, 超时阈值: {self.default_heartbeat_timeout}s)")

        while self._scanner_running:
            try:
                from jettask.worker.lifecycle import WorkerManager

                worker_manager = WorkerManager(
                    redis_client=self.redis,
                    redis_prefix=self.redis_prefix
                )

                worker_ids = await worker_manager.get_all_workers()

                if worker_ids:
                    current_time = time.time()
                    logger.debug(f"检查 {len(worker_ids)} 个 Worker 的心跳状态")

                    all_workers_info = await worker_manager.get_all_workers_info(only_alive=False)

                    offline_count = 0
                    for worker_id in worker_ids:
                        worker_data = all_workers_info.get(worker_id)
                        if not worker_data:
                            continue

                        try:
                            last_heartbeat = float(worker_data.get('last_heartbeat', 0))
                            is_alive = worker_data.get('is_alive') == 'true'
                            heartbeat_timeout = float(
                                worker_data.get('heartbeat_timeout', self.default_heartbeat_timeout)
                            )
                            consumer_id = worker_data.get('consumer_id', worker_id)

                            heartbeat_age = current_time - last_heartbeat
                            if is_alive and heartbeat_age > heartbeat_timeout:
                                logger.info(
                                    f"Worker {consumer_id} 心跳超时 ({heartbeat_age:.1f}s > {heartbeat_timeout}s)，标记为离线"
                                )

                                await worker_manager.set_worker_offline(
                                    worker_id=worker_id,
                                    reason="heartbeat_timeout"
                                )
                                offline_count += 1

                        except Exception as e:
                            logger.error(f"检查 worker {worker_id} 心跳时出错: {e}", exc_info=True)

                    if offline_count > 0:
                        logger.info(f"本次扫描标记了 {offline_count} 个 Worker 为离线")

                await asyncio.sleep(self.scanner_interval)

            except asyncio.CancelledError:
                logger.info("心跳扫描器收到取消信号")
                break
            except Exception as e:
                logger.error(f"心跳扫描器出错: {e}", exc_info=True)
                await asyncio.sleep(self.scanner_interval)

        logger.info("心跳扫描器已停止运行")

    async def check_worker_heartbeat(self, worker_id: str) -> bool:
        try:
            worker_key = f"{self.redis_prefix}:WORKER:{worker_id}"
            worker_data = await self.redis.hgetall(worker_key)

            if not worker_data:
                logger.warning(f"Worker {worker_id} 不存在")
                return False

            last_heartbeat = float(worker_data.get('last_heartbeat', 0))
            is_alive = worker_data.get('is_alive', 'true').lower() == 'true'
            heartbeat_timeout = float(worker_data.get('heartbeat_timeout', self.default_heartbeat_timeout))

            current_time = time.time()
            heartbeat_age = current_time - last_heartbeat

            return is_alive and heartbeat_age <= heartbeat_timeout

        except Exception as e:
            logger.error(f"检查 worker {worker_id} 心跳状态时出错: {e}", exc_info=True)
            return False

    async def get_heartbeat_stats(self) -> dict:
        try:
            from jettask.worker.lifecycle import WorkerManager

            worker_manager = WorkerManager(
                redis_client=self.redis,
                redis_prefix=self.redis_prefix
            )

            worker_ids = await worker_manager.get_all_workers()

            if not worker_ids:
                return {
                    'total_workers': 0,
                    'online_workers': 0,
                    'timeout_workers': 0,
                    'offline_workers': 0
                }

            all_workers_info = await worker_manager.get_all_workers_info(only_alive=False)

            current_time = time.time()
            online_count = 0
            timeout_count = 0
            offline_count = 0

            for worker_id in worker_ids:
                worker_data = all_workers_info.get(worker_id)
                if not worker_data:
                    continue

                last_heartbeat = float(worker_data.get('last_heartbeat', 0))
                is_alive = worker_data.get('is_alive') == 'true'
                heartbeat_timeout = float(worker_data.get('heartbeat_timeout', self.default_heartbeat_timeout))

                heartbeat_age = current_time - last_heartbeat

                if not is_alive:
                    offline_count += 1
                elif heartbeat_age > heartbeat_timeout:
                    timeout_count += 1
                else:
                    online_count += 1

            return {
                'total_workers': len(worker_ids),
                'online_workers': online_count,
                'timeout_workers': timeout_count,
                'offline_workers': offline_count,
                'scanner_running': self._scanner_running,
                'scanner_interval': self.scanner_interval,
                'heartbeat_timeout': self.default_heartbeat_timeout
            }

        except Exception as e:
            logger.error(f"获取心跳统计信息时出错: {e}", exc_info=True)
            return {
                'total_workers': 0,
                'online_workers': 0,
                'timeout_workers': 0,
                'offline_workers': 0,
                'error': str(e)
            }
