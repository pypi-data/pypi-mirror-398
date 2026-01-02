"""
消息读取器 - 统一的消息读取和确认接口
从 EventPool 中提取的消息读取逻辑
"""

import logging
from typing import List, Dict, Optional, Tuple
from redis.asyncio import Redis as AsyncRedis

from ..utils.serializer import loads_str

logger = logging.getLogger('app')


class MessageReader:
    """
    统一的消息读取接口

    职责：
    1. 从 Redis Stream 读取消息（支持consumer group）
    2. 确认消息（ACK）
    3. 支持优先级队列
    4. 支持历史消息和新消息的读取
    5. 追踪读取进度（offset）
    """

    def __init__(
        self,
        async_redis_client: AsyncRedis,
        async_binary_redis_client: AsyncRedis,
        redis_prefix: str = 'jettask'
    ):
        self.redis = async_redis_client
        self.binary_redis = async_binary_redis_client
        self.redis_prefix = redis_prefix

        logger.debug(f"MessageReader initialized with prefix: {redis_prefix}")

    def _get_prefixed_queue_name(self, queue: str) -> str:
        return f"{self.redis_prefix}:QUEUE:{queue}"

    async def create_consumer_group(
        self,
        queue: str,
        group_name: str,
        start_id: str = "0"
    ) -> bool:
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            await self.redis.xgroup_create(
                name=prefixed_queue,
                groupname=group_name,
                id=start_id,
                mkstream=True  
            )
            logger.info(f"Created consumer group {group_name} for queue {queue}")
            return True
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group {group_name} already exists for queue {queue}")
                return False
            else:
                logger.error(f"Error creating consumer group {group_name} for queue {queue}: {e}")
                raise

    async def read_messages(
        self,
        queue: str,
        group_name: str,
        consumer_name: str,
        count: int = 1,
        block: int = 1000,
        start_id: str = ">"
    ) -> List[Tuple[str, Dict]]:
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            results = await self.binary_redis.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={prefixed_queue: start_id},
                count=count,
                block=block
            )

            if not results:
                return []

            messages = []
            for stream_name, stream_messages in results:
                for message_id, message_fields in stream_messages:
                    if isinstance(message_id, bytes):
                        message_id = message_id.decode('utf-8')

                    decoded_fields = {}
                    for key, value in message_fields.items():
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                        if key_str == 'data':
                            decoded_fields[key_str] = value  
                        else:
                            value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                            decoded_fields[key_str] = value_str

                    if 'data' in decoded_fields:
                        try:
                            data = loads_str(decoded_fields['data'])
                        except Exception as e:
                            logger.warning(f"Failed to parse message data: {e}")
                            data = decoded_fields['data']
                    else:
                        data = decoded_fields

                    if 'offset' in decoded_fields:
                        if isinstance(data, dict):
                            data['_offset'] = int(decoded_fields['offset'])

                    messages.append((message_id, data))

            logger.debug(f"Read {len(messages)} messages from queue {queue}")
            return messages

        except Exception as e:
            if "NOGROUP" in str(e):
                logger.warning(f"Consumer group {group_name} does not exist for queue {queue}")
                await self.create_consumer_group(queue, group_name, start_id="0")
                return await self.read_messages(
                    queue, group_name, consumer_name, count, block, start_id
                )
            else:
                logger.error(f"Error reading messages from queue {queue}: {e}")
                raise

    async def read_from_multiple_queues(
        self,
        queues: List[str],
        group_name: str,
        consumer_name: str,
        count: int = 1,
        block: int = 1000,
        priority_order: bool = True
    ) -> List[Tuple[str, str, Dict]]:
        all_messages = []
        messages_needed = count

        for queue in queues:
            if messages_needed <= 0:
                break

            messages = await self.read_messages(
                queue, group_name, consumer_name,
                count=messages_needed, block=block
            )

            for message_id, message_data in messages:
                all_messages.append((queue, message_id, message_data))

            messages_needed -= len(messages)

            if priority_order and messages:
                break

        return all_messages

    async def acknowledge_message(
        self,
        queue: str,
        group_name: str,
        message_id: str
    ) -> bool:
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            result = await self.binary_redis.xack(
                prefixed_queue,
                group_name,
                message_id
            )
            logger.debug(f"ACK message {message_id} in queue {queue}")
            return result > 0
        except Exception as e:
            logger.error(f"Error acknowledging message {message_id} in queue {queue}: {e}")
            return False

    async def acknowledge_messages(
        self,
        queue: str,
        group_name: str,
        message_ids: List[str]
    ) -> int:
        if not message_ids:
            return 0

        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            result = await self.binary_redis.xack(
                prefixed_queue,
                group_name,
                *message_ids
            )
            logger.debug(f"ACK {result} messages in queue {queue}")
            return result
        except Exception as e:
            logger.error(f"Error acknowledging {len(message_ids)} messages in queue {queue}: {e}")
            return 0

    async def get_pending_messages(
        self,
        queue: str,
        group_name: str,
        consumer_name: Optional[str] = None,
        count: int = 10
    ) -> List[Dict]:
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            if consumer_name:
                result = await self.binary_redis.xpending_range(
                    prefixed_queue,
                    group_name,
                    min="-",
                    max="+",
                    count=count,
                    consumername=consumer_name
                )
            else:
                result = await self.binary_redis.xpending_range(
                    prefixed_queue,
                    group_name,
                    min="-",
                    max="+",
                    count=count
                )

            pending = []
            for item in result:
                pending.append({
                    'message_id': item['message_id'].decode('utf-8') if isinstance(item['message_id'], bytes) else item['message_id'],
                    'consumer': item['consumer'].decode('utf-8') if isinstance(item['consumer'], bytes) else item['consumer'],
                    'time_since_delivered': item['time_since_delivered'],
                    'times_delivered': item['times_delivered']
                })

            return pending

        except Exception as e:
            logger.error(f"Error getting pending messages from queue {queue}: {e}")
            return []

    async def claim_messages(
        self,
        queue: str,
        group_name: str,
        consumer_name: str,
        message_ids: List[str],
        min_idle_time: int = 60000
    ) -> List[Tuple[str, Dict]]:
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            results = await self.binary_redis.xclaim(
                prefixed_queue,
                group_name,
                consumer_name,
                min_idle_time,
                message_ids
            )

            messages = []
            for message_id, message_fields in results:
                if isinstance(message_id, bytes):
                    message_id = message_id.decode('utf-8')

                decoded_fields = {}
                for key, value in message_fields.items():
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    if key_str == 'data':
                        decoded_fields[key_str] = value
                    else:
                        value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                        decoded_fields[key_str] = value_str

                if 'data' in decoded_fields:
                    try:
                        data = loads_str(decoded_fields['data'])
                    except Exception:
                        data = decoded_fields['data']
                else:
                    data = decoded_fields

                if 'offset' in decoded_fields and isinstance(data, dict):
                    data['_offset'] = int(decoded_fields['offset'])

                messages.append((message_id, data))

            logger.info(f"Claimed {len(messages)} messages from queue {queue}")
            return messages

        except Exception as e:
            logger.error(f"Error claiming messages from queue {queue}: {e}")
            return []

    async def update_read_offset(
        self,
        queue: str,
        group_name: str,
        offset: int
    ):
        read_offsets_key = f"{self.redis_prefix}:READ_OFFSETS"

        task_name = group_name.split(':')[-1]

        field = f"{queue}:{task_name}"

        try:
            lua_script = """
            local hash_key = KEYS[1]
            local field = KEYS[2]
            local new_value = tonumber(ARGV[1])

            local current = redis.call('HGET', hash_key, field)
            if current == false or tonumber(current) < new_value then
                redis.call('HSET', hash_key, field, new_value)
                return 1
            else
                return 0
            end
            """

            await self.redis.eval(
                lua_script,
                2,
                read_offsets_key,
                field,
                str(offset)
            )

            logger.debug(f"Updated read offset for {field} to {offset}")

        except Exception as e:
            logger.error(f"Error updating read offset: {e}")

    async def get_queue_length(self, queue: str) -> int:
        prefixed_queue = self._get_prefixed_queue_name(queue)
        return await self.binary_redis.xlen(prefixed_queue)

    async def get_consumer_group_info(self, queue: str) -> List[Dict]:
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            groups = await self.binary_redis.xinfo_groups(prefixed_queue)
            return groups
        except Exception as e:
            logger.error(f"Error getting consumer group info for queue {queue}: {e}")
            return []
