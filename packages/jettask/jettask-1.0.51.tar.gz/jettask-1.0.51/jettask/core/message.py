"""
任务消息类 - 完全独立的任务发送对象
与task定义完全解耦，可以在任何项目中使用
"""
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
import time


@dataclass
class TaskMessage:
    """
    任务消息对象
    
    这是一个完全独立的类，不依赖任何task定义。
    可以在没有执行器代码的项目中单独使用。
    
    使用示例:
        # 创建任务消息
        msg = TaskMessage(
            queue="order_processing",
            args=(12345,),
            kwargs={"customer_id": "C001", "amount": 99.99},
            delay=5  # 延迟5秒执行
        )
        
        # 批量创建
        messages = [
            TaskMessage(queue="email", kwargs={"to": "user1@example.com"}),
            TaskMessage(queue="email", kwargs={"to": "user2@example.com"}),
        ]
        
        # 发送
        await app.send_tasks([msg])
        await app.send_tasks(messages)
    """
    
    queue: str  
    
    args: Tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    
    delay: Optional[int] = None  
    priority: Optional[int] = None  
    
    scheduled_task_id: Optional[int] = None  
    
    routing: Optional[Dict[str, Any]] = None
    
    trigger_time: Optional[float] = None  
    
    def __post_init__(self):
        if self.trigger_time is None:
            self.trigger_time = time.time()
    
    def to_dict(self) -> dict:
        data = {
            'queue': self.queue,
            'args': self.args,
            'kwargs': self.kwargs,
            'trigger_time': self.trigger_time
        }
        
        optional_fields = [
            'delay', 'priority', 'scheduled_task_id', 'routing'
        ]
        
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                if isinstance(value, (list, dict)) and not value:
                    continue
                data[field_name] = value
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TaskMessage':
        init_fields = {
            'queue', 'args', 'kwargs', 
            'delay', 'priority', 'scheduled_task_id', 'routing', 'trigger_time'
        }
        
        init_data = {k: v for k, v in data.items() if k in init_fields}
        return cls(**init_data)
    
    def validate(self) -> bool:
        if not self.queue:
            raise ValueError("Queue name is required")
        
        if self.delay and self.delay < 0:
            raise ValueError(f"Delay must be non-negative, got {self.delay}")
        
        if self.priority is not None and self.priority < 1:
            raise ValueError(f"Priority must be positive (1 is highest), got {self.priority}")
        
        return True
    
    def __repr__(self) -> str:
        parts = [f"TaskMessage(queue='{self.queue}'"]
        
        if self.args:
            parts.append(f"args={self.args}")
        
        if self.kwargs:
            parts.append(f"kwargs={self.kwargs}")
        
        if self.delay:
            parts.append(f"delay={self.delay}s")
        
        return ", ".join(parts) + ")"