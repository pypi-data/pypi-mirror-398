"""
限流器管理器

统一管理所有任务的限流器实例
职责：
1. 限流器生命周期管理
2. 配置动态更新
3. 统一的限流接口
"""

import asyncio
import logging
import time
from redis.asyncio import Redis
from typing import Dict, Optional, List, Any

from .task_limiter import TaskRateLimiter
from .config import RateLimitConfig, parse_rate_limit_config

logger = logging.getLogger('app')


class RateLimiterManager:
    """限流器管理器

    管理多个任务的限流器。
    """

    def __init__(
        self,
        redis_client: Redis,
        worker_id: str,
        redis_prefix: str = "jettask",
        worker_state_manager = None
    ):
        self.redis = redis_client
        self.worker_id = worker_id
        self.redis_prefix = redis_prefix
        self.worker_state_manager = worker_state_manager

        self.limiters: Dict[str, TaskRateLimiter] = {}

        logger.debug(f"RateLimiterManager initialized for worker {worker_id}")

    @staticmethod
    def register_rate_limit_config(redis_client, task_name: str, config: RateLimitConfig, redis_prefix: str = "jettask"):
        try:
            rate_limit_key = f"{redis_prefix}:RATE_LIMIT:CONFIG:{task_name}"
            config_dict = config.to_dict()
            redis_client.hset(rate_limit_key, mapping=config_dict)

            index_key = f"{redis_prefix}:RATE_LIMIT:INDEX"
            redis_client.sadd(index_key, task_name)

            logger.debug(f"Registered rate limit config for task '{task_name}': {config}")
        except Exception as e:
            logger.error(f"Failed to register rate limit config for task '{task_name}': {e}")

    @staticmethod
    def unregister_rate_limit_config(redis_client, task_name: str, redis_prefix: str = "jettask"):
        try:
            rate_limit_key = f"{redis_prefix}:RATE_LIMIT:CONFIG:{task_name}"
            deleted = redis_client.delete(rate_limit_key)

            if deleted:
                index_key = f"{redis_prefix}:RATE_LIMIT:INDEX"
                redis_client.srem(index_key, task_name)
                logger.debug(f"Removed rate limit config for task '{task_name}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove rate limit config for task '{task_name}': {e}")
            return False

    async def add_limiter(self, task_name: str, config: RateLimitConfig):
        if task_name in self.limiters:
            logger.warning(f"Limiter for {task_name} already exists")
            return

        limiter = TaskRateLimiter(
            redis_client=self.redis,
            task_name=task_name,
            worker_id=self.worker_id,
            config=config,
            redis_prefix=self.redis_prefix,
            worker_state_manager=self.worker_state_manager
        )

        await limiter.start()
        self.limiters[task_name] = limiter

        logger.debug(f"Added rate limiter for {task_name}: {config}")

    async def remove_limiter(self, task_name: str, remove_from_redis: bool = False):
        if task_name not in self.limiters:
            return

        limiter = self.limiters.pop(task_name)
        await limiter.stop()

        if remove_from_redis:
            try:
                rate_limit_key = f"{self.redis_prefix}:RATE_LIMIT:CONFIG:{task_name}"
                await self.redis.delete(rate_limit_key)

                index_key = f"{self.redis_prefix}:RATE_LIMIT:INDEX"
                await self.redis.srem(index_key, task_name)

                logger.debug(f"Removed rate limit config and index for {task_name} from Redis")
            except Exception as e:
                logger.error(f"Failed to remove rate limit config from Redis: {e}")

        logger.debug(f"Removed rate limiter for {task_name}")

    async def load_config_from_redis(self, task_names: list = None):
        try:
            config_count = 0
            loaded_limiters = []

            if not task_names:
                index_key = f"{self.redis_prefix}:RATE_LIMIT:INDEX"
                task_names_bytes = await self.redis.smembers(index_key)
                task_names = [
                    name.decode('utf-8') if isinstance(name, bytes) else name
                    for name in task_names_bytes
                ]

                if not task_names:
                    logger.debug(f"No rate limit configs found in index {index_key}")
                    return

            for task_name in task_names:
                key = f"{self.redis_prefix}:RATE_LIMIT:CONFIG:{task_name}"

                exists = await self.redis.exists(key)
                if not exists:
                    continue

                key_type = await self.redis.type(key)
                if key_type != "hash":
                    logger.debug(f"Skipping non-hash key: {key} (type: {key_type})")
                    continue

                config_dict = await self.redis.hgetall(key)
                if not config_dict:
                    continue

                config_dict = {
                    k.decode() if isinstance(k, bytes) else k:
                    v.decode() if isinstance(v, bytes) else v
                    for k, v in config_dict.items()
                }

                config = parse_rate_limit_config(config_dict)
                if config and task_name not in self.limiters:
                    try:
                        await self.add_limiter(task_name, config)
                        config_count += 1
                        loaded_limiters.append(task_name)
                    except Exception as e:
                        logger.error(f"Failed to add limiter for {task_name}: {e}")

            logger.debug(f"Loaded {config_count} rate limit configs from Redis")
            logger.debug(f"Loaded rate limit config from Redis, limiters: {loaded_limiters}")
        except Exception as e:
            logger.error(f"Failed to load config from Redis: {e}")

    async def acquire(self, task_name: str, timeout: float = 10.0) -> Optional[str]:
        limiter = self.limiters.get(task_name)
        if not limiter:
            return True

        return await limiter.acquire(timeout)

    async def release(self, task_name: str, task_id: Optional[str] = None):
        limiter = self.limiters.get(task_name)
        if limiter:
            await limiter.release(task_id)

    async def stop_all(self):
        for task_name, limiter in list(self.limiters.items()):
            await limiter.stop()
        self.limiters.clear()
        logger.debug("Stopped all rate limiters")

    def get_all_stats(self) -> Dict[str, dict]:
        stats = {}
        for task_name, limiter in self.limiters.items():
            if hasattr(limiter, 'get_stats'):
                stats[task_name] = limiter.get_stats()
        return stats


__all__ = ['RateLimiterManager']
