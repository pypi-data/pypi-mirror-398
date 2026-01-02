"""
时间轴服务

提供队列任务的时间分布分析功能
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

from .redis_monitor_service import RedisMonitorService

logger = logging.getLogger(__name__)


class TimelineService:
    """时间轴服务类"""

    def __init__(self, redis_service: RedisMonitorService):
        self.redis_service = redis_service

    @property
    def redis(self):
        return self.redis_service.redis

    @property
    def redis_prefix(self) -> str:
        return self.redis_service.redis_prefix

    async def get_redis_timeline(
        self,
        queue_name: str,
        interval: str = "1m",
        duration: str = "1h",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        context: str = "detail"
    ) -> Dict[str, Any]:
        try:
            interval_seconds = self._parse_time_duration(interval)

            if context == "overview":
                duration_seconds = 3600  
                now = int(datetime.now(timezone.utc).timestamp() * 1000)
                start = now - duration_seconds * 1000
                min_id = f"{start}-0"
                max_id = "+"
                max_count = 100000  
            else:
                if start_time and end_time:
                    min_id = start_time
                    max_id = end_time if end_time != '+' else '+'
                else:
                    duration_seconds = self._parse_time_duration(duration)
                    now = int(datetime.now(timezone.utc).timestamp() * 1000)
                    start = now - duration_seconds * 1000
                    min_id = f"{start}-0"
                    max_id = "+"
                max_count = 10000  

            prefixed_queue_name = self.redis_service.get_prefixed_queue_name(queue_name)
            messages = await self.redis.xrange(
                prefixed_queue_name,
                min=min_id,
                max=max_id,
                count=max_count
            )

            buckets = {}
            bucket_size = interval_seconds * 1000  

            if start_time and end_time:
                if start_time != '-':
                    actual_start = int(start_time.split('-')[0])
                else:
                    actual_start = int(datetime.now(timezone.utc).timestamp() * 1000) - 86400000

                if end_time != '+':
                    actual_end = int(end_time.split('-')[0])
                else:
                    actual_end = int(datetime.now(timezone.utc).timestamp() * 1000)
            else:
                actual_start = start
                actual_end = now

            for msg_id, _ in messages:
                timestamp = int(msg_id.split('-')[0])
                bucket_key = (timestamp // bucket_size) * bucket_size
                buckets[bucket_key] = buckets.get(bucket_key, 0) + 1

            timeline_data = []
            current_bucket = (actual_start // bucket_size) * bucket_size

            while current_bucket <= actual_end:
                timeline_data.append({
                    "timestamp": current_bucket,
                    "count": buckets.get(current_bucket, 0)
                })
                current_bucket += bucket_size

            total_tasks = len(messages)

            has_more = False
            if context == "detail" and total_tasks >= max_count:
                has_more = True

            logger.info(f"Redis 时间轴: 队列={queue_name}, 任务数={total_tasks}, 数据点={len(timeline_data)}")

            return {
                "timeline": timeline_data,
                "interval": interval,
                "duration": duration,
                "start": actual_start,
                "end": actual_end,
                "total_tasks": total_tasks,
                "message_count": len(messages),
                "has_more": has_more,
                "limit": max_count if context == "detail" else None,
                "source": "redis"
            }

        except Exception as e:
            logger.error(f"获取 Redis 时间轴失败: 队列={queue_name}, 错误={e}", exc_info=True)
            return {
                "timeline": [],
                "error": str(e),
                "source": "redis"
            }

    def _parse_time_duration(self, duration_str: str) -> int:
        units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }

        if duration_str[-1] in units:
            value = int(duration_str[:-1])
            unit = duration_str[-1]
            return value * units[unit]

        return int(duration_str)
