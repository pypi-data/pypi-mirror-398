"""
命名空间管理路由
提供命名空间的增删改查和管理功能
"""
from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional, List, Dict, Any
import logging
import traceback

from jettask.schemas import NamespaceCreate, NamespaceUpdate, NamespaceResponse, NamespaceStatisticsResponse
from jettask.webui.services.namespace_service import NamespaceService

logger = logging.getLogger(__name__)

global_router = APIRouter(prefix="/namespaces", tags=["namespaces"])
namespace_router = APIRouter(tags=["namespaces"])


async def get_meta_db_session(request: Request):
    if not hasattr(request.app.state, 'meta_db_session_factory'):
        raise HTTPException(status_code=500, detail="元数据库会话工厂未初始化")
    return request.app.state.meta_db_session_factory()


@global_router.get(
    "/",
    summary="列出所有命名空间",
    description="获取系统中所有命名空间的列表，支持分页和按状态筛选",
    response_model=List[NamespaceResponse],
    responses={
        200: {
            "description": "成功返回命名空间列表"
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {"detail": "获取命名空间列表失败: Database error"}
                }
            }
        }
    }
)
async def list_namespaces(
    request: Request,
    page: int = Query(1, ge=1, description="页码，从 1 开始", example=1),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，范围 1-100", example=20),
    is_active: Optional[bool] = Query(None, description="是否只返回激活的命名空间", example=True)
) -> List[Dict[str, Any]]:
    try:
        async with await get_meta_db_session(request) as session:
            return await NamespaceService.list_namespaces(session, page, page_size, is_active)
    except Exception as e:
        logger.error(f"获取命名空间列表失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@global_router.post(
    "/",
    summary="创建新的命名空间",
    description="创建一个新的命名空间，可以选择直接配置或使用 Nacos 配置",
    response_model=NamespaceResponse,
    status_code=201,
    responses={
        201: {
            "description": "命名空间创建成功"
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "example": {"detail": "命名空间名称已存在"}
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def create_namespace(
    request: Request,
    namespace: NamespaceCreate
) -> Dict[str, Any]:
    try:
        async with await get_meta_db_session(request) as session:
            return await NamespaceService.create_namespace(session, namespace)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建命名空间失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@namespace_router.get(
    "/",
    summary="获取命名空间详细信息",
    description="获取指定命名空间的完整配置信息和状态",
    response_model=NamespaceResponse,
    responses={
        200: {
            "description": "成功返回命名空间详情"
        },
        404: {
            "description": "命名空间不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "命名空间 'production' 不存在"}
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def get_namespace(
    request: Request,
    namespace: str  
) -> Dict[str, Any]:
    try:
        async with await get_meta_db_session(request) as session:
            return await NamespaceService.get_namespace(session, namespace)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取命名空间失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@namespace_router.put(
    "/",
    summary="更新命名空间配置",
    description="更新指定命名空间的配置信息，支持部分更新",
    response_model=NamespaceResponse,
    responses={
        200: {
            "description": "命名空间更新成功"
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "example": {"detail": "配置参数无效"}
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
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def update_namespace(
    request: Request,
    namespace_update: NamespaceUpdate,
    namespace: str  
) -> Dict[str, Any]:
    _ = namespace  
    try:
        ns = request.state.ns
        namespace_name = ns.name
        async with await get_meta_db_session(request) as session:
            return await NamespaceService.update_namespace(session, namespace_name, namespace_update)
    except ValueError as e:
        status_code = 404 if "不存在" in str(e) else 400
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        logger.error(f"更新命名空间失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@namespace_router.delete(
    "/",
    summary="删除命名空间",
    description="删除指定的命名空间，默认命名空间不能删除",
    responses={
        200: {
            "description": "命名空间删除成功",
            "content": {
                "application/json": {
                    "example": {"success": True, "message": "命名空间已删除"}
                }
            }
        },
        400: {
            "description": "操作不允许",
            "content": {
                "application/json": {
                    "example": {"detail": "默认命名空间不能删除"}
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
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def delete_namespace(
    request: Request,
    namespace: str  
) -> Dict[str, Any]:
    _ = namespace  
    try:
        ns = request.state.ns
        namespace_name = ns.name
        async with await get_meta_db_session(request) as session:
            return await NamespaceService.delete_namespace(session, namespace_name)
    except ValueError as e:
        status_code = 400 if "默认命名空间" in str(e) else 404
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        logger.error(f"删除命名空间失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@namespace_router.get(
    "/statistics",
    summary="获取命名空间统计信息",
    description="获取指定命名空间的统计数据，包括队列数、任务数、Worker 数等",
    response_model=NamespaceStatisticsResponse,
    responses={
        200: {
            "description": "成功返回统计信息"
        },
        404: {
            "description": "命名空间不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "命名空间 'production' 不存在"}
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def get_namespace_statistics(
    request: Request,
    namespace: str  
) -> Dict[str, Any]:
    _ = namespace  
    try:
        ns = request.state.ns
        namespace_name = ns.name
        async with await get_meta_db_session(request) as session:
            return await NamespaceService.get_namespace_statistics(session, namespace_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取命名空间统计信息失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

__all__ = ['global_router', 'namespace_router']
