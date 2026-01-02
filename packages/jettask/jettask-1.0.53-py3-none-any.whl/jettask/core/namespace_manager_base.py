"""
命名空间管理器基类
为 Consumer 和 Scheduler 提供统一的命名空间管理逻辑
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from jettask.core.namespace import NamespaceManagerAPI, NamespaceContext

logger = logging.getLogger(__name__)


class NamespaceWorkerManagerBase(ABC):
    """
    命名空间工作器管理器基类

    提供统一的命名空间管理逻辑，子类只需实现具体的工作器运行逻辑。

    核心功能：
    1. 自动检测单/多命名空间模式
    2. 统一的命名空间配置获取
    3. 命名空间动态检测和管理
    4. 资源清理
    """

    def __init__(self,
                 task_center_url: str,
                 check_interval: int = 30,
                 debug: bool = False,
                 api_key: Optional[str] = None,
                 **kwargs):
        self.task_center_url = task_center_url.rstrip('/')
        self.check_interval = check_interval
        self.debug = debug
        self.api_key = api_key

        self.is_single_namespace, self.namespace_name = self._detect_mode()

        self.namespace_manager: Optional[NamespaceManagerAPI] = None

        self.running = False

        self._extra_params = kwargs

        logger.info(f"{self.__class__.__name__} 初始化完成")
        logger.info(f"  模式: {'单命名空间' if self.is_single_namespace else '多命名空间'}")
        if self.is_single_namespace:
            logger.info(f"  命名空间: {self.namespace_name}")
        logger.info(f"  任务中心: {self.task_center_url}")
        if self.api_key:
            logger.info(f"  鉴权: 已启用")

    def _detect_mode(self) -> tuple[bool, Optional[str]]:
        import re

        match = re.search(r'/api/task/v1/([^/]+)/?$', self.task_center_url)
        if match:
            namespace_name = match.group(1)
            logger.info(f"检测到单命名空间模式: {namespace_name}")
            return True, namespace_name

        logger.info("检测到多命名空间模式")
        return False, None

    def _get_base_url(self) -> str:
        if self.is_single_namespace:
            return self.task_center_url.rsplit('/api/task/v1/', 1)[0]

        url = self.task_center_url
        for suffix in ['/api/task/v1', '/api/task', '/api']:
            if url.endswith(suffix):
                url = url[:-len(suffix)]
                break

        return url

    @abstractmethod
    async def _run_worker_for_namespace(self, ns: NamespaceContext):
        pass

    @abstractmethod
    def _should_start_worker(self, ns: NamespaceContext) -> bool:
        pass

    @abstractmethod
    async def _start_worker(self, ns_or_name: Any):
        pass

    @abstractmethod
    async def _stop_worker(self, ns_name: str):
        pass

    @abstractmethod
    def _get_running_workers(self) -> set[str]:
        pass

    async def _namespace_check_loop(self):
        logger.info("命名空间检查循环已启动")

        while self.running:
            try:
                await self.namespace_manager.refresh()
                namespaces = await self.namespace_manager.list_namespaces(enabled_only=True)

                current_ns_map = {
                    ns.name: ns for ns in namespaces
                    if self._should_start_worker(ns)
                }
                current_namespaces = set(current_ns_map.keys())
                known_namespaces = self._get_running_workers()

                new_namespaces = current_namespaces - known_namespaces
                if new_namespaces:
                    logger.info(f"发现新命名空间: {new_namespaces}")
                    for ns_name in new_namespaces:
                        ns = current_ns_map[ns_name]
                        await self._start_worker(ns)

                removed_namespaces = known_namespaces - current_namespaces
                if removed_namespaces:
                    logger.info(f"命名空间已删除或禁用: {removed_namespaces}")
                    for ns_name in removed_namespaces:
                        await self._stop_worker(ns_name)

                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"命名空间检查循环异常: {e}", exc_info=self.debug)
                await asyncio.sleep(10)

    async def run(self):
        try:
            self.running = True

            base_url = self._get_base_url()
            self.namespace_manager = NamespaceManagerAPI(base_url, api_key=self.api_key)

            if self.is_single_namespace:
                logger.info(f"单命名空间模式: {self.namespace_name}")

                ns = await self.namespace_manager.get_namespace(self.namespace_name)

                await self._run_worker_for_namespace(ns)

            else:
                logger.info("多命名空间模式")
                logger.info(f"命名空间检测间隔: {self.check_interval}秒")

                await self.namespace_manager.refresh()
                namespaces = await self.namespace_manager.list_namespaces(enabled_only=True)

                for ns in namespaces:
                    if self._should_start_worker(ns):
                        await self._start_worker(ns)
                    else:
                        logger.warning(f"跳过命名空间 {ns.name}: 配置不满足要求")

                namespace_check_task = asyncio.create_task(self._namespace_check_loop())

                await namespace_check_task

        except KeyboardInterrupt:
            logger.info("收到中断信号，停止所有工作器...")
        except Exception as e:
            logger.error(f"运行错误: {e}", exc_info=self.debug)
            raise
        finally:
            self.running = False

            for ns_name in list(self._get_running_workers()):
                await self._stop_worker(ns_name)

            if self.namespace_manager:
                await self.namespace_manager.close()

            logger.info("所有工作器已停止")


__all__ = ['NamespaceWorkerManagerBase']
