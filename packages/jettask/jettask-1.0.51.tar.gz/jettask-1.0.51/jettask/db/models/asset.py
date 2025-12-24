"""
资产管理模型

用于存储各种类型的资源配置，如：
- 计算节点（ComfyUI、SD WebUI 等）
- API 密钥（OpenAI、Claude 等）
- 第三方服务配置
"""
from sqlalchemy import Column, Integer, Text, TIMESTAMP, Index, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from typing import Dict, Any
import enum

from ..base import Base


class AssetType(str, enum.Enum):
    """资产类型"""
    COMPUTE_NODE = "compute_node"      

    API_KEY = "api_key"                

    CONFIG = "config"                  


class AssetStatus(str, enum.Enum):
    """资产状态"""
    ACTIVE = "active"        
    INACTIVE = "inactive"    
    ERROR = "error"          


class Asset(Base):
    """
    资产表

    存储各种类型的资源配置
    """
    __tablename__ = 'assets'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')

    namespace = Column(Text, nullable=False, comment='命名空间')

    asset_type = Column(
        SQLEnum(
            AssetType,
            name='asset_type',
            create_constraint=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        comment='资产类型'
    )
    asset_group = Column(Text, nullable=False, comment='资产分组（如 comfyui、openai、claude）')
    name = Column(Text, nullable=False, comment='资产名称（唯一标识）')

    config = Column(JSONB, nullable=False, default={}, comment='资产配置（如 URL、密钥等）')

    status = Column(
        SQLEnum(
            AssetStatus,
            name='asset_status',
            create_constraint=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=AssetStatus.ACTIVE,
        comment='资产状态'
    )

    weight = Column(Integer, nullable=False, default=1, comment='权重（用于负载均衡）')

    metadata_ = Column('metadata', JSONB, nullable=True, comment='额外元数据')
    description = Column(Text, nullable=True, comment='描述')

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment='创建时间'
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment='更新时间'
    )

    __table_args__ = (
        Index('idx_assets_namespace', 'namespace'),
        Index('idx_assets_namespace_type', 'namespace', 'asset_type'),
        Index('idx_assets_namespace_group', 'namespace', 'asset_group'),
        Index('idx_assets_namespace_type_group', 'namespace', 'asset_type', 'asset_group'),
        Index('idx_assets_unique_name', 'namespace', 'asset_group', 'name', unique=True),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'namespace': self.namespace,
            'asset_type': self.asset_type.value if self.asset_type else None,
            'asset_group': self.asset_group,
            'name': self.name,
            'config': self.config,
            'status': self.status.value if self.status else None,
            'weight': self.weight,
            'metadata': self.metadata_,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, group='{self.asset_group}', name='{self.name}')>"
