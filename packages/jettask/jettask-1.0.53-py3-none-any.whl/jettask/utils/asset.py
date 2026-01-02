"""
资产获取工具类

提供给任务使用的资产获取和负载均衡功能
通过 HTTP API 获取资产列表，无需直接连接数据库
"""
import asyncio
import random
import logging
import time
import uuid
from typing import Optional, Dict, Any, List, Callable, Awaitable
from datetime import datetime, timezone
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import httpx

logger = logging.getLogger(__name__)

ASSET_TASK_PREFIX = "jettask:asset:tasks:"


@dataclass
class NodeStatus:
    """节点状态"""
    asset_id: int
    name: str
    url: str
    config: Dict[str, Any]
    weight: int
    queue_remaining: int = 0
    is_available: bool = True
    last_check: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class AcquiredNode:
    """已获取的节点（包含释放信息）"""
    asset_id: int
    name: str
    url: str
    config: Dict[str, Any]
    weight: int
    task_id: str  
    queue_remaining: int = 0

    def to_node_status(self) -> NodeStatus:
        return NodeStatus(
            asset_id=self.asset_id,
            name=self.name,
            url=self.url,
            config=self.config,
            weight=self.weight,
            queue_remaining=self.queue_remaining,
            is_available=True
        )


@dataclass
class AssetInfo:
    """资产信息"""
    id: int
    name: str
    asset_type: str
    asset_group: str
    config: Dict[str, Any]
    status: str
    weight: int


@dataclass
class AssetCache:
    """资产缓存"""
    assets: List[AssetInfo] = field(default_factory=list)
    last_refresh: Optional[datetime] = None


