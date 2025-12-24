"""
通用数据模型
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(default=False, description="请求是否成功")
    error: str = Field(..., description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class FilterCondition(BaseModel):
    """筛选条件模型"""
    field: str = Field(..., description="字段名称")
    operator: str = Field(
        ..., 
        description="操作符", 
        pattern="^(eq|ne|gt|gte|lt|lte|in|not_in|like|not_like|is_null|is_not_null|between)$"
    )
    value: Optional[Union[str, int, float, bool, List[Any]]] = Field(None, description="比较值")
    case_sensitive: bool = Field(default=True, description="是否区分大小写（字符串比较时）")


class BaseListRequest(BaseModel):
    """基础列表请求模型"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: str = Field(default="desc", description="排序顺序", pattern="^(asc|desc)$")
    filters: List[FilterCondition] = Field(default=[], description="筛选条件")
    search: Optional[str] = Field(None, description="搜索关键词")


class TimeRangeRequest(BaseModel):
    """时间范围请求模型"""
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    time_range: Optional[str] = Field(None, description="时间范围，如 '15m', '1h', '6h', '1d', '7d', '30d'")
    timezone: str = Field(default="UTC", description="时区")
    
    def get_time_bounds(self) -> tuple[Optional[datetime], Optional[datetime]]:
        if self.start_time and self.end_time:
            return self.start_time, self.end_time
        elif self.time_range:
            return None, None
        return None, None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class BatchOperationRequest(BaseModel):
    """批量操作请求模型"""
    operation: str = Field(..., description="操作类型")
    target_ids: List[str] = Field(..., min_items=1, description="目标ID列表")
    parameters: Dict[str, Any] = Field(default={}, description="操作参数")
    force: bool = Field(default=False, description="是否强制执行")
    reason: Optional[str] = Field(None, description="操作原因")


class BatchOperationResponse(BaseModel):
    """批量操作响应模型"""
    success: bool = Field(..., description="整体操作是否成功")
    total_count: int = Field(..., description="总操作数")
    success_count: int = Field(..., description="成功数")
    failure_count: int = Field(..., description="失败数")
    results: List[Dict[str, Any]] = Field(default=[], description="详细结果")
    errors: List[str] = Field(default=[], description="错误信息列表")


class PaginationResponse(BaseModel):
    """分页响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class ListResponse(BaseModel):
    """列表响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    data: List[Any] = Field(default=[], description="数据列表")
    pagination: Optional[PaginationResponse] = Field(None, description="分页信息")
    filters_applied: List[FilterCondition] = Field(default=[], description="已应用的筛选条件")
    sort_applied: Optional[Dict[str, str]] = Field(None, description="已应用的排序")


class HealthCheck(BaseModel):
    """健康检查模型"""
    status: str = Field(..., description="服务状态", pattern="^(healthy|unhealthy|degraded)$")
    version: str = Field(..., description="服务版本")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="检查时间")
    uptime: int = Field(..., description="运行时间（秒）")
    dependencies: Dict[str, Dict[str, Any]] = Field(default={}, description="依赖服务状态")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SystemConfigUpdateRequest(BaseModel):
    """系统配置更新请求模型"""
    config_key: str = Field(..., description="配置键")
    config_value: Any = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    category: Optional[str] = Field(None, description="配置分类")
    is_sensitive: bool = Field(default=False, description="是否为敏感配置")


class ApiResponse(BaseModel):
    """通用API响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    data: Optional[Any] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应消息")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }