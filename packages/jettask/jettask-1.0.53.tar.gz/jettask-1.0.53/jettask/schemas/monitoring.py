"""
监控和分析相关的数据模型
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class MetricPoint(BaseModel):
    """指标数据点模型"""
    timestamp: datetime = Field(..., description="时间戳")
    value: Union[int, float] = Field(..., description="指标值")
    labels: Dict[str, str] = Field(default={}, description="标签")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TimeSeries(BaseModel):
    """时间序列模型"""
    metric_name: str = Field(..., description="指标名称")
    labels: Dict[str, str] = Field(default={}, description="标签")
    data_points: List[MetricPoint] = Field(default=[], description="数据点列表")
    unit: Optional[str] = Field(None, description="指标单位")
    description: Optional[str] = Field(None, description="指标描述")


class MonitoringMetrics(BaseModel):
    """监控指标模型"""
    namespace: str = Field(..., description="命名空间")
    timestamp: datetime = Field(..., description="采集时间")
    
    cpu_usage: Optional[float] = Field(None, description="CPU使用率")
    memory_usage: Optional[float] = Field(None, description="内存使用率")
    disk_usage: Optional[float] = Field(None, description="磁盘使用率")
    network_io: Optional[Dict[str, float]] = Field(None, description="网络IO统计")
    
    redis_memory_usage: Optional[float] = Field(None, description="Redis内存使用")
    redis_connected_clients: Optional[int] = Field(None, description="Redis连接数")
    redis_operations_per_sec: Optional[float] = Field(None, description="Redis每秒操作数")
    redis_keyspace_hits: Optional[int] = Field(None, description="Redis键空间命中数")
    redis_keyspace_misses: Optional[int] = Field(None, description="Redis键空间未命中数")
    
    total_queues: int = Field(default=0, description="总队列数")
    total_tasks: int = Field(default=0, description="总任务数")
    pending_tasks: int = Field(default=0, description="待处理任务数")
    processing_tasks: int = Field(default=0, description="处理中任务数")
    completed_tasks: int = Field(default=0, description="已完成任务数")
    failed_tasks: int = Field(default=0, description="失败任务数")
    
    active_workers: int = Field(default=0, description="活跃工作节点数")
    idle_workers: int = Field(default=0, description="空闲工作节点数")
    busy_workers: int = Field(default=0, description="忙碌工作节点数")
    
    avg_task_processing_time: Optional[float] = Field(None, description="平均任务处理时间")
    task_throughput: Optional[float] = Field(None, description="任务吞吐量")
    success_rate: Optional[float] = Field(None, description="任务成功率")
    error_rate: Optional[float] = Field(None, description="错误率")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class AnalyticsData(BaseModel):
    """分析数据模型"""
    metric_type: str = Field(..., description="指标类型")
    aggregation_period: str = Field(..., description="聚合周期")
    time_series: List[TimeSeries] = Field(default=[], description="时间序列数据")
    summary: Dict[str, Any] = Field(default={}, description="汇总信息")
    insights: List[str] = Field(default=[], description="数据洞察")
    recommendations: List[str] = Field(default=[], description="建议")


class SystemHealth(BaseModel):
    """系统健康状态模型"""
    overall_status: str = Field(..., description="整体状态", pattern="^(healthy|warning|critical|unknown)$")
    last_check: datetime = Field(..., description="最后检查时间")
    
    redis_status: str = Field(..., description="Redis状态")
    database_status: str = Field(..., description="数据库状态")
    queue_system_status: str = Field(..., description="队列系统状态")
    worker_system_status: str = Field(..., description="工作节点系统状态")
    
    redis_latency: Optional[float] = Field(None, description="Redis延迟（毫秒）")
    database_latency: Optional[float] = Field(None, description="数据库延迟（毫秒）")
    queue_backlog_health: str = Field(..., description="队列积压健康状态")
    error_rate_health: str = Field(..., description="错误率健康状态")
    
    active_alerts: List[Dict[str, Any]] = Field(default=[], description="活跃告警")
    warnings: List[str] = Field(default=[], description="警告信息")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class DashboardOverviewRequest(BaseModel):
    """仪表板概览请求模型"""
    namespace: Optional[str] = Field(None, description="命名空间筛选")
    time_range: str = Field(default="1h", description="时间范围")
    refresh_interval: int = Field(default=30, description="刷新间隔（秒）")
    include_metrics: List[str] = Field(
        default=["tasks", "queues", "workers", "performance"],
        description="包含的指标类型"
    )


class DashboardOverview(BaseModel):
    """仪表板概览模型"""
    timestamp: datetime = Field(..., description="数据时间戳")
    namespace: Optional[str] = Field(None, description="命名空间")
    
    total_namespaces: int = Field(default=0, description="总命名空间数")
    total_queues: int = Field(default=0, description="总队列数")
    total_tasks: int = Field(default=0, description="总任务数")
    active_workers: int = Field(default=0, description="活跃工作节点数")
    
    task_status_distribution: Dict[str, int] = Field(default={}, description="任务状态分布")
    
    current_throughput: float = Field(default=0.0, description="当前吞吐量")
    avg_processing_time: Optional[float] = Field(None, description="平均处理时间")
    success_rate: float = Field(default=0.0, description="成功率")
    
    task_trends: List[TimeSeries] = Field(default=[], description="任务趋势")
    performance_trends: List[TimeSeries] = Field(default=[], description="性能趋势")
    
    top_queues: List[Dict[str, Any]] = Field(default=[], description="热门队列")
    recent_failures: List[Dict[str, Any]] = Field(default=[], description="最近失败任务")
    
    system_health: SystemHealth = Field(..., description="系统健康状态")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class WorkerMetrics(BaseModel):
    """工作节点指标模型"""
    worker_id: str = Field(..., description="工作节点ID")
    namespace: str = Field(..., description="命名空间")
    status: str = Field(..., description="状态")
    last_heartbeat: datetime = Field(..., description="最后心跳时间")
    
    tasks_processed: int = Field(default=0, description="已处理任务数")
    tasks_succeeded: int = Field(default=0, description="成功任务数")
    tasks_failed: int = Field(default=0, description="失败任务数")
    current_task: Optional[str] = Field(None, description="当前处理任务")
    
    avg_task_time: Optional[float] = Field(None, description="平均任务处理时间")
    cpu_usage: Optional[float] = Field(None, description="CPU使用率")
    memory_usage: Optional[float] = Field(None, description="内存使用率")
    
    queues: List[str] = Field(default=[], description="监听的队列")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }