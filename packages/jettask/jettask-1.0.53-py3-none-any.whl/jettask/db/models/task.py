"""
Task 模型

对应 tasks 表，用于存储任务消息（实际表结构）
"""
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Index, Float
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from ..base import Base


class Task(Base):
    """
    任务消息表

    存储发送到队列的任务消息
    """
    __tablename__ = 'tasks'

    stream_id = Column(Text, primary_key=True, comment='Redis Stream 事件ID，唯一标识一个任务')
    trigger_time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False, comment='任务触发时间（TIMESTAMP 类型），分区键')

    queue = Column(Text, nullable=False, comment='队列名称')
    namespace = Column(Text, nullable=False, comment='命名空间')

    scheduled_task_id = Column(Text, nullable=True, comment='关联的定时任务ID')

    payload = Column(JSONB, nullable=False, comment='消息载荷（任务数据）')

    priority = Column(Integer, nullable=True, comment='优先级（数字越小优先级越高）')
    delay = Column(Integer, nullable=True, comment='延迟时间（秒）')

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment='记录创建时间'
    )

    source = Column(Text, nullable=False, comment='消息来源（如 scheduler, manual, api）')

    task_metadata = Column('metadata', JSONB, nullable=True, comment='任务元数据')

    __table_args__ = (
        Index('idx_tasks_queue', 'queue'),
        Index('idx_tasks_namespace', 'namespace'),
        Index('idx_tasks_queue_namespace', 'queue', 'namespace'),
        Index('idx_tasks_scheduled_task_id', 'scheduled_task_id'),
        Index('idx_tasks_created_at', 'created_at'),
        Index('idx_tasks_source', 'source'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'stream_id': self.stream_id,
            'queue': self.queue,
            'namespace': self.namespace,
            'scheduled_task_id': self.scheduled_task_id,
            'payload': self.payload,
            'priority': self.priority,
            'delay': self.delay,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'trigger_time': self.trigger_time.isoformat() if self.trigger_time else None,
            'source': self.source,
            'metadata': self.task_metadata,
        }

    def __repr__(self) -> str:
        return f"<Task(stream_id='{self.stream_id}', queue='{self.queue}', namespace='{self.namespace}')>"
