"""
Webhook 工具类

提供给任务使用的 webhook 相关工具函数
"""
import asyncio
import json
import uuid
import logging
from typing import Optional, Dict, Any, List, Callable, AsyncIterator
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

WEBHOOK_CHANNEL_PREFIX = "jettask:webhook:"


def generate_callback_id() -> str:
    return f"cb_{uuid.uuid4().hex[:16]}"


def build_webhook_url(base_url: str, namespace: str, callback_id: str) -> str:
    if not base_url.endswith('/'):
        base_url = base_url + '/'

    path = f"{namespace}/webhooks/{callback_id}"
    return urljoin(base_url, path)


class WebhookAwaiter:
    """
    Webhook 等待器

    支持接收多次回调通知，提供迭代器和条件等待两种使用方式。

    Example 1: 等待直到满足条件（推荐）
        ```python
        @app.task(queue="image_gen")
        async def generate_image(prompt: str):
            async with WebhookAwaiter(
                redis_client=app.redis,
                namespace="default",
                base_url="https://api.example.com"
            ) as awaiter:
                # 调用第三方 API
                await replicate.run(
                    model="stability-ai/sdxl",
                    input={"prompt": prompt},
                    webhook=awaiter.webhook_url
                )

                # 等待直到状态为 completed 或 failed
                result = await awaiter.wait_until(
                    condition=lambda p: p.get("status") in ("succeeded", "failed"),
                    timeout=600
                )

            return result
        ```

    Example 2: 迭代接收所有回调
        ```python
        @app.task(queue="video_process")
        async def process_video(video_url: str):
            async with WebhookAwaiter(
                redis_client=app.redis,
                namespace="default",
                base_url="https://api.example.com"
            ) as awaiter:
                # 调用第三方 API
                await start_video_process(video_url, webhook=awaiter.webhook_url)

                # 迭代接收所有回调
                async for payload in awaiter.iter_callbacks(timeout=1800):
                    status = payload.get("status")
                    progress = payload.get("progress", 0)

                    print(f"状态: {status}, 进度: {progress}%")

                    if status == "completed":
                        return payload.get("output")
                    elif status == "failed":
                        raise Exception(payload.get("error"))

            raise TimeoutError("处理超时")
        ```

    Example 3: 手动循环接收
        ```python
        async with WebhookAwaiter(...) as awaiter:
            await start_task(webhook=awaiter.webhook_url)

            while True:
                payload = await awaiter.wait_next(timeout=60)
                if payload is None:
                    continue  # 超时，继续等待

                if payload.get("status") == "completed":
                    return payload
        ```
    """

    def __init__(
        self,
        redis_client,
        namespace: str,
        base_url: str,
        callback_id: Optional[str] = None
    ):
        self.redis_client = redis_client
        self.namespace = namespace
        self.base_url = base_url
        self.callback_id = callback_id or generate_callback_id()
        self._webhook_url = None
        self._pubsub = None
        self._channel_name = f"{WEBHOOK_CHANNEL_PREFIX}{namespace}:{self.callback_id}"
        self._result_key = f"{WEBHOOK_CHANNEL_PREFIX}result:{namespace}:{self.callback_id}"
        self._started = False
        self._closed = False

    @property
    def webhook_url(self) -> str:
        if self._webhook_url is None:
            self._webhook_url = build_webhook_url(
                self.base_url, self.namespace, self.callback_id
            )
        return self._webhook_url

    async def _ensure_subscribed(self):
        if self._pubsub is None:
            self._pubsub = self.redis_client.pubsub()
            await self._pubsub.subscribe(self._channel_name)
            self._started = True
            logger.debug(f"已订阅 webhook channel: {self._channel_name}")

    async def _pubsub_listener(self, result_queue: asyncio.Queue) -> None:
        while not self._closed:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )

                if message and message.get("type") == "message":
                    try:
                        data = json.loads(message["data"])
                        logger.debug(f"通过 pub/sub 收到 webhook: callback_id={self.callback_id}")
                        await result_queue.put(("pubsub", data.get("payload")))
                        return  
                    except json.JSONDecodeError:
                        logger.warning(f"解析 pub/sub 消息失败: {message}")

            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.warning(f"pub/sub 异常: {e}")
                await asyncio.sleep(0.5)

    async def _poll_listener(self, result_queue: asyncio.Queue, poll_interval: float = 2.0) -> None:
        while not self._closed:
            try:
                result = await self.redis_client.lpop(self._result_key)
                if result:
                    try:
                        data = json.loads(result)
                        logger.debug(f"通过轮询收到 webhook: callback_id={self.callback_id}")
                        await result_queue.put(("poll", data.get("payload")))
                        return  
                    except json.JSONDecodeError:
                        logger.warning(f"解析 Redis list 结果失败: {result}")
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.warning(f"轮询 Redis 失败: {e}")

            await asyncio.sleep(poll_interval)

    async def _get_next_message(self, timeout: float) -> Optional[Dict[str, Any]]:
        await self._ensure_subscribed()

        if self._closed:
            return None

        result_queue: asyncio.Queue = asyncio.Queue()

        pubsub_task = asyncio.create_task(self._pubsub_listener(result_queue))
        poll_task = asyncio.create_task(self._poll_listener(result_queue))

        try:
            result = await asyncio.wait_for(result_queue.get(), timeout=timeout)
            source, payload = result
            logger.debug(f"收到 webhook（来源: {source}）: callback_id={self.callback_id}")
            return payload

        except asyncio.TimeoutError:
            logger.debug(f"等待 webhook 超时: callback_id={self.callback_id}")
            return None

        finally:
            pubsub_task.cancel()
            poll_task.cancel()

            for task in [pubsub_task, poll_task]:
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def wait_next(self, timeout: float = 60.0) -> Optional[Dict[str, Any]]:
        try:
            result = await self.redis_client.lpop(self._result_key)
            if result:
                data = json.loads(result)
                logger.debug(f"获取已存在的 webhook: callback_id={self.callback_id}")
                return data.get("payload")
        except Exception:
            pass

        return await self._get_next_message(timeout)

    async def wait_until(
        self,
        condition: Callable[[Dict[str, Any]], bool],
        timeout: float = 300.0,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Optional[Dict[str, Any]]:
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            remaining = timeout - elapsed

            if remaining <= 0:
                logger.warning(f"wait_until 超时: callback_id={self.callback_id}")
                return None

            payload = await self.wait_next(timeout=min(remaining, 60.0))

            if payload is None:
                continue

            if on_progress:
                try:
                    on_progress(payload)
                except Exception as e:
                    logger.warning(f"进度回调异常: {e}")

            try:
                if condition(payload):
                    logger.info(f"wait_until 条件满足: callback_id={self.callback_id}")
                    return payload
            except Exception as e:
                logger.warning(f"条件检查异常: {e}")

    async def iter_callbacks(
        self,
        timeout: float = 300.0,
        idle_timeout: float = 60.0
    ) -> AsyncIterator[Dict[str, Any]]:
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            remaining = timeout - elapsed

            if remaining <= 0:
                logger.debug(f"iter_callbacks 总超时: callback_id={self.callback_id}")
                return

            wait_time = min(remaining, idle_timeout)
            payload = await self.wait_next(timeout=wait_time)

            if payload is None:
                logger.debug(f"iter_callbacks 空闲超时: callback_id={self.callback_id}")
                return

            yield payload

    async def get_all_pending(self) -> List[Dict[str, Any]]:
        results = []
        while True:
            try:
                result = await self.redis_client.lpop(self._result_key)
                if not result:
                    break
                data = json.loads(result)
                results.append(data.get("payload"))
            except Exception as e:
                logger.warning(f"获取待处理回调失败: {e}")
                break
        return results

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._closed = True

        if self._pubsub:
            try:
                await self._pubsub.unsubscribe(self._channel_name)
                await self._pubsub.close()
            except Exception:
                pass

        try:
            await self.redis_client.delete(self._result_key)
        except Exception:
            pass

        return False


async def wait_for_webhook(
    redis_client,
    namespace: str,
    callback_id: str,
    timeout: float = 300.0,
    fallback_poll_interval: float = 5.0
) -> Optional[Dict[str, Any]]:
    awaiter = WebhookAwaiter(
        redis_client=redis_client,
        namespace=namespace,
        base_url="",  
        callback_id=callback_id
    )

    async with awaiter:
        return await awaiter.wait_next(timeout=timeout)
