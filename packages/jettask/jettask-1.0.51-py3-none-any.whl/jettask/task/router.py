"""
Task Router for modular task organization
Similar to FastAPI's APIRouter
"""

from typing import Dict, List, Any, Callable
import logging
from jettask.utils.rate_limit.config import RateLimitConfig

logger = logging.getLogger(__name__)


class TaskRouter:
    """
    任务路由器，用于模块化组织任务
    
    使用示例：
        # tasks/email_tasks.py
        from jettask import TaskRouter
        
        router = TaskRouter(prefix="email", queue="emails")
        
        @router.task()
        async def send_welcome_email(user_id: str):
            # 实际任务名会是: email.send_welcome_email
            # 默认队列会是: emails
            pass
        
        # main.py
        from jettask import Jettask
        from tasks.email_tasks import router as email_router
        
        app = Jettask(redis_url="redis://localhost:6379/0")
        app.register_router(email_router)
    """
    
    def __init__(
        self,
        prefix: str = None,
        queue: str = None,
        tags: List[str] = None,
        default_timeout: int = None,
        default_max_retries: int = None,
        default_retry_delay: int = None,
    ):
        self.prefix = prefix
        self.default_queue = queue
        self.tags = tags or []
        self.default_timeout = default_timeout
        self.default_max_retries = default_max_retries
        self.default_retry_delay = default_retry_delay
        
        self._tasks: Dict[str, Dict[str, Any]] = {}
        
    def task(
        self,
        name: str = None,
        queue: str = None,
        timeout: int = None,
        max_retries: int = None,
        retry_delay: int = None,
        rate_limit: RateLimitConfig = None,
        auto_ack: bool = True,
        **kwargs
    ):
        def decorator(func: Callable):
            task_name = name or func.__name__
            if self.prefix:
                full_task_name = f"{self.prefix}.{task_name}"
            else:
                full_task_name = task_name

            task_config = {
                'func': func,
                'name': full_task_name,
                'queue': queue or self.default_queue,
                'timeout': timeout or self.default_timeout,
                'max_retries': max_retries or self.default_max_retries,
                'retry_delay': retry_delay or self.default_retry_delay,
                'rate_limit': rate_limit,
                'auto_ack': auto_ack,
                'tags': self.tags,
                **kwargs
            }

            task_config = {k: v for k, v in task_config.items() if v is not None}

            self._tasks[full_task_name] = task_config

            return func

        return decorator
    
    def include_router(self, router: 'TaskRouter', prefix: str = None):
        if prefix:
            if self.prefix:
                combined_prefix = f"{self.prefix}.{prefix}"
            else:
                combined_prefix = prefix
        else:
            combined_prefix = self.prefix
        
        for task_name, task_config in router._tasks.items():
            if combined_prefix and not task_name.startswith(combined_prefix):
                if router.prefix and task_name.startswith(router.prefix):
                    new_name = task_name.replace(router.prefix, combined_prefix, 1)
                else:
                    new_name = f"{combined_prefix}.{task_name}"
            else:
                new_name = task_name
            
            new_config = task_config.copy()
            new_config['name'] = new_name
            
            if 'queue' not in new_config or new_config['queue'] is None:
                new_config['queue'] = self.default_queue
            
            self._tasks[new_name] = new_config
    
    def get_tasks(self) -> Dict[str, Dict[str, Any]]:
        return self._tasks