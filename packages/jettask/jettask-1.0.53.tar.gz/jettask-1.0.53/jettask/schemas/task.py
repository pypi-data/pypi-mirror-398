"""
任务相关的数据模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TasksRequest(BaseModel):
    """任务查询请求模型"""
    queue_name: str = Field(..., description="队列名称")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")
    filters: Optional[List[Dict]] = Field(default=[], description="筛选条件")
    time_range: Optional[str] = Field(None, description="时间范围，如 '15m', '1h', '7d'")
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")


class TaskInfo(BaseModel):
    """任务信息模型"""
    id: str = Field(..., description="任务ID")
    queue_name: str = Field(..., description="队列名称")
    status: str = Field(..., description="任务状态")
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    worker_id: Optional[str] = Field(None, description="工作节点ID")
    task_name: Optional[str] = Field(None, description="任务名称")
    task_data: Optional[Dict[str, Any]] = Field(None, description="任务数据")
    result: Optional[Any] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")
    retry_count: int = Field(default=0, description="重试次数")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    priority: Optional[int] = Field(None, description="优先级")
    consumer_group: Optional[str] = Field(None, description="消费者组")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TaskDetailResponse(BaseModel):
    """任务详细信息响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    data: Optional[TaskInfo] = Field(None, description="任务详细信息")
    error: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TaskActionRequest(BaseModel):
    """任务操作请求模型"""
    task_ids: List[str] = Field(..., min_items=1, description="任务ID列表")
    action: str = Field(..., description="操作类型", pattern="^(retry|cancel|delete)$")
    reason: Optional[str] = Field(None, description="操作原因")


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    data: List[TaskInfo] = Field(default=[], description="任务列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")
    error: Optional[str] = Field(None, description="错误信息")


class TaskMessageRequest(BaseModel):
    """单个任务消息请求模型"""
    queue: str = Field(..., description="队列名称（必需）", min_length=1)
    priority: Optional[int] = Field(None, description="优先级（1最高，数字越大优先级越低）", ge=1)
    delay: Optional[int] = Field(None, description="延迟执行时间（秒）", ge=0)
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="任务参数（字典格式）")
    args: Optional[List[Any]] = Field(None, description="任务位置参数（可选）")

    class Config:
        json_schema_extra = {
            "example": {
                "queue": "email_queue",
                "priority": 5,
                "delay": 10,
                "kwargs": {
                    "to": "user@example.com",
                    "subject": "Hello",
                    "body": "This is a test email"
                }
            }
        }


class SendTasksRequest(BaseModel):
    """批量发送任务请求模型（namespace 在 URL 路径中）"""
    messages: List[TaskMessageRequest] = Field(..., description="任务消息列表", min_items=1)

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "queue": "email_queue",
                        "priority": 5,
                        "kwargs": {
                            "to": "user1@example.com",
                            "subject": "Test Email 1"
                        }
                    },
                    {
                        "queue": "sms_queue",
                        "delay": 60,
                        "kwargs": {
                            "phone": "+1234567890",
                            "message": "Test SMS"
                        }
                    }
                ]
            }
        }


class SendTasksResponse(BaseModel):
    """批量发送任务响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    message: str = Field(default="Tasks sent successfully", description="响应消息")
    event_ids: List[str] = Field(default=[], description="任务事件ID列表")
    total_sent: int = Field(default=0, description="成功发送的任务数量")
    namespace: str = Field(..., description="命名空间")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Tasks sent successfully",
                "event_ids": [
                    "1730361234567-0",
                    "1730361234568-0"
                ],
                "total_sent": 2,
                "namespace": "default"
            }
        }