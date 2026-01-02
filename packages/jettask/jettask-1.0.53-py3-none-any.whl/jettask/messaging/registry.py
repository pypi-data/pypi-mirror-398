"""
队列注册管理模块
负责队列、延迟队列、消费者组的注册和查询功能
"""

import logging
from typing import Set, List

logger = logging.getLogger(__name__)


class QueueRegistry:
    """
    队列注册管理器
    维护队列的注册信息，提供队列发现功能
    """

    def __init__(self, redis_client, async_redis_client, redis_prefix: str = 'jettask'):
        self.redis = redis_client

        self.async_redis = async_redis_client

        self.redis_prefix = redis_prefix

        self.queues_registry_key = f"{redis_prefix}:REGISTRY:QUEUES"  
        self.consumer_groups_registry_key = f"{redis_prefix}:REGISTRY:CONSUMER_GROUPS"


    async def register_queue(self, queue_name: str):
        await self.async_redis.sadd(self.queues_registry_key, queue_name)
        logger.debug(f"Registered queue: {queue_name}")

    async def unregister_queue(self, queue_name: str):
        await self.async_redis.srem(self.queues_registry_key, queue_name)
        logger.debug(f"Unregistered queue: {queue_name}")

    async def get_all_queues(self) -> Set[str]:
        return await self.async_redis.smembers(self.queues_registry_key)

    async def get_queue_count(self) -> int:
        return await self.async_redis.scard(self.queues_registry_key)

    async def get_base_queues(self) -> Set[str]:
        all_queues = await self.get_all_queues()

        base_queues = set()
        for queue in all_queues:
            if isinstance(queue, bytes):
                queue = queue.decode('utf-8')

            parts = queue.split(':')
            if len(parts) >= 2 and parts[-1].isdigit():
                base_queue = ':'.join(parts[:-1])
                base_queues.add(base_queue)
            else:
                base_queues.add(queue)

        return base_queues

    async def discover_matching_queues(self, wildcard_pattern: str) -> Set[str]:
        from jettask.utils.queue_matcher import discover_matching_queues

        all_registered_queues = await self.get_all_queues()

        all_registered_queues = {
            q.decode('utf-8') if isinstance(q, bytes) else q
            for q in all_registered_queues
        }

        matched_queues = discover_matching_queues([wildcard_pattern], all_registered_queues)
        return matched_queues


    async def register_consumer_group(self, queue: str, group_name: str):
        key = f"{self.consumer_groups_registry_key}:{queue}"
        await self.async_redis.sadd(key, group_name)
        logger.debug(f"Registered consumer group: {group_name} for queue: {queue}")

    async def unregister_consumer_group(self, queue: str, group_name: str):
        key = f"{self.consumer_groups_registry_key}:{queue}"
        await self.async_redis.srem(key, group_name)
        logger.debug(f"Unregistered consumer group: {group_name} for queue: {queue}")

    async def get_consumer_groups_for_queue(self, queue: str) -> Set[str]:
        key = f"{self.consumer_groups_registry_key}:{queue}"
        return await self.async_redis.smembers(key)


    async def register_priority_queue(self, base_queue: str, priority: int):
        priority_queue = f"{base_queue}:{priority}"
        await self.async_redis.sadd(self.queues_registry_key, priority_queue)
        logger.debug(f"Registered priority queue: {priority_queue}")

    async def unregister_priority_queue(self, base_queue: str, priority: int):
        priority_queue = f"{base_queue}:{priority}"
        await self.async_redis.srem(self.queues_registry_key, priority_queue)
        logger.debug(f"Unregistered priority queue: {priority_queue}")

    async def get_priority_queues_for_base(self, base_queue: str) -> List[str]:
        all_queues = await self.async_redis.smembers(self.queues_registry_key)

        result = []
        for queue in all_queues:
            if isinstance(queue, bytes):
                queue = queue.decode('utf-8')

            if queue.startswith(f"{base_queue}:"):
                parts = queue.split(':')
                if len(parts) >= 2 and parts[-1].isdigit():
                    result.append(queue)

        result.sort(key=lambda x: int(x.split(':')[-1]))
        return result

    async def clear_priority_queues_for_base(self, base_queue: str):
        priority_queues = await self.get_priority_queues_for_base(base_queue)

        if priority_queues:
            await self.async_redis.srem(self.queues_registry_key, *priority_queues)
            logger.debug(f"Cleared {len(priority_queues)} priority queues for base queue: {base_queue}")


    async def get_task_names_by_queue(self, base_queue: str) -> Set[str]:
        read_offsets_key = f"{self.redis_prefix}:READ_OFFSETS"

        all_keys = await self.async_redis.hkeys(read_offsets_key)

        task_names = set()
        for key in all_keys:
            if isinstance(key, bytes):
                key = key.decode('utf-8')

            if not key.startswith(f"{base_queue}:"):
                continue

            suffix = key[len(base_queue) + 1:]  

            parts = suffix.split(':')

            if parts[0].isdigit() and len(parts) > 1:
                task_name = ':'.join(parts[1:])
            else:
                task_name = suffix

            if task_name:  
                task_names.add(task_name)

        return task_names
