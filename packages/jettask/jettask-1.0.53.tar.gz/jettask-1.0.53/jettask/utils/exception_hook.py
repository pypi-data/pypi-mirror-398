"""
自定义异常钩子，用于简化任务执行错误的显示
"""
import sys
import os
from ..exceptions import TaskExecutionError


_original_excepthook = sys.excepthook


def custom_excepthook(exc_type, exc_value, exc_traceback):
    if isinstance(exc_value, TaskExecutionError):
        print(f"\n任务执行失败 (Task ID: {exc_value.task_id}):", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        if exc_value.error_traceback and exc_value.error_traceback != "Task execution failed":
            print(exc_value.error_traceback, file=sys.stderr)
        else:
            print("Task execution failed (no detailed error information available)", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        sys.exit(1)
    else:
        _original_excepthook(exc_type, exc_value, exc_traceback)


def install_clean_traceback():
    sys.excepthook = custom_excepthook


def uninstall_clean_traceback():
    sys.excepthook = _original_excepthook


if os.environ.get('JETTASK_FULL_TRACEBACK', '').lower() not in ('1', 'true', 'yes'):
    install_clean_traceback()