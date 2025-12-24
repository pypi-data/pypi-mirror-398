"""
JetTask 异常定义
"""
import sys
import traceback as tb


class JetTaskException(Exception):
    """JetTask 基础异常类"""
    pass


class TaskTimeoutError(JetTaskException):
    """任务等待超时异常"""
    pass


class TaskExecutionError(JetTaskException):
    """任务执行错误异常
    
    这个异常会直接打印错误信息并退出，避免显示框架层堆栈
    """
    def __init__(self, task_id, error_traceback):
        self.task_id = task_id
        self.error_traceback = error_traceback
        super().__init__(f"Task {task_id} failed")
    
    def print_and_exit(self, exit_code=1):
        print(f"\n任务执行失败 (Task ID: {self.task_id}):", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        if self.error_traceback and self.error_traceback != "Task execution failed":
            print(self.error_traceback, file=sys.stderr)
        else:
            print("Task execution failed (no detailed error information available)", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        sys.exit(exit_code)
    
    def __str__(self):
        return f"Task {self.task_id} failed:\n{self.error_traceback}"


class TaskNotFoundError(JetTaskException):
    """任务未找到异常"""
    pass


class RetryableError(JetTaskException):
    """
    可重试的错误
    
    使用这个异常可以指定建议的重试延迟时间
    
    Example:
        raise RetryableError("Service temporarily unavailable", retry_after=30)
    """
    
    def __init__(self, message: str, retry_after: float = None):
        super().__init__(message)
        self.retry_after = retry_after