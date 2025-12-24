"""
队列模块 - 队列管理、任务处理、队列统计和监控、任务发送
提供轻量级的路由入口，业务逻辑在 QueueService 中实现
包含跨语言任务发送 API
"""
from fastapi import APIRouter, HTTPException, Request, Query, Path, Depends
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from jettask.schemas import (
    TimeRangeQuery,
    TrimQueueRequest,
    TasksRequest,
    TaskActionRequest,
    BacklogLatestRequest,
    BacklogTrendRequest,
    SendTasksRequest,
    SendTasksResponse
)
from jettask.core.message import TaskMessage
from jettask.webui.services.queue_service import QueueService, TrendMetric
from jettask.webui.services.task_service import TaskService
from jettask.webui.services.sql_history_service import SQLHistoryService
from jettask.utils.redis_monitor import RedisMonitorService
from jettask.utils.task_logger import LogContext, get_task_logger

router = APIRouter(prefix="/queues", tags=["queues"])
logger = get_task_logger(__name__)



@router.get(
    "/overview",
    summary="获取队列概览信息",
    description="""从 task_runs_metrics_minute 聚合表查询队列的详细统计信息。

**主要功能**:
- 自动将基础队列名展开为所有优先级队列（如 email_queue -> email_queue:1, email_queue:2）
- 按基础队列 + 任务名称分组，返回每个任务的完整统计信息
- 支持多种时间筛选模式（time_range 字符串或 start_time/end_time）
- 最小时间粒度为分钟级别

**返回字段说明**:
- queue_name: 基础队列名称（不含优先级后缀）
- task_count: 该队列下的任务类型数量
- tasks: 每个任务类型的详细统计（包含执行时间、延迟、并发、成功率等）

**使用场景**: 监控面板展示、队列健康状态概览、任务性能分析、延迟监控""",
    responses={
        200: {
            "description": "成功返回队列概览数据",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "queue_name": "notification_queue",
                                "task_count": 1,
                                "tasks": [
                                    {
                                        "task_name": "send_notification",
                                        "total_count": 10,
                                        "success_count": 10,
                                        "failed_count": 0,
                                        "retry_count": 0,
                                        "total_duration": 0.0097,
                                        "max_duration": 0.0015,
                                        "min_duration": 0.0005,
                                        "total_delay": 574.9868,
                                        "max_delay": 58.726,
                                        "min_delay": 56.3472,
                                        "max_concurrency": 1,
                                        "avg_duration": 0.001,
                                        "avg_delay": 57.4987,
                                        "success_rate": 100.0
                                    }
                                ]
                            },
                            {
                                "queue_name": "email_queue",
                                "task_count": 1,
                                "tasks": [
                                    {
                                        "task_name": "send_email",
                                        "total_count": 10003,
                                        "success_count": 10003,
                                        "failed_count": 0,
                                        "retry_count": 0,
                                        "total_duration": 13.7266,
                                        "max_duration": 0.0743,
                                        "min_duration": 0.0003,
                                        "total_delay": 47804.0201,
                                        "max_delay": 9.0691,
                                        "min_delay": 0.0022,
                                        "max_concurrency": 500,
                                        "avg_duration": 0.0014,
                                        "avg_delay": 4.779,
                                        "success_rate": 100.0
                                    }
                                ]
                            }
                        ],
                        "total": 2,
                        "granularity": "hour",
                        "time_range": {
                            "start_time": "2025-11-02T15:31:16.749024+00:00",
                            "end_time": "2025-11-16T15:31:16.749024+00:00",
                            "interval": "6 hours",
                            "interval_seconds": 21600
                        }
                    }
                }
            }
        },
        400: {"description": "请求参数错误（queues 参数为空）"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_queue_overview(
    request: Request,
    queues: str = Query(..., description="队列名称列表（必填），多个队列用逗号分隔", example="email_queue,sms_queue"),
    start_time: Optional[datetime] = Query(None, description="开始时间（ISO格式），用于统计成功/失败数", example="2025-11-16T15:46:35.900Z"),
    end_time: Optional[datetime] = Query(None, description="结束时间（ISO格式），用于统计成功/失败数", example="2025-11-29T16:41:45.900Z"),
    time_range: Optional[str] = Query(None, description="时间范围，如 15m, 1h, 24h 等，与 start_time/end_time 二选一", example="15m")
) -> Dict[str, Any]:
    try:
        ns = request.state.ns

        pg_session = await ns.get_pg_session()

        try:
            queue_list = [q.strip() for q in queues.split(',') if q.strip()]

            if not queue_list:
                raise HTTPException(status_code=400, detail="queues 参数不能为空")

            registry = await ns.get_queue_registry()

            result = await QueueService.get_queue_overview(
                namespace=ns.name,
                pg_session=pg_session,
                registry=registry,  
                queues=queue_list,
                start_time=start_time,
                end_time=end_time,
                time_range=time_range
            )

            return result

        finally:
            await pg_session.close()

    except Exception as e:
        logger.error(f"获取队列概览失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/runs-trend",
    summary="获取队列任务执行趋势",
    description="""从 task_runs_metrics_minute 聚合表查询任务执行（task_run）趋势数据。

**主要功能**:
- 自动将基础队列名展开为所有优先级队列
- 支持多种指标的选择性聚合（节省算力）
- 时间间隔自动计算，最小粒度为分钟级别
- 支持多种时间筛选模式（time_range 字符串或 start_time/end_time）

**支持的聚合指标**:
- total_count: 总任务数
- success_count: 成功数
- failed_count: 失败数
- retry_count: 重试次数
- avg_duration/max_duration/min_duration: 执行时间（秒）
- avg_delay/max_delay/min_delay: 延迟（秒）
- max_concurrency: 最大并发数
- success_rate: 成功率（百分比）

**时间间隔自动计算**:
- 1小时内：1分钟间隔
- 1-6小时：5分钟间隔
- 6-24小时：10-30分钟间隔
- 1-7天：1小时间隔
- 7天以上：6-12小时间隔

**使用场景**: 队列任务执行速率监控、成功率趋势分析、延迟监控、并发量监控、异常检测""",
    responses={
        200: {
            "description": "成功返回队列趋势数据",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "queue_name": "email_queue",
                                "trend": [
                                    {
                                        "time": "2025-11-11T10:00:00+00:00",
                                        "total_count": 10,
                                        "success_count": 9,
                                        "avg_duration": 5.5
                                    },
                                    {
                                        "time": "2025-11-11T10:05:00+00:00",
                                        "total_count": 15,
                                        "success_count": 14,
                                        "avg_duration": 4.8
                                    }
                                ]
                            }
                        ],
                        "metrics": ["total_count", "success_count", "avg_duration"],
                        "granularity": "minute",
                        "time_range": {
                            "start_time": "2025-11-11T10:00:00+00:00",
                            "end_time": "2025-11-11T11:00:00+00:00",
                            "interval": "5 minutes",
                            "interval_seconds": 300
                        }
                    }
                }
            }
        },
        400: {"description": "请求参数错误（无效的指标名称）"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_queue_runs_trend(
    request: Request,
    queues: str = Query(..., description="基础队列名称列表（必填），多个队列用逗号分隔", example="email_queue,sms_queue"),
    metrics: Optional[str] = Query(
        None,
        description="要聚合的指标列表，多个指标用逗号分隔。默认只聚合 total_count。\n"
                    "支持的指标: total_count, success_count, failed_count, retry_count, "
                    "avg_duration, max_duration, min_duration, avg_delay, max_delay, min_delay, "
                    "max_concurrency, success_rate",
        example="total_count,success_count,avg_duration"
    ),
    start_time: Optional[datetime] = Query(None, description="开始时间（ISO格式）", example="2025-11-11T10:00:00Z"),
    end_time: Optional[datetime] = Query(None, description="结束时间（ISO格式）", example="2025-11-11T11:00:00Z"),
    time_range: Optional[str] = Query(None, description="时间范围，如 15m, 1h, 24h 等，与 start_time/end_time 二选一", example="1h")
) -> Dict[str, Any]:
    try:
        ns = request.state.ns

        pg_session = await ns.get_pg_session()

        registry = await ns.get_queue_registry()

        try:
            queue_list = [q.strip() for q in queues.split(',') if q.strip()]

            if not queue_list:
                raise HTTPException(status_code=400, detail="queues 参数不能为空")

            metric_list = None
            if metrics:
                metric_list = []
                for m in metrics.split(','):
                    m = m.strip()
                    try:
                        metric_list.append(TrendMetric(m))
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail=f"无效的指标: {m}。支持的指标: {', '.join([e.value for e in TrendMetric])}"
                        )

            result = await QueueService.get_queue_runs_trend(
                namespace=ns.name,
                pg_session=pg_session,
                registry=registry,
                queues=queue_list,
                start_time=start_time,
                end_time=end_time,
                time_range=time_range,
                metrics=metric_list
            )

            return result

        finally:
            await pg_session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取队列执行趋势失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/tasks-trend",
    summary="获取队列任务创建趋势",
    description="""从 task_metrics_minute 聚合表查询任务创建（task）趋势数据。

**主要功能**:
- 统计任务提交/创建数量（与 runs-trend 统计执行情况不同）
- 自动将基础队列名展开为所有优先级队列
- 时间间隔自动计算，最小粒度为分钟级别
- 支持多种时间筛选模式（time_range 字符串或 start_time/end_time）

**与 runs-trend 的区别**:
- tasks-trend: 统计任务提交/创建数量（来自 task_metrics_minute）
- runs-trend: 统计任务执行情况（来自 task_runs_metrics_minute），包含成功/失败/延迟等指标

**时间间隔自动计算**:
- 1小时内：1分钟间隔
- 1-6小时：5分钟间隔
- 6-24小时：10-30分钟间隔
- 1-7天：1小时间隔
- 7天以上：6-12小时间隔

**使用场景**: 任务提交速率监控、流量分析、容量规划、峰值检测""",
    responses={
        200: {
            "description": "成功返回队列任务创建趋势数据",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "queue_name": "email_queue",
                                "trend": [
                                    {
                                        "time": "2025-11-11T10:00:00+00:00",
                                        "task_count": 100
                                    },
                                    {
                                        "time": "2025-11-11T10:05:00+00:00",
                                        "task_count": 150
                                    }
                                ]
                            }
                        ],
                        "metrics": ["task_count"],
                        "granularity": "minute",
                        "time_range": {
                            "start_time": "2025-11-11T10:00:00+00:00",
                            "end_time": "2025-11-11T11:00:00+00:00",
                            "interval": "5 minutes",
                            "interval_seconds": 300
                        }
                    }
                }
            }
        },
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_queue_tasks_trend(
    request: Request,
    queues: str = Query(..., description="基础队列名称列表（必填），多个队列用逗号分隔", example="email_queue,sms_queue"),
    start_time: Optional[datetime] = Query(None, description="开始时间（ISO格式）", example="2025-11-11T10:00:00Z"),
    end_time: Optional[datetime] = Query(None, description="结束时间（ISO格式）", example="2025-11-11T11:00:00Z"),
    time_range: Optional[str] = Query(None, description="时间范围，如 15m, 1h, 24h 等，与 start_time/end_time 二选一", example="1h")
) -> Dict[str, Any]:
    try:
        ns = request.state.ns

        pg_session = await ns.get_pg_session()

        registry = await ns.get_queue_registry()

        try:
            queue_list = [q.strip() for q in queues.split(',') if q.strip()]

            if not queue_list:
                raise HTTPException(status_code=400, detail="queues 参数不能为空")

            result = await QueueService.get_queue_tasks_trend(
                namespace=ns.name,
                pg_session=pg_session,
                registry=registry,
                queues=queue_list,
                start_time=start_time,
                end_time=end_time,
                time_range=time_range
            )

            return result

        finally:
            await pg_session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取队列任务创建趋势失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "",
    summary="获取命名空间队列列表",
    description="""获取指定命名空间下所有基础队列的列表。

**主要功能**:
- 从 QueueRegistry 获取所有注册的队列
- 自动过滤优先级队列，只返回基础队列名称
- 实时从 Redis 获取数据

**使用场景**: 队列管理页面列表、队列状态监控、队列选择器、管理界面展示""",
    responses={
        200: {
            "description": "成功返回队列列表",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "namespace": "default",
                        "queues": [
                            {"name": "email_queue"},
                            {"name": "sms_queue"}
                        ],
                        "total": 2
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_queues(request: Request) -> Dict[str, Any]:
    try:
        ns = request.state.ns

        registry = await ns.get_queue_registry()

        base_queues = await registry.get_base_queues()

        queues_list = []
        for queue_name in sorted(base_queues):
            if queue_name == "TASK_CHANGES":
                continue
            queues_list.append({
                "name": queue_name
            })

        logger.info(f"获取命名空间 {ns.name} 的队列列表成功，共 {len(queues_list)} 个队列")

        return {
            "success": True,
            "namespace": ns.name,
            "queues": queues_list,
            "total": len(queues_list)
        }

    except Exception as e:
        logger.error(f"获取队列列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




@router.get(
    "/stats-v2",
    summary="获取队列统计信息 v2",
    description="""获取队列的详细统计信息，支持消费者组和优先级队列。

**增强特性**:
- 支持消费者组详细统计
- 支持优先级队列分析
- 支持时间范围筛选
- 支持单队列或全部队列查询

**返回信息**: 队列基本统计、消费者组状态和积压、优先级队列分布、时间范围内的任务统计

**使用场景**: 队列详细监控、消费者组管理、优先级队列分析、性能优化""",
    responses={
        200: {"description": "成功返回队列统计"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_queue_stats(
    request: Request,
    queue: Optional[str] = Query(None, description="队列名称，为空则返回所有队列", example="email_queue"),
    start_time: Optional[datetime] = Query(None, description="开始时间（ISO格式）"),
    end_time: Optional[datetime] = Query(None, description="结束时间（ISO格式）"),
    time_range: Optional[str] = Query(None, description="时间范围（如 1h, 24h, 7d）", example="24h")
) -> Dict[str, Any]:
    try:
        ns = request.state.ns

        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")

        namespace_data_access = app.state.namespace_data_access
        return await QueueService.get_queue_stats_v2(
            namespace_data_access, ns.name, queue, start_time, end_time, time_range
        )
    except Exception as e:
        logger.error(f"获取队列统计v2失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/consumer-groups/{group_name}/stats",
    summary="获取消费者组统计",
    description="""获取 Redis Stream 消费者组的详细统计信息。

**返回信息**: 消费者组名称、待处理消息数 (pending)、活跃消费者数量、消费延迟 (lag)、最后交付的消息 ID

**使用场景**: 消费者组监控、积压问题诊断、消费者负载均衡、性能优化

**注意**: 仅适用于使用 Redis Stream 的队列，建议定期监控 pending 和 lag 指标""",
    responses={
        200: {
            "description": "成功返回消费者组统计",
            "content": {
                "application/json": {
                    "example": {
                        "group_name": "email_workers",
                        "pending_messages": 120,
                        "consumers": 5,
                        "lag": 95,
                        "last_delivered_id": "1697644800000-0"
                    }
                }
            }
        },
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_consumer_group_stats(
    request: Request,
    group_name: str = Path(..., description="消费者组名称", example="email_workers")
) -> Dict[str, Any]:
    try:
        ns = request.state.ns

        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")

        namespace_data_access = app.state.namespace_data_access
        return await QueueService.get_consumer_group_stats(namespace_data_access, ns.name, group_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取消费者组统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/stream-backlog",
    summary="获取 Stream 积压监控数据",
    description="""获取 Redis Stream 的积压情况和历史趋势数据。

**返回信息**: Stream 当前长度、消费者组数量、总待处理消息数、历史趋势数据（按小时）

**使用场景**: Stream 积压监控、容量规划、性能趋势分析、异常检测

**注意**: 仅适用于使用 Redis Stream 的队列，hours 参数范围 1-168（7天），历史数据按小时聚合""",
    responses={
        200: {
            "description": "成功返回 Stream 积压数据",
            "content": {
                "application/json": {
                    "example": {
                        "stream_name": "task_stream",
                        "current_length": 1500,
                        "consumer_groups": 3,
                        "total_pending": 250,
                        "history": [
                            {"timestamp": "2025-10-18T10:00:00Z", "length": 1400},
                            {"timestamp": "2025-10-18T11:00:00Z", "length": 1500}
                        ]
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_stream_backlog(
    request: Request,
    stream_name: Optional[str] = Query(None, description="Stream 名称，为空则返回所有", example="task_stream"),
    hours: int = Query(24, ge=1, le=168, description="查询最近多少小时的数据", example=24)
) -> Dict[str, Any]:
    try:
        ns = request.state.ns

        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")

        data_access = app.state.data_access
        return await QueueService.get_stream_backlog(data_access, ns.name, stream_name, hours)
    except Exception as e:
        logger.error(f"获取Stream积压监控数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stream-backlog/summary",
    summary="获取 Stream 积压汇总",
    description="""获取指定命名空间下所有 Redis Stream 的积压汇总统计。

**返回信息**: Stream 总数、总消息数、总待处理消息数、平均积压率、各 Stream 的简要信息

**使用场景**: 全局积压监控、命名空间健康检查、快速问题定位、管理报表

**注意**: 实时计算，可能有延迟，仅包含使用 Stream 的队列""",
    responses={
        200: {
            "description": "成功返回积压汇总",
            "content": {
                "application/json": {
                    "example": {
                        "total_streams": 5,
                        "total_length": 7500,
                        "total_pending": 850,
                        "avg_backlog_rate": 12.5,
                        "streams": [
                            {"name": "task_stream", "length": 1500, "pending": 250},
                            {"name": "email_stream", "length": 2000, "pending": 180}
                        ]
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_stream_backlog_summary(request: Request) -> Dict[str, Any]:
    try:
        ns = request.state.ns

        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")

        data_access = app.state.data_access
        return await QueueService.get_stream_backlog_summary(data_access, ns.name)
    except Exception as e:
        logger.error(f"获取Stream积压监控汇总失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post(
    "/backlog/latest",
    summary="获取最新积压数据快照",
    description="""获取指定命名空间下队列的最新积压数据实时快照。

**返回信息**: 待处理任务数、处理中任务数、已完成任务数、失败任务数、队列大小、最老任务年龄（秒）

**使用场景**: 实时积压监控、队列健康检查、告警触发依据、运维大盘展示

**注意**: 数据为实时快照，queues 参数为空时返回所有队列，oldest_task_age 为空表示队列无待处理任务""",
    responses={
        200: {
            "description": "成功返回积压快照数据",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "namespace": "default",
                        "timestamp": "2025-10-18T10:30:00Z",
                        "snapshots": [
                            {
                                "queue_name": "email_queue",
                                "pending_count": 120,
                                "processing_count": 8,
                                "completed_count": 5430,
                                "failed_count": 12,
                                "queue_size": 128,
                                "oldest_task_age": 45
                            }
                        ]
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_latest_backlog(
    request: Request,
    backlog_request: BacklogLatestRequest = ...
) -> Dict[str, Any]:
    try:
        ns = request.state.ns

        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")

        data_access = app.state.data_access
        queues = backlog_request.queues or []


        return {
            "success": True,
            "namespace": ns.name,
            "timestamp": datetime.now().isoformat(),
            "snapshots": [],
            "message": "Backlog monitoring endpoint - implementation pending"
        }
    except Exception as e:
        logger.error(f"获取最新积压数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/backlog/trend",
    summary="获取队列积压趋势",
    description="""获取指定队列在一段时间内的积压趋势数据。

**支持的时间范围**: 1h, 6h, 24h (1d), 7d，或使用 start_time/end_time 指定精确时间

**支持的时间间隔**: 1m, 5m, 15m, 1h

**支持的指标类型**: pending, processing, completed, failed

**返回信息**: 时间戳序列、各指标的时间序列数据、统计摘要（峰值、平均值、成功率等）

**使用场景**: 积压趋势分析、性能问题诊断、容量规划、历史数据回溯、运维报表生成""",
    responses={
        200: {
            "description": "成功返回积压趋势数据",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "namespace": "default",
                        "queue_name": "email_queue",
                        "time_range": "1h",
                        "interval": "5m",
                        "timestamps": [
                            "2025-10-18T10:00:00Z",
                            "2025-10-18T10:05:00Z",
                            "2025-10-18T10:10:00Z"
                        ],
                        "metrics": {
                            "pending": [120, 115, 108],
                            "processing": [8, 10, 9],
                            "completed": [5430, 5445, 5462],
                            "failed": [12, 12, 13]
                        },
                        "statistics": {
                            "peak_pending": 120,
                            "avg_pending": 114.3,
                            "avg_throughput": 10.7,
                            "overall_success_rate": 99.76
                        }
                    }
                }
            }
        },
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_backlog_trend(
    request: Request,
    trend_request: BacklogTrendRequest = ...
) -> Dict[str, Any]:
    try:
        ns = request.state.ns

        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")

        data_access = app.state.data_access


        return {
            "success": True,
            "namespace": ns.name,
            "queue_name": trend_request.queue_name,
            "time_range": trend_request.time_range,
            "interval": trend_request.interval,
            "timestamps": [],
            "metrics": {},
            "statistics": {},
            "message": "Backlog trend endpoint - implementation pending"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取积压趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))



def get_task_service(request: Request) -> TaskService:
    if not hasattr(request.app.state, 'data_access'):
        raise HTTPException(status_code=500, detail="Data access not initialized")
    return TaskService(request.app.state.data_access)



@router.post(
    "/tasks-v2",
    summary="获取任务列表 v2",
    description="""获取任务列表的增强版本，支持 tasks 和 task_runs 表的连表查询。

**增强特性**: 支持多表连接查询、复杂过滤条件、排序和分页、返回任务执行历史

**支持的任务状态**: pending, processing, completed, failed, retrying

**请求体参数**: queue_name, status, page, page_size, start_time, end_time, sort_by, sort_order

**使用场景**: 任务管理页面、任务历史查询、任务状态监控、故障排查""",
    responses={
        200: {
            "description": "成功返回任务列表",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "task_id": "task-001",
                                "queue_name": "email_queue",
                                "status": "completed",
                                "created_at": "2025-10-18T10:00:00Z",
                                "runs": []
                            }
                        ],
                        "total": 150,
                        "page": 1,
                        "page_size": 20
                    }
                }
            }
        },
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_tasks_v2(request: Request):
    try:
        ns = request.state.ns

        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")

        namespace_data_access = app.state.namespace_data_access

        body = await request.json()

        return await QueueService.get_tasks_v2(namespace_data_access, ns.name, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务列表v2失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/redis/monitor",
    summary="获取 Redis 性能监控数据",
    description="""获取指定命名空间的 Redis 实例的实时性能监控数据。

**监控指标**: 内存使用（已用内存、峰值内存、内存碎片率）、连接信息（当前连接数、阻塞的客户端数）、命令统计（总命令数、QPS）、缓存命中（命中次数、未命中次数、命中率）、持久化状态、键空间统计

**性能指标**: hit_rate（缓存命中率）、qps（每秒查询数）、memory_fragmentation_ratio（内存碎片率）

**使用场景**: Redis 性能监控、容量规划、性能优化、故障诊断、运维大盘

**注意**: 数据实时获取，建议监控间隔 5-10 秒，内存碎片率 > 1.5 时建议重启 Redis""",
    responses={
        200: {
            "description": "成功返回 Redis 监控数据",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "namespace": "default",
                        "redis_info": {
                            "used_memory": "10485760",
                            "used_memory_human": "10M",
                            "connected_clients": "25",
                            "total_commands_processed": "1500000",
                            "instantaneous_ops_per_sec": "150",
                            "keyspace_hits": "98500",
                            "keyspace_misses": "1500"
                        },
                        "performance": {
                            "hit_rate": "98.5%",
                            "qps": 150,
                            "memory_fragmentation_ratio": 1.2
                        }
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_redis_monitor(request: Request):
    try:
        ns = request.state.ns

        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")

        namespace_data_access = app.state.namespace_data_access
        redis_monitor_service = RedisMonitorService(namespace_data_access)
        return await redis_monitor_service.get_redis_monitor_data(ns.name)
    except Exception as e:
        logger.error(f"获取Redis监控数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/redis/slow-log",
    summary="获取 Redis 慢查询日志",
    description="""获取 Redis 实例的慢查询日志，帮助识别性能瓶颈。

**日志信息**: 日志 ID、执行时间戳、执行耗时（微秒）、执行的命令、客户端地址和端口

**使用场景**: 性能问题诊断、慢查询优化、Redis 性能分析、识别不合理的命令使用

**注意**: 慢查询阈值由 Redis 配置 slowlog-log-slower-than 决定（默认10ms），日志按时间倒序返回，重启后清空，常见慢命令: KEYS、SMEMBERS、HGETALL（大集合）""",
    responses={
        200: {
            "description": "成功返回慢查询日志",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "namespace": "default",
                        "slow_logs": [
                            {
                                "id": 12345,
                                "timestamp": 1697644800,
                                "duration_us": 15000,
                                "command": "KEYS pattern*",
                                "client_addr": "127.0.0.1:54321"
                            }
                        ],
                        "total": 10
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_redis_slow_log(
    request: Request,
    limit: int = Query(10, ge=1, le=100, description="返回记录数，范围 1-100", example=10)
):
    try:
        ns = request.state.ns

        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")

        namespace_data_access = app.state.namespace_data_access
        redis_monitor_service = RedisMonitorService(namespace_data_access)
        return await redis_monitor_service.get_slow_log(ns.name, limit)
    except Exception as e:
        logger.error(f"获取Redis慢查询日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/redis/command-stats",
    summary="获取 Redis 命令统计",
    description="""获取 Redis 实例的命令执行统计信息。

**统计信息**: 命令名称、调用次数 (calls)、总耗时（微秒）(usec)、平均耗时（微秒/次）(usec_per_call)

**使用场景**: 分析 Redis 命令使用模式、识别高频命令、性能优化、命令耗时分析、容量规划

**注意**: 统计数据为累计值（从 Redis 启动开始），重启后清零，按调用次数降序排序，可通过 usec_per_call 识别慢命令""",
    responses={
        200: {
            "description": "成功返回命令统计",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "namespace": "default",
                        "command_stats": [
                            {
                                "command": "GET",
                                "calls": 1500000,
                                "usec": 45000000,
                                "usec_per_call": 30.0
                            },
                            {
                                "command": "SET",
                                "calls": 800000,
                                "usec": 32000000,
                                "usec_per_call": 40.0
                            }
                        ],
                        "total_commands": 25
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_redis_command_stats(request: Request):
    try:
        ns = request.state.ns

        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")

        namespace_data_access = app.state.namespace_data_access
        redis_monitor_service = RedisMonitorService(namespace_data_access)
        return await redis_monitor_service.get_command_stats(ns.name)
    except Exception as e:
        logger.error(f"获取Redis命令统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/redis/stream-stats",
    summary="获取 Redis Stream 统计",
    description="""获取 Redis Stream 的详细统计信息。

**Stream 统计**: Stream 名称、消息总数（length）、第一条消息 ID、最后一条消息 ID、消费者组列表及其状态

**消费者组统计**: 组名称、消费者数量、待处理消息数 (pending)、最后交付的消息 ID

**使用场景**: Stream 使用情况监控、消费者组管理、积压分析、容量规划、性能优化

**注意**: 仅返回使用 Redis Stream 的队列统计，消息 ID 格式为 timestamp-sequence，pending 表示已分配但未确认的消息数""",
    responses={
        200: {
            "description": "成功返回 Stream 统计",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "namespace": "default",
                        "streams": [
                            {
                                "stream_name": "task_stream",
                                "length": 1500,
                                "first_entry_id": "1697644800000-0",
                                "last_entry_id": "1697731200000-5",
                                "groups": [
                                    {
                                        "name": "workers",
                                        "consumers": 5,
                                        "pending": 120,
                                        "last_delivered_id": "1697730000000-3"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_redis_stream_stats(
    request: Request,
    stream_name: Optional[str] = Query(None, description="Stream 名称，为空则返回所有 Stream 的统计", example="task_stream")
):
    try:
        ns = request.state.ns

        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")

        namespace_data_access = app.state.namespace_data_access
        redis_monitor_service = RedisMonitorService(namespace_data_access)
        return await redis_monitor_service.get_stream_stats(ns.name, stream_name)
    except Exception as e:
        logger.error(f"获取Redis Stream统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/task-runs",
    summary="查询任务执行记录",
    description="""从 tasks + task_runs 连表查询任务执行记录，支持灵活的 SQL WHERE 条件。

**请求示例**:
```
GET /task-runs?queue=email_queue&time_range=1h&where=status%20%3D%20'success'&page=1&page_size=20
```

**主要功能**:
- 自动将基础队列名展开为所有优先级队列
- 支持灵活的 SQL WHERE 条件查询
- 支持分页和排序
- 自动按命名空间筛选
- 内置安全校验，禁止危险操作

**可用字段**（无需指定表名前缀）:
- Task 字段: stream_id, scheduled_task_id, priority, delay, source, trigger_time, created_at, payload
- TaskRun 字段: task_name, status, result, error, started_at, completed_at, retries, duration, consumer

**WHERE 条件示例**:
- `status = 'success'` - 筛选成功的任务
- `status IN ('failed', 'error')` - 筛选失败的任务
- `task_name LIKE '%email%'` - 模糊匹配任务名
- `duration > 1.0 AND retries > 0` - 执行时间超过1秒且有重试
- `started_at IS NOT NULL AND completed_at IS NULL` - 正在执行的任务
- `error IS NOT NULL` - 有错误信息的任务
- `payload->>'to' = 'user@example.com'` - JSONB 字段查询

**安全限制**（以下关键字被禁止）:
- DDL 操作: DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER, CREATE
- 权限操作: GRANT, REVOKE, EXEC, EXECUTE
- 查询修改: UNION, INTO, GROUP BY, ORDER BY, HAVING, LIMIT, OFFSET
- 注释符号: --, /*, */

**使用场景**: 任务执行历史查询、任务状态监控、故障排查、性能分析""",
    responses={
        200: {
            "description": "成功返回任务执行记录列表",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "queue": "email_queue",
                        "data": [
                            {
                                "stream_id": "1731234567890-0",
                                "namespace": "default",
                                "scheduled_task_id": None,
                                "payload": {"args": [], "kwargs": {"to": "user@example.com"}},
                                "priority": 1,
                                "delay": 0,
                                "created_at": "2025-11-17T10:00:00+00:00",
                                "trigger_time": 1731834000.123,
                                "source": "redis_stream",
                                "metadata": {},
                                "task_name": "send_email",
                                "status": "success",
                                "result": {"sent": True},
                                "error": None,
                                "started_at": 1731834001.456,
                                "completed_at": 1731834002.789,
                                "retries": 0,
                                "duration": 1.333,
                                "consumer": "worker-1"
                            }
                        ],
                        "total": 150,
                        "page": 1,
                        "page_size": 20,
                        "time_range": {
                            "start_time": "2025-11-17T09:00:00+00:00",
                            "end_time": "2025-11-17T10:00:00+00:00"
                        }
                    }
                }
            }
        },
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_task_runs_list(
    request: Request,
    queue: str = Query(..., description="基础队列名称（必填），系统会自动展开为所有优先级队列", example="email_queue"),
    start_time: Optional[datetime] = Query(None, description="开始时间（ISO格式）", example="2025-11-17T09:00:00Z"),
    end_time: Optional[datetime] = Query(None, description="结束时间（ISO格式）", example="2025-11-17T10:00:00Z"),
    time_range: Optional[str] = Query(None, description="时间范围，如 15m, 1h, 24h 等，与 start_time/end_time 二选一", example="1h"),
    where: Optional[str] = Query(None, description="SQL WHERE 条件（不含 WHERE 关键字）", example="status = 'success' AND duration > 1.0"),
    where_id: Optional[int] = Query(None, description="SQL 历史记录 ID（选择已有历史时传入，手动输入时为空）", example=1),
    page: int = Query(1, ge=1, description="页码（从1开始）", example=1),
    page_size: int = Query(20, ge=1, le=1000, description="每页大小（1-1000）", example=20),
    sort_field: str = Query("created_at", description="排序字段", example="created_at"),
    sort_order: str = Query("desc", description="排序方向（asc/desc）", example="desc")
) -> Dict[str, Any]:
    try:
        ns = request.state.ns

        pg_session = await ns.get_pg_session()

        registry = await ns.get_queue_registry()

        result = await QueueService.get_task_runs_list(
            namespace=ns.name,
            pg_session=pg_session,
            registry=registry,
            queue=queue.strip(),
            start_time=start_time,
            end_time=end_time,
            time_range=time_range,
            where_clause=where,
            page=page,
            page_size=page_size,
            sort_field=sort_field,
            sort_order=sort_order
        )

        if result.get('success'):
            try:
                if where_id is not None:
                    await SQLHistoryService.increment_usage(
                        pg_session=pg_session,
                        history_id=where_id
                    )
                    logger.debug(f"SQL 历史记录使用次数已更新: id={where_id}")
                elif where and where.strip():
                    await SQLHistoryService.save_or_update(
                        pg_session=pg_session,
                        namespace=ns.name,
                        where_clause=where.strip()
                    )
                    logger.debug(f"SQL 历史记录已保存: {where.strip()[:50]}...")
            except Exception as save_err:
                logger.warning(f"更新 SQL 历史记录失败: {save_err}")

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询任务执行记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/tasks",
    summary="获取队列任务列表（简化版）",
    description="""获取指定队列的任务列表，简化版本用于向后兼容。

**功能特点**: 简单的时间范围查询、支持分页限制、按时间倒序返回（最新的在前）

**查询参数**: queue_name（必填）、start_time（可选，默认 "-" 表示最早）、end_time（可选，默认 "+" 表示最新）、limit（返回数量限制）

**使用场景**: 快速查看队列任务、简单的任务列表查询、旧版本API兼容

**注意**: 默认从新到旧排序，如需更复杂的查询请使用 POST /tasks-v2 接口，最大返回1000条记录""",
    responses={
        200: {
            "description": "成功返回任务列表",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "task_id": "task-001",
                                "queue_name": "email_queue",
                                "status": "completed",
                                "created_at": "2025-10-18T10:00:00Z"
                            }
                        ],
                        "total": 50
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_queue_tasks_simple(
    request: Request,
    queue_name: str = Query(..., description="队列名称", example="email_queue"),
    start_time: Optional[str] = Query(None, description="开始时间（ISO格式或 \"-\" 表示最早）", example="2025-10-18T00:00:00Z"),
    end_time: Optional[str] = Query(None, description="结束时间（ISO格式或 \"+\" 表示最新）", example="2025-10-18T23:59:59Z"),
    limit: int = Query(50, ge=1, le=1000, description="返回数量限制，范围 1-1000", example=50)
):
    try:
        ns = request.state.ns

        if not hasattr(request.app.state, 'monitor'):
            raise HTTPException(status_code=500, detail="Monitor service not initialized")

        monitor = request.app.state.monitor
        result = await monitor.get_queue_tasks(
            queue_name,
            start_time or "-",
            end_time or "+",
            limit,
            reverse=True  
        )

        return result
    except Exception as e:
        logger.error(f"获取队列 {queue_name} 任务列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/send-queue",
    summary="发送任务到队列",
    description="""跨语言的任务发送接口，支持从任何编程语言通过 HTTP API 发送任务。

**功能特性**: 支持批量发送多个任务、设置任务优先级、延迟执行、返回每个任务的事件 ID

**请求体参数**: messages 数组，每个 message 包含 queue（必需）、priority（可选，1最高）、delay（可选，秒）、kwargs（字典）、args（列表）

**使用场景**: Go/Java 服务发送任务到 Python worker、微服务跨语言任务调度、外部系统集成（Webhook、第三方服务）、定时任务触发器、批量数据处理任务

**注意**: 命名空间必须存在，priority: 1 是最高优先级，返回的 event_ids 可用于追踪任务状态""",
    response_model=SendTasksResponse,
    responses={
        200: {
            "description": "任务发送成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Tasks sent successfully",
                        "event_ids": [
                            "1730361234567-0",
                            "1730361234568-0"
                        ],
                        "total_sent": 2,
                        "namespace": "default"
                    }
                }
            }
        },
        400: {"description": "请求参数错误"},
        404: {"description": "命名空间不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def send_tasks(
    request: Request,
    send_request: SendTasksRequest
) -> SendTasksResponse:
    try:
        ns = request.state.ns
        namespace = ns.name

        client_host = request.client.host if request.client else 'unknown'
        client_port = request.client.port if request.client else 'unknown'

        with LogContext(
            endpoint='/queues/send-queue',
            namespace=namespace,
            client_ip=client_host,
            client_port=client_port,
            task_count=len(send_request.messages)
        ):
            logger.info(
                f"收到任务发送请求",
                extra={
                    'extra_fields': {
                        'namespace': namespace,
                        'task_count': len(send_request.messages),
                        'client_ip': client_host,
                        'client_port': client_port,
                        'request_path': str(request.url.path),
                        'method': request.method,
                        'messages': [msg.model_dump() for msg in send_request.messages ]
                    }
                }
            )

            for idx, msg_req in enumerate(send_request.messages):
                logger.debug(
                    f"任务 #{idx+1} 详情",
                    extra={
                        'extra_fields': {
                            'task_index': idx + 1,
                            'queue': msg_req.queue,
                            'priority': msg_req.priority,
                            'delay': msg_req.delay,
                            'has_args': bool(msg_req.args),
                            'args_count': len(msg_req.args) if msg_req.args else 0,
                            'kwargs_keys': list(msg_req.kwargs.keys()) if msg_req.kwargs else [],
                            'kwargs': msg_req.kwargs
                        }
                    }
                )

            logger.debug(f"正在获取命名空间 '{namespace}' 的 Jettask 实例")
            jettask_app = await ns.get_jettask_app()

            task_messages = []
            for msg_req in send_request.messages:
                msg = TaskMessage(
                    queue=msg_req.queue,
                    kwargs=msg_req.kwargs,
                    priority=msg_req.priority,
                    delay=msg_req.delay,
                    args=tuple(msg_req.args) if msg_req.args else ()
                )
                task_messages.append(msg)

            logger.info(
                f"开始发送 {len(task_messages)} 个任务到命名空间 '{namespace}'"
            )
            event_ids = await jettask_app.send_tasks(task_messages, asyncio=True)

            if not event_ids:
                logger.error(
                    "任务发送失败: 未返回事件ID",
                    extra={
                        'extra_fields': {
                            'namespace': namespace,
                            'task_count': len(task_messages)
                        }
                    }
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to send tasks: no event IDs returned"
                )

            logger.info(
                f"成功发送 {len(event_ids)} 个任务到命名空间 '{namespace}'",
                extra={
                    'extra_fields': {
                        'namespace': namespace,
                        'event_ids': event_ids,
                        'total_sent': len(event_ids),
                        'client_ip': client_host
                    }
                }
            )

            return SendTasksResponse(
                success=True,
                message="Tasks sent successfully",
                event_ids=event_ids,
                total_sent=len(event_ids),
                namespace=namespace
            )

    except HTTPException:
        raise
    except Exception as e:
        namespace_name = getattr(request.state, 'ns', None)
        namespace_name = namespace_name.name if namespace_name else 'unknown'

        logger.error(
            f"任务发送失败",
            extra={
                'extra_fields': {
                    'namespace': namespace_name,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            },
            exc_info=True
        )

        return SendTasksResponse(
            success=False,
            message="Failed to send tasks",
            event_ids=[],
            total_sent=0,
            namespace=namespace_name,
            error=str(e)
        )


__all__ = ['router']