class ComfyUINodeManager:
    """
    ComfyUI 节点任务管理器

    使用 Redis 有序集合维护每个节点的任务计数，实现实时的负载均衡。

    Redis 数据结构：
    - Key: jettask:asset:tasks:{namespace}:{asset_group}:{asset_id}
    - Type: Sorted Set (ZSET)
    - Member: task_id (UUID)
    - Score: timestamp (任务开始时间)

    Example:
        ```python
        manager = ComfyUINodeManager(redis_client, "default", "comfyui")

        # 获取节点（自动注册任务）
        async with manager.acquire_node(client, max_queue=2, timeout=60) as node:
            # 使用节点
            result = await call_comfyui(node.url, prompt)
            return result
        # 离开 context 时自动释放
        ```
    """

    def __init__(
        self,
        redis_client,
        namespace: str,
        asset_group: str = "comfyui",
        task_expire: int = 3600,  
        cleanup_interval: int = 300  
    ):
        self.redis_client = redis_client
        self.namespace = namespace
        self.asset_group = asset_group
        self.task_expire = task_expire
        self.cleanup_interval = cleanup_interval
        self._last_cleanup: float = 0

    def _get_task_key(self, asset_id: int) -> str:
        return f"{ASSET_TASK_PREFIX}{self.namespace}:{self.asset_group}:{asset_id}"

    async def get_task_count(self, asset_id: int) -> int:
        key = self._get_task_key(asset_id)
        try:
            count = await self.redis_client.zcard(key)
            return count or 0
        except Exception as e:
            logger.warning(f"获取节点任务数量失败: asset_id={asset_id}, error={e}")
            return 0

    async def get_all_task_counts(self, asset_ids: List[int]) -> Dict[int, int]:
        result = {}
        try:
            pipe = self.redis_client.pipeline()
            for asset_id in asset_ids:
                key = self._get_task_key(asset_id)
                pipe.zcard(key)

            counts = await pipe.execute()
            for asset_id, count in zip(asset_ids, counts):
                result[asset_id] = count or 0
        except Exception as e:
            logger.warning(f"批量获取节点任务数量失败: {e}")
            for asset_id in asset_ids:
                result[asset_id] = await self.get_task_count(asset_id)

        return result

    async def register_task(self, asset_id: int, task_id: Optional[str] = None) -> str:
        if task_id is None:
            task_id = f"task_{uuid.uuid4().hex[:16]}"

        key = self._get_task_key(asset_id)
        score = time.time()

        try:
            await self.redis_client.zadd(key, {task_id: score})
            await self.redis_client.expire(key, self.task_expire + 60)
            logger.debug(f"注册任务: asset_id={asset_id}, task_id={task_id}")
        except Exception as e:
            logger.error(f"注册任务失败: asset_id={asset_id}, task_id={task_id}, error={e}")
            raise

        return task_id

    async def release_task(self, asset_id: int, task_id: str) -> bool:
        key = self._get_task_key(asset_id)

        try:
            removed = await self.redis_client.zrem(key, task_id)
            if removed:
                logger.debug(f"释放任务: asset_id={asset_id}, task_id={task_id}")
            else:
                logger.warning(f"任务不存在或已释放: asset_id={asset_id}, task_id={task_id}")
            return bool(removed)
        except Exception as e:
            logger.error(f"释放任务失败: asset_id={asset_id}, task_id={task_id}, error={e}")
            return False

    async def cleanup_expired_tasks(self, asset_id: Optional[int] = None, force: bool = False) -> int:
        current_time = time.time()

        if not force and (current_time - self._last_cleanup) < self.cleanup_interval:
            return 0

        self._last_cleanup = current_time
        expire_threshold = current_time - self.task_expire
        total_removed = 0

        try:
            if asset_id is not None:
                key = self._get_task_key(asset_id)
                removed = await self.redis_client.zremrangebyscore(key, "-inf", expire_threshold)
                total_removed = removed or 0
            else:
                pattern = f"{ASSET_TASK_PREFIX}{self.namespace}:{self.asset_group}:*"
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                    for key in keys:
                        removed = await self.redis_client.zremrangebyscore(key, "-inf", expire_threshold)
                        total_removed += removed or 0
                    if cursor == 0:
                        break

            if total_removed > 0:
                logger.info(f"清理过期任务: namespace={self.namespace}, group={self.asset_group}, removed={total_removed}")

        except Exception as e:
            logger.error(f"清理过期任务失败: {e}")

        return total_removed

    async def acquire_node(
        self,
        asset_client: "AssetClient",
        max_queue: int = 0,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
        strategy: str = "least_busy"
    ) -> Optional[AcquiredNode]:
        start_time = time.time()

        await self.cleanup_expired_tasks()

        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                logger.warning(f"获取节点超时: asset_group={self.asset_group}")
                return None

            assets = await asset_client.get_assets(
                asset_group=self.asset_group,
                asset_type="compute_node",
                status="active",
                use_cache=False
            )

            if not assets:
                logger.warning(f"没有可用的计算节点: asset_group={self.asset_group}")
                await asyncio.sleep(poll_interval)
                continue

            asset_ids = [a.id for a in assets]
            task_counts = await self.get_all_task_counts(asset_ids)

            available_nodes: List[tuple] = []  

            for asset in assets:
                url = asset.config.get("url", "")
                if not url:
                    continue

                task_count = task_counts.get(asset.id, 0)

                if max_queue == 0:
                    is_available = task_count == 0
                else:
                    is_available = task_count < max_queue

                if is_available:
                    available_nodes.append((asset, task_count))

            if not available_nodes:
                logger.debug(
                    f"所有节点都忙，等待 {poll_interval} 秒... "
                    f"(节点任务数: {[(a.name, task_counts.get(a.id, 0)) for a in assets]})"
                )
                await asyncio.sleep(poll_interval)
                continue

            selected_asset, selected_count = self._select_node(available_nodes, strategy)

            task_id = await self.register_task(selected_asset.id)

            logger.info(
                f"选中节点: {selected_asset.name} (tasks={selected_count}, "
                f"可用={len(available_nodes)}/{len(assets)})"
            )

            return AcquiredNode(
                asset_id=selected_asset.id,
                name=selected_asset.name,
                url=selected_asset.config.get("url", ""),
                config=selected_asset.config,
                weight=selected_asset.weight,
                task_id=task_id,
                queue_remaining=selected_count
            )

    def _select_node(
        self,
        nodes: List[tuple],  
        strategy: str
    ) -> tuple:
        if strategy == "random":
            return random.choice(nodes)

        elif strategy == "weighted":
            total_weight = sum(n[0].weight for n in nodes)
            if total_weight == 0:
                return random.choice(nodes)

            r = random.uniform(0, total_weight)
            cumulative = 0
            for node in nodes:
                cumulative += node[0].weight
                if r <= cumulative:
                    return node
            return nodes[-1]

        else:  
            nodes.sort(key=lambda n: (n[1], -n[0].weight))
            return nodes[0]

    @asynccontextmanager
    async def acquire(
        self,
        asset_client: "AssetClient",
        max_queue: int = 0,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
        strategy: str = "least_busy"
    ):
        node = await self.acquire_node(
            asset_client=asset_client,
            max_queue=max_queue,
            timeout=timeout,
            poll_interval=poll_interval,
            strategy=strategy
        )

        if node is None:
            raise TimeoutError(f"获取节点超时: asset_group={self.asset_group}")

        try:
            yield node
        finally:
            await self.release_task(node.asset_id, node.task_id)


