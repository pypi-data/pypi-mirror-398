"""
Webhook 模块 - 接收第三方平台的 webhook 回调通知

提供统一的 webhook 接收接口，支持：
- 接收任意第三方平台的回调通知（支持任意 JSON 结构）
- 通过 callback_id 关联到原始任务
- 存储 webhook 数据并通过 Redis pub/sub 通知等待的任务
"""
from fastapi import APIRouter, HTTPException, Request, Query, Path
from typing import Optional, Dict, Any
import logging

from jettask.schemas.webhook import (
    WebhookReceiveResponse,
    WebhookListResponse
)
from jettask.db.models.webhook import WebhookStatus
from jettask.webui.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post(
    "/{callback_id}",
    summary="接收 webhook 通知",
    description="""接收第三方平台的 webhook 回调通知。

**设计理念**:
这是一个极简的通用 webhook 接收接口，支持接收任意 JSON 格式的数据。
第三方平台回调时，直接 POST 任意 JSON 到这个 URL 即可。

**使用流程**:
1. 任务中生成 callback_id 并构建 webhook URL
2. 调用第三方 API 时传递 webhook URL
3. 第三方平台完成后回调此接口
4. 任务通过 wait_for_webhook() 等待并获取结果

**Webhook URL 格式**:
```
POST /api/task/v1/{namespace}/webhooks/{callback_id}
Content-Type: application/json

{... 任意 JSON 数据 ...}
```

**任务中的使用示例**:
```python
from jettask.utils.webhook import WebhookAwaiter

@app.task(queue="image_gen")
async def generate_image(prompt: str):
    async with WebhookAwaiter(
        redis_client=app.redis,
        namespace="default",
        base_url="https://your-api.com"
    ) as awaiter:
        # 调用第三方 API，传递 webhook URL
        await replicate.run(
            model="stability-ai/sdxl",
            input={"prompt": prompt},
            webhook=awaiter.webhook_url
        )

        # 等待回调结果（阻塞直到收到或超时）
        result = await awaiter.wait(timeout=600)

    return result
```
""",
    response_model=WebhookReceiveResponse,
    responses={
        200: {
            "description": "Webhook 接收成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Webhook received successfully",
                        "callback_id": "cb_abc123"
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"}
    }
)
async def receive_webhook(
    request: Request,
    callback_id: str = Path(..., description="回调 ID，由任务生成并传递给第三方", example="cb_abc123")
) -> WebhookReceiveResponse:
    try:
        ns = request.state.ns

        try:
            payload = await request.json()
        except Exception:
            body = await request.body()
            payload = {"raw": body.decode('utf-8', errors='replace')}

        pg_session = await ns.get_pg_session()

        redis_client = await ns.get_redis_client()

        try:
            result = await WebhookService.receive_webhook(
                pg_session=pg_session,
                redis_client=redis_client,
                namespace=ns.name,
                callback_id=callback_id,
                payload=payload
            )
            return result
        finally:
            await pg_session.close()

    except Exception as e:
        logger.error(f"接收 webhook 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "",
    summary="查询 webhook 列表",
    description="""查询 webhook 通知记录列表。

**筛选条件**:
- callback_id: 按回调 ID 筛选
- status: 按处理状态筛选（pending/success/failed）

**使用场景**: 查看 webhook 通知历史、监控回调状态、排查问题
""",
    response_model=WebhookListResponse,
    responses={
        200: {"description": "成功返回 webhook 列表"},
        500: {"description": "服务器内部错误"}
    }
)
async def list_webhooks(
    request: Request,
    callback_id: Optional[str] = Query(None, description="按回调 ID 筛选", example="cb_abc123"),
    status: Optional[str] = Query(None, description="按状态筛选（pending/success/failed）", example="pending"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小")
) -> WebhookListResponse:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        webhook_status = None
        if status:
            try:
                webhook_status = WebhookStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的状态值: {status}。有效值: pending, success, failed"
                )

        try:
            result = await WebhookService.list_webhooks(
                pg_session=pg_session,
                namespace=ns.name,
                callback_id=callback_id,
                status=webhook_status,
                page=page,
                page_size=page_size
            )
            return result
        finally:
            await pg_session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询 webhook 列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{callback_id}",
    summary="获取 webhook 详情",
    description="根据 callback_id 获取最新的 webhook 通知详情",
    responses={
        200: {"description": "成功返回 webhook 详情"},
        404: {"description": "Webhook 不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_webhook(
    request: Request,
    callback_id: str = Path(..., description="回调 ID", example="cb_abc123")
) -> Dict[str, Any]:
    try:
        ns = request.state.ns
        pg_session = await ns.get_pg_session()

        try:
            result = await WebhookService.get_webhook_by_callback_id(
                pg_session=pg_session,
                namespace=ns.name,
                callback_id=callback_id
            )

            if not result:
                raise HTTPException(status_code=404, detail="Webhook not found")

            return {
                "success": True,
                "data": result.model_dump()
            }
        finally:
            await pg_session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 webhook 详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']
