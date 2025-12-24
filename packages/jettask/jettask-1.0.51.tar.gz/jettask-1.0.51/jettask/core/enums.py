"""
任务状态和结果定义
"""
from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional, Dict
import time


class TaskType(Enum):
    """任务类型"""
    ONCE = "once"        
    INTERVAL = "interval"  
    CRON = "cron"        


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"          
    RUNNING = "running"          
    SUCCESS = "success"          
    ERROR = "error"              
    FAILED = "failed"            
    
    DELAYED = "delayed"          
    REJECTED = "rejected"        
    RETRY = "retry"              
    TIMEOUT = "timeout"          
    CANCELLED = "cancelled"      
    
    SCHEDULED = "scheduled"      
    
    @classmethod
    def is_terminal(cls, status: 'TaskStatus') -> bool:
        return status in {cls.SUCCESS, cls.ERROR, cls.FAILED, cls.REJECTED, cls.TIMEOUT, cls.CANCELLED}
    
    @classmethod
    def is_active(cls, status: 'TaskStatus') -> bool:
        return status in {cls.PENDING, cls.RUNNING, cls.DELAYED, cls.RETRY, cls.SCHEDULED}


@dataclass
class TaskResult:
    """
    任务结果对象
    apply_async 返回的结果，包含任务的完整信息
    """
    id: str                                    
    name: str                                   
    queue: str                                  
    status: TaskStatus = TaskStatus.PENDING    
    created_at: float = None                   
    trigger_time: float = None                 
    scheduled_task_id: Optional[int] = None    
    args: tuple = None                         
    kwargs: dict = None                        
    metadata: Dict[str, Any] = None           
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.trigger_time is None:
            self.trigger_time = self.created_at
        if self.args is None:
            self.args = ()
        if self.kwargs is None:
            self.kwargs = {}
        if self.metadata is None:
            self.metadata = {}
    
    def __str__(self) -> str:
        return f"TaskResult(id={self.id}, name={self.name}, status={self.status.value})"
    
    def __repr__(self) -> str:
        return (f"TaskResult(id={self.id}, name={self.name}, queue={self.queue}, "
                f"status={self.status.value}, created_at={self.created_at})")
    
    async def wait(self, timeout: Optional[float] = None):
        raise NotImplementedError("wait method not implemented yet")
    
    async def get_result(self, timeout: Optional[float] = None):
        raise NotImplementedError("get_result method not implemented yet")
    
    async def cancel(self) -> bool:
        raise NotImplementedError("cancel method not implemented yet")
    
    async def get_status(self) -> TaskStatus:
        raise NotImplementedError("get_status method not implemented yet")
    
    @property
    def is_ready(self) -> bool:
        return TaskStatus.is_terminal(self.status)
    
    @property
    def is_successful(self) -> bool:
        return self.status == TaskStatus.SUCCESS
    
    @property
    def is_failed(self) -> bool:
        return self.status in {TaskStatus.ERROR, TaskStatus.TIMEOUT, TaskStatus.REJECTED}