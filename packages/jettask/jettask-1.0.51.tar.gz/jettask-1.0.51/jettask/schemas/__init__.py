"""
数据模型定义
所有的Pydantic模型集中管理
"""

from .task import (
    TasksRequest,
    TaskDetailResponse,
    TaskInfo,
    TaskActionRequest,
    TaskListResponse,
    TaskMessageRequest,
    SendTasksRequest,
    SendTasksResponse
)

from .queue import (
    TimeRangeQuery,
    QueueStatsResponse,
    QueueTimelineResponse,
    TrimQueueRequest,
    QueueInfo,
    QueueStats,
    QueueActionRequest,
    TaskRunsQueryRequest
)

from .scheduled_task import (
    ScheduledTaskRequest,
    ScheduledTaskResponse,
    ScheduledTaskInfo,
    ScheduleConfig,
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskCreateRequest
)

from .alert import (
    AlertRuleRequest,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRule,
    AlertInstance,
    AlertSummary
)

from .namespace import (
    ConfigMode,
    NamespaceCreate,
    NamespaceUpdate,
    NamespaceResponse,
    NamespaceInfo,
    NamespaceCreateRequest,
    NamespaceUpdateRequest
)

from .backlog import (
    BacklogLatestRequest,
    BacklogTrendRequest,
    BacklogSnapshot,
    BacklogStatistics,
    BacklogTrendResponse,
    BacklogAlert
)

from .auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    RefreshResponse
)

from .common import (
    ErrorResponse,
    FilterCondition,
    BaseListRequest,
    TimeRangeRequest,
    BatchOperationRequest,
    BatchOperationResponse,
    PaginationResponse,
    ListResponse,
    HealthCheck,
    SystemConfigUpdateRequest,
    ApiResponse
)

from .monitoring import (
    MetricPoint,
    TimeSeries,
    MonitoringMetrics,
    AnalyticsData,
    SystemHealth,
    DashboardOverviewRequest,
    DashboardOverview,
    WorkerMetrics
)

from .webhook import (
    WebhookStatus as WebhookStatusSchema,
    WebhookReceiveResponse,
    WebhookInfo,
    WebhookListResponse
)

from .asset import (
    AssetType as AssetTypeSchema,
    AssetStatus as AssetStatusSchema,
    AssetCreate,
    AssetUpdate,
    AssetInfo,
    AssetListResponse,
    AssetGroupSummary,
    ComputeNodeStatus
)

from .responses import (
    SuccessResponse,
    DataResponse,
    PaginatedDataResponse,
    SystemStatsData,
    SystemStatsResponse,
    DashboardStatsData,
    DashboardStatsResponse,
    QueueRankingItem,
    TopQueuesResponse,
    NamespaceStatistics,
    NamespaceStatisticsResponse,
    WorkerHeartbeatInfo,
    WorkersResponse,
    WorkerSummary,
    WorkerSummaryResponse,
    WorkerOfflineRecord,
    WorkerOfflineHistoryResponse,
    DatabaseStatus,
    SystemSettings,
    SystemSettingsResponse,
    DatabaseStatusResponse
)

__all__ = [
    'LoginRequest',
    'TokenResponse',
    'RefreshRequest',
    'RefreshResponse',

    'TasksRequest',
    'TaskDetailResponse',
    'TaskInfo',
    'TaskActionRequest',
    'TaskListResponse',
    'TaskMessageRequest',
    'SendTasksRequest',
    'SendTasksResponse',

    'TimeRangeQuery',
    'QueueStatsResponse',
    'QueueTimelineResponse',
    'TrimQueueRequest',
    'QueueInfo',
    'QueueStats',
    'QueueActionRequest',
    'TaskRunsQueryRequest',

    'ScheduledTaskRequest',
    'ScheduledTaskResponse',
    'ScheduledTaskInfo',
    'ScheduleConfig',
    'ScheduledTaskCreate',
    'ScheduledTaskUpdate',
    'ScheduledTaskCreateRequest',
    
    'AlertRuleRequest',
    'AlertRuleCreate',
    'AlertRuleUpdate',
    'AlertRule',
    'AlertInstance',
    'AlertSummary',
    
    'ConfigMode',
    'NamespaceCreate',
    'NamespaceUpdate',
    'NamespaceResponse',
    'NamespaceInfo',
    'NamespaceCreateRequest',
    'NamespaceUpdateRequest',
    
    'BacklogTrendRequest',
    'BacklogSnapshot',
    'BacklogStatistics',
    'BacklogTrendResponse',
    'BacklogAlert',
    
    'ErrorResponse',
    'FilterCondition',
    'BaseListRequest',
    'TimeRangeRequest',
    'BatchOperationRequest',
    'BatchOperationResponse',
    'PaginationResponse',
    'ListResponse',
    'HealthCheck',
    'SystemConfigUpdateRequest',
    'ApiResponse',
    
    'MetricPoint',
    'TimeSeries',
    'MonitoringMetrics',
    'AnalyticsData',
    'SystemHealth',
    'DashboardOverviewRequest',
    'DashboardOverview',
    'WorkerMetrics',

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

    'WebhookStatusSchema',
    'WebhookReceiveResponse',
    'WebhookInfo',
    'WebhookListResponse',

    'AssetTypeSchema',
    'AssetStatusSchema',
    'AssetCreate',
    'AssetUpdate',
    'AssetInfo',
    'AssetListResponse',
    'AssetGroupSummary',
    'ComputeNodeStatus'
]