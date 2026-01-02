"""
TaskRun 模型

对应 task_runs 表，用于存储任务执行记录
"""
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Float, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from ..base import Base


class TaskRun(Base):
    """
    任务执行记录表

    存储每次任务执行的状态、结果和执行时间等信息
    """
    __tablename__ = 'task_runs'

    task_name = Column(Text, primary_key=True, nullable=False, comment='任务名称（粗粒度）')
    trigger_time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False, comment='任务触发时间（分区键）')
    stream_id = Column(Text, primary_key=True, comment='Redis Stream 事件ID（细粒度）')

    status = Column(String(50), nullable=True, comment='任务状态 (pending/running/success/failed/retrying)')

    result = Column(JSONB, nullable=True, comment='任务执行结果')
    error = Column(Text, nullable=True, comment='错误信息（如果失败）')

    started_at = Column(TIMESTAMP(timezone=True), nullable=True, comment='开始执行时间（TIMESTAMP 类型），可能因重试而变化')
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True, comment='完成时间（TIMESTAMP 类型）')

    retries = Column(Integer, nullable=True, default=0, comment='重试次数')

    duration = Column(Float, nullable=True, comment='执行时长（秒）')

    consumer = Column(Text, nullable=True, comment='执行该任务的消费者ID')

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment='记录创建时间'
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment='记录更新时间'
    )

    __table_args__ = (
        Index('idx_task_runs_status', 'status'),
        Index('idx_task_runs_stream_id', 'stream_id'),  
        Index('idx_task_runs_started_at', 'started_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_name': self.task_name,
            'trigger_time': self.trigger_time.isoformat() if self.trigger_time else None,
            'stream_id': self.stream_id,
            'status': self.status,
            'result': self.result,
            'error': self.error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retries': self.retries,
            'duration': self.duration,
            'consumer': self.consumer,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<TaskRun(stream_id='{self.stream_id}', status='{self.status}')>"
