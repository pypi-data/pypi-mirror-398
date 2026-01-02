"""
资产管理相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AssetType(str, Enum):
    """资产类型"""
    COMPUTE_NODE = "compute_node"   
    API_KEY = "api_key"             
    CONFIG = "config"               


class AssetStatus(str, Enum):
    """资产状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class AssetCreate(BaseModel):
    """创建资产请求"""
    asset_type: AssetType = Field(..., description="资产类型")
    asset_group: str = Field(..., description="资产分组（如 comfyui、openai）")
    name: str = Field(..., description="资产名称（同一分组内唯一）")
    config: Dict[str, Any] = Field(default_factory=dict, description="资产配置")
    weight: int = Field(default=1, ge=0, description="权重（用于负载均衡）")
    description: Optional[str] = Field(None, description="描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "asset_type": "compute_node",
                "asset_group": "comfyui",
                "name": "node-1",
                "config": {
                    "url": "http://192.168.1.100:8188",
                    "max_concurrent": 2
                },
                "weight": 1,
                "description": "ComfyUI 节点 1"
            }
        }


class AssetUpdate(BaseModel):
    """更新资产请求"""
    config: Optional[Dict[str, Any]] = Field(None, description="资产配置")
    status: Optional[AssetStatus] = Field(None, description="状态")
    weight: Optional[int] = Field(None, ge=0, description="权重")
    description: Optional[str] = Field(None, description="描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class AssetInfo(BaseModel):
    """资产信息"""
    id: int = Field(..., description="资产 ID")
    namespace: str = Field(..., description="命名空间")
    asset_type: AssetType = Field(..., description="资产类型")
    asset_group: str = Field(..., description="资产分组")
    name: str = Field(..., description="资产名称")
    config: Dict[str, Any] = Field(..., description="资产配置")
    status: AssetStatus = Field(..., description="状态")
    weight: int = Field(..., description="权重")
    description: Optional[str] = Field(None, description="描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class AssetListResponse(BaseModel):
    """资产列表响应"""
    success: bool = Field(True)
    data: List[AssetInfo] = Field(default_factory=list)
    total: int = Field(...)
    page: int = Field(...)
    page_size: int = Field(...)


class AssetGroupSummary(BaseModel):
    """资产分组摘要"""
    asset_group: str = Field(..., description="分组名称")
    asset_type: AssetType = Field(..., description="资产类型")
    total: int = Field(..., description="总数")
    active: int = Field(..., description="可用数量")
    inactive: int = Field(..., description="停用数量")
    error: int = Field(..., description="异常数量")


class ComputeNodeStatus(BaseModel):
    """计算节点状态（用于负载均衡）"""
    asset_id: int = Field(..., description="资产 ID")
    name: str = Field(..., description="节点名称")
    url: str = Field(..., description="节点 URL")
    status: AssetStatus = Field(..., description="资产状态")
    weight: int = Field(..., description="权重")
    queue_remaining: int = Field(0, description="队列剩余任务数")
    is_available: bool = Field(True, description="是否可用")
    last_check: Optional[datetime] = Field(None, description="最后检查时间")
    error: Optional[str] = Field(None, description="错误信息")
