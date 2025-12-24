"""
队列监控服务

提供队列相关的监控功能
"""
import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from .redis_monitor_service import RedisMonitorService

logger = logging.getLogger(__name__)


class QueueMonitorService:
    """队列监控服务类"""

    def __init__(self, redis_service: RedisMonitorService):
        self.redis_service = redis_service

    @property
    def redis(self):
        return self.redis_service.redis

    @property
    def redis_prefix(self) -> str:
        return self.redis_service.redis_prefix

    async def get_all_queues(self) -> List[str]:
        try:
            current_time = time.time()
            if (self.redis_service._queues_cache is not None and
                    (current_time - self.redis_service._queues_cache_time) < self.redis_service._queues_cache_ttl):
                logger.debug("Returning cached queue list")
                return self.redis_service._queues_cache

            global_queues_key = f'{self.redis_prefix}:global:queues'
            queues = await self.redis.smembers(global_queues_key)

            if queues:
                result = sorted(list(queues))
                self.redis_service._queues_cache = result
                self.redis_service._queues_cache_time = current_time
                logger.info(f"Retrieved {len(result)} queues from global set")
                return result

            from jettask.messaging.registry import QueueRegistry

            from jettask.db.connector import get_sync_redis_client
            sync_redis_client = get_sync_redis_client(self.redis_service.redis_url, decode_responses=True)

            queue_registry = QueueRegistry(
                redis_client=sync_redis_client,
                async_redis_client=self.redis,
                redis_prefix=self.redis_prefix
            )

            queues = await queue_registry.get_all_queues()

            result = sorted(list(queues))
            self.redis_service._queues_cache = result
            self.redis_service._queues_cache_time = current_time
            logger.info(f"Retrieved {len(result)} queues from registry")
            return result

        except Exception as e:
            logger.error(f"Error getting all queues: {e}", exc_info=True)
            return []

    async def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        prefixed_queue_name = self.redis_service.get_prefixed_queue_name(queue_name)

        try:
            info = await self.redis.xinfo_stream(prefixed_queue_name)
            groups = await self.redis.xinfo_groups(prefixed_queue_name)

        except Exception as e:
            logger.warning(f"Queue {queue_name} does not exist or has no groups: {e}")
            return {
                "queue": queue_name,
                "messages": 0,
                "messages_ready": 0,
                "messages_unacknowledged": 0,
                "consumers": 0,
                "message_stats": {
                    "publish": 0,
                    "deliver_get": 0,
                    "ack": 0
                },
                "consumer_groups": [],
                "error": str(e)
            }

        total_messages = info["length"]
        total_pending = 0
        total_consumers = 0
        total_delivered = 0

        consumer_groups_info = []

        for group in groups:
            group_pending = group["pending"]
            group_consumers_count = group["consumers"]

            total_pending += group_pending
            total_consumers += group_consumers_count

            group_info = {
                "name": group["name"],
                "consumers": group_consumers_count,
                "pending": group_pending,
                "last_delivered_id": group["last-delivered-id"]
            }

            try:
                consumers = await self.redis.xinfo_consumers(prefixed_queue_name, group["name"])
                group_info["consumer_details"] = consumers

                for consumer in consumers:
                    total_delivered += consumer.get("pel-count", 0)

            except Exception as e:
                group_info["consumer_details"] = []
                logger.warning(f"Error getting consumers for group {group['name']}: {e}")

            consumer_groups_info.append(group_info)

        try:
            from .worker_monitor_service import WorkerMonitorService
            worker_service = WorkerMonitorService(self.redis_service)
            worker_summary = await worker_service.get_queue_worker_summary_fast(queue_name)

            publish_count = worker_summary.get('total_count', 0)
            deliver_count = worker_summary.get('total_success_count', 0) + worker_summary.get('total_failed_count', 0)
            ack_count = worker_summary.get('total_success_count', 0)
            avg_processing_time = worker_summary.get('avg_processing_time', 0.0)
            avg_latency_time = worker_summary.get('avg_latency_time', 0.0)
            total_running_tasks = worker_summary.get('total_running_tasks', 0)
        except Exception as e:
            logger.warning(f"Error getting worker summary for queue {queue_name}: {e}")
            publish_count = 0
            deliver_count = 0
            ack_count = 0
            avg_processing_time = 0.0
            avg_latency_time = 0.0
            total_running_tasks = 0

        messages_ready = max(0, total_messages - total_pending)

        stats = {
            "queue": queue_name,
            "messages": total_messages,  
            "messages_ready": messages_ready,  
            "messages_unacknowledged": total_pending,  
            "consumers": total_consumers,  
            "message_stats": {
                "publish": publish_count,  
                "deliver_get": deliver_count,  
                "ack": ack_count  
            },
            "length": info["length"],
            "first_entry": info.get("first-entry"),
            "last_entry": info.get("last-entry"),
            "consumer_groups": consumer_groups_info,
            "performance_stats": {
                "avg_processing_time": avg_processing_time,
                "avg_latency_time": avg_latency_time,
                "total_running_tasks": total_running_tasks
            }
        }

        logger.debug(f"Queue stats for {queue_name}: {total_messages} messages, {total_consumers} consumers")
        return stats

    async def get_stream_info(self, queue_name: str, event_id: str) -> Optional[Dict[str, Any]]:
        try:
            prefixed_queue_name = self.redis_service.get_prefixed_queue_name(queue_name)

            messages = await self.redis.xrange(prefixed_queue_name, min=event_id, max=event_id, count=1)

            if messages:
                msg_id, data = messages[0]
                logger.debug(f"Found task {event_id} in queue {queue_name}")
                return {
                    "message_id": msg_id,
                    "data": data,
                    "queue": queue_name
                }

            messages = await self.redis.xrange(prefixed_queue_name, count=100)
            for msg_id, data in messages:
                if data.get("event_id") == event_id or data.get("id") == event_id:
                    logger.debug(f"Found task {event_id} in recent messages")
                    return {
                        "message_id": msg_id,
                        "data": data,
                        "queue": queue_name
                    }

            logger.warning(f"Task {event_id} not found in queue {queue_name}")
            return None

        except Exception as e:
            logger.error(f"Error reading from stream {prefixed_queue_name}: {e}", exc_info=True)
            return None

    async def get_queue_tasks(
        self,
        queue_name: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        all_tasks = []

        try:
            if not end_time:
                end_time = '+'
            if not start_time:
                start_time = '-'

            prefixed_queue_name = self.redis_service.get_prefixed_queue_name(queue_name)
            messages = await self.redis.xrevrange(
                prefixed_queue_name,
                max=end_time,
                min=start_time,
                count=limit
            )

            for msg_id, data in messages:
                event_id = msg_id

                task_info = {
                    "event_id": event_id,
                    "message_id": msg_id,
                    "stream_data": data,
                    "task_name": data.get("name", "unknown"),
                    "queue": data.get("queue", queue_name),
                    "trigger_time": data.get("trigger_time")
                }

                params_str = self._parse_task_params(data)
                task_info["params_str"] = params_str

                status_info = await self._get_task_status(event_id, queue_name, data)
                task_info.update(status_info)

                all_tasks.append(task_info)

            logger.info(f"Retrieved {len(all_tasks)} tasks from queue {queue_name}")

        except Exception as e:
            logger.error(f"Error reading queue {queue_name}: {e}", exc_info=True)
            return {
                "tasks": [],
                "count": 0,
                "oldest_id": None,
                "newest_id": None,
                "has_more": False,
                "limit": limit
            }

        oldest_id = all_tasks[-1]["message_id"] if all_tasks else None
        newest_id = all_tasks[0]["message_id"] if all_tasks else None

        return {
            "tasks": all_tasks,
            "count": len(all_tasks),
            "oldest_id": oldest_id,
            "newest_id": newest_id,
            "has_more": len(all_tasks) >= limit,
            "limit": limit
        }

    def _parse_task_params(self, data: Dict[str, Any]) -> str:
        try:
            args_list = []
            kwargs_dict = {}

            if data.get("args"):
                args_list = json.loads(data["args"])

            if data.get("kwargs"):
                kwargs_dict = json.loads(data["kwargs"])

            params_parts = []
            if args_list:
                params_parts.extend([str(arg) for arg in args_list])
            if kwargs_dict:
                params_parts.extend([f"{k}={v}" for k, v in kwargs_dict.items()])

            return ", ".join(params_parts) if params_parts else "无参数"

        except Exception as e:
            logger.warning(f"Error parsing task params: {e}")
            return "解析失败"

    async def _get_task_status(
        self,
        event_id: str,
        queue_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        status_key = f"{self.redis_prefix}:STATUS:{event_id}"
        status = await self.redis.get(status_key)

        if status:
            try:
                parsed_status = json.loads(status)
                return {
                    "status": status,
                    "parsed_status": parsed_status,
                    "consumer": parsed_status.get("consumer", "-")
                }
            except Exception as e:
                logger.warning(f"Error parsing status for task {event_id}: {e}")
                return {
                    "status": status,
                    "parsed_status": {"status": "unknown"},
                    "consumer": "-"
                }
        else:
            default_status = {
                "status": "未知",
                "queue": queue_name,
                "created_at": datetime.fromtimestamp(
                    float(data.get("trigger_time", 0))
                ).isoformat() if data.get("trigger_time") else None
            }

            return {
                "status": json.dumps(default_status),
                "parsed_status": default_status,
                "consumer": "-"
            }
