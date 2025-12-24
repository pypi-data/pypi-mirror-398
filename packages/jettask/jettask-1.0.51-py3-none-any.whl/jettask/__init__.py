"""
JetTask - High Performance Distributed Task Queue System
"""

import logging
import inspect

from jettask.core.app import Jettask
from jettask.core.message import TaskMessage
from jettask.core.context import TaskContext
from jettask.task.router import TaskRouter
from jettask.scheduler.definition import Schedule

from jettask.utils.rate_limit.config import QPSLimit, ConcurrencyLimit

from jettask.utils.task_logger import (
    TaskContextFilter,
    ExtendedTextFormatter,
    LogContext
)

__version__ = "0.1.0"


def get_task_logger(name: str = None) -> logging.Logger:
    if name is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'jettask')
        else:
            name = 'jettask'
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ExtendedTextFormatter(
            '%(asctime)s - %(levelname)s - [%(task_id)s] - %(name)s - %(message)s'
        ))
        handler.addFilter(TaskContextFilter())
        logger.addHandler(handler)
        logger.propagate = False
    
    return logger


__all__ = [
    "Jettask",
    "TaskMessage",
    "Schedule",
    "TaskRouter",
    "QPSLimit",
    "ConcurrencyLimit",
    "get_task_logger",
    "LogContext",
    "TaskContext"
]