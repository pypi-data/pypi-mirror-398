"""
Webhook 服务层

处理 webhook 通知的接收、存储和 Redis pub/sub 通知
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import json
import logging

from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from jettask.db.models.webhook import Webhook, WebhookStatus
from jettask.schemas.webhook import (
    WebhookReceiveResponse,
    WebhookInfo,
    WebhookListResponse
)

logger = logging.getLogger(__name__)

WEBHOOK_CHANNEL_PREFIX = "jettask:webhook:"


class WebhookService:
    """Webhook 服务类"""

    @staticmethod
    def get_channel_name(namespace: str, callback_id: str) -> str:
        return f"{WEBHOOK_CHANNEL_PREFIX}{namespace}:{callback_id}"

    @staticmethod
    async def receive_webhook(
        pg_session: AsyncSession,
        redis_client,
        namespace: str,
        callback_id: str,
        payload: Dict[str, Any]
    ) -> WebhookReceiveResponse:
        webhook = Webhook(
            namespace=namespace,
            callback_id=callback_id,
            payload=payload,
            status=WebhookStatus.PENDING,
            received_at=datetime.now(timezone.utc)
        )

        pg_session.add(webhook)
        await pg_session.commit()

        logger.info(f"Webhook 已接收: callback_id={callback_id}, namespace={namespace}")

        channel = WebhookService.get_channel_name(namespace, callback_id)
        message = json.dumps({
            "callback_id": callback_id,
            "payload": payload,
            "received_at": datetime.now(timezone.utc).isoformat()
        })

        try:
            await redis_client.publish(channel, message)
            logger.debug(f"Webhook 通知已发布到 channel: {channel}")
        except Exception as e:
            logger.warning(f"发布 webhook 通知失败: {e}")

        result_key = f"{WEBHOOK_CHANNEL_PREFIX}result:{namespace}:{callback_id}"
        try:
            await redis_client.rpush(result_key, message)
            await redis_client.expire(result_key, 86400)
        except Exception as e:
            logger.warning(f"写入 webhook 结果到 Redis 失败: {e}")

        return WebhookReceiveResponse(
            success=True,
            message="Webhook received successfully",
            callback_id=callback_id
        )

    @staticmethod
    async def list_webhooks(
        pg_session: AsyncSession,
        namespace: str,
        callback_id: Optional[str] = None,
        status: Optional[WebhookStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> WebhookListResponse:
        query = select(Webhook).where(Webhook.namespace == namespace)

        if callback_id:
            query = query.where(Webhook.callback_id == callback_id)
        if status:
            query = query.where(Webhook.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await pg_session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(desc(Webhook.received_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await pg_session.execute(query)
        webhooks = result.scalars().all()

        data = []
        for webhook in webhooks:
            data.append(WebhookInfo(
                id=webhook.id,
                namespace=webhook.namespace,
                callback_id=webhook.callback_id,
                payload=webhook.payload,
                status=webhook.status,
                received_at=webhook.received_at
            ))

        return WebhookListResponse(
            success=True,
            data=data,
            total=total,
            page=page,
            page_size=page_size
        )

    @staticmethod
    async def get_webhook_by_callback_id(
        pg_session: AsyncSession,
        namespace: str,
        callback_id: str
    ) -> Optional[WebhookInfo]:
        query = select(Webhook).where(
            Webhook.namespace == namespace,
            Webhook.callback_id == callback_id
        ).order_by(desc(Webhook.received_at)).limit(1)

        result = await pg_session.execute(query)
        webhook = result.scalar_one_or_none()

        if not webhook:
            return None

        return WebhookInfo(
            id=webhook.id,
            namespace=webhook.namespace,
            callback_id=webhook.callback_id,
            payload=webhook.payload,
            status=webhook.status,
            received_at=webhook.received_at
        )

    @staticmethod
    async def mark_webhook_success(
        pg_session: AsyncSession,
        namespace: str,
        callback_id: str
    ) -> bool:
        stmt = (
            update(Webhook)
            .where(
                Webhook.namespace == namespace,
                Webhook.callback_id == callback_id,
                Webhook.status == WebhookStatus.PENDING
            )
            .values(status=WebhookStatus.SUCCESS)
        )

        result = await pg_session.execute(stmt)
        await pg_session.commit()

        return result.rowcount > 0
