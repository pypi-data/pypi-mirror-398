"""
定时任务模块 - 定时任务管理、执行和监控
提供轻量级的路由入口，业务逻辑在 ScheduledTaskService 中实现
"""
from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional
import logging

from jettask.schemas import ScheduledTaskRequest
from jettask.webui.services.scheduled_task_service import ScheduledTaskService

router = APIRouter(prefix="/scheduled", tags=["scheduled"])
logger = logging.getLogger(__name__)



@router.get(
    "/",
    summary="获取定时任务列表",
    description="获取定时任务列表，支持分页、搜索和状态筛选",
    responses={
        200: {
            "description": "成功返回定时任务列表",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": "task-001",
                                "name": "每日数据统计",
                                "namespace": "default",
                                "queue_name": "stat_queue",
                                "schedule_type": "cron",
                                "schedule_config": {"cron": "0 0 * * *"},
                                "is_active": True,
                                "next_run_time": "2025-10-19T00:00:00Z"
                            }
                        ],
                        "total": 50,
                        "page": 1,
                        "page_size": 20
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_scheduled_tasks(
    request: Request,
    page: int = Query(1, ge=1, description="页码，从 1 开始", example=1),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，范围 1-100", example=20),
    search: Optional[str] = Query(None, description="搜索关键字，支持按名称、描述搜索", example="数据统计"),
    is_active: Optional[bool] = Query(None, description="是否只返回激活的任务", example=True)
):
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        async with data_access.get_session() as session:
            tasks, total = await data_access.fetch_scheduled_tasks(
                session=session,
                page=page,
                page_size=page_size,
                search=search,
                is_active=is_active
            )
        
        return {
            "success": True,
            "data": tasks,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(f"获取定时任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/filter",
    summary="获取定时任务列表（高级筛选）",
    description="获取定时任务列表，支持高级筛选条件、时间范围查询和多维度过滤",
    responses={
        200: {
            "description": "成功返回筛选后的定时任务列表",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": "task-001",
                                "name": "每日数据统计",
                                "namespace": "default",
                                "queue_name": "stat_queue",
                                "schedule_type": "cron",
                                "schedule_config": {"cron": "0 0 * * *"},
                                "is_active": True,
                                "next_run_time": "2025-10-19T00:00:00Z"
                            }
                        ],
                        "total": 50,
                        "page": 1,
                        "page_size": 20
                    }
                }
            }
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "example": {"detail": "时间范围参数无效"}
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_scheduled_tasks_with_filters(request: Request):
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        body = await request.json()
        
        page = body.get('page', 1)
        page_size = body.get('page_size', 20)
        search = body.get('search')
        is_active = body.get('is_active')
        filters = body.get('filters', [])
        time_range = body.get('time_range')
        start_time = body.get('start_time')
        end_time = body.get('end_time')
        
        async with data_access.get_session() as session:
            tasks, total = await data_access.fetch_scheduled_tasks(
                session=session,
                page=page,
                page_size=page_size,
                search=search,
                is_active=is_active,
                filters=filters,
                time_range=time_range,
                start_time=start_time,
                end_time=end_time
            )
        
        return {
            "success": True,
            "data": tasks,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(f"获取定时任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/",
    summary="创建定时任务",
    description="创建一个新的定时任务，支持多种调度类型和配置选项",
    status_code=201,
    responses={
        201: {
            "description": "定时任务创建成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "id": "task-001",
                            "name": "每日数据统计",
                            "namespace": "default",
                            "queue_name": "stat_queue",
                            "schedule_type": "cron",
                            "schedule_config": {"cron": "0 0 * * *"},
                            "is_active": True,
                            "created_at": "2025-10-19T12:00:00Z"
                        },
                        "message": "定时任务创建成功"
                    }
                }
            }
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "example": {"detail": "调度配置无效: Cron表达式格式错误"}
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def create_scheduled_task(request: Request, task_request: ScheduledTaskRequest):
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        ScheduledTaskService.validate_schedule_config(
            task_request.schedule_type, 
            task_request.schedule_config
        )
        
        task_data = {
            "namespace": task_request.namespace,
            "name": task_request.name,
            "queue_name": task_request.queue_name,
            "task_data": task_request.task_data,
            "schedule_type": task_request.schedule_type,
            "schedule_config": task_request.schedule_config,
            "is_active": task_request.is_active,
            "description": task_request.description,
            "max_retry": task_request.max_retry,
            "timeout": task_request.timeout
        }
        
        async with data_access.get_session() as session:
            task = await data_access.create_scheduled_task(session, task_data)
        
        return {
            "success": True,
            "data": task,
            "message": "定时任务创建成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{task_id}",
    summary="更新定时任务",
    description="更新指定定时任务的配置信息，支持部分更新",
    responses={
        200: {
            "description": "定时任务更新成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "id": "task-001",
                            "name": "每日数据统计（已更新）",
                            "namespace": "default",
                            "queue_name": "stat_queue",
                            "schedule_type": "cron",
                            "schedule_config": {"cron": "0 1 * * *"},
                            "is_active": True,
                            "updated_at": "2025-10-19T12:30:00Z"
                        },
                        "message": "定时任务更新成功"
                    }
                }
            }
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "example": {"detail": "调度配置无效"}
                }
            }
        },
        404: {
            "description": "任务不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "定时任务不存在"}
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def update_scheduled_task(request: Request, task_id: str, task_request: ScheduledTaskRequest):
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        ScheduledTaskService.validate_schedule_config(
            task_request.schedule_type,
            task_request.schedule_config
        )
        
        task_data = {
            "namespace": task_request.namespace,
            "name": task_request.name,
            "queue_name": task_request.queue_name,
            "task_data": task_request.task_data,
            "schedule_type": task_request.schedule_type,
            "schedule_config": task_request.schedule_config,
            "is_active": task_request.is_active,
            "description": task_request.description,
            "max_retry": task_request.max_retry,
            "timeout": task_request.timeout
        }
        
        async with data_access.get_session() as session:
            task = await data_access.update_scheduled_task(session, task_id, task_data)
        
        return {
            "success": True,
            "data": task,
            "message": "定时任务更新成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{task_id}",
    summary="删除定时任务",
    description="删除指定的定时任务，操作不可逆",
    responses={
        200: {
            "description": "定时任务删除成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "定时任务 task-001 已删除"
                    }
                }
            }
        },
        404: {
            "description": "任务不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "定时任务不存在"}
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def delete_scheduled_task(request: Request, task_id: str):
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        async with data_access.get_session() as session:
            success = await data_access.delete_scheduled_task(session, task_id)
        
        if success:
            return {
                "success": True,
                "message": f"定时任务 {task_id} 已删除"
            }
        else:
            raise HTTPException(status_code=404, detail="定时任务不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{task_id}/toggle",
    summary="启用/禁用定时任务",
    description="切换定时任务的启用状态，启用的任务会自动执行，禁用的任务会暂停调度",
    responses={
        200: {
            "description": "任务状态切换成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "id": "task-001",
                            "is_active": False
                        },
                        "message": "定时任务状态已更新"
                    }
                }
            }
        },
        404: {
            "description": "任务不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "定时任务不存在"}
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def toggle_scheduled_task(request: Request, task_id: str):
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        async with data_access.get_session() as session:
            task = await data_access.toggle_scheduled_task(session, task_id)
        
        if task:
            return {
                "success": True,
                "data": {
                    "id": task["id"],
                    "is_active": task["enabled"]  
                },
                "message": "定时任务状态已更新"
            }
        else:
            raise HTTPException(status_code=404, detail="定时任务不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换定时任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{task_id}/execute",
    summary="立即执行定时任务",
    description="手动触发定时任务立即执行一次，不影响原有调度计划",
    responses={
        200: {
            "description": "任务已加入执行队列",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "task_id": "task-001",
                            "job_id": "job-123456",
                            "queue_name": "stat_queue",
                            "status": "queued"
                        },
                        "message": "定时任务已加入执行队列"
                    }
                }
            }
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "example": {"detail": "任务已禁用，无法执行"}
                }
            }
        },
        404: {
            "description": "任务不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "定时任务不存在"}
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def execute_scheduled_task_now(request: Request, task_id: str):
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        if not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")
        
        data_access = app.state.data_access
        namespace_data_access = app.state.namespace_data_access
        
        result = await ScheduledTaskService.execute_task_now(
            data_access,
            namespace_data_access,
            task_id
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"执行定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@router.get(
    "/{task_id}/trend",
    summary="获取定时任务执行趋势",
    description="获取指定定时任务的执行趋势数据，用于可视化分析和监控",
    responses={
        200: {
            "description": "成功返回执行趋势数据",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "task_id": "task-001",
                            "time_points": [
                                "2025-10-13T00:00:00Z",
                                "2025-10-14T00:00:00Z",
                                "2025-10-15T00:00:00Z",
                                "2025-10-16T00:00:00Z",
                                "2025-10-17T00:00:00Z",
                                "2025-10-18T00:00:00Z",
                                "2025-10-19T00:00:00Z"
                            ],
                            "success_count": [10, 12, 11, 13, 12, 14, 15],
                            "failed_count": [1, 0, 2, 0, 1, 0, 0],
                            "avg_duration": [320, 315, 330, 310, 325, 318, 312],
                            "total_executions": 91,
                            "success_rate": 95.6
                        },
                        "time_range": "7d"
                    }
                }
            }
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "example": {"detail": "无效的时间范围参数"}
                }
            }
        },
        404: {
            "description": "任务不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "定时任务不存在"}
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_scheduled_task_execution_trend(
    request: Request,
    task_id: str,
    time_range: str = Query("7d", description="时间范围，支持: 1h, 24h, 7d, 30d, 90d", example="7d")
):
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        async with data_access.get_session() as session:
            data = await data_access.fetch_task_execution_trend(
                session=session,
                task_id=task_id,
                time_range=time_range
            )
        
        return {
            "success": True,
            "data": data,
            "time_range": time_range
        }
    except Exception as e:
        logger.error(f"获取定时任务执行趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/statistics",
    summary="获取定时任务统计数据",
    description="获取指定命名空间下所有定时任务的统计数据和概览信息",
    responses={
        200: {
            "description": "成功返回统计数据",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "namespace": "default",
                            "total_tasks": 25,
                            "active_tasks": 18,
                            "inactive_tasks": 7,
                            "total_executions_today": 156,
                            "successful_executions_today": 148,
                            "failed_executions_today": 8,
                            "success_rate_today": 94.9,
                            "avg_execution_duration": 285,
                            "next_executions": [
                                {
                                    "task_id": "task-001",
                                    "task_name": "每日数据统计",
                                    "next_run_time": "2025-10-20T00:00:00Z"
                                },
                                {
                                    "task_id": "task-002",
                                    "task_name": "健康检查",
                                    "next_run_time": "2025-10-19T13:00:00Z"
                                }
                            ],
                            "task_type_distribution": {
                                "cron": 15,
                                "interval": 8,
                                "date": 2
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "命名空间不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "命名空间 'production' 不存在"}
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def get_scheduled_tasks_statistics(request: Request, namespace: str):
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        async with data_access.AsyncSessionLocal() as session:
            stats = await data_access.get_scheduled_tasks_statistics(session, namespace)
            return stats
    except Exception as e:
        logger.error(f"获取定时任务统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']