"""
命名空间服务

提供命名空间的完整管理功能，包括增删改查、激活/停用、统计等
使用 SQLAlchemy ORM 操作数据库
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from jettask.db.models import Namespace
from jettask.schemas import (
    ConfigMode,
    NamespaceCreate,
    NamespaceUpdate,
    NamespaceResponse
)

logger = logging.getLogger(__name__)


class NamespaceService:
    """命名空间服务类 - 提供命名空间的所有管理功能"""

    @staticmethod
    def validate_redis_url(redis_url: str) -> bool:
        try:
            parsed = urlparse(redis_url)
            return parsed.scheme in ['redis', 'rediss']
        except Exception:
            return False

    @staticmethod
    def validate_pg_url(pg_url: str) -> bool:
        try:
            parsed = urlparse(pg_url)
            return parsed.scheme in ['postgresql', 'postgres', 'postgresql+asyncpg']
        except Exception:
            return False

    @staticmethod
    def mask_url_password(url: str) -> str:
        try:
            parsed = urlparse(url)
            if parsed.password:
                if parsed.username:
                    netloc = f"{parsed.username}:***@{parsed.hostname}"
                else:
                    netloc = f":***@{parsed.hostname}"

                if parsed.port:
                    netloc += f":{parsed.port}"

                masked_url = f"{parsed.scheme}://{netloc}{parsed.path}"
                if parsed.query:
                    masked_url += f"?{parsed.query}"
                if parsed.fragment:
                    masked_url += f"#{parsed.fragment}"

                return masked_url
            return url
        except Exception:
            return url

    @staticmethod
    async def get_config_from_nacos(key: str) -> str:
        try:
            from jettask.config.nacos_config import config
            value = config.config.get(key)
            if not value:
                raise ValueError(f"Nacos配置键 '{key}' 不存在或为空")
            return value
        except ImportError:
            raise ValueError("无法加载Nacos配置模块")
        except Exception as e:
            raise ValueError(f"从Nacos获取配置失败: {str(e)}")

    @staticmethod
    def _build_namespace_response(ns: Namespace) -> NamespaceResponse:
        redis_config_dict = ns.redis_config if ns.redis_config else {}
        pg_config_dict = ns.pg_config if ns.pg_config else {}

        redis_config_mode = redis_config_dict.get('config_mode', 'direct')
        pg_config_mode = pg_config_dict.get('config_mode', 'direct')

        if redis_config_mode == 'nacos':
            redis_url = None
            redis_nacos_key = redis_config_dict.get('nacos_key')
            logger.debug(f"命名空间 {ns.name} 使用 Nacos 模式，返回 Redis key: {redis_nacos_key}")
        else:
            redis_url = redis_config_dict.get('url', '')
            redis_nacos_key = None
            logger.debug(f"命名空间 {ns.name} 使用 Direct 模式，返回真实 Redis URL")

        if pg_config_mode == 'nacos':
            pg_url = None
            pg_nacos_key = pg_config_dict.get('nacos_key')
            logger.debug(f"命名空间 {ns.name} 使用 Nacos 模式，返回 PG key: {pg_nacos_key}")
        else:
            pg_url = pg_config_dict.get('url')
            pg_nacos_key = None
            if pg_url:
                logger.debug(f"命名空间 {ns.name} 使用 Direct 模式，返回真实 PG URL")

        return NamespaceResponse(
            name=ns.name,
            description=ns.description,
            redis_url=redis_url,
            redis_config_mode=redis_config_mode,
            redis_nacos_key=redis_nacos_key,
            pg_url=pg_url,
            pg_config_mode=pg_config_mode,
            pg_nacos_key=pg_nacos_key,
            connection_url=f"/api/v1/namespaces/{ns.name}",
            version=ns.version or 1,
            enabled=ns.is_active,
            created_at=ns.created_at,
            updated_at=ns.updated_at
        )

    @staticmethod
    async def list_namespaces(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None
    ) -> List[NamespaceResponse]:
        logger.info(f"列出命名空间: page={page}, page_size={page_size}, is_active={is_active}")

        stmt = select(Namespace)

        if is_active is not None:
            stmt = stmt.where(Namespace.is_active == is_active)

        stmt = stmt.order_by(Namespace.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await session.execute(stmt)
        namespaces = result.scalars().all()

        responses = [NamespaceService._build_namespace_response(ns) for ns in namespaces]

        logger.info(f"成功获取 {len(responses)} 个命名空间")
        return responses

    @staticmethod
    async def create_namespace(
        session: AsyncSession,
        namespace: NamespaceCreate
    ) -> NamespaceResponse:
        redis_config_mode = namespace.redis_config_mode or namespace.config_mode or ConfigMode.DIRECT
        pg_config_mode = namespace.pg_config_mode or namespace.config_mode or ConfigMode.DIRECT

        logger.info(
            f"创建命名空间: {namespace.name}, "
            f"Redis模式: {redis_config_mode}, PG模式: {pg_config_mode}"
        )

        stmt = select(func.count()).select_from(Namespace).where(Namespace.name == namespace.name)
        result = await session.execute(stmt)
        if result.scalar() > 0:
            logger.error(f"命名空间 '{namespace.name}' 已存在")
            raise ValueError(f"命名空间 '{namespace.name}' 已存在")

        redis_config = {'config_mode': redis_config_mode.value}
        if redis_config_mode == ConfigMode.DIRECT:
            if not namespace.redis_url:
                raise ValueError("Redis直接配置模式下，redis_url是必需的")
            if namespace.redis_nacos_key:
                raise ValueError("Redis直接配置模式下不应提供redis_nacos_key")

            if not NamespaceService.validate_redis_url(namespace.redis_url):
                raise ValueError("无效的Redis URL格式")

            redis_config['url'] = namespace.redis_url
            logger.debug(f"Redis URL: {NamespaceService.mask_url_password(namespace.redis_url)}")

        elif redis_config_mode == ConfigMode.NACOS:
            if not namespace.redis_nacos_key:
                raise ValueError("Redis Nacos配置模式下，redis_nacos_key是必需的")
            if namespace.redis_url:
                raise ValueError("Redis Nacos配置模式下不应提供redis_url")

            redis_config['nacos_key'] = namespace.redis_nacos_key
            logger.info(f"Redis Nacos模式：存储配置键 '{namespace.redis_nacos_key}'")

        pg_config = {'config_mode': pg_config_mode.value}
        if pg_config_mode == ConfigMode.DIRECT:
            if namespace.pg_url:
                if not NamespaceService.validate_pg_url(namespace.pg_url):
                    raise ValueError("无效的PostgreSQL URL格式")
                pg_config['url'] = namespace.pg_url
                logger.debug(f"PG URL: {NamespaceService.mask_url_password(namespace.pg_url)}")
            if namespace.pg_nacos_key:
                raise ValueError("PostgreSQL直接配置模式下不应提供pg_nacos_key")

        elif pg_config_mode == ConfigMode.NACOS:
            if namespace.pg_nacos_key:
                pg_config['nacos_key'] = namespace.pg_nacos_key
                logger.info(f"PostgreSQL Nacos模式：存储配置键 '{namespace.pg_nacos_key}'")
            if namespace.pg_url:
                raise ValueError("PostgreSQL Nacos配置模式下不应提供pg_url")

        ns = Namespace(
            name=namespace.name,
            description=namespace.description,
            redis_config=redis_config,
            pg_config=pg_config,
            version=1
        )
        session.add(ns)
        await session.commit()
        await session.refresh(ns)

        logger.info(f"成功创建命名空间: {namespace.name}")
        return NamespaceService._build_namespace_response(ns)

    @staticmethod
    async def get_namespace(
        session: AsyncSession,
        namespace_name: str
    ) -> NamespaceResponse:
        logger.debug(f"获取命名空间详情: {namespace_name}")

        stmt = select(Namespace).where(Namespace.name == namespace_name)
        result = await session.execute(stmt)
        ns = result.scalar_one_or_none()

        if not ns:
            logger.error(f"命名空间 '{namespace_name}' 不存在")
            raise ValueError(f"命名空间 '{namespace_name}' 不存在")

        return NamespaceService._build_namespace_response(ns)

    @staticmethod
    async def update_namespace(
        session: AsyncSession,
        namespace_name: str,
        namespace: NamespaceUpdate
    ) -> NamespaceResponse:
        logger.info(f"更新命名空间: {namespace_name}")

        stmt = select(Namespace).where(Namespace.name == namespace_name)
        result = await session.execute(stmt)
        ns = result.scalar_one_or_none()

        if not ns:
            logger.error(f"命名空间 '{namespace_name}' 不存在")
            raise ValueError(f"命名空间 '{namespace_name}' 不存在")

        current_redis_config = ns.redis_config if ns.redis_config else {}
        current_pg_config = ns.pg_config if ns.pg_config else {}

        redis_mode = None
        pg_mode = None

        if namespace.redis_config_mode is not None:
            redis_mode = namespace.redis_config_mode
        elif namespace.config_mode is not None:
            redis_mode = namespace.config_mode

        if namespace.pg_config_mode is not None:
            pg_mode = namespace.pg_config_mode
        elif namespace.config_mode is not None:
            pg_mode = namespace.config_mode

        has_updates = False

        if namespace.description is not None:
            ns.description = namespace.description
            has_updates = True

        if redis_mode is not None:
            redis_config = {'config_mode': redis_mode.value}

            if redis_mode == ConfigMode.DIRECT:
                if namespace.redis_nacos_key:
                    raise ValueError("Redis直接配置模式下不应提供redis_nacos_key")

                if namespace.redis_url:
                    if not NamespaceService.validate_redis_url(namespace.redis_url):
                        raise ValueError("无效的Redis URL格式")
                    redis_config['url'] = namespace.redis_url
                    logger.debug(f"更新 Redis URL: {NamespaceService.mask_url_password(namespace.redis_url)}")
                else:
                    redis_config['url'] = current_redis_config.get('url', '')

            elif redis_mode == ConfigMode.NACOS:
                if namespace.redis_url:
                    raise ValueError("Redis Nacos配置模式下不应提供redis_url")

                if namespace.redis_nacos_key:
                    redis_config['nacos_key'] = namespace.redis_nacos_key
                    logger.info(f"Nacos模式：更新Redis配置键为 '{namespace.redis_nacos_key}'")
                else:
                    if current_redis_config.get('nacos_key'):
                        redis_config['nacos_key'] = current_redis_config.get('nacos_key')

            ns.redis_config = redis_config
            has_updates = True
        else:
            current_redis_mode = current_redis_config.get('config_mode', 'direct')

            if current_redis_mode == 'direct':
                if namespace.redis_nacos_key:
                    raise ValueError("Redis当前为直接配置模式，不能提供redis_nacos_key")

                if namespace.redis_url:
                    if not NamespaceService.validate_redis_url(namespace.redis_url):
                        raise ValueError("无效的Redis URL格式")
                    current_redis_config['url'] = namespace.redis_url
                    ns.redis_config = current_redis_config
                    has_updates = True
                    logger.debug(f"更新 Redis URL: {NamespaceService.mask_url_password(namespace.redis_url)}")

            else:  
                if namespace.redis_url:
                    raise ValueError("Redis当前为Nacos配置模式，不能提供redis_url")

                if namespace.redis_nacos_key:
                    current_redis_config['nacos_key'] = namespace.redis_nacos_key
                    ns.redis_config = current_redis_config
                    has_updates = True
                    logger.info(f"Nacos模式：更新Redis配置键为 '{namespace.redis_nacos_key}'")

        if pg_mode is not None:
            pg_config = {'config_mode': pg_mode.value}

            if pg_mode == ConfigMode.DIRECT:
                if namespace.pg_nacos_key:
                    raise ValueError("PostgreSQL直接配置模式下不应提供pg_nacos_key")

                if namespace.pg_url:
                    if not NamespaceService.validate_pg_url(namespace.pg_url):
                        raise ValueError("无效的PostgreSQL URL格式")
                    pg_config['url'] = namespace.pg_url
                    logger.debug(f"更新 PG URL: {NamespaceService.mask_url_password(namespace.pg_url)}")
                elif current_pg_config.get('url'):
                    pg_config['url'] = current_pg_config.get('url')

            elif pg_mode == ConfigMode.NACOS:
                if namespace.pg_url:
                    raise ValueError("PostgreSQL Nacos配置模式下不应提供pg_url")

                if namespace.pg_nacos_key:
                    pg_config['nacos_key'] = namespace.pg_nacos_key
                    logger.info(f"Nacos模式：更新PG配置键为 '{namespace.pg_nacos_key}'")
                else:
                    if current_pg_config.get('nacos_key'):
                        pg_config['nacos_key'] = current_pg_config.get('nacos_key')

            ns.pg_config = pg_config
            has_updates = True
        else:
            current_pg_mode = current_pg_config.get('config_mode', 'direct')

            if current_pg_mode == 'direct':
                if namespace.pg_nacos_key:
                    raise ValueError("PostgreSQL当前为直接配置模式，不能提供pg_nacos_key")

                if namespace.pg_url:
                    if not NamespaceService.validate_pg_url(namespace.pg_url):
                        raise ValueError("无效的PostgreSQL URL格式")
                    current_pg_config['url'] = namespace.pg_url
                    ns.pg_config = current_pg_config
                    has_updates = True
                    logger.debug(f"更新 PG URL: {NamespaceService.mask_url_password(namespace.pg_url)}")

            else:  
                if namespace.pg_url:
                    raise ValueError("PostgreSQL当前为Nacos配置模式，不能提供pg_url")

                if namespace.pg_nacos_key:
                    current_pg_config['nacos_key'] = namespace.pg_nacos_key
                    ns.pg_config = current_pg_config
                    has_updates = True
                    logger.info(f"Nacos模式：更新PG配置键为 '{namespace.pg_nacos_key}'")

        if namespace.enabled is not None:
            ns.is_active = namespace.enabled
            has_updates = True

        if not has_updates:
            raise ValueError("没有提供要更新的字段")

        ns.version = (ns.version or 0) + 1

        await session.commit()
        await session.refresh(ns)

        logger.info(f"成功更新命名空间: {namespace_name}")
        return NamespaceService._build_namespace_response(ns)

    @staticmethod
    async def delete_namespace(
        session: AsyncSession,
        namespace_name: str
    ) -> Dict[str, str]:
        if namespace_name == 'default':
            logger.error("尝试删除默认命名空间")
            raise ValueError("不能删除默认命名空间")

        logger.info(f"删除命名空间: {namespace_name}")

        stmt = select(Namespace).where(Namespace.name == namespace_name)
        result = await session.execute(stmt)
        ns = result.scalar_one_or_none()

        if not ns:
            logger.error(f"命名空间 '{namespace_name}' 不存在")
            raise ValueError(f"命名空间 '{namespace_name}' 不存在")

        await session.delete(ns)
        await session.commit()

        logger.info(f"成功删除命名空间: {namespace_name}")
        return {"message": f"命名空间 '{namespace_name}' 已删除"}

    @staticmethod
    async def activate_namespace(
        session: AsyncSession,
        namespace_name: str
    ) -> Dict[str, str]:
        logger.info(f"激活命名空间: {namespace_name}")

        stmt = (
            update(Namespace)
            .where(Namespace.name == namespace_name)
            .values(is_active=True)
        )
        result = await session.execute(stmt)

        if result.rowcount == 0:
            logger.error(f"命名空间 '{namespace_name}' 不存在")
            raise ValueError(f"命名空间 '{namespace_name}' 不存在")

        await session.commit()

        logger.info(f"成功激活命名空间: {namespace_name}")
        return {"message": f"命名空间 '{namespace_name}' 已激活"}

    @staticmethod
    async def deactivate_namespace(
        session: AsyncSession,
        namespace_name: str
    ) -> Dict[str, str]:
        if namespace_name == 'default':
            logger.error("尝试停用默认命名空间")
            raise ValueError("不能停用默认命名空间")

        logger.info(f"停用命名空间: {namespace_name}")

        stmt = (
            update(Namespace)
            .where(Namespace.name == namespace_name)
            .values(is_active=False)
        )
        result = await session.execute(stmt)

        if result.rowcount == 0:
            logger.error(f"命名空间 '{namespace_name}' 不存在")
            raise ValueError(f"命名空间 '{namespace_name}' 不存在")

        await session.commit()

        logger.info(f"成功停用命名空间: {namespace_name}")
        return {"message": f"命名空间 '{namespace_name}' 已停用"}

    @staticmethod
    async def get_namespace_statistics(
        session: AsyncSession,  
        namespace_name: str
    ) -> Dict[str, Any]:
        _ = session  
        logger.debug(f"获取命名空间统计信息: {namespace_name}")


        return {
            "success": True,
            "data": {
                "total_queues": 0,
                "total_tasks": 0,
                "active_workers": 0,
                "pending_tasks": 0,
                "processing_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0
            },
            "namespace": namespace_name,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    async def batch_activate_namespaces(
        session: AsyncSession,
        namespace_names: List[str]
    ) -> Dict[str, Any]:
        logger.info(f"批量激活命名空间: {namespace_names}")

        stmt = (
            update(Namespace)
            .where(Namespace.name.in_(namespace_names))
            .values(is_active=True)
        )
        result = await session.execute(stmt)
        await session.commit()

        activated_count = result.rowcount
        logger.info(f"批量激活了 {activated_count} 个命名空间")

        return {
            "activated": activated_count,
            "namespaces": namespace_names[:activated_count]
        }

    @staticmethod
    async def batch_deactivate_namespaces(
        session: AsyncSession,
        namespace_names: List[str]
    ) -> Dict[str, Any]:
        logger.info(f"批量停用命名空间: {namespace_names}")

        filtered_names = [name for name in namespace_names if name != 'default']

        if not filtered_names:
            logger.warning("批量停用操作中所有命名空间都被跳过（包含 default）")
            return {
                "deactivated": 0,
                "namespaces": [],
                "skipped": ["default"]
            }

        stmt = (
            update(Namespace)
            .where(Namespace.name.in_(filtered_names))
            .values(is_active=False)
        )
        result = await session.execute(stmt)
        await session.commit()

        deactivated_count = result.rowcount
        logger.info(f"批量停用了 {deactivated_count} 个命名空间")

        response = {
            "deactivated": deactivated_count,
            "namespaces": filtered_names[:deactivated_count]
        }

        skipped = [name for name in namespace_names if name not in filtered_names]
        if skipped:
            response["skipped"] = skipped

        return response


__all__ = ['NamespaceService']
