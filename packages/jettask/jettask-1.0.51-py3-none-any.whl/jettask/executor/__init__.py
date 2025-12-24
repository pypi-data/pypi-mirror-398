"""
执行器模块

提供任务执行的核心功能，支持单进程和多进程两种模式。

主要组件：
- TaskExecutor: 任务执行器（新）
- ProcessOrchestrator: 多进程编排器
- ExecutorCore: 核心执行逻辑
"""

from .core import ExecutorCore
from .orchestrator import ProcessConfig, ProcessOrchestrator
from .task_executor import TaskExecutor


__all__ = [
    'TaskExecutor',
    'ProcessOrchestrator',
    'ProcessConfig',
    'ExecutorCore',
]
