"""
TaskRunsMetricsMinute 模型

分钟级聚合统计表，用于高效查询任务执行概览数据
"""
from sqlalchemy import Column, Text, Integer, Float, TIMESTAMP, Index
from datetime import datetime, timezone

from ..base import Base


class TaskRunsMetricsMinute(Base):
    """
    任务执行指标分钟级聚合表

    按分钟粒度聚合 task_runs 数据，用于：
    - 任务成功/失败趋势图
    - 并发数量统计
    - 平均执行时间
    - 任务执行延迟（排队时间）
    """
    __tablename__ = 'task_runs_metrics_minute'

    time_bucket = Column(
        TIMESTAMP(timezone=True),
        primary_key=True,
        comment='时间桶（分钟级别，如 2025-11-16 12:30:00）'
    )
    namespace = Column(
        Text,
        primary_key=True,
        comment='任务所属命名空间'
    )
    queue = Column(
        Text,
        primary_key=True,
        comment='任务所属队列'
    )
    task_name = Column(
        Text,
        primary_key=True,
        comment='任务类型名称'
    )

    total_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment='此分钟内总任务数量'
    )
    success_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment='成功任务数'
    )
    failed_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment='失败任务数'
    )
    retry_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment='重试次数之和'
    )

    total_duration = Column(
        Float,
        nullable=False,
        default=0.0,
        comment='执行时间总和（秒），用于计算平均执行时长'
    )
    max_duration = Column(
        Float,
        nullable=True,
        comment='最大执行时间（秒）'
    )
    min_duration = Column(
        Float,
        nullable=True,
        comment='最小执行时间（秒）'
    )

    total_delay = Column(
        Float,
        nullable=False,
        default=0.0,
        comment='执行延迟总和（秒），即 started_at - trigger_time'
    )
    max_delay = Column(
        Float,
        nullable=True,
        comment='最大执行延迟（秒）'
    )
    min_delay = Column(
        Float,
        nullable=True,
        comment='最小执行延迟（秒）'
    )

    running_concurrency = Column(
        Integer,
        nullable=False,
        default=0,
        comment='当前分钟内并发峰值'
    )

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
        Index('idx_task_runs_metrics_minute_time_bucket', 'time_bucket'),
        Index('idx_task_runs_metrics_minute_namespace', 'namespace'),
        Index('idx_task_runs_metrics_minute_queue', 'queue'),
        Index('idx_task_runs_metrics_minute_task_name', 'task_name'),
    )

    def to_dict(self):
        return {
            'time_bucket': self.time_bucket.isoformat() if self.time_bucket else None,
            'namespace': self.namespace,
            'queue': self.queue,
            'task_name': self.task_name,
            'total_count': self.total_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'retry_count': self.retry_count,
            'total_duration': self.total_duration,
            'max_duration': self.max_duration,
            'min_duration': self.min_duration,
            'avg_duration': self.total_duration / self.total_count if self.total_count > 0 else 0,
            'total_delay': self.total_delay,
            'max_delay': self.max_delay,
            'min_delay': self.min_delay,
            'avg_delay': self.total_delay / self.total_count if self.total_count > 0 else 0,
            'running_concurrency': self.running_concurrency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return (
            f"<TaskRunsMetricsMinute("
            f"time_bucket={self.time_bucket}, "
            f"namespace={self.namespace}, "
            f"queue={self.queue}, "
            f"task={self.task_name}, "
            f"total={self.total_count}, "
            f"success={self.success_count}, "
            f"failed={self.failed_count}"
            f")>"
        )
