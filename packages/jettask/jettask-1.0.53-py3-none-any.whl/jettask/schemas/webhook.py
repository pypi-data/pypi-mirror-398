"""
Webhook 相关的 Pydantic 模型

用于接收第三方平台的 webhook 回调通知
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class WebhookStatus(str, Enum):
    """Webhook 处理状态"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class WebhookReceiveResponse(BaseModel):
    """
    接收 webhook 通知的响应模型
    """
    success: bool = Field(..., description="是否成功接收")
    message: str = Field(..., description="响应消息")
    callback_id: str = Field(..., description="回调 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Webhook received successfully",
                "callback_id": "cb_abc123"
            }
        }


class WebhookInfo(BaseModel):
    """
    Webhook 记录信息
    """
    id: int = Field(..., description="Webhook 记录 ID")
    namespace: str = Field(..., description="命名空间")
    callback_id: str = Field(..., description="回调 ID")
    payload: Dict[str, Any] = Field(..., description="原始 webhook 载荷")
    status: WebhookStatus = Field(..., description="处理状态")
    received_at: datetime = Field(..., description="接收时间")


class WebhookListResponse(BaseModel):
    """
    Webhook 列表响应
    """
    success: bool = Field(True, description="是否成功")
    data: List[WebhookInfo] = Field(default_factory=list, description="Webhook 记录列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
