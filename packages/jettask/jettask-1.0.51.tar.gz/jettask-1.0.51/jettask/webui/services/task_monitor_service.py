"""
任务监控服务

提供任务相关的监控功能
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import redis.asyncio as aioredis

from .redis_monitor_service import RedisMonitorService

logger = logging.getLogger(__name__)


class TaskMonitorService:
    """任务监控服务类"""

    def __init__(self, redis_service: RedisMonitorService):
        self.redis_service = redis_service

    @property
    def redis(self) -> aioredis.Redis:
        return self.redis_service.redis

    @property
    def redis_prefix(self) -> str:
        return self.redis_service.redis_prefix

    async def get_task_info(self, stream_id: str, queue_name: str) -> Optional[Dict[str, Any]]:
        try:
            prefixed_queue = self.redis_service.get_prefixed_queue_name(queue_name)

            messages = await self.redis.xrange(prefixed_queue, min=stream_id, max=stream_id, count=1)

            if not messages:
                logger.warning(f"Task not found in stream: {stream_id} in queue {queue_name}")
                return None

            msg_id, msg_data = messages[0]

            pending_entries = await self.redis.xpending_range(
                prefixed_queue,
                f"{self.redis_prefix}:GROUP:{queue_name}",
                min=msg_id,
                max=msg_id,
                count=1
            )

            is_pending = len(pending_entries) > 0
            consumer_name = pending_entries[0]["consumer"].decode() if is_pending else None
            delivery_count = pending_entries[0]["times_delivered"] if is_pending else 0

            task_info = {
                "stream_id": msg_id,
                "queue": queue_name,
                "data": msg_data,
                "is_pending": is_pending,
                "consumer": consumer_name,
                "delivery_count": delivery_count,
                "timestamp": int(msg_id.split('-')[0])
            }

            logger.debug(f"Retrieved task info for {stream_id}: pending={is_pending}, consumer={consumer_name}")
            return task_info

        except Exception as e:
            logger.error(f"Error getting task info for {stream_id} in queue {queue_name}: {e}", exc_info=True)
            return None

    async def get_stream_info(self, queue_name: str) -> Optional[Dict[str, Any]]:
        try:
            prefixed_queue = self.redis_service.get_prefixed_queue_name(queue_name)

            info = await self.redis.xinfo_stream(prefixed_queue)

            stream_info = {
                "length": info.get("length", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
                "groups": info.get("groups", 0)
            }

            logger.debug(f"Retrieved stream info for queue {queue_name}: length={stream_info['length']}")
            return stream_info

        except Exception as e:
            logger.error(f"Error getting stream info for queue {queue_name}: {e}", exc_info=True)
            return None

    async def get_queue_tasks(
        self,
        queue_name: str,
        start: str = "-",
        end: str = "+",
        count: int = 100,
        reverse: bool = False
    ) -> List[Dict[str, Any]]:
        try:
            prefixed_queue = self.redis_service.get_prefixed_queue_name(queue_name)

            if reverse:
                messages = await self.redis.xrevrange(prefixed_queue, max=end, min=start, count=count)
            else:
                messages = await self.redis.xrange(prefixed_queue, min=start, max=end, count=count)

            if not messages:
                logger.debug(f"No tasks found in queue {queue_name}")
                return []

            group_name = f"{self.redis_prefix}:GROUP:{queue_name}"

            try:
                pending_entries = await self.redis.xpending_range(
                    prefixed_queue,
                    group_name,
                    min="-",
                    max="+",
                    count=10000  
                )
                pending_map = {}
                for entry in pending_entries:
                    msg_id = entry["message_id"]
                    pending_map[msg_id] = {
                        "consumer": entry["consumer"].decode() if isinstance(entry["consumer"], bytes) else entry["consumer"],
                        "delivery_count": entry["times_delivered"]
                    }
            except Exception as e:
                logger.warning(f"Error getting pending info for queue {queue_name}: {e}")
                pending_map = {}

            tasks = []
            for msg_id, msg_data in messages:
                pending_info = pending_map.get(msg_id)
                is_pending = pending_info is not None

                try:
                    timestamp_ms = int(msg_id.split('-')[0])
                except (ValueError, IndexError):
                    timestamp_ms = 0

                task_data = {}
                for key, value in msg_data.items():
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    if isinstance(value, bytes):
                        value = value.decode('utf-8')
                    task_data[key] = value

                task = {
                    "stream_id": msg_id,
                    "queue": queue_name,
                    "data": task_data,
                    "is_pending": is_pending,
                    "consumer": pending_info["consumer"] if is_pending else None,
                    "delivery_count": pending_info["delivery_count"] if is_pending else 0,
                    "timestamp": timestamp_ms,
                    "timestamp_iso": datetime.fromtimestamp(timestamp_ms / 1000).isoformat() if timestamp_ms else None
                }

                tasks.append(task)

            logger.info(f"Retrieved {len(tasks)} tasks from queue {queue_name} (reverse={reverse})")
            return tasks

        except Exception as e:
            logger.error(f"Error getting queue tasks for {queue_name}: {e}", exc_info=True)
            return []
