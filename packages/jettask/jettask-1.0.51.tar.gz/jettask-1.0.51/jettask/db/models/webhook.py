"""
Webhook 模型

对应 webhooks 表，用于存储第三方平台的 webhook 回调通知
"""
from sqlalchemy import Column, Integer, Text, TIMESTAMP, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from typing import Dict, Any
import enum

from ..base import Base


class WebhookStatus(str, enum.Enum):
    """Webhook 处理状态"""
    PENDING = "pending"      
    SUCCESS = "success"      
    FAILED = "failed"        


class Webhook(Base):
    """
    Webhook 回调通知表

    存储第三方平台（如模型服务商）发送的 webhook 通知
    设计为极简模式，任意 JSON 数据都可以存储
    """
    __tablename__ = 'webhooks'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')

    namespace = Column(Text, nullable=False, comment='命名空间')

    callback_id = Column(Text, nullable=False, index=True, comment='回调 ID，用于关联任务')

    payload = Column(JSONB, nullable=False, comment='原始 webhook 载荷（任意 JSON）')

    status = Column(
        SQLEnum(
            WebhookStatus,
            name='webhook_status',
            create_constraint=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=WebhookStatus.PENDING,
        comment='处理状态'
    )

    received_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment='接收时间'
    )

    __table_args__ = (
        Index('idx_webhooks_namespace', 'namespace'),
        Index('idx_webhooks_namespace_callback_id', 'namespace', 'callback_id'),
        Index('idx_webhooks_received_at', 'received_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'namespace': self.namespace,
            'callback_id': self.callback_id,
            'payload': self.payload,
            'status': self.status.value if self.status else None,
            'received_at': self.received_at.isoformat() if self.received_at else None,
        }

    def __repr__(self) -> str:
        return f"<Webhook(id={self.id}, callback_id='{self.callback_id}', status='{self.status}')>"
