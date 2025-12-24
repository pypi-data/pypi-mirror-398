"""
统一的调度器管理器
基于 NamespaceWorkerManagerBase 实现
"""
import asyncio
import logging
from typing import Dict
from jettask.core.namespace_manager_base import NamespaceWorkerManagerBase
from jettask.core.namespace import NamespaceContext
from jettask.scheduler.scheduler import TaskScheduler

logger = logging.getLogger(__name__)


class UnifiedSchedulerManager(NamespaceWorkerManagerBase):
    """
    统一的调度器管理器

    基于 NamespaceWorkerManagerBase，专注于调度器特定的逻辑
    """

    def __init__(self,
                 task_center_url: str,
                 scan_interval: float = 1.0,
                 batch_size: int = 100,
                 lookahead_seconds: int = 3600,
                 check_interval: int = 30,
                 api_key: str = None,
                 debug: bool = False):
        self.scan_interval = scan_interval
        self.batch_size = batch_size
        self.lookahead_seconds = lookahead_seconds

        self.scheduler_tasks: Dict[str, asyncio.Task] = {}
        self.schedulers: Dict[str, TaskScheduler] = {}

        super().__init__(task_center_url, check_interval, debug, api_key=api_key)

        logger.info(f"扫描间隔: {self.scan_interval}秒")
        logger.info(f"批次大小: {self.batch_size}")
        logger.info(f"提前查看: {self.lookahead_seconds}秒")

    async def _run_worker_for_namespace(self, ns: NamespaceContext):
        logger.info(f"启动命名空间 {ns.name} 的调度器")

        try:
            jettask_app = await ns.get_jettask_app()

            logger.info(f"命名空间 {ns.name} 配置:")
            logger.info(f"  - Redis: 已配置")
            logger.info(f"  - PostgreSQL: 已配置")
            logger.info(f"  - Redis Prefix: {ns.redis_prefix}")

            scheduler = TaskScheduler(
                app=jettask_app,
                db_url=ns.pg_config['url'],
                scan_interval=self.scan_interval,
                batch_size=self.batch_size,
                lookahead_seconds=self.lookahead_seconds
            )

            self.schedulers[ns.name] = scheduler

            logger.info(f"✓ 调度器已创建: {ns.name}")

            await scheduler.start(wait=True)

        except asyncio.CancelledError:
            logger.info(f"调度器被取消: {ns.name}")
            raise
        except Exception as e:
            logger.error(f"命名空间 {ns.name} 调度器运行失败: {e}", exc_info=self.debug)
            raise
        finally:
            if ns.name in self.schedulers:
                scheduler = self.schedulers[ns.name]
                await scheduler.stop()
                del self.schedulers[ns.name]
                logger.info(f"调度器已停止: {ns.name}")

    def _should_start_worker(self, ns: NamespaceContext) -> bool:
        return ns.has_pg and ns.has_redis

    async def _start_worker(self, ns_or_name):
        ns = ns_or_name

        if ns.name in self.scheduler_tasks:
            task = self.scheduler_tasks[ns.name]
            if not task.done():
                logger.debug(f"命名空间 {ns.name} 的调度器任务已在运行")
                return
            else:
                try:
                    task.result()
                except Exception as e:
                    logger.error(f"命名空间 {ns.name} 的调度器任务异常退出: {e}")

        logger.info(f"启动命名空间 {ns.name} 的调度器任务")

        task = asyncio.create_task(
            self._run_worker_for_namespace(ns),
            name=f"Scheduler-{ns.name}"
        )
        self.scheduler_tasks[ns.name] = task

        logger.info(f"✓ 调度器任务已启动: {ns.name}")

    async def _stop_worker(self, ns_name: str):
        if ns_name in self.scheduler_tasks:
            task = self.scheduler_tasks[ns_name]
            logger.info(f"停止调度器任务: {ns_name}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.scheduler_tasks[ns_name]

        if ns_name in self.schedulers:
            scheduler = self.schedulers[ns_name]
            logger.info(f"停止调度器实例: {ns_name}")
            await scheduler.stop()
            del self.schedulers[ns_name]

    def _get_running_workers(self) -> set[str]:
        return set(self.scheduler_tasks.keys())


__all__ = ['UnifiedSchedulerManager']
