"""
命名空间上下文 - 简洁的命名空间管理类
"""
import asyncio
import logging
import os
import sys
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker
from jettask.core.center_client import TaskCenterClient
from jettask.db.connector import (
    get_dual_mode_async_redis_client,
    get_pg_engine_and_factory
)
from jettask.config.nacos_config import config as nacos_config

if TYPE_CHECKING:
    from jettask.webui.services.namespace_service import NamespaceService


log_format = os.environ.get('JETTASK_LOG_FORMAT', 'text').lower()
log_level = logging.INFO

logger = logging.getLogger(__name__)

from jettask.utils.task_logger import JSONFormatter, ExtendedTextFormatter, TaskContextFilter

logger.handlers.clear()
logger.setLevel(log_level)

handler = logging.StreamHandler(sys.stderr)
handler.addFilter(TaskContextFilter())

if log_format == 'json':
    handler.setFormatter(JSONFormatter())
else:
    handler.setFormatter(ExtendedTextFormatter(
        '%(asctime)s - %(levelname)s - [%(task_id)s] - %(name)s - %(message)s'
    ))

logger.addHandler(handler)
logger.propagate = False  


class NamespaceContext:
    """
    命名空间上下文 - 管理命名空间的数据库连接和相关信息

    简洁的设计，专注于连接管理和基本信息维护
    """

    def __init__(
        self,
        pg_info: Dict[str, Any],
        redis_info: Dict[str, Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[int] = None,
        enabled: bool = True,
        connection_url: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        **kwargs
    ):
        self.name = name
        self.description = description
        self.version = version
        self.enabled = enabled
        self.connection_url = connection_url
        self.created_at = created_at
        self.updated_at = updated_at

        self.pg_info = pg_info
        self.redis_info = redis_info

        self.extra_info = kwargs

        self._redis_text_client: Optional[redis.Redis] = None
        self._redis_binary_client: Optional[redis.Redis] = None
        self._pg_engine: Optional[AsyncEngine] = None
        self._pg_session_factory: Optional[async_sessionmaker] = None

        self._jettask_app: Optional['Jettask'] = None

        self._queue_registry: Optional['QueueRegistry'] = None

        self._redis_initialized = False
        self._pg_initialized = False
        self._jettask_initialized = False
        self._queue_registry_initialized = False

    @classmethod
    def from_flat_dict(cls, data: Dict[str, Any]) -> 'NamespaceContext':
        pg_info = {
            'url': data.get('pg_url'),
            'config_mode': data.get('pg_config_mode', 'direct'),
            'nacos_key': data.get('pg_nacos_key')
        }

        redis_info = {
            'url': data.get('redis_url'),
            'config_mode': data.get('redis_config_mode', 'direct'),
            'nacos_key': data.get('redis_nacos_key'),
            'prefix': data.get('redis_prefix')  
        }

        return cls(
            pg_info=pg_info,
            redis_info=redis_info,
            name=data.get('name'),
            description=data.get('description'),
            version=data.get('version'),
            enabled=data.get('enabled', True),
            connection_url=data.get('connection_url'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def _resolve_config_url(self, config_info: Dict[str, Any], config_type: str) -> Optional[str]:
        if not config_info:
            logger.debug(f"Namespace {self.name} has no {config_type} configuration")
            return None

        config_mode = config_info.get('config_mode', 'direct')

        if config_mode == 'direct':
            url = config_info.get('url')
            if url:
                logger.debug(f"Namespace {self.name} {config_type} using direct mode: {url}")
                return url
            else:
                logger.warning(f"Namespace {self.name} {config_type} config_mode is 'direct' but no URL provided")
                return None

        elif config_mode == 'nacos':
            nacos_key = config_info.get('nacos_key')
            if not nacos_key:
                logger.warning(f"Namespace {self.name} {config_type} config_mode is 'nacos' but no nacos_key provided")
                return None

            try:
                logger.debug(f"Namespace {self.name} {config_type} fetching URL from Nacos with key: {nacos_key}")
                url = nacos_config.get(nacos_key)
                if url:
                    logger.info(f"Namespace {self.name} {config_type} successfully fetched from Nacos: {nacos_key}")
                    return url
                else:
                    logger.warning(f"Namespace {self.name} {config_type} Nacos key '{nacos_key}' returned empty value")
                    return None
            except Exception as e:
                logger.error(f"Namespace {self.name} failed to fetch {config_type} URL from Nacos (key: {nacos_key}): {e}", exc_info=True)
                return None

        else:
            logger.error(f"Namespace {self.name} {config_type} unknown config_mode: {config_mode}")
            return None

    async def _initialize_redis(self):
        if self._redis_initialized:
            logger.debug(f"Namespace {self.name} Redis already initialized, skipping")
            return

        try:
            redis_url = self._resolve_config_url(self.redis_info, 'Redis')
            if redis_url:
                logger.debug(f"Lazy-loading Redis connection for namespace {self.name}")
                self._redis_text_client, self._redis_binary_client = get_dual_mode_async_redis_client(
                    redis_url=redis_url,
                    max_connections=50
                )
                logger.info(f"Namespace {self.name} Redis connection initialized successfully")
            else:
                logger.debug(f"Namespace {self.name} has no valid Redis configuration")

            self._redis_initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize Redis for namespace {self.name}: {e}", exc_info=True)
            raise

    async def _initialize_pg(self):
        if self._pg_initialized:
            logger.debug(f"Namespace {self.name} PostgreSQL already initialized, skipping")
            return

        try:
            pg_url = self._resolve_config_url(self.pg_info, 'PostgreSQL')
            if pg_url:
                if pg_url.startswith('postgresql://'):
                    pg_url = pg_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

                logger.debug(f"Lazy-loading PostgreSQL connection for namespace {self.name}")
                self._pg_engine, self._pg_session_factory = get_pg_engine_and_factory(
                    dsn=pg_url,
                    pool_size=10,
                    max_overflow=5,
                    pool_recycle=3600,
                    echo=False
                )
                logger.info(f"Namespace {self.name} PostgreSQL connection initialized successfully")
            else:
                logger.debug(f"Namespace {self.name} has no valid PostgreSQL configuration")

            self._pg_initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL for namespace {self.name}: {e}", exc_info=True)
            raise

    async def get_redis_client(self, decode: bool = True) -> redis.Redis:
        if not self._redis_initialized:
            await self._initialize_redis()

        client = self._redis_text_client if decode else self._redis_binary_client
        if not client:
            raise ValueError(f"Namespace {self.name} has no Redis configuration")

        return client

    async def get_pg_session(self) -> AsyncSession:
        if not self._pg_initialized:
            await self._initialize_pg()

        if not self._pg_session_factory:
            raise ValueError(f"Namespace {self.name} has no PostgreSQL configuration")

        return self._pg_session_factory()

    @property
    def redis_prefix(self) -> str:
        prefix = self.redis_info.get('prefix') if self.redis_info else None
        return prefix or self.name or 'jettask'

    @property
    def redis_config(self) -> Dict[str, Any]:
        return {
            'url': self._resolve_config_url(self.redis_info, 'Redis'),
            'prefix': self.redis_prefix
        }

    @property
    def pg_config(self) -> Dict[str, Any]:
        return {
            'url': self._resolve_config_url(self.pg_info, 'PostgreSQL')
        }

    async def get_jettask_app(self) -> 'Jettask':
        if self._jettask_initialized and self._jettask_app:
            logger.debug(f"Namespace {self.name} Jettask already initialized, reusing instance")
            return self._jettask_app

        try:
            redis_url = self._resolve_config_url(self.redis_info, 'Redis')
            pg_url = self._resolve_config_url(self.pg_info, 'PostgreSQL')

            if not redis_url:
                raise ValueError(f"Namespace {self.name} has no Redis configuration")
            if not pg_url:
                raise ValueError(f"Namespace {self.name} has no PostgreSQL configuration")

            from jettask import Jettask

            logger.info(f"Creating Jettask instance for namespace {self.name}")
            logger.debug(f"  Redis URL: {redis_url}")
            logger.debug(f"  Redis Prefix: {self.redis_prefix}")
            logger.debug(f"  PG URL: {pg_url[:50]}...")

            self._jettask_app = Jettask(
                redis_url=redis_url,
                redis_prefix=self.redis_prefix,
                pg_url=pg_url
            )

            self._jettask_initialized = True
            logger.info(f"Namespace {self.name} Jettask instance created successfully")

            return self._jettask_app

        except Exception as e:
            logger.error(f"Failed to create Jettask instance for namespace {self.name}: {e}", exc_info=True)
            raise

    async def get_queue_registry(self) -> 'QueueRegistry':
        if self._queue_registry_initialized and self._queue_registry:
            logger.debug(f"Namespace {self.name} QueueRegistry already initialized, reusing instance")
            return self._queue_registry

        try:
            if not self._redis_initialized:
                await self._initialize_redis()

            if not self._redis_binary_client or not self._redis_text_client:
                raise ValueError(f"Namespace {self.name} has no Redis configuration")

            from jettask.messaging.registry import QueueRegistry

            logger.info(f"Creating QueueRegistry instance for namespace {self.name}")
            logger.debug(f"  Redis Prefix: {self.redis_prefix}")

            self._queue_registry = QueueRegistry(
                redis_client=self._redis_binary_client,  
                async_redis_client=self._redis_text_client,  
                redis_prefix=self.redis_prefix
            )

            self._queue_registry_initialized = True
            logger.info(f"Namespace {self.name} QueueRegistry instance created successfully")

            return self._queue_registry

        except Exception as e:
            logger.error(f"Failed to create QueueRegistry instance for namespace {self.name}: {e}", exc_info=True)
            raise

    @property
    def is_initialized(self) -> bool:
        return self._redis_initialized or self._pg_initialized

    @property
    def has_redis(self) -> bool:
        if not self.redis_info:
            return False
        if self.redis_info.get('config_mode') == 'direct':
            return bool(self.redis_info.get('url'))
        elif self.redis_info.get('config_mode') == 'nacos':
            return bool(self.redis_info.get('nacos_key'))
        return False

    @property
    def has_pg(self) -> bool:
        if not self.pg_info:
            return False
        if self.pg_info.get('config_mode') == 'direct':
            return bool(self.pg_info.get('url'))
        elif self.pg_info.get('config_mode') == 'nacos':
            return bool(self.pg_info.get('nacos_key'))
        return False

    async def close(self):
        if not self.is_initialized:
            return

        logger.debug(f"Closing namespace {self.name} connections")

        self._redis_text_client = None
        self._redis_binary_client = None
        self._pg_engine = None
        self._pg_session_factory = None
        self._jettask_app = None
        self._queue_registry = None

        self._redis_initialized = False
        self._pg_initialized = False
        self._jettask_initialized = False
        self._queue_registry_initialized = False

        logger.info(f"Namespace {self.name} closed")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'enabled': self.enabled,
            'connection_url': self.connection_url,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'pg_info': self.pg_info,
            'redis_info': self.redis_info,
            'redis_prefix': self.redis_prefix,
            'is_initialized': self.is_initialized,
            'redis_initialized': self._redis_initialized,
            'pg_initialized': self._pg_initialized,
            'jettask_initialized': self._jettask_initialized,
            'queue_registry_initialized': self._queue_registry_initialized,
            'has_redis': self.has_redis,
            'has_pg': self.has_pg,
            **self.extra_info
        }

    def __repr__(self) -> str:
        redis_mark = 'YES' if self.has_redis else 'NO'
        pg_mark = 'YES' if self.has_pg else 'NO'
        redis_init = 'INIT' if self._redis_initialized else 'LAZY'
        pg_init = 'INIT' if self._pg_initialized else 'LAZY'
        return (
            f"<NamespaceContext "
            f"name='{self.name}' "
            f"version={self.version} "
            f"redis={redis_mark}({redis_init}) "
            f"pg={pg_mark}({pg_init}) "
            f"enabled={self.enabled}>"
        )

class BaseNamespaceManager:
    """
    命名空间管理器基类

    提供命名空间管理的通用功能，子类只需实现数据加载逻辑。
    """

    def __init__(self, auto_refresh: bool = True, refresh_interval: int = 60):
        self._contexts: Dict[str, NamespaceContext] = {}
        self._initialized = False
        self._refresh_interval = refresh_interval
        self._refresh_task: Optional[asyncio.Task] = None
        self._auto_refresh_enabled = auto_refresh
        self._closed = False

    async def _ensure_loaded(self):
        if not self._initialized:
            await self.refresh()
            if self._auto_refresh_enabled and self._refresh_task is None:
                self.start_auto_refresh()

    async def refresh(self):
        raise NotImplementedError("子类必须实现 refresh() 方法")

    async def get_namespace(self, name: str) -> NamespaceContext:
        await self._ensure_loaded()

        if name not in self._contexts:
            logger.error(f"命名空间 '{name}' 不存在")
            raise ValueError(f"命名空间 '{name}' 不存在")

        return self._contexts[name]

    async def list_namespaces(self, enabled_only: bool = False) -> List[NamespaceContext]:
        await self._ensure_loaded()

        contexts = list(self._contexts.values())

        if enabled_only:
            contexts = [ctx for ctx in contexts if ctx.enabled]

        logger.debug(f"列出 {len(contexts)} 个命名空间（enabled_only={enabled_only}）")
        return contexts

    async def get_namespace_names(self, enabled_only: bool = False) -> List[str]:
        await self._ensure_loaded()

        if enabled_only:
            names = [name for name, ctx in self._contexts.items() if ctx.enabled]
        else:
            names = list(self._contexts.keys())

        logger.debug(f"获取 {len(names)} 个命名空间名称（enabled_only={enabled_only}）")
        return names

    def start_auto_refresh(self):
        if self._refresh_task is not None:
            logger.warning("定时刷新任务已在运行，跳过启动")
            return

        if self._closed:
            logger.warning("管理器已关闭，无法启动定时刷新")
            return

        logger.info(f"启动命名空间定时刷新任务，间隔: {self._refresh_interval}秒")
        self._refresh_task = asyncio.create_task(self._auto_refresh_loop())

    def stop_auto_refresh(self):
        if self._refresh_task is not None:
            logger.info("停止命名空间定时刷新任务")
            self._refresh_task.cancel()
            self._refresh_task = None

    async def _auto_refresh_loop(self):
        logger.info(f"定时刷新循环已启动，刷新间隔: {self._refresh_interval}秒")

        try:
            while not self._closed:
                await asyncio.sleep(self._refresh_interval)

                if self._closed:
                    break

                try:
                    logger.debug("执行定时刷新命名空间列表...")
                    await self.refresh()
                    logger.debug("定时刷新命名空间列表完成")
                except Exception as e:
                    logger.error(f"定时刷新命名空间失败: {e}", exc_info=True)

        except asyncio.CancelledError:
            logger.info("定时刷新任务被取消")
        except Exception as e:
            logger.error(f"定时刷新循环异常退出: {e}", exc_info=True)
        finally:
            logger.info("定时刷新循环已结束")

    def _clear_contexts(self):
        self._contexts.clear()
        self._initialized = False

    async def _close_contexts(self):
        for ctx in self._contexts.values():
            if ctx.is_initialized:
                await ctx.close()

    async def close(self):
        logger.info(f"关闭命名空间管理器: {len(self._contexts)} 个命名空间")

        self._closed = True

        self.stop_auto_refresh()

        if self._refresh_task is not None:
            try:
                await asyncio.wait_for(self._refresh_task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                logger.debug("定时刷新任务已取消或超时")

        await self._close_contexts()
        self._clear_contexts()

        logger.info("命名空间管理器已关闭")

    async def __aenter__(self):
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        await self.close()


class NamespaceManagerAPI(BaseNamespaceManager):
    """
    基于 API 的多命名空间管理器

    通过 TaskCenterClient 从 API 获取命名空间数据，并管理多个 NamespaceContext 实例。
    适合客户端或远程调用场景。

    特点：
    - 通过 HTTP API 获取命名空间配置
    - 自动创建和缓存 NamespaceContext 实例
    - 支持懒加载：只有在访问时才创建上下文
    - 支持刷新：可以重新从 API 加载最新配置
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None, auto_refresh: bool = True, refresh_interval: int = 60):
        super().__init__(auto_refresh=auto_refresh, refresh_interval=refresh_interval)


        self.base_url = base_url
        self._client = TaskCenterClient(base_url, api_key=api_key)

        logger.info(f"NamespaceManagerAPI 初始化: base_url={base_url}")
        if api_key:
            logger.info("API 密钥已配置")

    async def refresh(self):

        try:
            namespace_list = await self._client.get_namespace_list(page_size=100)

            old_contexts = self._contexts
            self._contexts = {}

            for ns_data in namespace_list:
                name = ns_data.get('name')
                if name:
                    ctx = NamespaceContext.from_flat_dict(ns_data)
                    self._contexts[name] = ctx
                    logger.debug(f"创建命名空间上下文: {name}")

            for old_ctx in old_contexts.values():
                if old_ctx.is_initialized:
                    await old_ctx.close()

            self._initialized = True
            logger.debug(f"成功从 API 刷新 {len(self._contexts)} 个命名空间")

        except Exception as e:
            logger.error(f"从 API 刷新命名空间失败: {e}", exc_info=True)
            raise

    async def close(self):
        logger.info(f"关闭 NamespaceManagerAPI: {len(self._contexts)} 个命名空间")

        await self._close_contexts()

        await self._client.close()

        self._clear_contexts()

        logger.info("NamespaceManagerAPI 已关闭")

    def __repr__(self) -> str:
        return (
            f"<NamespaceManagerAPI "
            f"base_url='{self.base_url}' "
            f"namespaces={len(self._contexts)} "
            f"initialized={self._initialized}>"
        )


class NamespaceManagerDB(BaseNamespaceManager):
    """
    基于数据库的多命名空间管理器

    通过 NamespaceService 直接从数据库读取命名空间数据，并管理多个 NamespaceContext 实例。
    适合服务端或有直接数据库访问权限的场景。

    特点：
    - 直接从数据库读取命名空间配置（不经过 API）
    - 自动创建和缓存 NamespaceContext 实例
    - 支持懒加载：只有在访问时才创建上下文
    - 支持刷新：可以重新从数据库加载最新配置
    """

    def __init__(self, auto_refresh: bool = True, refresh_interval: int = 60):
        super().__init__(auto_refresh=auto_refresh, refresh_interval=refresh_interval)
        logger.info("NamespaceManagerDB 初始化")

    async def refresh(self):
        logger.info("从数据库刷新命名空间列表")

        try:
            from jettask.webui.services.namespace_service import NamespaceService
            from jettask.webui.config import webui_config
            from jettask.db.connector import get_pg_engine_and_factory

            _, session_factory = get_pg_engine_and_factory(webui_config.meta_database_url)

            async with session_factory() as session:
                namespace_list = await NamespaceService.list_namespaces(session, page=1, page_size=1000)

            old_contexts = self._contexts
            self._contexts = {}

            for ns in namespace_list:
                name = ns.name
                if name:
                    ns_data = {
                        'name': ns.name,
                        'description': ns.description,
                        'redis_url': ns.redis_url,
                        'redis_config_mode': ns.redis_config_mode,
                        'redis_nacos_key': ns.redis_nacos_key,
                        'pg_url': ns.pg_url,
                        'pg_config_mode': ns.pg_config_mode,
                        'pg_nacos_key': ns.pg_nacos_key,
                        'connection_url': ns.connection_url,
                        'version': ns.version,
                        'enabled': ns.enabled,
                        'created_at': ns.created_at,
                        'updated_at': ns.updated_at
                    }

                    ctx = NamespaceContext.from_flat_dict(ns_data)
                    self._contexts[name] = ctx
                    logger.debug(f"创建命名空间上下文: {name}")

            for old_ctx in old_contexts.values():
                if old_ctx.is_initialized:
                    await old_ctx.close()

            self._initialized = True
            logger.info(f"成功从数据库刷新 {len(self._contexts)} 个命名空间")

        except Exception as e:
            logger.error(f"从数据库刷新命名空间失败: {e}", exc_info=True)
            raise

    def __repr__(self) -> str:
        return (
            f"<NamespaceManagerDB "
            f"namespaces={len(self._contexts)} "
            f"initialized={self._initialized}>"
        )


