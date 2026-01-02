"""
资产管理模块 - 管理各种资源配置

支持的资产类型：
- compute_node: 计算节点（如 ComfyUI、SD WebUI）
- api_key: API 密钥（如 OpenAI、Claude）
- config: 通用配置项
"""
from fastapi import APIRouter, HTTPException, Request, Query, Path
from typing import Optional, Dict, Any, List
import logging

from jettask.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetInfo,
    AssetListResponse,
    AssetGroupSummary,
    AssetType,
    AssetStatus
)
from jettask.db.models.asset import AssetType as DBAssetType, AssetStatus as DBAssetStatus
from jettask.webui.services.asset_service import AssetService

router = APIRouter(prefix="/assets", tags=["assets"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    summary="创建资产",
    description="""创建新的资产配置。

**资产类型**:
- `compute_node`: 计算节点，用于负载均衡（如 ComfyUI、SD WebUI 节点）
- `api_key`: API 密钥，可能有配额限制（如 OpenAI Key）
- `config`: 通用配置项

**示例**:
```json
{
    "asset_type": "compute_node",
    "asset_group": "comfyui",
    "name": "node-1",
    "config": {
        "url": "http://192.168.1.100:8188",
        "max_concurrent": 2
    },
    "weight": 1,
    "description": "ComfyUI 主节点"
}
```
""",
    responses={
        200: {"description": "创建成功"},
        400: {"description": "资产已存在或参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
async def create_asset(
    request: Request,
    asset_request: AssetCreate
) -> Dict[str, Any]:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        try:
            result = await AssetService.create_asset(
                pg_session=pg_session,
                namespace=ns.name,
                request=asset_request
            )
            return {
                "success": True,
                "message": "Asset created successfully",
                "data": result.model_dump()
            }
        finally:
            await pg_session.close()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建资产失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "",
    summary="查询资产列表",
    description="""查询资产列表，支持按类型、分组、状态筛选。

**筛选参数**:
- `asset_type`: 资产类型（compute_node/api_key/config）
- `asset_group`: 资产分组（如 comfyui、openai）
- `status`: 状态（active/inactive/error）
""",
    response_model=AssetListResponse,
    responses={
        200: {"description": "成功返回资产列表"},
        500: {"description": "服务器内部错误"}
    }
)
async def list_assets(
    request: Request,
    asset_type: Optional[str] = Query(None, description="资产类型"),
    asset_group: Optional[str] = Query(None, description="资产分组"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小")
) -> AssetListResponse:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        db_asset_type = None
        if asset_type:
            try:
                db_asset_type = DBAssetType(asset_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的资产类型: {asset_type}")

        db_status = None
        if status:
            try:
                db_status = DBAssetStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的状态: {status}")

        try:
            result = await AssetService.list_assets(
                pg_session=pg_session,
                namespace=ns.name,
                asset_type=db_asset_type,
                asset_group=asset_group,
                status=db_status,
                page=page,
                page_size=page_size
            )
            return result
        finally:
            await pg_session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询资产列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/groups",
    summary="获取资产分组摘要",
    description="获取所有资产分组的统计摘要",
    responses={
        200: {"description": "成功返回分组摘要"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_group_summary(request: Request) -> Dict[str, Any]:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        try:
            summaries = await AssetService.get_group_summary(
                pg_session=pg_session,
                namespace=ns.name
            )
            return {
                "success": True,
                "data": [s.model_dump() for s in summaries]
            }
        finally:
            await pg_session.close()

    except Exception as e:
        logger.error(f"获取资产分组摘要失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/group/{asset_group}",
    summary="获取分组下所有资产",
    description="获取指定分组下的所有资产（不分页）",
    responses={
        200: {"description": "成功返回资产列表"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_assets_by_group(
    request: Request,
    asset_group: str = Path(..., description="资产分组"),
    status: Optional[str] = Query(None, description="状态筛选")
) -> Dict[str, Any]:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        db_status = None
        if status:
            try:
                db_status = DBAssetStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的状态: {status}")

        try:
            assets = await AssetService.list_assets_by_group(
                pg_session=pg_session,
                namespace=ns.name,
                asset_group=asset_group,
                status=db_status
            )
            return {
                "success": True,
                "asset_group": asset_group,
                "data": [a.model_dump() for a in assets],
                "total": len(assets)
            }
        finally:
            await pg_session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分组资产失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{asset_id}",
    summary="获取资产详情",
    description="根据 ID 获取资产详情",
    responses={
        200: {"description": "成功返回资产详情"},
        404: {"description": "资产不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_asset(
    request: Request,
    asset_id: int = Path(..., description="资产 ID")
) -> Dict[str, Any]:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        try:
            result = await AssetService.get_asset(
                pg_session=pg_session,
                namespace=ns.name,
                asset_id=asset_id
            )

            if not result:
                raise HTTPException(status_code=404, detail="Asset not found")

            return {
                "success": True,
                "data": result.model_dump()
            }
        finally:
            await pg_session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取资产详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{asset_id}",
    summary="更新资产",
    description="更新资产配置",
    responses={
        200: {"description": "更新成功"},
        404: {"description": "资产不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def update_asset(
    request: Request,
    asset_id: int = Path(..., description="资产 ID"),
    asset_request: AssetUpdate = ...
) -> Dict[str, Any]:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        try:
            result = await AssetService.update_asset(
                pg_session=pg_session,
                namespace=ns.name,
                asset_id=asset_id,
                request=asset_request
            )

            if not result:
                raise HTTPException(status_code=404, detail="Asset not found")

            return {
                "success": True,
                "message": "Asset updated successfully",
                "data": result.model_dump()
            }
        finally:
            await pg_session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新资产失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{asset_id}",
    summary="删除资产",
    description="删除资产配置",
    responses={
        200: {"description": "删除成功"},
        404: {"description": "资产不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def delete_asset(
    request: Request,
    asset_id: int = Path(..., description="资产 ID")
) -> Dict[str, Any]:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        try:
            success = await AssetService.delete_asset(
                pg_session=pg_session,
                namespace=ns.name,
                asset_id=asset_id
            )

            if not success:
                raise HTTPException(status_code=404, detail="Asset not found")

            return {
                "success": True,
                "message": "Asset deleted successfully"
            }
        finally:
            await pg_session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除资产失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/batch-status",
    summary="批量更新状态",
    description="批量更新资产状态",
    responses={
        200: {"description": "更新成功"},
        500: {"description": "服务器内部错误"}
    }
)
async def batch_update_status(
    request: Request,
    asset_ids: List[int] = Query(..., description="资产 ID 列表"),
    status: str = Query(..., description="新状态（active/inactive/error）")
) -> Dict[str, Any]:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        try:
            db_status = DBAssetStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {status}")

        try:
            count = await AssetService.batch_update_status(
                pg_session=pg_session,
                namespace=ns.name,
                asset_ids=asset_ids,
                status=db_status
            )
            return {
                "success": True,
                "message": f"Updated {count} assets",
                "updated_count": count
            }
        finally:
            await pg_session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量更新状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']
