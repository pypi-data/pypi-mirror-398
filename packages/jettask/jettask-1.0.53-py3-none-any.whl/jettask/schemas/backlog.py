"""
积压监控相关的数据模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BacklogLatestRequest(BaseModel):
    """获取最新积压数据请求模型"""
    queues: Optional[List[str]] = Field(None, description="队列名称列表，为空时返回所有队列")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "queues": ["email_queue", "sms_queue"]
            },
            {
                "queues": []
            }
        ]
    })


class BacklogTrendRequest(BaseModel):
    """积压趋势请求模型"""
    queue_name: Optional[str] = Field(None, description="队列名称，为空时查询所有队列")
    time_range: Optional[str] = Field("1h", description="时间范围，如 '1h', '6h', '1d', '7d'")
    start_time: Optional[str] = Field(None, description="开始时间（ISO格式）")
    end_time: Optional[str] = Field(None, description="结束时间（ISO格式）")
    interval: str = Field(default="5m", description="数据聚合间隔，如 '1m', '5m', '1h'")
    metrics: List[str] = Field(
        default=["pending", "processing", "completed", "failed"],
        description="要查询的指标类型"
    )

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "queue_name": "email_queue",
                "time_range": "1h",
                "interval": "5m",
                "metrics": ["pending", "processing"]
            },
            {
                "queue_name": "sms_queue",
                "start_time": "2025-10-18T09:00:00Z",
                "end_time": "2025-10-18T10:00:00Z",
                "interval": "1m",
                "metrics": ["pending", "processing", "completed", "failed"]
            },
            {
                "time_range": "24h",
                "interval": "1h"
            }
        ]
    })


class BacklogSnapshot(BaseModel):
    """积压快照模型"""
    timestamp: datetime = Field(..., description="快照时间")
    namespace: str = Field(..., description="命名空间")
    queue_name: str = Field(..., description="队列名称")
    
    pending_count: int = Field(default=0, description="待处理任务数")
    processing_count: int = Field(default=0, description="处理中任务数")
    completed_count: int = Field(default=0, description="已完成任务数")
    failed_count: int = Field(default=0, description="失败任务数")
    total_count: int = Field(default=0, description="总任务数")
    
    throughput: float = Field(default=0.0, description="吞吐量（任务/分钟）")
    avg_processing_time: Optional[float] = Field(None, description="平均处理时间（秒）")
    success_rate: float = Field(default=0.0, description="成功率")
    
    queue_size: int = Field(default=0, description="队列大小")
    oldest_task_age: Optional[int] = Field(None, description="最老任务年龄（秒）")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class BacklogStatistics(BaseModel):
    """积压统计模型"""
    namespace: str = Field(..., description="命名空间")
    queue_name: Optional[str] = Field(None, description="队列名称")
    time_period: str = Field(..., description="统计时间段")
    
    total_tasks: int = Field(default=0, description="总任务数")
    peak_pending: int = Field(default=0, description="峰值待处理任务数")
    avg_pending: float = Field(default=0.0, description="平均待处理任务数")
    peak_processing: int = Field(default=0, description="峰值处理中任务数")
    avg_processing: float = Field(default=0.0, description="平均处理中任务数")
    
    avg_throughput: float = Field(default=0.0, description="平均吞吐量")
    peak_throughput: float = Field(default=0.0, description="峰值吞吐量")
    avg_processing_time: Optional[float] = Field(None, description="平均处理时间")
    overall_success_rate: float = Field(default=0.0, description="总体成功率")
    
    start_time: datetime = Field(..., description="统计开始时间")
    end_time: datetime = Field(..., description="统计结束时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class BacklogTrendResponse(BaseModel):
    """积压趋势响应模型"""
    namespace: str = Field(..., description="命名空间")
    queue_name: Optional[str] = Field(None, description="队列名称")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    interval: str = Field(..., description="数据间隔")
    
    timestamps: List[datetime] = Field(default=[], description="时间戳列表")
    pending_series: List[int] = Field(default=[], description="待处理任务数时间序列")
    processing_series: List[int] = Field(default=[], description="处理中任务数时间序列")
    completed_series: List[int] = Field(default=[], description="已完成任务数时间序列")
    failed_series: List[int] = Field(default=[], description="失败任务数时间序列")
    throughput_series: List[float] = Field(default=[], description="吞吐量时间序列")
    
    statistics: Optional[BacklogStatistics] = Field(None, description="统计摘要")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class BacklogAlert(BaseModel):
    """积压告警模型"""
    id: str = Field(..., description="告警ID")
    namespace: str = Field(..., description="命名空间")
    queue_name: str = Field(..., description="队列名称")
    alert_type: str = Field(..., description="告警类型")
    severity: str = Field(..., description="严重级别")
    message: str = Field(..., description="告警消息")
    current_value: float = Field(..., description="当前值")
    threshold: float = Field(..., description="阈值")
    status: str = Field(..., description="告警状态")
    created_at: datetime = Field(..., description="创建时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }