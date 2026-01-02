"""
TaskMetricsMinute 模型

按分钟粒度聚合的任务指标表，用于优化时间序列查询性能
"""
from sqlalchemy import Column, String, Integer, TIMESTAMP, Index, BigInteger
from datetime import datetime, timezone
from typing import Dict, Any

from ..base import Base


class TaskMetricsMinute(Base):
    """
    任务指标分钟级聚合表

    按照 namespace + queue + time_bucket (分钟) 维度聚合任务数量
    用于快速查询任务创建趋势等时间序列数据
    """
    __tablename__ = 'task_metrics_minute'

    namespace = Column(String, primary_key=True, comment='命名空间')
    queue = Column(String, primary_key=True, comment='队列名称')
    time_bucket = Column(
        TIMESTAMP(timezone=True),
        primary_key=True,
        comment='时间桶（分钟级别，如 2025-11-11 10:00:00）'
    )

    task_count = Column(BigInteger, nullable=False, default=0, comment='任务数量')


    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment='最后更新时间'
    )

    __table_args__ = (
        Index('idx_metrics_min_ns_queue_time', 'namespace', 'queue', 'time_bucket'),
        Index('idx_metrics_min_time_bucket', 'time_bucket'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'namespace': self.namespace,
            'queue': self.queue,
            'time_bucket': self.time_bucket.isoformat() if self.time_bucket else None,
            'task_count': self.task_count,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<TaskMetricsMinute("
            f"namespace='{self.namespace}', "
            f"queue='{self.queue}', "
            f"time_bucket='{self.time_bucket}', "
            f"task_count={self.task_count}"
            f")>"
        )
