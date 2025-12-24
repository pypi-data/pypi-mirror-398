"""
告警管理路由
提供轻量级的路由入口，业务逻辑在 AlertService 中实现
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from jettask.schemas import AlertRuleRequest
from jettask.webui.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])
logger = logging.getLogger(__name__)


@router.get(
    "/rules",
    summary="获取告警规则列表",
    description="分页获取系统中配置的所有告警规则，支持按激活状态筛选",
    responses={
        200: {
            "description": "成功返回告警规则列表"
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {"detail": "获取告警规则列表失败: Database error"}
                }
            }
        }
    }
)
async def get_alert_rules(
    page: int = Query(1, ge=1, description="页码，从 1 开始", example=1),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，范围 1-100", example=20),
    is_active: Optional[bool] = Query(None, description="是否只返回激活的规则", example=True)
):
    try:
        return AlertService.get_alert_rules(page, page_size, is_active)
    except Exception as e:
        logger.error(f"获取告警规则列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/rules",
    summary="创建告警规则",
    description="创建一个新的告警规则，用于监控系统指标并在达到阈值时触发告警",
    status_code=201,
    responses={
        201: {
            "description": "告警规则创建成功"
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "example": {"detail": "规则名称已存在"}
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def create_alert_rule(request: AlertRuleRequest):
    try:
        return AlertService.create_alert_rule(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建告警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/rules/{rule_id}",
    summary="更新告警规则",
    description="更新指定告警规则的配置信息，包括阈值、告警级别等",
    responses={
        200: {
            "description": "告警规则更新成功"
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
            "description": "告警规则不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "告警规则 'xxx' 不存在"}
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def update_alert_rule(rule_id: str, request: AlertRuleRequest):
    try:
        return AlertService.update_alert_rule(rule_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新告警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/rules/{rule_id}",
    summary="删除告警规则",
    description="删除指定的告警规则，删除后将停止监控该规则",
    responses={
        200: {
            "description": "告警规则删除成功",
            "content": {
                "application/json": {
                    "example": {"success": True, "message": "告警规则已删除"}
                }
            }
        },
        404: {
            "description": "告警规则不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "告警规则 'xxx' 不存在"}
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def delete_alert_rule(rule_id: str):
    try:
        return AlertService.delete_alert_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除告警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/rules/{rule_id}/toggle",
    summary="启用/禁用告警规则",
    description="切换告警规则的启用状态，禁用后将暂停监控",
    responses={
        200: {
            "description": "告警规则状态切换成功",
            "content": {
                "application/json": {
                    "example": {"success": True, "enabled": True, "message": "告警规则已启用"}
                }
            }
        },
        404: {
            "description": "告警规则不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "告警规则 'xxx' 不存在"}
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def toggle_alert_rule(rule_id: str):
    try:
        return AlertService.toggle_alert_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"切换告警规则状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/rules/{rule_id}/history",
    summary="获取告警触发历史",
    description="分页获取指定告警规则的历史触发记录",
    responses={
        200: {
            "description": "成功返回告警历史记录"
        },
        404: {
            "description": "告警规则不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "告警规则 'xxx' 不存在"}
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def get_alert_history(
    rule_id: str,
    page: int = Query(1, ge=1, description="页码，从 1 开始", example=1),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，范围 1-100", example=20)
):
    try:
        return AlertService.get_alert_history(rule_id, page, page_size)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取告警历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/rules/{rule_id}/test",
    summary="测试告警规则",
    description="测试告警规则的通知功能，发送测试告警消息",
    responses={
        200: {
            "description": "测试通知发送成功",
            "content": {
                "application/json": {
                    "example": {"success": True, "message": "测试通知已发送"}
                }
            }
        },
        404: {
            "description": "告警规则不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "告警规则 'xxx' 不存在"}
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def test_alert_rule(rule_id: str):
    try:
        return AlertService.test_alert_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"测试告警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/statistics",
    summary="获取告警统计信息",
    description="获取告警系统的统计数据，包括告警数量、级别分布等",
    responses={
        200: {
            "description": "成功返回告警统计信息"
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {"detail": "获取告警统计信息失败: Database error"}
                }
            }
        }
    }
)
async def get_alert_statistics(
    namespace: Optional[str] = Query(None, description="命名空间名称，不指定则统计所有命名空间", example="default")
):
    try:
        return AlertService.get_alert_statistics(namespace)
    except Exception as e:
        logger.error(f"获取告警统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/active",
    summary="获取当前活跃的告警",
    description="获取系统中当前正在活跃状态的告警列表",
    responses={
        200: {
            "description": "成功返回活跃告警列表"
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {"detail": "获取活跃告警失败: Database error"}
                }
            }
        }
    }
)
async def get_active_alerts(
    namespace: Optional[str] = Query(None, description="命名空间名称，不指定则返回所有命名空间的活跃告警", example="default")
):
    try:
        return AlertService.get_active_alerts(namespace)
    except Exception as e:
        logger.error(f"获取活跃告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/active/{alert_id}/acknowledge",
    summary="确认告警",
    description="确认一个活跃的告警，表示已知晓该告警并正在处理",
    responses={
        200: {
            "description": "告警确认成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "告警已确认",
                        "acknowledged_at": "2025-10-19T10:30:00Z",
                        "acknowledged_by": "admin"
                    }
                }
            }
        },
        404: {
            "description": "告警不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "告警 'xxx' 不存在"}
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def acknowledge_alert(
    alert_id: str,
    user: str = Query("system", description="确认用户名称", example="admin")
):
    try:
        return AlertService.acknowledge_alert(alert_id, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"确认告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/active/{alert_id}/resolve",
    summary="解决告警",
    description="标记告警为已解决状态，并可添加解决说明",
    responses={
        200: {
            "description": "告警解决成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "告警已解决",
                        "resolved_at": "2025-10-19T10:45:00Z"
                    }
                }
            }
        },
        404: {
            "description": "告警不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "告警 'xxx' 不存在"}
                }
            }
        },
        500: {
            "description": "服务器内部错误"
        }
    }
)
async def resolve_alert(
    alert_id: str,
    resolution_note: Optional[str] = Query(None, description="解决说明，记录如何解决该告警", example="已修复任务处理逻辑，重启相关服务")
):
    try:
        return AlertService.resolve_alert(alert_id, resolution_note)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"解决告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']