"""
任务日志管理器
提供结构化日志输出，自动注入任务上下文信息
"""
import logging
import json
import sys
import contextvars
from typing import Optional, Dict, Any
from datetime import datetime


task_context = contextvars.ContextVar('task_context', default={})


class TaskContextFilter(logging.Filter):
    """
    日志过滤器，自动添加任务上下文信息
    """
    def filter(self, record):
        ctx = task_context.get()
        if ctx:
            record.task_id = ctx.get('task_id', '')
            record.task_name = ctx.get('task_name', '')
            record.queue = ctx.get('queue', '')
            record.event_id = ctx.get('event_id', '')
            record.worker_id = ctx.get('worker_id', '')
            
            custom_fields = {}
            for key, value in ctx.items():
                if key not in ('task_id', 'task_name', 'queue', 'event_id', 'worker_id'):
                    custom_fields[key] = value
            
            if custom_fields:
                if hasattr(record, 'extra_fields'):
                    record.extra_fields = {**custom_fields, **record.extra_fields}
                else:
                    record.extra_fields = custom_fields
        else:
            record.task_id = ''
            record.task_name = ''
            record.queue = ''
            record.event_id = ''
            record.worker_id = ''
        return True


class ExtendedTextFormatter(logging.Formatter):
    """
    扩展的文本格式化器，支持输出额外字段
    """
    def format(self, record):
        result = super().format(record)
        
        extra_parts = []
        
        if hasattr(record, 'extra_fields') and record.extra_fields:
            for key, value in record.extra_fields.items():
                extra_parts.append(f"{key}={value}")
        
        if extra_parts:
            result += f" | {', '.join(extra_parts)}"
        
        return result


class JSONFormatter(logging.Formatter):
    """
    JSON格式化器，输出结构化JSON日志
    """
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if hasattr(record, 'task_id') and record.task_id:
            log_obj['task_id'] = record.task_id
        if hasattr(record, 'task_name') and record.task_name:
            log_obj['task_name'] = record.task_name
        if hasattr(record, 'queue') and record.queue:
            log_obj['queue'] = record.queue
        if hasattr(record, 'event_id') and record.event_id:
            log_obj['event_id'] = record.event_id
        if hasattr(record, 'worker_id') and record.worker_id:
            log_obj['worker_id'] = record.worker_id
        
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra_fields'):
            log_obj.update(record.extra_fields)
        
        return json.dumps(log_obj, ensure_ascii=False)


class TaskLogger:
    """
    任务日志管理器
    """
    def __init__(self, name: str = 'jettask.worker', level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self._configured = False
        
    def configure_json_output(self, stream=None):
        if self._configured:
            return
        
        self.logger.handlers.clear()
        
        handler = logging.StreamHandler(stream or sys.stdout)
        handler.setFormatter(JSONFormatter())
        
        handler.addFilter(TaskContextFilter())
        
        self.logger.addHandler(handler)
        self._configured = True
        
        self.logger.propagate = False
    
    def configure_text_output(self, stream=None, format_string=None):
        if self._configured:
            return
        
        self.logger.handlers.clear()
        
        if format_string is None:
            format_string = '%(asctime)s - %(levelname)s - [%(task_id)s] - %(name)s - %(message)s'
        
        handler = logging.StreamHandler(stream or sys.stderr)
        handler.setFormatter(ExtendedTextFormatter(format_string))
        
        handler.addFilter(TaskContextFilter())
        
        self.logger.addHandler(handler)
        self._configured = True
        
        self.logger.propagate = False
    
    def get_logger(self):
        if not self._configured:
            self.configure_text_output()
        return self.logger


class TaskContextManager:
    """
    任务上下文管理器，用于设置和清理任务上下文
    """
    def __init__(self, event_id: str, task_name: str, queue: str, 
                 worker_id: Optional[str] = None, **extra):
        self.context = {
            'event_id': event_id,
            'task_id': event_id,  
            'task_name': task_name,
            'queue': queue,
            'worker_id': worker_id or '',
            **extra
        }
        self.token = None
    
    def __enter__(self):
        self.token = task_context.set(self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            task_context.reset(self.token)
    
    async def __aenter__(self):
        self.token = task_context.set(self.context)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            task_context.reset(self.token)


def set_task_context(event_id: str, task_name: str, queue: str, 
                     worker_id: Optional[str] = None, **extra):
    context = {
        'event_id': event_id,
        'task_id': event_id,
        'task_name': task_name,
        'queue': queue,
        'worker_id': worker_id or '',
        **extra
    }
    return task_context.set(context)


def clear_task_context(token=None):
    if token:
        task_context.reset(token)
    else:
        task_context.set({})


class LogContext:
    """
    灵活的日志上下文管理器，用于临时添加额外的日志字段
    
    特点:
    - 不需要必填字段
    - 可在同步和异步函数中使用
    - 会合并而不是覆盖现有的上下文
    - 退出时自动恢复原始上下文
    
    Example:
        # 在同步函数中使用
        def sync_func():
            with LogContext(user_id='123', action='login'):
                logger.info("用户登录")  # 自动带上 user_id 和 action
        
        # 在异步函数中使用（直接用 with，不需要 async with）
        async def async_func():
            with LogContext(request_id='req-001'):
                logger.info("处理请求")  # 自动带上 request_id
                await some_async_operation()
            
        # 嵌套使用
        with LogContext(user_id='123'):
            logger.info("外层日志")  # 带 user_id
            with LogContext(action='update', item_id='456'):
                logger.info("内层日志")  # 带 user_id, action, item_id
            logger.info("回到外层")  # 只带 user_id
    """
    
    def __init__(self, **fields):
        self.fields = fields
        self.token = None
        self.original_context = None
    
    def __enter__(self):
        current_ctx = task_context.get()
        self.original_context = current_ctx.copy() if current_ctx else {}
        
        new_ctx = {**self.original_context, **self.fields}
        
        self.token = task_context.set(new_ctx)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            task_context.set(self.original_context)


def get_task_logger(name: str = None) -> logging.Logger:
    import inspect
    if name is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'jettask.worker')
        else:
            name = 'jettask.worker'
    
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


task_logger_manager = TaskLogger()


def configure_task_logging(format: str = 'text', level: int = logging.INFO, **kwargs):
    task_logger_manager.logger.setLevel(level)
    
    if format == 'json':
        task_logger_manager.configure_json_output(
            stream=kwargs.get('stream', sys.stdout)
        )
    else:
        task_logger_manager.configure_text_output(
            stream=kwargs.get('stream', sys.stderr),
            format_string=kwargs.get('format_string')
        )
    
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        
        for handler in logger.handlers:
            handler.filters.clear()
            
            handler.addFilter(TaskContextFilter())
            
            if format == 'json':
                handler.setFormatter(JSONFormatter())
            else:
                format_string = kwargs.get('format_string', 
                    '%(asctime)s - %(levelname)s - [%(task_id)s] - %(name)s - %(message)s')
                handler.setFormatter(ExtendedTextFormatter(format_string))
    
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(TaskContextFilter())
        
        if format == 'json':
            handler.setFormatter(JSONFormatter())