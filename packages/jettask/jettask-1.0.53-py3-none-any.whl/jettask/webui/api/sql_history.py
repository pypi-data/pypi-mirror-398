"""
SQL 历史查询模块 - SQL WHERE 条件的历史记录管理、模糊搜索和使用统计
"""
from fastapi import APIRouter, HTTPException, Request, Query, Path
from typing import Optional, Dict, Any

from jettask.webui.services.sql_history_service import SQLHistoryService
from jettask.utils.task_logger import get_task_logger

router = APIRouter(prefix="/sql-history", tags=["sql-history"])
logger = get_task_logger(__name__)


@router.get(
    "/search",
    summary="搜索 SQL 历史记录",
    description="""模糊搜索 SQL WHERE 查询历史记录，支持自动补全。

**主要功能**:
- 模糊匹配 WHERE 条件和别名
- 按使用次数 + 创建时间降序排列
- 支持按类别过滤（系统内置/用户历史）
- 使用 PostgreSQL pg_trgm 扩展实现高效搜索

**使用场景**: 前端输入框自动补全、查询建议""",
    responses={
        200: {
            "description": "成功返回匹配的 SQL 历史记录",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": 1,
                                "namespace": "default",
                                "where_clause": "status = 'success'",
                                "alias": "成功的任务",
                                "category": "system",
                                "usage_count": 150,
                                "created_at": "2025-11-18T00:00:00+00:00",
                                "last_used_at": "2025-11-18T10:30:00+00:00"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def search_sql_history(
    request: Request,
    keyword: Optional[str] = Query(None, description="搜索关键词（模糊匹配 WHERE 条件和别名）", example="status"),
    category: Optional[str] = Query(None, description="类别过滤: system（系统内置）/ user（用户历史），为空返回所有", example="user"),
    limit: int = Query(10, ge=1, le=50, description="返回数量限制", example=10)
) -> Dict[str, Any]:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        results = await SQLHistoryService.search(
            pg_session=pg_session,
            namespace=ns.name,
            keyword=keyword,
            category=category,
            limit=limit
        )

        if category == 'system' and not results:
            logger.info(f"命名空间 '{ns.name}' 中没有系统内置查询，尝试从 'default' 复制")
            copied_count = await SQLHistoryService.copy_system_templates(
                pg_session=pg_session,
                target_namespace=ns.name,
                template_namespace='default'
            )

            if copied_count > 0:
                results = await SQLHistoryService.search(
                    pg_session=pg_session,
                    namespace=ns.name,
                    keyword=keyword,
                    category=category,
                    limit=limit
                )
                logger.info(f"复制成功，重新查询返回 {len(results)} 条记录")

        return {
            "success": True,
            "data": results
        }

    except Exception as e:
        logger.error(f"搜索 SQL 历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{history_id}",
    summary="删除 SQL 历史记录",
    description="""删除用户的历史记录（系统内置记录不可删除）。

**限制**: 只有 category='user' 的记录可以删除，系统内置（category='system'）不可删除""",
    responses={
        200: {
            "description": "成功删除记录",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "历史记录已删除"
                    }
                }
            }
        },
        404: {"description": "记录不存在或不可删除"}
    }
)
async def delete_sql_history(
    request: Request,
    history_id: int = Path(..., description="历史记录 ID", example=1)
) -> Dict[str, Any]:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        success = await SQLHistoryService.delete_history(
            pg_session=pg_session,
            history_id=history_id
        )

        if success:
            return {
                "success": True,
                "message": "历史记录已删除"
            }
        else:
            raise HTTPException(status_code=404, detail="记录不存在或不可删除（系统内置记录不可删除）")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除 SQL 历史记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
