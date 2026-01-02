"""
任务服务层
处理任务相关的业务逻辑
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


class TaskService:
    """任务服务类"""
    
    def __init__(self, data_access):
        self.data_access = data_access
    
    async def get_tasks_with_filters(
        self,
        queue_name: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[List[Dict]] = None,
        time_range: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not start_time or not end_time:
            if time_range:
                start_time, end_time = await self._calculate_time_range(
                    time_range, queue_name
                )
        
        if start_time and isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time and isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        logger.info(
            f"获取队列 {queue_name} 的任务列表, "
            f"页码: {page}, 每页: {page_size}, "
            f"筛选条件: {filters}, "
            f"时间范围: {start_time} - {end_time}"
        )
        
        return await self.data_access.fetch_tasks_with_filters(
            queue_name=queue_name,
            page=page,
            page_size=page_size,
            filters=filters or [],
            start_time=start_time,
            end_time=end_time
        )
    
    async def get_task_details(
        self, 
        task_id: str,
        consumer_group: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(
            f"获取任务 {task_id} 的详细数据, "
            f"consumer_group={consumer_group}"
        )
        
        task_details = await self.data_access.fetch_task_details(
            task_id, consumer_group
        )
        
        if not task_details:
            raise ValueError(f"Task {task_id} not found")
        
        return task_details
    
    async def _calculate_time_range(
        self,
        time_range: str,
        queue_name: str
    ) -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        
        time_range_map = {
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "3h": timedelta(hours=3),
            "6h": timedelta(hours=6),
            "12h": timedelta(hours=12),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        
        delta = time_range_map.get(time_range, timedelta(minutes=15))
        
        latest_time = await self.data_access.get_latest_task_time(queue_name)
        if latest_time:
            end_time = latest_time.replace(second=59, microsecond=999999)
            logger.info(f"使用最新任务时间: {latest_time}")
        else:
            end_time = now.replace(second=0, microsecond=0)
        
        start_time = end_time - delta
        logger.info(
            f"使用时间范围 {time_range}: {start_time} 到 {end_time}"
        )
        
        return start_time, end_time