class AssetClient:
    """
    资产客户端

    通过 HTTP API 获取和管理资产，提供负载均衡功能

    Example:
        ```python
        from jettask.utils.asset import AssetClient

        @app.task(queue="image_gen")
        async def generate_image(prompt: str):
            # 创建资产客户端（使用 API Key 认证）
            client = AssetClient(
                api_base_url="http://localhost:8080",
                namespace="default",
                api_key="your-api-key"
            )

            # 获取最空闲的 ComfyUI 节点
            node = await client.acquire_compute_node(
                asset_group="comfyui",
                max_queue=0,      # 只选择空闲节点
                timeout=600       # 等待最多 10 分钟
            )

            if node is None:
                raise Exception("没有可用的 ComfyUI 节点")

            # 使用节点
            result = await call_comfyui(node.url, prompt)
            return result
        ```
    """

    def __init__(
        self,
        api_base_url: str,
        namespace: str,
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        cache_ttl: int = 60,
        http_timeout: float = 10.0
    ):
        self.api_base_url = api_base_url.rstrip('/')
        self.namespace = namespace
        self.api_key = api_key
        self.jwt_token = jwt_token
        self.cache_ttl = cache_ttl
        self.http_timeout = http_timeout
        self._cache: Dict[str, AssetCache] = {}

    def _get_auth_headers(self) -> Dict[str, str]:
        headers = {}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        elif self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        return headers

    def _get_api_url(self, path: str) -> str:
        return f"{self.api_base_url}/{self.namespace}{path}"

    async def get_assets(
        self,
        asset_group: str,
        asset_type: Optional[str] = None,
        status: str = "active",
        use_cache: bool = True
    ) -> List[AssetInfo]:
        cache_key = f"{asset_group}:{asset_type}:{status}"

        if use_cache and cache_key in self._cache:
            cache = self._cache[cache_key]
            if cache.last_refresh:
                age = (datetime.now(timezone.utc) - cache.last_refresh).total_seconds()
                if age < self.cache_ttl:
                    return cache.assets

        url = self._get_api_url(f"/assets/group/{asset_group}")
        params = {"status": status}
        headers = self._get_auth_headers()

        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as http_client:
                resp = await http_client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                assets = []
                for item in data.get("data", []):
                    if asset_type and item.get("asset_type") != asset_type:
                        continue

                    assets.append(AssetInfo(
                        id=item["id"],
                        name=item["name"],
                        asset_type=item["asset_type"],
                        asset_group=item["asset_group"],
                        config=item.get("config", {}),
                        status=item["status"],
                        weight=item.get("weight", 1)
                    ))

                self._cache[cache_key] = AssetCache(
                    assets=assets,
                    last_refresh=datetime.now(timezone.utc)
                )

                return assets

        except Exception as e:
            logger.error(f"获取资产列表失败: {e}")
            if cache_key in self._cache:
                return self._cache[cache_key].assets
            return []

    async def acquire_compute_node(
        self,
        asset_group: str,
        check_func: Optional[Callable[[str, Dict[str, Any]], Awaitable[int]]] = None,
        max_queue: int = 0,
        timeout: float = 300.0,
        poll_interval: float = 5.0,
        strategy: str = "least_busy"
    ) -> Optional[NodeStatus]:
        if check_func is None:
            check_func = self._default_comfyui_check

        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                logger.warning(f"获取计算节点超时: asset_group={asset_group}")
                return None

            assets = await self.get_assets(
                asset_group=asset_group,
                asset_type="compute_node",
                status="active",
                use_cache=False  
            )

            if not assets:
                logger.warning(f"没有可用的计算节点: asset_group={asset_group}")
                await asyncio.sleep(poll_interval)
                continue

            node_statuses: List[NodeStatus] = []

            for asset in assets:
                url = asset.config.get("url", "")
                if not url:
                    continue

                status = NodeStatus(
                    asset_id=asset.id,
                    name=asset.name,
                    url=url,
                    config=asset.config,
                    weight=asset.weight,
                    last_check=datetime.now(timezone.utc)
                )

                try:
                    queue_remaining = await check_func(url, asset.config)
                    status.queue_remaining = queue_remaining
                    status.is_available = queue_remaining <= max_queue
                except Exception as e:
                    status.is_available = False
                    status.error = str(e)
                    logger.warning(f"检查节点 {asset.name} 失败: {e}")

                node_statuses.append(status)

            available_nodes = [n for n in node_statuses if n.is_available]

            if not available_nodes:
                logger.debug(
                    f"所有节点都忙，等待 {poll_interval} 秒后重试... "
                    f"(节点状态: {[(n.name, n.queue_remaining) for n in node_statuses]})"
                )
                await asyncio.sleep(poll_interval)
                continue

            selected = self._select_node(available_nodes, strategy)

            logger.info(
                f"选中计算节点: {selected.name} (queue={selected.queue_remaining}, "
                f"可用节点数={len(available_nodes)}/{len(node_statuses)})"
            )

            return selected

    def _select_node(self, nodes: List[NodeStatus], strategy: str) -> NodeStatus:
        if strategy == "random":
            return random.choice(nodes)

        elif strategy == "weighted":
            total_weight = sum(n.weight for n in nodes)
            if total_weight == 0:
                return random.choice(nodes)

            r = random.uniform(0, total_weight)
            cumulative = 0
            for node in nodes:
                cumulative += node.weight
                if r <= cumulative:
                    return node
            return nodes[-1]

        else:  
            nodes.sort(key=lambda n: (n.queue_remaining, -n.weight))
            return nodes[0]

    async def get_api_key(
        self,
        asset_group: str,
        strategy: str = "random"
    ) -> Optional[Dict[str, Any]]:
        assets = await self.get_assets(
            asset_group=asset_group,
            asset_type="api_key",
            status="active"
        )

        if not assets:
            return None

        if strategy == "weighted":
            total_weight = sum(a.weight for a in assets)
            if total_weight == 0:
                selected = random.choice(assets)
            else:
                r = random.uniform(0, total_weight)
                cumulative = 0
                selected = assets[-1]
                for asset in assets:
                    cumulative += asset.weight
                    if r <= cumulative:
                        selected = asset
                        break
        else:  
            selected = random.choice(assets)

        return {
            "asset_id": selected.id,
            "name": selected.name,
            "config": selected.config
        }

    async def get_config(
        self,
        asset_group: str,
        name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        assets = await self.get_assets(
            asset_group=asset_group,
            asset_type="config",
            status="active"
        )

        if not assets:
            return None

        if name:
            for asset in assets:
                if asset.name == name:
                    return asset.config
            return None

        return assets[0].config

    @staticmethod
    async def _default_comfyui_check(url: str, config: Dict[str, Any]) -> int:
        timeout = config.get("timeout", 5.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{url}/api/queue/remaining")
            resp.raise_for_status()
            data = resp.json()
            return data.get("queue_remaining", 0)

    def clear_cache(self):
        self._cache.clear()


async def acquire_comfyui_node(
    redis_client,
    api_base_url: str,
    namespace: str,
    asset_group: str = "comfyui",
    max_queue: int = 0,
    timeout: float = 300.0,
    api_key: Optional[str] = None,
    jwt_token: Optional[str] = None
) -> Optional[AcquiredNode]:
    client = AssetClient(api_base_url, namespace, api_key=api_key, jwt_token=jwt_token)
    manager = ComfyUINodeManager(redis_client, namespace, asset_group)
    return await manager.acquire_node(
        asset_client=client,
        max_queue=max_queue,
        timeout=timeout
    )


async def release_comfyui_node(
    redis_client,
    namespace: str,
    asset_group: str,
    node: AcquiredNode
) -> bool:
    manager = ComfyUINodeManager(redis_client, namespace, asset_group)
    return await manager.release_task(node.asset_id, node.task_id)


@asynccontextmanager
async def acquire_comfyui_node_ctx(
    redis_client,
    api_base_url: str,
    namespace: str,
    asset_group: str = "comfyui",
    max_queue: int = 0,
    timeout: float = 300.0,
    api_key: Optional[str] = None,
    jwt_token: Optional[str] = None
):
    client = AssetClient(api_base_url, namespace, api_key=api_key, jwt_token=jwt_token)
    manager = ComfyUINodeManager(redis_client, namespace, asset_group)

    async with manager.acquire(
        asset_client=client,
        max_queue=max_queue,
        timeout=timeout
    ) as node:
        yield node


async def get_api_key(
    api_base_url: str,
    namespace: str,
    asset_group: str,
    api_key: Optional[str] = None,
    jwt_token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    client = AssetClient(api_base_url, namespace, api_key=api_key, jwt_token=jwt_token)
    return await client.get_api_key(asset_group)
