"""
队列相关的数据模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TimeRangeQuery(BaseModel):
    """时间范围查询模型"""
    queues: Optional[List[str]] = Field(None, description="队列名称列表，为空时统计所有队列")
    time_range: Optional[str] = Field(None, description="时间范围（如 '1h', '24h', '7d'），与 start_time/end_time 二选一")
    start_time: Optional[str] = Field(None, description="开始时间（ISO格式），与 time_range 二选一")
    end_time: Optional[str] = Field(None, description="结束时间（ISO格式），与 time_range 二选一")
    interval: Optional[str] = Field(default="1h", description="时间间隔")
    queue_name: Optional[str] = Field(None, description="队列名称（可选）")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "time_range": "1h",
                "queue_name": "email_queue"
            },
            {
                "start_time": "2025-10-18T09:00:00Z",
                "end_time": "2025-10-18T10:00:00Z",
                "queues": ["email_queue", "sms_queue"],
                "interval": "5m"
            }
        ]
    })


class QueueStatsResponse(BaseModel):
    """队列统计响应模型"""
    queue_name: str = Field(..., description="队列名称")
    pending_count: int = Field(default=0, description="待处理任务数")
    processing_count: int = Field(default=0, description="处理中任务数")
    completed_count: int = Field(default=0, description="已完成任务数")
    failed_count: int = Field(default=0, description="失败任务数")
    success_rate: float = Field(default=0.0, description="成功率")
    avg_processing_time: Optional[float] = Field(None, description="平均处理时间")


class QueueTimelineResponse(BaseModel):
    """队列时间线响应模型"""
    queue_name: str = Field(..., description="队列名称")
    timeline: List[Dict[str, Any]] = Field(default=[], description="时间线数据")


class TrimQueueRequest(BaseModel):
    """修剪队列请求模型"""
    queue_name: str = Field(..., description="队列名称")
    max_length: int = Field(..., ge=1, description="最大长度")
    trim_strategy: str = Field(default="oldest", description="修剪策略", pattern="^(oldest|newest)$")


class QueueInfo(BaseModel):
    """队列信息模型"""
    name: str = Field(..., description="队列名称")
    namespace: str = Field(..., description="命名空间")
    pending_count: int = Field(default=0, description="待处理任务数")
    processing_count: int = Field(default=0, description="处理中任务数")
    completed_count: int = Field(default=0, description="已完成任务数")
    failed_count: int = Field(default=0, description="失败任务数")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class QueueStats(BaseModel):
    """队列统计模型"""
    queue_name: str = Field(..., description="队列名称")
    total_tasks: int = Field(default=0, description="总任务数")
    pending_tasks: int = Field(default=0, description="待处理任务数")
    processing_tasks: int = Field(default=0, description="处理中任务数")
    completed_tasks: int = Field(default=0, description="已完成任务数")
    failed_tasks: int = Field(default=0, description="失败任务数")
    success_rate: float = Field(default=0.0, description="成功率")
    avg_processing_time: Optional[float] = Field(None, description="平均处理时间")
    throughput: Optional[float] = Field(None, description="吞吐量（任务/秒）")
    last_activity: Optional[datetime] = Field(None, description="最后活动时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class QueueActionRequest(BaseModel):
    """队列操作请求模型"""
    queue_names: List[str] = Field(..., min_items=1, description="队列名称列表")
    action: str = Field(..., description="操作类型", pattern="^(pause|resume|clear|delete)$")
    reason: Optional[str] = Field(None, description="操作原因")
    force: bool = Field(default=False, description="是否强制执行")


class TaskRunsQueryRequest(BaseModel):
    """任务执行记录查询请求模型"""
    queue: str = Field(..., description="基础队列名称（必填），系统会自动展开为所有优先级队列")
    start_time: Optional[datetime] = Field(None, description="开始时间（ISO格式）")
    end_time: Optional[datetime] = Field(None, description="结束时间（ISO格式）")
    time_range: Optional[str] = Field(None, description="时间范围，如 15m, 1h, 24h 等，与 start_time/end_time 二选一")
    where: Optional[str] = Field(None, description="SQL WHERE 条件（不含 WHERE 关键字），如: status = 'success' AND duration > 1.0")
    page: int = Field(default=1, ge=1, description="页码（从1开始）")
    page_size: int = Field(default=20, ge=1, le=1000, description="每页大小（1-1000）")
    sort_field: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向（asc/desc）", pattern="^(asc|desc)$")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "queue": "email_queue",
            "time_range": "1h",
            "where": "status = 'success' AND task_name LIKE '%email%'",
            "page": 1,
            "page_size": 20,
            "sort_field": "created_at",
            "sort_order": "desc"
        }
    })