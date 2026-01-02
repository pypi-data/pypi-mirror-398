"""
服务基类
提供公共的时间范围处理方法
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import logging

from jettask.schemas import TimeRangeQuery

logger = logging.getLogger(__name__)


class TimeRangeResult:
    """时间范围处理结果"""
    def __init__(self, start_time: datetime, end_time: datetime, interval: str, interval_seconds: int, granularity: str):
        self.start_time = start_time
        self.end_time = end_time
        self.interval = interval
        self.interval_seconds = interval_seconds
        self.granularity = granularity


class QueueResolutionResult:
    """队列解析结果"""
    def __init__(
        self,
        target_queues: List[str],
        all_priority_queues: List[str],
        base_queue_map: Dict[str, str]
    ):
        self.target_queues = target_queues
        self.all_priority_queues = all_priority_queues
        self.base_queue_map = base_queue_map


class BaseService:
    """服务基类，提供公共的集成方法"""

    @staticmethod
    def _parse_time_range(time_range: str, end_time: datetime) -> datetime:
        if time_range.endswith('m'):
            minutes = int(time_range[:-1])
            return end_time - timedelta(minutes=minutes)
        elif time_range.endswith('h'):
            hours = int(time_range[:-1])
            return end_time - timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            return end_time - timedelta(days=days)
        else:
            return end_time - timedelta(hours=24)  

    @staticmethod
    def _parse_time_range_query(query: TimeRangeQuery) -> TimeRangeResult:
        if query.end_time:
            end_time = datetime.fromisoformat(query.end_time.replace('Z', '+00:00')) if isinstance(query.end_time, str) else query.end_time
        else:
            end_time = datetime.now(timezone.utc)

        if query.start_time:
            start_time = datetime.fromisoformat(query.start_time.replace('Z', '+00:00')) if isinstance(query.start_time, str) else query.start_time
        else:
            interval = query.interval or "24h"
            start_time = BaseService._parse_time_range(interval, end_time)

        return BaseService._calculate_dynamic_interval(start_time, end_time)

    @staticmethod
    def _calculate_dynamic_interval(start_time: datetime, end_time: datetime, target_points: int = 200) -> TimeRangeResult:
        duration = (end_time - start_time).total_seconds()
        ideal_interval_seconds = duration / target_points

        intervals = [
            (1, '1 seconds', 'second'),
            (5, '5 seconds', 'second'),
            (10, '10 seconds', 'second'),
            (30, '30 seconds', 'second'),
            (60, '1 minute', 'minute'),
            (300, '5 minutes', 'minute'),
            (600, '10 minutes', 'minute'),
            (1800, '30 minutes', 'minute'),
            (3600, '1 hour', 'hour'),
            (21600, '6 hours', 'hour'),
            (43200, '12 hours', 'hour'),
            (86400, '1 day', 'day')
        ]

        for seconds, interval_str, granularity in intervals:
            if ideal_interval_seconds <= seconds:
                return TimeRangeResult(start_time, end_time, interval_str, seconds, granularity)

        return TimeRangeResult(start_time, end_time, '1 day', 86400, 'day')

    @classmethod
    def _resolve_time_range(
        cls,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_range: Optional[str] = None,
        default_range: str = "1h",
        target_points: int = 200,
        min_interval_seconds: int = 0
    ) -> TimeRangeResult:
        now = datetime.now(timezone.utc)

        if time_range and not start_time:
            start_time = cls._parse_time_range(time_range, now)
            end_time = now
        elif not start_time:
            start_time = cls._parse_time_range(default_range, now)
            end_time = now

        if not end_time:
            end_time = now

        result = cls._calculate_dynamic_interval(start_time, end_time, target_points)

        if min_interval_seconds > 0 and result.interval_seconds < min_interval_seconds:
            granularity = "second"
            if min_interval_seconds >= 86400:
                granularity = "day"
            elif min_interval_seconds >= 3600:
                granularity = "hour"
            elif min_interval_seconds >= 60:
                granularity = "minute"

            if min_interval_seconds == 60:
                interval_str = "1 minute"
            elif min_interval_seconds == 300:
                interval_str = "5 minutes"
            elif min_interval_seconds == 600:
                interval_str = "10 minutes"
            elif min_interval_seconds == 1800:
                interval_str = "30 minutes"
            elif min_interval_seconds == 3600:
                interval_str = "1 hour"
            else:
                interval_str = f"{min_interval_seconds} seconds"

            logger.debug(
                f"时间间隔 {result.interval_seconds}s 小于最小值 {min_interval_seconds}s，"
                f"已调整为 {interval_str}"
            )

            result = TimeRangeResult(
                start_time=result.start_time,
                end_time=result.end_time,
                interval=interval_str,
                interval_seconds=min_interval_seconds,
                granularity=granularity
            )

        return result

    @staticmethod
    async def _resolve_queues(
        queues: List[str],
        registry,
        expand_priority: bool = True
    ) -> QueueResolutionResult:
        all_base_queues = await registry.get_base_queues()

        target_queues = [q for q in queues if q in all_base_queues]

        if not expand_priority:
            base_queue_map = {q: q for q in target_queues}
            return QueueResolutionResult(
                target_queues=target_queues,
                all_priority_queues=target_queues,
                base_queue_map=base_queue_map
            )

        all_priority_queues = []
        base_queue_map = {}  

        for base_queue in target_queues:
            priority_queues = await registry.get_priority_queues_for_base(base_queue)
            if priority_queues:
                all_priority_queues.extend(priority_queues)
                for pq in priority_queues:
                    base_queue_map[pq] = base_queue
            else:
                all_priority_queues.append(base_queue)
                base_queue_map[base_queue] = base_queue

        logger.debug(f"队列解析: {queues} -> target={target_queues}, priority={all_priority_queues}")

        return QueueResolutionResult(
            target_queues=target_queues,
            all_priority_queues=all_priority_queues,
            base_queue_map=base_queue_map
        )
