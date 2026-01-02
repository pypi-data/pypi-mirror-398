"""
告警相关的数据模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AlertRuleRequest(BaseModel):
    """告警规则请求模型"""
    rule_name: str = Field(..., description="规则名称")
    metric_type: str = Field(..., description="指标类型")
    threshold: float = Field(..., description="阈值")
    operator: str = Field(..., description="比较操作符", pattern="^(gt|gte|lt|lte|eq|ne)$")
    duration: int = Field(..., ge=1, description="持续时间（秒）")
    severity: str = Field(..., description="严重级别", pattern="^(low|medium|high|critical)$")
    enabled: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(None, description="规则描述")


class AlertRuleCreate(BaseModel):
    """创建告警规则请求模型"""
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    metric_type: str = Field(..., description="监控指标类型")
    threshold: float = Field(..., description="告警阈值")
    comparison_operator: str = Field(..., description="比较操作符")
    evaluation_window: int = Field(..., description="评估窗口（秒）")
    severity: str = Field(..., description="告警级别")
    notification_channels: List[str] = Field(default=[], description="通知渠道")
    enabled: bool = Field(default=True, description="是否启用")


class AlertRuleUpdate(BaseModel):
    """更新告警规则请求模型"""
    name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    metric_type: Optional[str] = Field(None, description="监控指标类型")
    threshold: Optional[float] = Field(None, description="告警阈值")
    comparison_operator: Optional[str] = Field(None, description="比较操作符")
    evaluation_window: Optional[int] = Field(None, description="评估窗口（秒）")
    severity: Optional[str] = Field(None, description="告警级别")
    notification_channels: Optional[List[str]] = Field(None, description="通知渠道")
    enabled: Optional[bool] = Field(None, description="是否启用")


class AlertRule(BaseModel):
    """告警规则模型"""
    id: str = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    metric_type: str = Field(..., description="监控指标类型")
    threshold: float = Field(..., description="告警阈值")
    comparison_operator: str = Field(..., description="比较操作符")
    evaluation_window: int = Field(..., description="评估窗口（秒）")
    severity: str = Field(..., description="告警级别")
    notification_channels: List[str] = Field(default=[], description="通知渠道")
    enabled: bool = Field(default=True, description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class AlertInstance(BaseModel):
    """告警实例模型"""
    id: str = Field(..., description="告警实例ID")
    rule_id: str = Field(..., description="规则ID")
    rule_name: str = Field(..., description="规则名称")
    status: str = Field(..., description="告警状态", pattern="^(active|resolved|suppressed)$")
    severity: str = Field(..., description="告警级别")
    message: str = Field(..., description="告警消息")
    metric_value: float = Field(..., description="当前指标值")
    threshold: float = Field(..., description="阈值")
    started_at: datetime = Field(..., description="开始时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    acknowledged_at: Optional[datetime] = Field(None, description="确认时间")
    acknowledged_by: Optional[str] = Field(None, description="确认人")
    namespace: str = Field(..., description="命名空间")
    labels: Dict[str, str] = Field(default={}, description="标签")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class AlertSummary(BaseModel):
    """告警摘要模型"""
    total_alerts: int = Field(default=0, description="总告警数")
    active_alerts: int = Field(default=0, description="活跃告警数")
    resolved_alerts: int = Field(default=0, description="已解决告警数")
    critical_alerts: int = Field(default=0, description="严重告警数")
    high_alerts: int = Field(default=0, description="高级告警数")
    medium_alerts: int = Field(default=0, description="中级告警数")
    low_alerts: int = Field(default=0, description="低级告警数")