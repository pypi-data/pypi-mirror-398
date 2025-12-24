"""
Namespace 中间件 - 自动注入命名空间上下文

这个中间件会自动检测路由中的 {namespace} 参数，并将 NamespaceContext 注入到 request.state.ns
这样所有路由都无需手动使用 Depends(get_namespace_context)，直接访问 request.state.ns 即可
"""
import asyncio
import logging
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Callable

from jettask.core.namespace import NamespaceManagerDB

logger = logging.getLogger(__name__)


class NamespaceMiddleware(BaseHTTPMiddleware):
    """
    Namespace 自动注入中间件

    功能：
    1. 自动检测路由路径中的 {namespace} 参数
    2. 使用 NamespaceManagerDB 查询命名空间配置
    3. 将 NamespaceContext 注入到 request.state.ns
    4. 统一处理命名空间不存在等错误

    使用方式：
    ```python
    # 在 app.py 中注册
    app.add_middleware(NamespaceMiddleware)

    # 在路由中使用
    @router.get("/{namespace}/queues")
    async def get_queues(request: Request):
        ns = request.state.ns  # 已自动注入 NamespaceContext
        redis_client = await ns.get_redis_client()
        # ... 业务逻辑
    ```
    """

    NAMESPACE_PATTERN = re.compile(r'/api/task/v1/([^/]+)')

    EXCLUDED_PATHS = (
        '/api/task/v1/namespaces',  
        '/docs',               
        '/openapi.json',       
        '/redoc',              
        '/health',             
    )

    NON_NAMESPACE_RESOURCES = frozenset(['namespaces', 'auth'])

    def __init__(self, app):
        super().__init__(app)
        self._manager = NamespaceManagerDB(auto_refresh=True, refresh_interval=60)
        logger.info("NamespaceMiddleware 初始化完成，使用 NamespaceManagerDB（自动刷新已启用，间隔60秒）")

        asyncio.create_task(self._preload_namespaces())

    async def _preload_namespaces(self):
        try:
            logger.info("开始预加载命名空间列表...")
            namespaces = await self._manager.list_namespaces()
            logger.info(f"命名空间预加载完成，共 {len(namespaces)} 个命名空间，自动刷新已启动")
        except Exception as e:
            logger.warning(f"命名空间预加载失败: {e}，将在第一次请求时重试")

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path

        if path.startswith(self.EXCLUDED_PATHS):
            return await call_next(request)

        namespace_match = self.NAMESPACE_PATTERN.search(path)

        if not namespace_match:
            return await call_next(request)

        namespace = namespace_match.group(1)

        if namespace in self.NON_NAMESPACE_RESOURCES:
            return await call_next(request)

        try:
            namespace_context = await self._manager.get_namespace(namespace)

            request.state.ns = namespace_context

            logger.debug(f"已为请求 {path} 注入命名空间上下文: {namespace}")

        except ValueError as e:
            logger.warning(f"命名空间 '{namespace}' 不存在: {e}")
            return JSONResponse(
                status_code=404,
                content={"detail": f"命名空间 '{namespace}' 不存在"}
            )
        except Exception as e:
            logger.error(f"获取命名空间 '{namespace}' 失败: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": f"获取命名空间失败: {str(e)}"}
            )

        response = await call_next(request)
        return response
