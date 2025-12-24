"""
设置模块 - 系统配置
提供轻量级的路由入口，业务逻辑在 SettingsService 中实现
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import traceback

from jettask.schemas import SystemSettingsResponse, DatabaseStatusResponse
from jettask.webui.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])



@router.get(
    "/system",
    summary="获取系统配置信息",
    description="获取系统级别的配置信息，包括 API 版本、服务名称、运行环境、数据库状态等",
    response_model=SystemSettingsResponse,
    responses={
        200: {
            "description": "成功返回系统配置信息"
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "获取系统配置失败: Configuration error"
                    }
                }
            }
        }
    }
)
async def get_system_settings() -> Dict[str, Any]:
    try:
        return SettingsService.get_system_settings()
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/database-status",
    summary="检查数据库连接状态",
    description="检查数据库（PostgreSQL/MySQL）的连接状态和性能指标",
    response_model=DatabaseStatusResponse,
    responses={
        200: {
            "description": "成功返回数据库状态"
        },
        500: {
            "description": "服务器内部错误或数据库连接失败",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "数据库状态检查失败: Connection refused"
                    }
                }
            }
        }
    }
)
async def check_database_status() -> Dict[str, Any]:
    try:
        return await SettingsService.check_database_status()
    except Exception as e:
        logger.error(f"数据库状态检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']