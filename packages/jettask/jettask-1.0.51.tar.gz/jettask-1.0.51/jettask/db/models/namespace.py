"""
Namespace 模型

对应 namespaces 表，用于存储命名空间配置
"""
from sqlalchemy import Column, String, Integer, Text, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from ..base import Base


class Namespace(Base):
    """
    命名空间配置表

    存储各个命名空间的配置信息，包括 Redis 和 PostgreSQL 连接配置
    """
    __tablename__ = 'namespaces'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')

    name = Column(Text, unique=True, nullable=False, comment='命名空间名称')

    description = Column(Text, nullable=True, comment='命名空间描述')

    redis_config = Column(JSONB, nullable=True, comment='Redis 配置')

    pg_config = Column(JSONB, nullable=True, comment='PostgreSQL 配置')

    is_active = Column(Boolean, nullable=False, default=True, comment='是否激活')

    version = Column(Integer, nullable=False, default=1, comment='配置版本号')

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        comment='创建时间'
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment='更新时间'
    )

    def get_redis_config_mode(self) -> str:
        if self.redis_config:
            return self.redis_config.get('config_mode', 'direct')
        return 'direct'

    def get_redis_url(self) -> Optional[str]:
        if self.redis_config and self.get_redis_config_mode() == 'direct':
            return self.redis_config.get('url')
        return None

    def get_redis_nacos_key(self) -> Optional[str]:
        if self.redis_config and self.get_redis_config_mode() == 'nacos':
            return self.redis_config.get('nacos_key')
        return None

    def get_pg_config_mode(self) -> str:
        if self.pg_config:
            return self.pg_config.get('config_mode', 'direct')
        return 'direct'

    def get_pg_url(self) -> Optional[str]:
        if self.pg_config and self.get_pg_config_mode() == 'direct':
            return self.pg_config.get('url')
        return None

    def get_pg_nacos_key(self) -> Optional[str]:
        if self.pg_config and self.get_pg_config_mode() == 'nacos':
            return self.pg_config.get('nacos_key')
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'redis_config': self.redis_config,
            'pg_config': self.pg_config,
            'is_active': self.is_active,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Namespace(id={self.id}, name='{self.name}', is_active={self.is_active})>"
