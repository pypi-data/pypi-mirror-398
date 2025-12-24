"""
数据库模型定义

所有表的 SQLAlchemy 模型定义
"""

from .task import Task
from .task_run import TaskRun
from .scheduled_task import ScheduledTask
from .task_metrics_minute import TaskMetricsMinute
from .task_runs_metrics_minute import TaskRunsMetricsMinute
from .sql_history import SQLHistory
from .namespace import Namespace
from .webhook import Webhook, WebhookStatus
from .asset import Asset, AssetType, AssetStatus

from jettask.core.enums import TaskType, TaskStatus

__all__ = [
    'Task',
    'TaskRun',
    'ScheduledTask',
    'TaskMetricsMinute',
    'TaskRunsMetricsMinute',
    'SQLHistory',
    'Namespace',
    'Webhook',
    'WebhookStatus',
    'Asset',
    'AssetType',
    'AssetStatus',
    'TaskType',
    'TaskStatus',
]
