"""
命名空间依赖注入工具
提供统一的命名空间参数处理和数据库连接管理
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Path, Request
from jettask.namespace import NamespaceConnection, NamespaceDataAccessManager

logger = logging.getLogger(__name__)


class NamespaceContext:
    """
    命名空间上下文对象
    封装命名空间的所有信息和数据库连接
    """

    def __init__(
        self,
        namespace_name: str,
        connection: NamespaceConnection,
        manager: NamespaceDataAccessManager
    ):
        self.namespace_name = namespace_name
        self.connection = connection
        self.manager = manager

    async def get_redis_client(self, decode: bool = True):
        return await self.connection.get_redis_client(decode=decode)

    async def get_pg_session(self):
        return await self.connection.get_pg_session()

    @property
    def redis_prefix(self) -> str:
        return self.connection.redis_prefix

    @property
    def redis_config(self) -> dict:
        return self.connection.redis_config

    @property
    def pg_config(self) -> dict:
        return self.connection.pg_config


def get_namespace_manager(request: Request) -> NamespaceDataAccessManager:
    if not hasattr(request.app.state, 'namespace_data_access'):
        raise HTTPException(
            status_code=500,
            detail="Namespace data access not initialized"
        )

    return request.app.state.namespace_data_access.manager


async def get_namespace_context(
    namespace: str = Path(..., description="命名空间名称", example="default"),
    manager: NamespaceDataAccessManager = Depends(get_namespace_manager)
) -> NamespaceContext:
    try:
        connection = await manager.get_connection(namespace)

        return NamespaceContext(
            namespace_name=namespace,
            connection=connection,
            manager=manager
        )

    except ValueError as e:
        logger.error(f"命名空间 '{namespace}' 配置错误: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"命名空间 '{namespace}' 不存在或配置错误"
        )
    except Exception as e:
        logger.error(f"获取命名空间 '{namespace}' 上下文失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取命名空间连接失败: {str(e)}"
        )


async def get_namespace_connection(
    namespace: str = Path(..., description="命名空间名称", example="default"),
    manager: NamespaceDataAccessManager = Depends(get_namespace_manager)
) -> NamespaceConnection:
    try:
        return await manager.get_connection(namespace)
    except ValueError as e:
        logger.error(f"命名空间 '{namespace}' 配置错误: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"命名空间 '{namespace}' 不存在或配置错误"
        )
    except Exception as e:
        logger.error(f"获取命名空间 '{namespace}' 连接失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取命名空间连接失败: {str(e)}"
        )


__all__ = [
    'NamespaceContext',
    'get_namespace_context',
    'get_namespace_connection',
    'get_namespace_manager'
]
