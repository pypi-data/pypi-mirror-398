"""
定时任务相关的数据模型
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ScheduleConfig(BaseModel):
    """调度配置模型"""
    schedule_type: str = Field(..., description="调度类型", pattern="^(cron|interval)$")
    cron_expression: Optional[str] = Field(None, description="Cron表达式（当schedule_type为cron时）")
    interval_seconds: Optional[int] = Field(None, ge=1, description="间隔秒数（当schedule_type为interval时）")
    timezone: str = Field(default="UTC", description="时区")
    max_instances: int = Field(default=1, ge=1, description="最大实例数")
    
    def validate_schedule_config(self):
        if self.schedule_type == "cron" and not self.cron_expression:
            raise ValueError("Cron类型调度必须提供cron_expression")
        if self.schedule_type == "interval" and not self.interval_seconds:
            raise ValueError("Interval类型调度必须提供interval_seconds")


class ScheduledTaskRequest(BaseModel):
    """定时任务请求模型"""
    task_name: str = Field(..., description="任务名称")
    task_function: str = Field(..., description="任务函数")
    schedule_config: ScheduleConfig = Field(..., description="调度配置")
    task_args: Optional[list] = Field(default=[], description="任务参数")
    task_kwargs: Optional[Dict[str, Any]] = Field(default={}, description="任务关键字参数")
    queue_name: Optional[str] = Field(None, description="队列名称")
    priority: int = Field(default=0, description="优先级")
    enabled: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(None, description="任务描述")


class ScheduledTaskCreate(BaseModel):
    """创建定时任务请求模型"""
    name: str = Field(..., description="任务名称")
    task_function: str = Field(..., description="任务函数")
    schedule_type: str = Field(..., description="调度类型", pattern="^(cron|interval)$")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, ge=1, description="间隔秒数")
    task_args: Optional[list] = Field(default=[], description="任务参数")
    task_kwargs: Optional[Dict[str, Any]] = Field(default={}, description="任务关键字参数")
    enabled: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(None, description="任务描述")


class ScheduledTaskUpdate(BaseModel):
    """更新定时任务请求模型"""
    name: Optional[str] = Field(None, description="任务名称")
    task_function: Optional[str] = Field(None, description="任务函数")
    schedule_type: Optional[str] = Field(None, description="调度类型")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, ge=1, description="间隔秒数")
    task_args: Optional[list] = Field(None, description="任务参数")
    task_kwargs: Optional[Dict[str, Any]] = Field(None, description="任务关键字参数")
    enabled: Optional[bool] = Field(None, description="是否启用")
    description: Optional[str] = Field(None, description="任务描述")


class ScheduledTaskCreateRequest(BaseModel):
    """定时任务创建请求模型（详细版）"""
    task_name: str = Field(..., min_length=1, max_length=255, description="任务名称")
    task_function: str = Field(..., min_length=1, description="任务函数路径")
    schedule_type: str = Field(..., description="调度类型", pattern="^(cron|interval|once)$")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, ge=1, le=86400*365, description="间隔秒数")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    task_args: list = Field(default=[], description="任务参数")
    task_kwargs: Dict[str, Any] = Field(default={}, description="任务关键字参数")
    queue_name: Optional[str] = Field(None, description="目标队列")
    priority: int = Field(default=0, ge=0, le=100, description="优先级")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    timeout: Optional[int] = Field(None, ge=1, description="超时时间（秒）")
    enabled: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(None, max_length=1000, description="任务描述")


class ScheduledTaskResponse(BaseModel):
    """定时任务响应模型"""
    id: str = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    task_function: str = Field(..., description="任务函数")
    schedule_type: str = Field(..., description="调度类型")
    next_run_time: Optional[datetime] = Field(None, description="下次运行时间")
    last_run_time: Optional[datetime] = Field(None, description="上次运行时间")
    status: str = Field(..., description="任务状态")
    enabled: bool = Field(..., description="是否启用")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ScheduledTaskInfo(BaseModel):
    """定时任务详细信息模型"""
    id: str = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    task_function: str = Field(..., description="任务函数")
    schedule_type: str = Field(..., description="调度类型")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, description="间隔秒数")
    task_args: list = Field(default=[], description="任务参数")
    task_kwargs: Dict[str, Any] = Field(default={}, description="任务关键字参数")
    queue_name: Optional[str] = Field(None, description="队列名称")
    priority: int = Field(default=0, description="优先级")
    max_retries: int = Field(default=3, description="最大重试次数")
    timeout: Optional[int] = Field(None, description="超时时间")
    enabled: bool = Field(default=True, description="是否启用")
    status: str = Field(..., description="任务状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    next_run_time: Optional[datetime] = Field(None, description="下次运行时间")
    last_run_time: Optional[datetime] = Field(None, description="上次运行时间")
    run_count: int = Field(default=0, description="运行次数")
    success_count: int = Field(default=0, description="成功次数")
    failure_count: int = Field(default=0, description="失败次数")
    description: Optional[str] = Field(None, description="任务描述")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }