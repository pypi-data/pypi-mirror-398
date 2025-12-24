"""
Redis 监控基础服务

提供 Redis 连接管理和基础功能
"""
import asyncio
import logging
from typing import Optional
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisMonitorService:
    """Redis 监控基础服务类"""

    def __init__(self, redis_url: str = "redis://localhost:6379", redis_prefix: str = "jettask"):
        self.redis_url = redis_url
        self.redis_prefix = redis_prefix
        self.redis: Optional[aioredis.Redis] = None
        self.worker_state_manager = None  

        self._queues_cache = None
        self._queues_cache_time = 0
        self._queues_cache_ttl = 60  

        self._workers_cache = None
        self._workers_cache_time = 0
        self._workers_cache_ttl = 5  

    async def connect(self):
        from jettask.db.connector import get_async_redis_pool

        pool = get_async_redis_pool(
            self.redis_url,
            decode_responses=True,
            max_connections=100,
            socket_connect_timeout=5,
            socket_timeout=10,
            socket_keepalive=True,
            health_check_interval=30
        )
        self.redis = aioredis.Redis(connection_pool=pool)

        from jettask.worker.lifecycle import WorkerManager
        self.worker_state_manager = WorkerManager(
            redis_client=self.redis,
            redis_prefix=self.redis_prefix
        )
        logger.info(f"Redis 监控服务已连接: {self.redis_url}")

    async def close(self):
        if self.redis:
            await self.redis.close()
            logger.info("Redis 监控服务已关闭")

    def get_prefixed_queue_name(self, queue_name: str) -> str:
        return f"{self.redis_prefix}:QUEUE:{queue_name}"

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
