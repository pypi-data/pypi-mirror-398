"""
概览模块 - 系统总览、健康检查和仪表板统计
提供轻量级的路由入口，业务逻辑在 OverviewService 中实现
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, Dict, Any
import logging
import traceback

from jettask.schemas import (
    TimeRangeQuery,
    SystemStatsResponse,
    DashboardStatsResponse,
    TopQueuesResponse,
    DataResponse
)
from jettask.webui.services.overview_service import OverviewService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/overview", tags=["overview"])



@router.get(
    "/",
    summary="API 根路径",
    description="获取 API 基本信息和健康状态",
    response_model=DataResponse,
    responses={
        200: {
            "description": "成功返回 API 信息",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "service": "JetTask WebUI API",
                            "version": "v1",
                            "status": "running"
                        }
                    }
                }
            }
        }
    }
)
async def root() -> Dict[str, Any]:
    return OverviewService.get_root_info()



@router.get(
    "/system-stats",
    summary="获取系统统计信息",
    description="获取指定命名空间的系统级统计数据，包括队列、任务、Worker 等关键指标",
    response_model=SystemStatsResponse,
    responses={
        200: {
            "description": "成功返回系统统计数据"
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "获取系统统计信息失败: Database connection error"
                    }
                }
            }
        }
    }
)
async def get_system_stats(
    namespace: str = Path(..., description="命名空间名称，用于隔离不同环境或项目的数据", example="default")
) -> Dict[str, Any]:
    try:
        return await OverviewService.get_system_stats(namespace)
    except Exception as e:
        logger.error(f"获取系统统计信息失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/dashboard-stats",
    summary="获取仪表板统计数据",
    description="获取仪表板展示所需的关键业务指标，支持按时间范围和队列过滤",
    response_model=DashboardStatsResponse,
    responses={
        200: {
            "description": "成功返回仪表板统计数据"
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def get_dashboard_stats(
    namespace: str = Path(..., description="命名空间名称", example="default"),
    time_range: str = Query(
        default="24h",
        description="时间范围，支持: 15m, 1h, 6h, 24h, 7d, 30d",
        example="24h",
        regex="^(15m|1h|6h|24h|7d|30d)$"
    ),
    queues: Optional[str] = Query(
        None,
        description="逗号分隔的队列名称列表，为空则统计所有队列",
        example="email_queue,sms_queue"
    )
) -> Dict[str, Any]:
    try:
        return await OverviewService.get_dashboard_stats(namespace, time_range, queues)
    except Exception as e:
        logger.error(f"获取仪表板统计数据失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/top-queues",
    summary="获取队列排行榜",
    description="根据指定指标获取队列排行榜，支持积压数和错误率两种排序方式",
    response_model=TopQueuesResponse,
    responses={
        200: {
            "description": "成功返回队列排行榜"
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "无效的指标类型: invalid_metric，仅支持 backlog 或 error"
                    }
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def get_top_queues(
    namespace: str = Path(..., description="命名空间名称", example="default"),
    metric: str = Query(
        default="backlog",
        description="排序指标类型",
        example="backlog",
        regex="^(backlog|error)$"
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="返回的队列数量限制",
        example=10
    ),
    time_range: str = Query(
        default="24h",
        description="统计时间范围",
        example="24h",
        regex="^(15m|1h|6h|24h|7d|30d)$"
    ),
    queues: Optional[str] = Query(
        None,
        description="逗号分隔的队列名称列表，为空则统计所有队列",
        example="email_queue,sms_queue"
    )
) -> Dict[str, Any]:
    try:
        return await OverviewService.get_top_queues(namespace, metric, limit, time_range, queues)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取队列排行榜失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))




@router.post(
    "/dashboard-overview-stats",
    summary="获取概览页面统计数据",
    description="获取概览页面所需的时间序列统计数据，包括任务处理趋势、并发数量、处理时间等",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "成功返回时间序列统计数据",
            "content": {
                "application/json": {
                    "example": {
                        "task_trend": [
                            {"timestamp": "2025-10-18T10:00:00Z", "completed": 120, "failed": 5},
                            {"timestamp": "2025-10-18T10:05:00Z", "completed": 135, "failed": 3}
                        ],
                        "concurrency": [
                            {"timestamp": "2025-10-18T10:00:00Z", "value": 15},
                            {"timestamp": "2025-10-18T10:05:00Z", "value": 18}
                        ],
                        "processing_time": [
                            {"timestamp": "2025-10-18T10:00:00Z", "avg": 2.3, "p50": 2.1, "p95": 4.5},
                            {"timestamp": "2025-10-18T10:05:00Z", "avg": 2.1, "p50": 1.9, "p95": 4.2}
                        ],
                        "creation_latency": [
                            {"timestamp": "2025-10-18T10:00:00Z", "avg": 0.5, "p95": 1.2}
                        ],
                        "granularity": "5m"
                    }
                }
            }
        },
        500: {
            "description": "服务器内部错误，返回空数据"
        }
    }
)
async def get_dashboard_overview_stats(
    namespace: str = Path(..., description="命名空间名称", example="default"),
    query: TimeRangeQuery = ...
) -> Dict[str, Any]:
    try:
        return await OverviewService.get_dashboard_overview_stats(namespace, query)
    except Exception as e:
        logger.error(f"获取概览统计数据失败: {e}")
        traceback.print_exc()
        return {
            "task_trend": [],
            "concurrency": [],
            "processing_time": [],
            "creation_latency": [],
            "granularity": "minute"
        }


__all__ = ['router']