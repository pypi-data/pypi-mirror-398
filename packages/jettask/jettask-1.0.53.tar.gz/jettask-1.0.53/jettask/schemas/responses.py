"""
API 响应模型定义
包含所有 API 接口的响应模型和示例数据
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict



class SuccessResponse(BaseModel):
    """通用成功响应"""
    success: bool = Field(default=True, description="请求是否成功")
    message: Optional[str] = Field(None, description="响应消息")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "message": "操作成功"
        }
    })


class DataResponse(BaseModel):
    """通用数据响应"""
    success: bool = Field(default=True, description="请求是否成功")
    data: Any = Field(..., description="响应数据")
    message: Optional[str] = Field(None, description="响应消息")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "data": {},
            "message": "获取成功"
        }
    })


class PaginatedDataResponse(BaseModel):
    """分页数据响应"""
    success: bool = Field(default=True, description="请求是否成功")
    data: List[Any] = Field(default=[], description="数据列表")
    total: int = Field(..., description="总记录数", ge=0)
    page: int = Field(..., description="当前页码", ge=1)
    page_size: int = Field(..., description="每页大小", ge=1, le=100)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "data": [],
            "total": 0,
            "page": 1,
            "page_size": 20
        }
    })



class SystemStatsData(BaseModel):
    """系统统计数据"""
    total_queues: int = Field(..., description="队列总数", ge=0)
    total_tasks: int = Field(..., description="任务总数", ge=0)
    active_workers: int = Field(..., description="活跃 Worker 数", ge=0)
    pending_tasks: int = Field(..., description="待处理任务数", ge=0)
    processing_tasks: int = Field(..., description="处理中任务数", ge=0)
    completed_tasks: int = Field(..., description="已完成任务数", ge=0)
    failed_tasks: int = Field(..., description="失败任务数", ge=0)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_queues": 5,
            "total_tasks": 1250,
            "active_workers": 12,
            "pending_tasks": 45,
            "processing_tasks": 8,
            "completed_tasks": 1180,
            "failed_tasks": 17
        }
    })


class SystemStatsResponse(BaseModel):
    """系统统计响应"""
    success: bool = Field(default=True, description="请求是否成功")
    data: SystemStatsData = Field(..., description="系统统计数据")
    namespace: str = Field(..., description="命名空间")
    timestamp: datetime = Field(default_factory=datetime.now, description="统计时间")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "data": {
                "total_queues": 5,
                "total_tasks": 1250,
                "active_workers": 12,
                "pending_tasks": 45,
                "processing_tasks": 8,
                "completed_tasks": 1180,
                "failed_tasks": 17
            },
            "namespace": "default",
            "timestamp": "2025-10-18T10:30:00Z"
        }
    })


class DashboardStatsData(BaseModel):
    """仪表板统计数据"""
    total_tasks: int = Field(..., description="任务总数", ge=0)
    success_count: int = Field(..., description="成功任务数", ge=0)
    failed_count: int = Field(..., description="失败任务数", ge=0)
    success_rate: float = Field(..., description="成功率 (0-100)", ge=0, le=100)
    throughput: float = Field(..., description="吞吐量 (任务/秒)", ge=0)
    avg_processing_time: float = Field(..., description="平均处理时间 (秒)", ge=0)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_tasks": 1250,
            "success_count": 1180,
            "failed_count": 17,
            "success_rate": 94.4,
            "throughput": 12.5,
            "avg_processing_time": 2.3
        }
    })


class DashboardStatsResponse(BaseModel):
    """仪表板统计响应"""
    success: bool = Field(default=True, description="请求是否成功")
    data: DashboardStatsData = Field(..., description="仪表板统计数据")
    namespace: str = Field(..., description="命名空间")
    time_range: str = Field(..., description="时间范围")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "data": {
                "total_tasks": 1250,
                "success_count": 1180,
                "failed_count": 17,
                "success_rate": 94.4,
                "throughput": 12.5,
                "avg_processing_time": 2.3
            },
            "namespace": "default",
            "time_range": "24h"
        }
    })


class QueueRankingItem(BaseModel):
    """队列排行项"""
    queue_name: str = Field(..., description="队列名称")
    value: float = Field(..., description="指标值", ge=0)
    rank: int = Field(..., description="排名", ge=1)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "queue_name": "email_queue",
            "value": 150.5,
            "rank": 1
        }
    })


class TopQueuesResponse(BaseModel):
    """队列排行榜响应"""
    success: bool = Field(default=True, description="请求是否成功")
    data: List[QueueRankingItem] = Field(..., description="排行榜数据")
    metric: str = Field(..., description="指标类型 (backlog/error)")
    namespace: str = Field(..., description="命名空间")
    time_range: str = Field(..., description="时间范围")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "data": [
                {"queue_name": "email_queue", "value": 150, "rank": 1},
                {"queue_name": "sms_queue", "value": 89, "rank": 2},
                {"queue_name": "push_queue", "value": 45, "rank": 3}
            ],
            "metric": "backlog",
            "namespace": "default",
            "time_range": "24h"
        }
    })



class NamespaceStatistics(BaseModel):
    """命名空间统计信息"""
    total_queues: int = Field(..., description="队列总数", ge=0)
    total_tasks: int = Field(..., description="任务总数", ge=0)
    active_workers: int = Field(..., description="活跃 Worker 数", ge=0)
    redis_memory_usage: Optional[int] = Field(None, description="Redis 内存使用 (bytes)", ge=0)
    db_connections: Optional[int] = Field(None, description="数据库连接数", ge=0)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_queues": 5,
            "total_tasks": 1250,
            "active_workers": 12,
            "redis_memory_usage": 10485760,
            "db_connections": 5
        }
    })


class NamespaceStatisticsResponse(BaseModel):
    """命名空间统计响应"""
    success: bool = Field(default=True, description="请求是否成功")
    data: NamespaceStatistics = Field(..., description="统计数据")
    namespace: str = Field(..., description="命名空间名称")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "data": {
                "total_queues": 5,
                "total_tasks": 1250,
                "active_workers": 12,
                "redis_memory_usage": 10485760,
                "db_connections": 5
            },
            "namespace": "default"
        }
    })



class WorkerHeartbeatInfo(BaseModel):
    """Worker 心跳信息"""
    worker_id: str = Field(..., description="Worker ID")
    queue_name: str = Field(..., description="队列名称")
    status: str = Field(..., description="状态 (online/offline)")
    last_heartbeat: datetime = Field(..., description="最后心跳时间")
    tasks_processed: int = Field(..., description="已处理任务数", ge=0)
    current_task: Optional[str] = Field(None, description="当前处理的任务 ID")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "worker_id": "worker-001",
            "queue_name": "email_queue",
            "status": "online",
            "last_heartbeat": "2025-10-18T10:30:00Z",
            "tasks_processed": 150,
            "current_task": "task-12345"
        }
    })


class WorkersResponse(BaseModel):
    """Workers 列表响应"""
    success: bool = Field(default=True, description="请求是否成功")
    namespace: str = Field(..., description="命名空间")
    queue: str = Field(..., description="队列名称")
    workers: List[WorkerHeartbeatInfo] = Field(..., description="Worker 列表")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "namespace": "default",
            "queue": "email_queue",
            "workers": [
                {
                    "worker_id": "worker-001",
                    "queue_name": "email_queue",
                    "status": "online",
                    "last_heartbeat": "2025-10-18T10:30:00Z",
                    "tasks_processed": 150,
                    "current_task": "task-12345"
                }
            ]
        }
    })


class WorkerSummary(BaseModel):
    """Worker 汇总统计"""
    total_workers: int = Field(..., description="总 Worker 数", ge=0)
    online_workers: int = Field(..., description="在线 Worker 数", ge=0)
    offline_workers: int = Field(..., description="离线 Worker 数", ge=0)
    total_tasks_processed: int = Field(..., description="总处理任务数", ge=0)
    avg_tasks_per_worker: float = Field(..., description="平均每个 Worker 处理任务数", ge=0)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_workers": 12,
            "online_workers": 10,
            "offline_workers": 2,
            "total_tasks_processed": 1500,
            "avg_tasks_per_worker": 125.0
        }
    })


class WorkerSummaryResponse(BaseModel):
    """Worker 汇总统计响应"""
    success: bool = Field(default=True, description="请求是否成功")
    namespace: str = Field(..., description="命名空间")
    queue: str = Field(..., description="队列名称")
    summary: WorkerSummary = Field(..., description="汇总统计")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "namespace": "default",
            "queue": "email_queue",
            "summary": {
                "total_workers": 12,
                "online_workers": 10,
                "offline_workers": 2,
                "total_tasks_processed": 1500,
                "avg_tasks_per_worker": 125.0
            }
        }
    })


class WorkerOfflineRecord(BaseModel):
    """Worker 离线记录"""
    worker_id: str = Field(..., description="Worker ID")
    queue_name: str = Field(..., description="队列名称")
    offline_time: datetime = Field(..., description="离线时间")
    last_task: Optional[str] = Field(None, description="最后处理的任务 ID")
    reason: Optional[str] = Field(None, description="离线原因")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "worker_id": "worker-002",
            "queue_name": "email_queue",
            "offline_time": "2025-10-18T09:30:00Z",
            "last_task": "task-12340",
            "reason": "heartbeat_timeout"
        }
    })


class WorkerOfflineHistoryResponse(BaseModel):
    """Worker 离线历史响应"""
    success: bool = Field(default=True, description="请求是否成功")
    history: List[WorkerOfflineRecord] = Field(..., description="离线历史记录")
    total: int = Field(..., description="总记录数", ge=0)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "history": [
                {
                    "worker_id": "worker-002",
                    "queue_name": "email_queue",
                    "offline_time": "2025-10-18T09:30:00Z",
                    "last_task": "task-12340",
                    "reason": "heartbeat_timeout"
                }
            ],
            "total": 1
        }
    })



class DatabaseStatus(BaseModel):
    """数据库状态"""
    connected: bool = Field(..., description="是否已连接")
    host: Optional[str] = Field(None, description="主机地址")
    port: Optional[int] = Field(None, description="端口")
    database: Optional[str] = Field(None, description="数据库名称")
    pool_size: Optional[int] = Field(None, description="连接池大小", ge=0)
    active_connections: Optional[int] = Field(None, description="活跃连接数", ge=0)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "connected": True,
            "host": "localhost",
            "port": 5432,
            "database": "jettask",
            "pool_size": 10,
            "active_connections": 3
        }
    })


class SystemSettings(BaseModel):
    """系统设置"""
    api_version: str = Field(..., description="API 版本")
    service_name: str = Field(..., description="服务名称")
    environment: str = Field(..., description="运行环境 (development/staging/production)")
    debug_mode: bool = Field(..., description="是否开启调试模式")
    database: DatabaseStatus = Field(..., description="数据库状态")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "api_version": "v1",
            "service_name": "JetTask WebUI",
            "environment": "development",
            "debug_mode": True,
            "database": {
                "connected": True,
                "host": "localhost",
                "port": 5432,
                "database": "jettask",
                "pool_size": 10,
                "active_connections": 3
            }
        }
    })


class SystemSettingsResponse(BaseModel):
    """系统设置响应"""
    success: bool = Field(default=True, description="请求是否成功")
    data: SystemSettings = Field(..., description="系统设置")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "data": {
                "api_version": "v1",
                "service_name": "JetTask WebUI",
                "environment": "development",
                "debug_mode": True,
                "database": {
                    "connected": True,
                    "host": "localhost",
                    "port": 5432,
                    "database": "jettask",
                    "pool_size": 10,
                    "active_connections": 3
                }
            }
        }
    })


class DatabaseStatusResponse(BaseModel):
    """数据库状态响应"""
    success: bool = Field(default=True, description="请求是否成功")
    data: DatabaseStatus = Field(..., description="数据库状态")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "data": {
                "connected": True,
                "host": "localhost",
                "port": 5432,
                "database": "jettask",
                "pool_size": 10,
                "active_connections": 3
            }
        }
    })


__all__ = [
    'SuccessResponse',
    'DataResponse',
    'PaginatedDataResponse',

    'SystemStatsData',
    'SystemStatsResponse',
    'DashboardStatsData',
    'DashboardStatsResponse',
    'QueueRankingItem',
    'TopQueuesResponse',

    'NamespaceStatistics',
    'NamespaceStatisticsResponse',

    'WorkerHeartbeatInfo',
    'WorkersResponse',
    'WorkerSummary',
    'WorkerSummaryResponse',
    'WorkerOfflineRecord',
    'WorkerOfflineHistoryResponse',

    'DatabaseStatus',
    'SystemSettings',
    'SystemSettingsResponse',
    'DatabaseStatusResponse',
]
