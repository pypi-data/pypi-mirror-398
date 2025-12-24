"""
Worker 监控模块 - Worker 状态监控、心跳管理、离线历史

提供 Worker 相关的监控和管理功能
"""
from fastapi import APIRouter, HTTPException, Request, Query, Path
from typing import Optional, List, Dict, Any
import logging

from jettask.schemas import (
    WorkersResponse,
    WorkerSummaryResponse,
    WorkerOfflineHistoryResponse
)

router = APIRouter(prefix="/workers", tags=["workers"])
logger = logging.getLogger(__name__)



@router.get(
    "/{queue_name}",
    summary="获取队列的 Worker 列表",
    description="获取指定队列所有 Worker 的实时心跳信息和状态",
    response_model=WorkersResponse,
    responses={
        200: {
            "description": "成功返回 Worker 列表"
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {"detail": "Monitor service not initialized"}
                }
            }
        }
    }
)
async def get_queue_workers(
    request: Request,
    namespace: str = Path(..., description="命名空间名称", example="default"),
    queue_name: str = Path(..., description="队列名称", example="email_queue")
) -> Dict[str, Any]:
    try:
        if not hasattr(request.app.state, 'monitor'):
            raise HTTPException(status_code=500, detail="Monitor service not initialized")

        monitor = request.app.state.monitor
        workers = await monitor.get_worker_heartbeats(queue_name)

        return {
            "success": True,
            "namespace": namespace,
            "queue": queue_name,
            "workers": workers
        }
    except Exception as e:
        logger.error(f"获取队列 {queue_name} 的 Worker 信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{queue_name}/summary",
    summary="获取队列 Worker 汇总统计",
    description="获取指定队列 Worker 的汇总统计信息，包括总数、在线数、离线数等",
    response_model=WorkerSummaryResponse,
    responses={
        200: {
            "description": "成功返回汇总统计"
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def get_queue_worker_summary(
    request: Request,
    namespace: str = Path(..., description="命名空间名称", example="default"),
    queue_name: str = Path(..., description="队列名称", example="email_queue"),
    fast: bool = Query(False, description="是否使用快速模式（不包含历史数据）", example=False)
) -> Dict[str, Any]:
    try:
        if not hasattr(request.app.state, 'monitor'):
            raise HTTPException(status_code=500, detail="Monitor service not initialized")

        monitor = request.app.state.monitor

        if fast:
            summary = await monitor.get_queue_worker_summary_fast(queue_name)
        else:
            summary = await monitor.get_queue_worker_summary(queue_name)

        return {
            "success": True,
            "namespace": namespace,
            "queue": queue_name,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"获取队列 {queue_name} 的 Worker 汇总统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/offline-history",
    summary="获取全局 Worker 离线历史",
    description="获取所有 Worker 的离线历史记录，支持时间范围筛选",
    response_model=WorkerOfflineHistoryResponse,
    responses={
        200: {
            "description": "成功返回离线历史"
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def get_workers_offline_history(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="返回记录数量限制", example=100),
    start_time: Optional[float] = Query(None, description="开始时间戳（Unix 时间戳）", example=1697644800),
    end_time: Optional[float] = Query(None, description="结束时间戳（Unix 时间戳）", example=1697731200)
) -> Dict[str, Any]:
    try:
        if not hasattr(request.app.state, 'monitor'):
            raise HTTPException(status_code=500, detail="Monitor service not initialized")

        monitor = request.app.state.monitor
        history = await monitor.get_worker_offline_history(limit, start_time, end_time)

        return {
            "success": True,
            "history": history,
            "total": len(history)
        }
    except Exception as e:
        logger.error(f"获取 Worker 离线历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{queue_name}/offline-history",
    summary="获取队列 Worker 离线历史",
    description="获取指定队列的 Worker 离线历史记录",
    response_model=WorkerOfflineHistoryResponse,
    responses={
        200: {
            "description": "成功返回队列离线历史"
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def get_queue_workers_offline_history(
    request: Request,
    namespace: str = Path(..., description="命名空间名称", example="default"),
    queue_name: str = Path(..., description="队列名称", example="email_queue"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数量限制", example=100),
    start_time: Optional[float] = Query(None, description="开始时间戳（Unix 时间戳）"),
    end_time: Optional[float] = Query(None, description="结束时间戳（Unix 时间戳）")
) -> Dict[str, Any]:
    try:
        if not hasattr(request.app.state, 'monitor'):
            raise HTTPException(status_code=500, detail="Monitor service not initialized")

        monitor = request.app.state.monitor

        all_history = await monitor.get_worker_offline_history(limit * 10, start_time, end_time)
        queue_history = [
            record for record in all_history
            if queue_name in record.get('queues', '').split(',')
        ][:limit]

        return {
            "success": True,
            "namespace": namespace,
            "queue": queue_name,
            "history": queue_history,
            "total": len(queue_history)
        }
    except Exception as e:
        logger.error(f"获取队列 {queue_name} 的 Worker 离线历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/heartbeat/stats",
    summary="获取心跳监控统计",
    description="获取所有 Worker 的心跳监控统计信息",
    responses={
        200: {
            "description": "成功返回心跳统计",
            "content": {
                "application/json": {
                    "example": {
                        "total_workers": 50,
                        "online_workers": 45,
                        "offline_workers": 3,
                        "timeout_workers": 2
                    }
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def get_heartbeat_stats(request: Request) -> Dict[str, Any]:
    try:
        if not hasattr(request.app.state, 'monitor'):
            raise HTTPException(status_code=500, detail="Monitor service not initialized")

        monitor = request.app.state.monitor
        stats = await monitor.get_heartbeat_stats()

        return stats
    except Exception as e:
        logger.error(f"获取心跳统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/heartbeat/{worker_id}",
    summary="检查 Worker 心跳状态",
    description="检查指定 Worker 的心跳状态，判断是否在线",
    responses={
        200: {
            "description": "成功返回心跳状态",
            "content": {
                "application/json": {
                    "example": {
                        "worker_id": "worker-001",
                        "is_online": True
                    }
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def check_worker_heartbeat(
    request: Request,
    worker_id: str = Path(..., description="Worker ID", example="worker-001")
) -> Dict[str, Any]:
    try:
        if not hasattr(request.app.state, 'monitor'):
            raise HTTPException(status_code=500, detail="Monitor service not initialized")

        monitor = request.app.state.monitor
        is_online = await monitor.check_worker_heartbeat(worker_id)

        return {
            "worker_id": worker_id,
            "is_online": is_online
        }
    except Exception as e:
        logger.error(f"检查 Worker {worker_id} 心跳状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
