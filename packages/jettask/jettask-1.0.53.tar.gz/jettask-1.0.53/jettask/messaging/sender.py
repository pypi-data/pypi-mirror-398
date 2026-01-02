"""
消息发送器 - 统一的消息发送接口
从 EventPool 中提取的消息发送逻辑
"""

import time
import logging
from typing import List, Dict, Optional, Tuple
from redis.asyncio import Redis as AsyncRedis

from ..utils.serializer import dumps_str

logger = logging.getLogger('app')


class MessageSender:
    """
    统一的消息发送接口

    职责：
    1. 发送普通消息到 Redis Stream
    2. 发送延迟消息到 Redis Sorted Set + Stream
    3. 发送优先级消息到优先级队列
    4. 批量发送优化
    """

    def __init__(
        self,
        async_redis_client: AsyncRedis,
        redis_prefix: str = 'jettask'
    ):
        self.redis = async_redis_client
        self.redis_prefix = redis_prefix

        self._batch_send_script = None
        self._delayed_task_script = None

        logger.debug(f"MessageSender initialized with prefix: {redis_prefix}")

    def _get_prefixed_queue_name(self, queue: str) -> str:
        return f"{self.redis_prefix}:QUEUE:{queue}"


    async def send_messages(
        self,
        queue: str,
        messages: List[Dict],
        priority: Optional[int] = None,
        delay: Optional[float] = None
    ) -> List[str]:
        if not messages:
            return []

        actual_queue = queue
        if priority is not None:
            actual_queue = f"{queue}:{priority}"

        if delay and delay > 0:
            current_time = time.time()
            marked_messages = []
            for msg in messages:
                msg_copy = msg.copy()
                msg_copy['execute_at'] = current_time + delay
                msg_copy['is_delayed'] = 1
                marked_messages.append(msg_copy)
            return await self._send_normal_messages(actual_queue, marked_messages)
        else:
            return await self._send_normal_messages(actual_queue, messages)

    async def _send_normal_messages(self, queue: str, messages: List[Dict]) -> List[str]:
        prefixed_queue = self._get_prefixed_queue_name(queue)

        lua_script = """
        local stream_key = KEYS[1]
        local prefix = ARGV[1]
        local results = {}

        -- 使用Hash存储所有队列的offset
        local offsets_hash = prefix .. ':QUEUE_OFFSETS'

        -- 从stream_key中提取队列名（去掉prefix:QUEUE:前缀）
        local queue_name = string.gsub(stream_key, '^' .. prefix .. ':QUEUE:', '')

        -- 将队列添加到全局队列注册表
        local queues_registry_key = prefix .. ':REGISTRY:QUEUES'
        redis.call('SADD', queues_registry_key, queue_name)

        -- 从ARGV[2]开始，每个参数是一个消息的data
        for i = 2, #ARGV do
            local data = ARGV[i]

            -- 使用HINCRBY原子递增offset（如果不存在会自动创建并设为1）
            local current_offset = redis.call('HINCRBY', offsets_hash, queue_name, 1)

            -- 添加消息到Stream（包含offset字段）
            local stream_id = redis.call('XADD', stream_key, '*',
                'data', data,
                'offset', current_offset)

            table.insert(results, stream_id)
        end

        return results
        """

        lua_args = [self.redis_prefix.encode() if isinstance(self.redis_prefix, str) else self.redis_prefix]

        for message in messages:
            if 'data' in message:
                data = message['data'] if isinstance(message['data'], bytes) else dumps_str(message['data'])
            else:
                data = dumps_str(message)
            lua_args.append(data)

        if not self._batch_send_script:
            self._batch_send_script = self.redis.register_script(lua_script)

        results = await self._batch_send_script(
            keys=[prefixed_queue],
            args=lua_args
        )

        decoded_results = [r.decode('utf-8') if isinstance(r, bytes) else r for r in results]

        logger.debug(f"Sent {len(decoded_results)} messages to queue {queue}")
        return decoded_results

    async def send_single_message(
        self,
        queue: str,
        message: Dict,
        priority: Optional[int] = None,
        delay: Optional[float] = None
    ) -> str:
        results = await self.send_messages(queue, [message], priority=priority, delay=delay)
        return results[0] if results else None

    async def get_queue_size(self, queue: str) -> int:
        prefixed_queue = self._get_prefixed_queue_name(queue)
        return await self.redis.xlen(prefixed_queue)

