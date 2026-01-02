"""
错误处理工具
"""
import sys
import functools
from contextlib import contextmanager
from ..exceptions import TaskExecutionError


@contextmanager
def clean_task_errors():
    try:
        yield
    except TaskExecutionError as e:
        print(f"\n任务执行失败 (Task ID: {e.task_id}):", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        if e.error_traceback and e.error_traceback != "Task execution failed":
            print(e.error_traceback, file=sys.stderr)
        else:
            print("Task execution failed (no detailed error information available)", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n操作被用户中断", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        raise


def handle_task_error(func):
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TaskExecutionError as e:
            print(f"\n任务执行失败 (Task ID: {e.task_id}):", file=sys.stderr)
            print("-" * 60, file=sys.stderr)
            if e.error_traceback and e.error_traceback != "Task execution failed":
                print(e.error_traceback, file=sys.stderr)
            else:
                print("Task execution failed (no detailed error information available)", file=sys.stderr)
            print("-" * 60, file=sys.stderr)
            sys.exit(1)
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TaskExecutionError as e:
            print(f"\n任务执行失败 (Task ID: {e.task_id}):", file=sys.stderr)
            print("-" * 60, file=sys.stderr)
            if e.error_traceback and e.error_traceback != "Task execution failed":
                print(e.error_traceback, file=sys.stderr)
            else:
                print("Task execution failed (no detailed error information available)", file=sys.stderr)
            print("-" * 60, file=sys.stderr)
            sys.exit(1)
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper