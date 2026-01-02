"""
Task Context - FastAPI风格的依赖注入
"""

from typing import TYPE_CHECKING, Optional, Any
from dataclasses import dataclass

if TYPE_CHECKING:
    from .app import Jettask


@dataclass
class TaskContext:
    """
    任务上下文信息

    通过类型注解自动注入到任务函数中：

    @app.task
    async def my_task(ctx: TaskContext, data: dict):
        print(f"Task ID: {ctx.event_id}")
        print(f"Task Name: {ctx.name}")
        if ctx.scheduled_task_id:
            print(f"Triggered by scheduled task: {ctx.scheduled_task_id}")
        # 访问元数据
        print(f"Priority: {ctx.metadata.get('priority')}")
        print(f"Delay: {ctx.metadata.get('delay')}")
        return data
    """
    event_id: str
    name: str
    trigger_time: float
    app: "Jettask"
    queue: Optional[str] = None
    worker_id: Optional[str] = None
    retry_count: int = 0
    scheduled_task_id: Optional[int] = None  
    group_name: Optional[str] = None  
    metadata: Optional[dict] = None  

    def __repr__(self) -> str:
        return f"TaskContext(event_id={self.event_id}, name={self.name}, queue={self.queue})"

    def acks(self, event_ids: list, offset: Optional[int] = None):
        if not event_ids:
            return

        if not self.queue:
            raise ValueError("TaskContext.queue is not set, cannot ACK")

        if not self.group_name:
            raise ValueError("TaskContext.group_name is not set, cannot ACK")

        ack_items = [
            (self.queue, event_id, self.group_name, offset)
            for event_id in event_ids
        ]

        self.app.ack(ack_items)