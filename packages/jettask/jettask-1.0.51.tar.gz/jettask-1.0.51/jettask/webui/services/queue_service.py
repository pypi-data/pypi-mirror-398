"""
队列服务层
处理队列相关的业务逻辑
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from enum import Enum
from sqlalchemy import text, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from jettask.db.models.task import Task
from jettask.db.models.task_run import TaskRun
from jettask.db.models.task_metrics_minute import TaskMetricsMinute
from jettask.db.models.task_runs_metrics_minute import TaskRunsMetricsMinute
from jettask.webui.services.base_service import BaseService

logger = logging.getLogger(__name__)


class TrendMetric(str, Enum):
    """趋势查询支持的聚合指标（task_run 维度）"""
    TOTAL_COUNT = "total_count"          
    SUCCESS_COUNT = "success_count"       
    FAILED_COUNT = "failed_count"         
    RETRY_COUNT = "retry_count"           
    AVG_DURATION = "avg_duration"         
    MAX_DURATION = "max_duration"         
    MIN_DURATION = "min_duration"         
    AVG_DELAY = "avg_delay"               
    MAX_DELAY = "max_delay"               
    MIN_DELAY = "min_delay"               
    MAX_CONCURRENCY = "max_concurrency"   
    SUCCESS_RATE = "success_rate"         


class TaskTrendMetric(str, Enum):
    """趋势查询支持的聚合指标（task 维度）"""
    TASK_COUNT = "task_count"             


class QueueService(BaseService):
    """队列服务类"""
    
    @staticmethod
    def get_base_queue_name(queue_name: str) -> str:
        if ':' in queue_name:
            parts = queue_name.rsplit(':', 1)
            if parts[-1].isdigit():
                return parts[0]
        return queue_name
    
    @staticmethod
    async def get_queues_by_namespace(namespace_data_access, namespace: str) -> Dict[str, Any]:
        queues_data = await namespace_data_access.get_queue_stats(namespace)
        return {
            "success": True,
            "data": list(set([QueueService.get_base_queue_name(q['queue_name']) for q in queues_data]))
        }
    
    @staticmethod
    async def get_queue_flow_rates(data_access, query) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        
        if query.start_time and query.end_time:
            start_time = query.start_time
            end_time = query.end_time
            logger.info(f"使用自定义时间范围: {start_time} 到 {end_time}")
        else:
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
            
            time_range_value = query.time_range if query.time_range else query.interval
            delta = time_range_map.get(time_range_value, timedelta(minutes=15))
            
            queue_name = query.queues[0] if query.queues else None
            if queue_name:
                latest_time = await data_access.get_latest_task_time(queue_name)
                if latest_time:
                    end_time = latest_time.replace(second=59, microsecond=999999)  
                    logger.info(f"使用最新任务时间: {latest_time}")
                else:
                    end_time = now.replace(second=0, microsecond=0)
            else:
                end_time = now.replace(second=0, microsecond=0)
            
            start_time = end_time - delta
            logger.info(f"使用预设时间范围 {time_range_value}: {start_time} 到 {end_time}, delta: {delta}")
        
        if not query.queues or len(query.queues) == 0:
            return {"data": [], "granularity": "minute"}
        
        queue_name = query.queues[0]
        filters = getattr(query, 'filters', None)
        data, granularity = await data_access.fetch_queue_flow_rates(
            queue_name, start_time, end_time, filters
        )
        
        return {"data": data, "granularity": granularity}
    
    @staticmethod
    async def get_global_stats(data_access) -> Dict[str, Any]:
        stats_data = await data_access.fetch_global_stats()
        return {
            "success": True,
            "data": stats_data
        }
    
    @staticmethod
    async def get_queues_detail(data_access) -> Dict[str, Any]:
        queues_data = await data_access.fetch_queues_data()
        return {
            "success": True,
            "data": queues_data
        }
    
    @staticmethod
    async def delete_queue(queue_name: str) -> Dict[str, Any]:
        logger.info(f"删除队列请求: {queue_name}")
        return {
            "success": True,
            "message": f"队列 {queue_name} 已删除"
        }
    
    @staticmethod
    async def trim_queue(queue_name: str, max_length: int) -> Dict[str, Any]:
        logger.info(f"裁剪队列请求: {queue_name}, 保留 {max_length} 条消息")
        return {
            "success": True,
            "message": f"队列 {queue_name} 已裁剪至 {max_length} 条消息"
        }
    
    @staticmethod
    async def get_queue_stats_v2(
        namespace_data_access,
        namespace: str,
        queue: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        conn = await namespace_data_access.manager.get_connection(namespace)
        
        redis_client = await conn.get_redis_client(decode=False)
        
        pg_session = None
        if conn.AsyncSessionLocal:
            pg_session = conn.AsyncSessionLocal()
        
        try:
            from jettask.webui.services.queue_stats_v2 import QueueStatsV2
            
            stats_service = QueueStatsV2(
                redis_client=redis_client,
                pg_session=pg_session,
                redis_prefix=conn.redis_prefix
            )
            
            time_filter = None
            if time_range or start_time or end_time:
                time_filter = {}
                
                if time_range and time_range != 'custom':
                    now = datetime.now(timezone.utc)
                    if time_range.endswith('m'):
                        minutes = int(time_range[:-1])
                        time_filter['start_time'] = now - timedelta(minutes=minutes)
                        time_filter['end_time'] = now
                    elif time_range.endswith('h'):
                        hours = int(time_range[:-1])
                        time_filter['start_time'] = now - timedelta(hours=hours)
                        time_filter['end_time'] = now
                    elif time_range.endswith('d'):
                        days = int(time_range[:-1])
                        time_filter['start_time'] = now - timedelta(days=days)
                        time_filter['end_time'] = now
                else:
                    if start_time:
                        time_filter['start_time'] = start_time
                    if end_time:
                        time_filter['end_time'] = end_time
            
            stats = await stats_service.get_queue_stats_grouped(time_filter)
            
            if queue:
                stats = [s for s in stats if s['queue_name'] == queue]
            
            return {
                "success": True,
                "data": stats
            }
            
        finally:
            if pg_session:
                await pg_session.close()
            await redis_client.aclose()
    
    @staticmethod
    async def get_tasks_v2(namespace_data_access, namespace: str, body: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import text
        from datetime import datetime, timezone, timedelta
        
        queue_name = body.get('queue_name')
        page = body.get('page', 1)
        page_size = body.get('page_size', 20)
        filters = body.get('filters', [])
        time_range = body.get('time_range', '1h')
        start_time = body.get('start_time')
        end_time = body.get('end_time')
        sort_field = body.get('sort_field', 'created_at')
        sort_order = body.get('sort_order', 'desc')
        
        if not queue_name:
            raise ValueError("queue_name is required")
        
        conn = await namespace_data_access.manager.get_connection(namespace)
        
        if not conn.pg_config or not conn.async_engine:
            return {
                "success": True,
                "data": [],
                "total": 0
            }
        
        if start_time and end_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            end_dt = datetime.now(timezone.utc)
            time_deltas = {
                '15m': timedelta(minutes=15),
                '30m': timedelta(minutes=30),
                '1h': timedelta(hours=1),
                '3h': timedelta(hours=3),
                '6h': timedelta(hours=6),
                '12h': timedelta(hours=12),
                '1d': timedelta(days=1),
                '3d': timedelta(days=3),
                '7d': timedelta(days=7),
                '30d': timedelta(days=30)
            }
            delta = time_deltas.get(time_range, timedelta(hours=1))
            start_dt = end_dt - delta
        
        offset = (page - 1) * page_size
        
        async with conn.async_engine.begin() as pg_conn:
            conditions = [
                "t.namespace = :namespace",
                "t.queue = :queue",
                "t.created_at >= :start_time",
                "t.created_at <= :end_time"
            ]
            query_params = {
                "namespace": namespace,
                "queue": queue_name,
                "start_time": start_dt,
                "end_time": end_dt,
                "limit": page_size,
                "offset": offset
            }
            
            for i, filter_item in enumerate(filters):
                field = filter_item.get('field')
                operator = filter_item.get('operator')
                value = filter_item.get('value')
                
                if field and operator and value is not None:
                    param_key = f"filter_{i}"
                    
                    db_field_map = {
                        'id': 't.stream_id',
                        'task_name': "t.payload::jsonb->'event_data'->>'__task_name'",
                        'status': "t.payload::jsonb->>'status'",
                        'worker_id': "t.payload::jsonb->>'worker_id'",
                        'scheduled_task_id': 't.scheduled_task_id'
                    }
                    
                    db_field = db_field_map.get(field, f't.{field}')
                    
                    if operator == 'eq':
                        conditions.append(f"{db_field} = :{param_key}")
                        query_params[param_key] = value
                    elif operator == 'contains':
                        conditions.append(f"{db_field} LIKE :{param_key}")
                        query_params[param_key] = f"%{value}%"
                    elif operator == 'gt':
                        conditions.append(f"{db_field} > :{param_key}")
                        query_params[param_key] = value
                    elif operator == 'lt':
                        conditions.append(f"{db_field} < :{param_key}")
                        query_params[param_key] = value
            
            where_clause = " AND ".join(conditions)
            
            count_query = f"""
                SELECT COUNT(*) as total 
                FROM tasks t
                WHERE {where_clause}
            """
            count_result = await pg_conn.execute(text(count_query), query_params)
            total = count_result.fetchone().total
            
            sort_map = {
                'created_at': 't.created_at',
                'started_at': 't.started_at',
                'completed_at': 't.completed_at'
            }
            order_by = sort_map.get(sort_field, 't.created_at')
            order_direction = 'DESC' if sort_order == 'desc' else 'ASC'
            
            query = f"""
                SELECT 
                    t.stream_id as id,
                    t.payload::jsonb->'event_data'->>'__task_name' as task_name,
                    t.queue,
                    t.payload::jsonb->>'status' as status,
                    t.priority,
                    COALESCE((t.payload::jsonb->>'retry_count')::int, 0) as retry_count,
                    COALESCE((t.payload::jsonb->>'max_retry')::int, 3) as max_retry,
                    t.created_at,
                    (t.payload::jsonb->>'started_at')::timestamptz as started_at,
                    (t.payload::jsonb->>'completed_at')::timestamptz as completed_at,
                    t.payload::jsonb->>'worker_id' as worker_id,
                    t.payload::jsonb->>'error_message' as error_message,
                    (t.payload::jsonb->>'execution_time')::float as execution_time,
                    CASE 
                        WHEN t.payload::jsonb->>'completed_at' IS NOT NULL AND t.created_at IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM ((t.payload::jsonb->>'completed_at')::timestamptz - t.created_at))
                        ELSE NULL 
                    END as duration,
                    t.scheduled_task_id,
                    t.source,
                    t.metadata
                FROM tasks t
                WHERE {where_clause}
                ORDER BY {order_by} {order_direction}
                LIMIT :limit OFFSET :offset
            """
            
            result = await pg_conn.execute(text(query), query_params)
            
            tasks = []
            for row in result:
                tasks.append({
                    "id": row.id,
                    "task_name": row.task_name or "unknown",
                    "queue": row.queue,
                    "status": row.status,
                    "priority": row.priority,
                    "retry_count": row.retry_count,
                    "max_retry": row.max_retry,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "started_at": row.started_at.isoformat() if row.started_at else None,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                    "duration": round(row.duration, 2) if row.duration else None,
                    "execution_time": float(row.execution_time) if row.execution_time else None,
                    "worker_id": row.worker_id,
                    "error_message": row.error_message
                })
            
            return {
                "success": True,
                "data": tasks,
                "total": total
            }
    
    @staticmethod
    async def get_consumer_group_stats(namespace_data_access, namespace: str, group_name: str) -> Dict[str, Any]:
        conn = await namespace_data_access.manager.get_connection(namespace)
        
        if not conn.AsyncSessionLocal:
            raise ValueError("PostgreSQL not configured for this namespace")
        
        async with conn.AsyncSessionLocal() as session:
            query = text("""
                WITH group_stats AS (
                    SELECT 
                        tr.consumer_group,
                        tr.task_name,
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN tr.status = 'success' THEN 1 END) as success_count,
                        COUNT(CASE WHEN tr.status = 'failed' THEN 1 END) as failed_count,
                        COUNT(CASE WHEN tr.status = 'running' THEN 1 END) as running_count,
                        AVG(tr.execution_time) as avg_execution_time,
                        MIN(tr.execution_time) as min_execution_time,
                        MAX(tr.execution_time) as max_execution_time,
                        AVG(tr.duration) as avg_duration,
                        MIN(tr.started_at) as first_task_time,
                        MAX(tr.completed_at) as last_task_time
                    FROM task_runs tr
                    WHERE tr.consumer_group = :group_name
                        AND tr.started_at > NOW() - INTERVAL '24 hours'
                    GROUP BY tr.consumer_group, tr.task_name
                ),
                hourly_stats AS (
                    SELECT 
                        DATE_TRUNC('hour', tr.started_at) as hour,
                        COUNT(*) as task_count,
                        AVG(tr.execution_time) as avg_exec_time
                    FROM task_runs tr
                    WHERE tr.consumer_group = :group_name
                        AND tr.started_at > NOW() - INTERVAL '24 hours'
                    GROUP BY DATE_TRUNC('hour', tr.started_at)
                    ORDER BY hour
                )
                SELECT 
                    (SELECT row_to_json(gs) FROM group_stats gs) as summary,
                    (SELECT json_agg(hs) FROM hourly_stats hs) as hourly_trend
            """)
            
            result = await session.execute(query, {'group_name': group_name})
            row = result.fetchone()
            
            if not row or not row.summary:
                return {
                    "success": True,
                    "data": {
                        "group_name": group_name,
                        "summary": {},
                        "hourly_trend": []
                    }
                }
            
            return {
                "success": True,
                "data": {
                    "group_name": group_name,
                    "summary": row.summary,
                    "hourly_trend": row.hourly_trend or []
                }
            }
    
    @staticmethod
    async def get_stream_backlog(
        data_access,
        namespace: str,
        stream_name: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        return {
            'success': False,
            'data': [],
            'total': 0,
            'message': 'stream_backlog_monitor 表已废弃，请使用其他积压监控接口'
        }
    
    @staticmethod
    async def get_stream_backlog_summary(data_access, namespace: str) -> Dict[str, Any]:
        return {
            'success': False,
            'data': {
                'total_streams': 0,
                'total_groups': 0,
                'total_backlog': 0,
                'total_pending': 0,
                'max_backlog': 0
            },
            'message': 'stream_backlog_monitor 表已废弃，请使用其他积压监控接口'
        }


    @classmethod
    async def get_queue_overview(
        cls,
        namespace: str,
        pg_session: AsyncSession,
        registry,  
        queues: List[str],  
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            time_range_result = cls._resolve_time_range(
                start_time=start_time,
                end_time=end_time,
                time_range=time_range,
                default_range="1h",
                min_interval_seconds=60  
            )
            start_time = time_range_result.start_time
            end_time = time_range_result.end_time

            queue_result = await cls._resolve_queues(queues, registry, expand_priority=True)
            target_queues = queue_result.target_queues
            all_priority_queues = queue_result.all_priority_queues
            base_queue_map = queue_result.base_queue_map

            if not target_queues:
                logger.warning(f"请求的队列 {queues} 在命名空间 {namespace} 中不存在")
                return {
                    "success": True,
                    "data": [],
                    "total": 0,
                    "granularity": time_range_result.granularity,
                    "time_range": {
                        "start_time": start_time.isoformat() if start_time else None,
                        "end_time": end_time.isoformat() if end_time else None,
                        "interval": time_range_result.interval,
                        "interval_seconds": time_range_result.interval_seconds
                    }
                }

            logger.info(
                f"队列概览查询: namespace={namespace}, queues={target_queues}, "
                f"priority_queues={all_priority_queues}, "
                f"time_range={start_time} to {end_time}, "
                f"granularity={time_range_result.granularity}"
            )

            stats_stmt = select(
                TaskRunsMetricsMinute.queue,
                TaskRunsMetricsMinute.task_name,
                func.sum(TaskRunsMetricsMinute.total_count).label('total_count'),
                func.sum(TaskRunsMetricsMinute.success_count).label('success_count'),
                func.sum(TaskRunsMetricsMinute.failed_count).label('failed_count'),
                func.sum(TaskRunsMetricsMinute.retry_count).label('retry_count'),
                func.sum(TaskRunsMetricsMinute.total_duration).label('total_duration'),
                func.max(TaskRunsMetricsMinute.max_duration).label('max_duration'),
                func.min(TaskRunsMetricsMinute.min_duration).label('min_duration'),
                func.sum(TaskRunsMetricsMinute.total_delay).label('total_delay'),
                func.max(TaskRunsMetricsMinute.max_delay).label('max_delay'),
                func.min(TaskRunsMetricsMinute.min_delay).label('min_delay'),
                func.max(TaskRunsMetricsMinute.running_concurrency).label('max_concurrency')
            ).where(
                and_(
                    TaskRunsMetricsMinute.queue.in_(all_priority_queues),
                    TaskRunsMetricsMinute.namespace == namespace,
                    TaskRunsMetricsMinute.time_bucket >= start_time,
                    TaskRunsMetricsMinute.time_bucket <= end_time
                )
            ).group_by(TaskRunsMetricsMinute.queue, TaskRunsMetricsMinute.task_name)

            result = await pg_session.execute(stats_stmt)
            rows = result.all()

            base_queue_tasks = {}
            for base_queue in target_queues:
                base_queue_tasks[base_queue] = {}

            for row in rows:
                priority_queue = row.queue
                base_queue = base_queue_map.get(priority_queue, cls.get_base_queue_name(priority_queue))
                task_name = row.task_name

                if base_queue not in base_queue_tasks:
                    continue

                if task_name not in base_queue_tasks[base_queue]:
                    base_queue_tasks[base_queue][task_name] = {
                        "task_name": task_name,
                        "total_count": 0,
                        "success_count": 0,
                        "failed_count": 0,
                        "retry_count": 0,
                        "total_duration": 0.0,
                        "max_duration": None,
                        "min_duration": None,
                        "total_delay": 0.0,
                        "max_delay": None,
                        "min_delay": None,
                        "max_concurrency": 0
                    }

                stats = base_queue_tasks[base_queue][task_name]
                stats["total_count"] += row.total_count or 0
                stats["success_count"] += row.success_count or 0
                stats["failed_count"] += row.failed_count or 0
                stats["retry_count"] += row.retry_count or 0
                stats["total_duration"] += row.total_duration or 0.0
                stats["total_delay"] += row.total_delay or 0.0
                if row.max_duration is not None:
                    stats["max_duration"] = max(stats["max_duration"] or 0, row.max_duration)
                if row.max_delay is not None:
                    stats["max_delay"] = max(stats["max_delay"] or 0, row.max_delay)
                if row.max_concurrency is not None:
                    stats["max_concurrency"] = max(stats["max_concurrency"], row.max_concurrency)
                if row.min_duration is not None:
                    if stats["min_duration"] is None:
                        stats["min_duration"] = row.min_duration
                    else:
                        stats["min_duration"] = min(stats["min_duration"], row.min_duration)
                if row.min_delay is not None:
                    if stats["min_delay"] is None:
                        stats["min_delay"] = row.min_delay
                    else:
                        stats["min_delay"] = min(stats["min_delay"], row.min_delay)

            overview_data = []
            for queue_name in sorted(target_queues):
                tasks_data = []
                for task_name, stats in base_queue_tasks[queue_name].items():
                    if stats["total_count"] > 0:
                        stats["avg_duration"] = round(stats["total_duration"] / stats["total_count"], 4)
                        stats["avg_delay"] = round(stats["total_delay"] / stats["total_count"], 4)
                        stats["success_rate"] = round(
                            (stats["success_count"] / (stats["success_count"] + stats["failed_count"])) * 100, 2
                        ) if (stats["success_count"] + stats["failed_count"]) > 0 else 0.0
                    else:
                        stats["avg_duration"] = 0.0
                        stats["avg_delay"] = 0.0
                        stats["success_rate"] = 0.0

                    stats["total_duration"] = round(stats["total_duration"], 4)
                    stats["total_delay"] = round(stats["total_delay"], 4)
                    if stats["max_duration"] is not None:
                        stats["max_duration"] = round(stats["max_duration"], 4)
                    if stats["min_duration"] is not None:
                        stats["min_duration"] = round(stats["min_duration"], 4)
                    if stats["max_delay"] is not None:
                        stats["max_delay"] = round(stats["max_delay"], 4)
                    if stats["min_delay"] is not None:
                        stats["min_delay"] = round(stats["min_delay"], 4)

                    tasks_data.append(stats)

                tasks_data.sort(key=lambda x: x["task_name"])

                overview_data.append({
                    "queue_name": queue_name,
                    "task_count": len(tasks_data),
                    "tasks": tasks_data
                })

            return {
                "success": True,
                "data": overview_data,
                "total": len(overview_data),
                "granularity": time_range_result.granularity,
                "time_range": {
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                    "interval": time_range_result.interval,
                    "interval_seconds": time_range_result.interval_seconds
                }
            }

        except Exception as e:
            logger.error(f"获取队列概览失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "granularity": "minute",
                "time_range": {}
            }

    @classmethod
    async def get_queue_tasks_detail(
        cls,
        namespace: str,
        queue_name: str,
        pg_session: AsyncSession,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            time_range_result = cls._resolve_time_range(
                start_time=start_time,
                end_time=end_time,
                time_range=time_range,
                default_range="15m"
            )
            start_time = time_range_result.start_time
            end_time = time_range_result.end_time

            logger.info(f"获取队列 tasks 详情: namespace={namespace}, queue={queue_name}, time_range={start_time} to {end_time}")

            task_stats_stmt = select(
                TaskRun.task_name,
                func.count().filter(TaskRun.status == 'success').label('success_count'),
                func.count().filter(TaskRun.status == 'failed').label('failed_count'),
                func.avg(TaskRun.duration).label('avg_duration')
            ).select_from(TaskRun).join(
                Task, TaskRun.stream_id == Task.stream_id
            ).where(
                and_(
                    Task.queue == queue_name,
                    Task.namespace == namespace,
                    TaskRun.created_at >= start_time,
                    TaskRun.created_at <= end_time,
                    TaskRun.task_name.isnot(None)
                )
            ).group_by(TaskRun.task_name)

            result = await pg_session.execute(task_stats_stmt)
            rows = result.all()

            tasks = []
            for row in rows:
                total_count = row.success_count + row.failed_count
                success_rate = round((row.success_count / total_count) * 100, 2) if total_count > 0 else 0.0

                tasks.append({
                    "task_name": row.task_name,
                    "success_count": row.success_count or 0,
                    "failed_count": row.failed_count or 0,
                    "success_rate": success_rate,
                    "avg_duration": round(row.avg_duration, 4) if row.avg_duration else 0.0
                })

            return {
                "success": True,
                "queue_name": queue_name,
                "tasks": tasks,
                "total": len(tasks),
                "time_range": {
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None
                }
            }

        except Exception as e:
            logger.error(f"获取队列 tasks 详情失败: queue={queue_name}, error={e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "queue_name": queue_name,
                "tasks": []
            }

    @classmethod
    async def get_queue_runs_trend(
        cls,
        namespace: str,
        pg_session: AsyncSession,
        registry,  
        queues: List[str],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_range: Optional[str] = None,
        metrics: Optional[List[TrendMetric]] = None
    ) -> Dict[str, Any]:
        try:
            if metrics is None:
                metrics = [TrendMetric.TOTAL_COUNT]

            time_range_result = cls._resolve_time_range(
                start_time=start_time,
                end_time=end_time,
                time_range=time_range,
                default_range="1h",
                min_interval_seconds=60  
            )
            start_time = time_range_result.start_time
            end_time = time_range_result.end_time

            queue_result = await cls._resolve_queues(queues, registry, expand_priority=True)
            target_queues = queue_result.target_queues
            all_priority_queues = queue_result.all_priority_queues
            base_queue_map = queue_result.base_queue_map

            logger.info(
                f"队列趋势查询: namespace={namespace}, queues={target_queues}, "
                f"priority_queues={all_priority_queues}, metrics={[m.value for m in metrics]}, "
                f"time_range={start_time} to {end_time}, "
                f"interval={time_range_result.interval}, granularity={time_range_result.granularity}"
            )

            if not target_queues:
                return {
                    "success": True,
                    "data": [],
                    "metrics": [m.value for m in metrics],
                    "granularity": time_range_result.granularity,
                    "time_range": {
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "interval": time_range_result.interval,
                        "interval_seconds": time_range_result.interval_seconds
                    }
                }

            interval_seconds = time_range_result.interval_seconds

            data = await cls._query_trend_from_runs_metrics(
                pg_session,
                namespace,
                target_queues,
                all_priority_queues,
                base_queue_map,
                start_time,
                end_time,
                interval_seconds,
                metrics
            )

            return {
                "success": True,
                "data": data,
                "metrics": [m.value for m in metrics],
                "granularity": time_range_result.granularity,
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "interval": time_range_result.interval,
                    "interval_seconds": time_range_result.interval_seconds
                }
            }

        except Exception as e:
            logger.error(f"获取队列趋势失败: queues={queues}, error={e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "metrics": [m.value for m in (metrics or [TrendMetric.TOTAL_COUNT])]
            }

    @classmethod
    async def get_queue_tasks_trend(
        cls,
        namespace: str,
        pg_session: AsyncSession,
        registry,  
        queues: List[str],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            time_range_result = cls._resolve_time_range(
                start_time=start_time,
                end_time=end_time,
                time_range=time_range,
                default_range="1h",
                min_interval_seconds=60  
            )
            start_time = time_range_result.start_time
            end_time = time_range_result.end_time

            queue_result = await cls._resolve_queues(queues, registry, expand_priority=True)
            target_queues = queue_result.target_queues
            all_priority_queues = queue_result.all_priority_queues
            base_queue_map = queue_result.base_queue_map

            logger.info(
                f"队列任务创建趋势查询: namespace={namespace}, queues={target_queues}, "
                f"priority_queues={all_priority_queues}, "
                f"time_range={start_time} to {end_time}, "
                f"interval={time_range_result.interval}, granularity={time_range_result.granularity}"
            )

            if not target_queues:
                return {
                    "success": True,
                    "data": [],
                    "metrics": ["task_count"],
                    "granularity": time_range_result.granularity,
                    "time_range": {
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "interval": time_range_result.interval,
                        "interval_seconds": time_range_result.interval_seconds
                    }
                }

            interval_seconds = time_range_result.interval_seconds

            stmt = select(
                TaskMetricsMinute.queue,
                TaskMetricsMinute.time_bucket,
                TaskMetricsMinute.task_count
            ).where(
                and_(
                    TaskMetricsMinute.namespace == namespace,
                    TaskMetricsMinute.queue.in_(all_priority_queues),
                    TaskMetricsMinute.time_bucket >= start_time,
                    TaskMetricsMinute.time_bucket <= end_time
                )
            ).order_by(
                TaskMetricsMinute.queue,
                TaskMetricsMinute.time_bucket
            )

            result = await pg_session.execute(stmt)
            rows = result.fetchall()

            time_buckets = []
            if interval_seconds > 60:
                start_timestamp = int(start_time.timestamp() / interval_seconds) * interval_seconds
                current = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)
                end_timestamp = int(end_time.timestamp() / interval_seconds) * interval_seconds
                end_aligned = datetime.fromtimestamp(end_timestamp, tz=timezone.utc)
            else:
                current = start_time.replace(second=0, microsecond=0)
                end_aligned = end_time.replace(second=0, microsecond=0)

            while current <= end_aligned:
                time_buckets.append(current)
                current += timedelta(seconds=interval_seconds)

            queue_data_map = {}
            for base_queue in target_queues:
                queue_data_map[base_queue] = {bucket: 0 for bucket in time_buckets}

            for row in rows:
                priority_queue = row.queue
                base_queue = base_queue_map.get(priority_queue)
                if not base_queue or base_queue not in queue_data_map:
                    continue

                time_bucket = row.time_bucket
                count = row.task_count or 0

                if interval_seconds > 60:
                    bucket_timestamp = int(time_bucket.timestamp() / interval_seconds) * interval_seconds
                    aligned_bucket = datetime.fromtimestamp(bucket_timestamp, tz=timezone.utc)
                else:
                    aligned_bucket = time_bucket

                if aligned_bucket in queue_data_map[base_queue]:
                    queue_data_map[base_queue][aligned_bucket] += count

            data = []
            for base_queue in target_queues:
                trend = []
                for bucket in sorted(time_buckets):
                    trend.append({
                        "time": bucket.isoformat(),
                        "task_count": queue_data_map[base_queue][bucket]
                    })

                data.append({
                    "queue_name": base_queue,
                    "trend": trend
                })

            return {
                "success": True,
                "data": data,
                "metrics": ["task_count"],
                "granularity": time_range_result.granularity,
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "interval": time_range_result.interval,
                    "interval_seconds": time_range_result.interval_seconds
                }
            }

        except Exception as e:
            logger.error(f"获取队列任务创建趋势失败: queues={queues}, error={e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "metrics": ["task_count"]
            }

    @classmethod
    async def _query_trend_from_runs_metrics(
        cls,
        pg_session: AsyncSession,
        namespace: str,
        target_queues: List[str],
        all_priority_queues: List[str],
        base_queue_map: Dict[str, str],
        start_time: datetime,
        end_time: datetime,
        interval_seconds: int,
        metrics: List[TrendMetric]
    ) -> List[Dict[str, Any]]:
        select_fields = [
            TaskRunsMetricsMinute.queue,
            TaskRunsMetricsMinute.time_bucket,
        ]

        metric_fields = {}
        for metric in metrics:
            if metric == TrendMetric.TOTAL_COUNT:
                metric_fields['total_count'] = TaskRunsMetricsMinute.total_count
            elif metric == TrendMetric.SUCCESS_COUNT:
                metric_fields['success_count'] = TaskRunsMetricsMinute.success_count
            elif metric == TrendMetric.FAILED_COUNT:
                metric_fields['failed_count'] = TaskRunsMetricsMinute.failed_count
            elif metric == TrendMetric.RETRY_COUNT:
                metric_fields['retry_count'] = TaskRunsMetricsMinute.retry_count
            elif metric in [TrendMetric.AVG_DURATION, TrendMetric.MAX_DURATION, TrendMetric.MIN_DURATION]:
                metric_fields['total_duration'] = TaskRunsMetricsMinute.total_duration
                metric_fields['max_duration'] = TaskRunsMetricsMinute.max_duration
                metric_fields['min_duration'] = TaskRunsMetricsMinute.min_duration
                if 'total_count' not in metric_fields:
                    metric_fields['total_count'] = TaskRunsMetricsMinute.total_count
            elif metric in [TrendMetric.AVG_DELAY, TrendMetric.MAX_DELAY, TrendMetric.MIN_DELAY]:
                metric_fields['total_delay'] = TaskRunsMetricsMinute.total_delay
                metric_fields['max_delay'] = TaskRunsMetricsMinute.max_delay
                metric_fields['min_delay'] = TaskRunsMetricsMinute.min_delay
                if 'total_count' not in metric_fields:
                    metric_fields['total_count'] = TaskRunsMetricsMinute.total_count
            elif metric == TrendMetric.MAX_CONCURRENCY:
                metric_fields['running_concurrency'] = TaskRunsMetricsMinute.running_concurrency
            elif metric == TrendMetric.SUCCESS_RATE:
                if 'success_count' not in metric_fields:
                    metric_fields['success_count'] = TaskRunsMetricsMinute.success_count
                if 'failed_count' not in metric_fields:
                    metric_fields['failed_count'] = TaskRunsMetricsMinute.failed_count

        for field in metric_fields.values():
            select_fields.append(field)

        stmt = select(*select_fields).where(
            and_(
                TaskRunsMetricsMinute.namespace == namespace,
                TaskRunsMetricsMinute.queue.in_(all_priority_queues),
                TaskRunsMetricsMinute.time_bucket >= start_time,
                TaskRunsMetricsMinute.time_bucket <= end_time
            )
        ).order_by(
            TaskRunsMetricsMinute.queue,
            TaskRunsMetricsMinute.time_bucket
        )

        result = await pg_session.execute(stmt)
        rows = result.fetchall()

        time_buckets = []
        if interval_seconds > 60:
            start_timestamp = int(start_time.timestamp() / interval_seconds) * interval_seconds
            current = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)
            end_timestamp = int(end_time.timestamp() / interval_seconds) * interval_seconds
            end_aligned = datetime.fromtimestamp(end_timestamp, tz=timezone.utc)
        else:
            current = start_time.replace(second=0, microsecond=0)
            end_aligned = end_time.replace(second=0, microsecond=0)

        while current <= end_aligned:
            time_buckets.append(current)
            current += timedelta(seconds=interval_seconds)

        queue_data_map = {}
        for base_queue in target_queues:
            queue_data_map[base_queue] = {}
            for bucket in time_buckets:
                queue_data_map[base_queue][bucket] = cls._init_metric_values(metrics)

        for row in rows:
            priority_queue = row.queue
            base_queue = base_queue_map.get(priority_queue)
            if not base_queue or base_queue not in queue_data_map:
                continue

            time_bucket = row.time_bucket

            if interval_seconds > 60:
                bucket_timestamp = int(time_bucket.timestamp() / interval_seconds) * interval_seconds
                aligned_bucket = datetime.fromtimestamp(bucket_timestamp, tz=timezone.utc)
            else:
                aligned_bucket = time_bucket

            if aligned_bucket not in queue_data_map[base_queue]:
                continue

            bucket_data = queue_data_map[base_queue][aligned_bucket]
            cls._aggregate_metric_row(bucket_data, row, metric_fields, metrics)

        data = []
        for base_queue in target_queues:
            trend = []
            for bucket in sorted(time_buckets):
                bucket_data = queue_data_map[base_queue][bucket]
                point = {"time": bucket.isoformat()}

                for metric in metrics:
                    if metric == TrendMetric.TOTAL_COUNT:
                        point["total_count"] = bucket_data.get("_total_count", 0)
                    elif metric == TrendMetric.SUCCESS_COUNT:
                        point["success_count"] = bucket_data.get("_success_count", 0)
                    elif metric == TrendMetric.FAILED_COUNT:
                        point["failed_count"] = bucket_data.get("_failed_count", 0)
                    elif metric == TrendMetric.RETRY_COUNT:
                        point["retry_count"] = bucket_data.get("_retry_count", 0)
                    elif metric == TrendMetric.AVG_DURATION:
                        total_count = bucket_data.get("_total_count", 0)
                        total_duration = bucket_data.get("_total_duration", 0)
                        point["avg_duration"] = round(total_duration / total_count, 4) if total_count > 0 else 0
                    elif metric == TrendMetric.MAX_DURATION:
                        point["max_duration"] = bucket_data.get("_max_duration")
                    elif metric == TrendMetric.MIN_DURATION:
                        point["min_duration"] = bucket_data.get("_min_duration")
                    elif metric == TrendMetric.AVG_DELAY:
                        total_count = bucket_data.get("_total_count", 0)
                        total_delay = bucket_data.get("_total_delay", 0)
                        point["avg_delay"] = round(total_delay / total_count, 4) if total_count > 0 else 0
                    elif metric == TrendMetric.MAX_DELAY:
                        point["max_delay"] = bucket_data.get("_max_delay")
                    elif metric == TrendMetric.MIN_DELAY:
                        point["min_delay"] = bucket_data.get("_min_delay")
                    elif metric == TrendMetric.MAX_CONCURRENCY:
                        point["max_concurrency"] = bucket_data.get("_max_concurrency", 0)
                    elif metric == TrendMetric.SUCCESS_RATE:
                        success = bucket_data.get("_success_count", 0)
                        failed = bucket_data.get("_failed_count", 0)
                        total = success + failed
                        point["success_rate"] = round((success / total) * 100, 2) if total > 0 else 0

                trend.append(point)

            data.append({
                "queue_name": base_queue,
                "trend": trend
            })

        return data

    @staticmethod
    def _init_metric_values(metrics: List[TrendMetric]) -> Dict[str, Any]:
        values = {}
        for metric in metrics:
            if metric in [TrendMetric.TOTAL_COUNT, TrendMetric.AVG_DURATION, TrendMetric.AVG_DELAY]:
                values["_total_count"] = 0
            if metric in [TrendMetric.SUCCESS_COUNT, TrendMetric.SUCCESS_RATE]:
                values["_success_count"] = 0
            if metric in [TrendMetric.FAILED_COUNT, TrendMetric.SUCCESS_RATE]:
                values["_failed_count"] = 0
            if metric == TrendMetric.RETRY_COUNT:
                values["_retry_count"] = 0
            if metric in [TrendMetric.AVG_DURATION, TrendMetric.MAX_DURATION, TrendMetric.MIN_DURATION]:
                values["_total_duration"] = 0.0
                values["_max_duration"] = None
                values["_min_duration"] = None
            if metric in [TrendMetric.AVG_DELAY, TrendMetric.MAX_DELAY, TrendMetric.MIN_DELAY]:
                values["_total_delay"] = 0.0
                values["_max_delay"] = None
                values["_min_delay"] = None
            if metric == TrendMetric.MAX_CONCURRENCY:
                values["_max_concurrency"] = 0
        return values

    @staticmethod
    def _aggregate_metric_row(
        bucket_data: Dict[str, Any],
        row: Any,
        metric_fields: Dict[str, Any],
        metrics: List[TrendMetric]
    ):
        if "total_count" in metric_fields:
            bucket_data["_total_count"] = bucket_data.get("_total_count", 0) + (row.total_count or 0)
        if "success_count" in metric_fields:
            bucket_data["_success_count"] = bucket_data.get("_success_count", 0) + (row.success_count or 0)
        if "failed_count" in metric_fields:
            bucket_data["_failed_count"] = bucket_data.get("_failed_count", 0) + (row.failed_count or 0)
        if "retry_count" in metric_fields:
            bucket_data["_retry_count"] = bucket_data.get("_retry_count", 0) + (row.retry_count or 0)

        if "total_duration" in metric_fields:
            bucket_data["_total_duration"] = bucket_data.get("_total_duration", 0) + (row.total_duration or 0)
        if "total_delay" in metric_fields:
            bucket_data["_total_delay"] = bucket_data.get("_total_delay", 0) + (row.total_delay or 0)

        if "max_duration" in metric_fields and row.max_duration is not None:
            current = bucket_data.get("_max_duration")
            bucket_data["_max_duration"] = max(current, row.max_duration) if current is not None else row.max_duration
        if "max_delay" in metric_fields and row.max_delay is not None:
            current = bucket_data.get("_max_delay")
            bucket_data["_max_delay"] = max(current, row.max_delay) if current is not None else row.max_delay
        if "running_concurrency" in metric_fields:
            bucket_data["_max_concurrency"] = max(bucket_data.get("_max_concurrency", 0), row.running_concurrency or 0)

        if "min_duration" in metric_fields and row.min_duration is not None:
            current = bucket_data.get("_min_duration")
            bucket_data["_min_duration"] = min(current, row.min_duration) if current is not None else row.min_duration
        if "min_delay" in metric_fields and row.min_delay is not None:
            current = bucket_data.get("_min_delay")
            bucket_data["_min_delay"] = min(current, row.min_delay) if current is not None else row.min_delay

    @classmethod
    async def _query_from_aggregation_table(
        cls,
        pg_session: AsyncSession,
        namespace: str,
        queues: List[str],
        start_time: datetime,
        end_time: datetime,
        interval_seconds: int
    ) -> List[Dict[str, Any]]:
        stmt = select(
            TaskMetricsMinute.queue,
            TaskMetricsMinute.time_bucket,
            TaskMetricsMinute.task_count
        ).where(
            and_(
                TaskMetricsMinute.namespace == namespace,
                TaskMetricsMinute.queue.in_(queues),
                TaskMetricsMinute.time_bucket >= start_time,
                TaskMetricsMinute.time_bucket <= end_time
            )
        ).order_by(
            TaskMetricsMinute.queue,
            TaskMetricsMinute.time_bucket
        )

        result = await pg_session.execute(stmt)
        rows = result.fetchall()

        time_buckets = []
        if interval_seconds > 60:
            start_timestamp = int(start_time.timestamp() / interval_seconds) * interval_seconds
            current = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)
            end_timestamp = int(end_time.timestamp() / interval_seconds) * interval_seconds
            end_aligned = datetime.fromtimestamp(end_timestamp, tz=timezone.utc)
        else:
            current = start_time.replace(second=0, microsecond=0)
            end_aligned = end_time.replace(second=0, microsecond=0)

        while current <= end_aligned:
            time_buckets.append(current)
            current += timedelta(seconds=interval_seconds)

        queue_data_map = {}
        for queue_name in queues:
            queue_data_map[queue_name] = {bucket: 0 for bucket in time_buckets}

        for row in rows:
            queue_name = row.queue
            time_bucket = row.time_bucket
            count = row.task_count

            if interval_seconds > 60:
                bucket_timestamp = int(time_bucket.timestamp() / interval_seconds) * interval_seconds
                aligned_bucket = datetime.fromtimestamp(bucket_timestamp, tz=timezone.utc)

                if queue_name in queue_data_map and aligned_bucket in queue_data_map[queue_name]:
                    queue_data_map[queue_name][aligned_bucket] += count
            else:
                if queue_name in queue_data_map and time_bucket in queue_data_map[queue_name]:
                    queue_data_map[queue_name][time_bucket] = count

        data = []
        for queue_name in queues:
            trend = []
            for bucket in sorted(time_buckets):
                trend.append({
                    "time": bucket.isoformat(),
                    "count": queue_data_map[queue_name].get(bucket, 0)
                })

            data.append({
                "queue_name": queue_name,
                "trend": trend
            })

        return data

    @classmethod
    async def _query_from_tasks_table(
        cls,
        pg_session: AsyncSession,
        namespace: str,
        queues: List[str],
        start_time: datetime,
        end_time: datetime,
        interval_seconds: int
    ) -> List[Dict[str, Any]]:
        stmt = select(
            Task.queue,
            Task.created_at
        ).where(
            and_(
                Task.namespace == namespace,
                Task.queue.in_(queues),
                Task.created_at >= start_time,
                Task.created_at <= end_time
            )
        ).order_by(Task.created_at)

        result = await pg_session.execute(stmt)
        tasks = result.fetchall()

        time_buckets = []
        current = start_time
        while current <= end_time:
            time_buckets.append(current)
            current += timedelta(seconds=interval_seconds)

        queue_data_map = {}
        for queue_name in queues:
            queue_data_map[queue_name] = {bucket: 0 for bucket in time_buckets}

        for row in tasks:
            queue_name = row.queue
            created_at = row.created_at

            bucket_timestamp = int(created_at.timestamp() / interval_seconds) * interval_seconds
            bucket = datetime.fromtimestamp(bucket_timestamp, tz=timezone.utc)

            if queue_name in queue_data_map and bucket in queue_data_map[queue_name]:
                queue_data_map[queue_name][bucket] += 1

        data = []
        for queue_name in queues:
            trend = []
            for bucket in sorted(time_buckets):
                trend.append({
                    "time": bucket.isoformat(),
                    "count": queue_data_map[queue_name].get(bucket, 0)
                })

            data.append({
                "queue_name": queue_name,
                "trend": trend
            })

        return data

    @classmethod
    async def get_task_runs_list(
        cls,
        namespace: str,
        pg_session: AsyncSession,
        registry,
        queue: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_range: Optional[str] = None,
        where_clause: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_field: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        from sqlalchemy import desc, asc, text

        try:
            time_range_result = cls._resolve_time_range(
                start_time=start_time,
                end_time=end_time,
                time_range=time_range,
                default_range="1h"
            )
            start_time = time_range_result.start_time
            end_time = time_range_result.end_time

            queue_result = await cls._resolve_queues([queue], registry, expand_priority=True)
            all_priority_queues = queue_result.all_priority_queues

            logger.info(
                f"任务执行记录查询: namespace={namespace}, queue={queue}, "
                f"priority_queues={all_priority_queues}, "
                f"time_range={start_time} to {end_time}, "
                f"where_clause={where_clause}, page={page}, page_size={page_size}"
            )

            if not all_priority_queues:
                return {
                    "success": True,
                    "data": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "time_range": {
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat()
                    }
                }

            if where_clause:
                forbidden_keywords = [
                    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER', 'CREATE',
                    'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'UNION', 'INTO',
                    'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'OFFSET',
                    '--', '/*', '*/', ';'
                ]
                upper_clause = where_clause.upper()
                for keyword in forbidden_keywords:
                    if keyword in upper_clause:
                        raise ValueError(f"WHERE 子句包含不允许的关键字: {keyword}")

            conditions = [
                Task.namespace == namespace,
                Task.queue.in_(all_priority_queues),
                Task.created_at >= start_time,
                Task.created_at <= end_time
            ]

            if where_clause and where_clause.strip():
                conditions.append(text(where_clause.strip()))

            count_stmt = select(func.count(Task.stream_id)).select_from(
                Task
            ).outerjoin(
                TaskRun, Task.stream_id == TaskRun.stream_id
            ).where(and_(*conditions))

            count_result = await pg_session.execute(count_stmt)
            total = count_result.scalar() or 0

            query_stmt = select(
                Task.stream_id,
                Task.queue,
                Task.namespace,
                Task.scheduled_task_id,
                Task.payload,
                Task.priority,
                Task.delay,
                Task.created_at,
                Task.trigger_time,
                Task.source,
                Task.task_metadata,
                TaskRun.task_name,
                TaskRun.status,
                TaskRun.result,
                TaskRun.error,
                TaskRun.started_at,
                TaskRun.completed_at,
                TaskRun.retries,
                TaskRun.duration,
                TaskRun.consumer
            ).select_from(
                Task
            ).outerjoin(
                TaskRun, Task.stream_id == TaskRun.stream_id
            ).where(and_(*conditions))

            sort_column = None
            if sort_field in ['stream_id', 'queue', 'namespace', 'priority', 'delay',
                              'created_at', 'trigger_time', 'source']:
                sort_column = getattr(Task, sort_field, None)
            elif sort_field in ['task_name', 'status', 'started_at', 'completed_at',
                                'retries', 'duration', 'consumer']:
                sort_column = getattr(TaskRun, sort_field, None)

            if sort_column is not None:
                if sort_order.lower() == 'desc':
                    query_stmt = query_stmt.order_by(desc(sort_column))
                else:
                    query_stmt = query_stmt.order_by(asc(sort_column))
            else:
                query_stmt = query_stmt.order_by(desc(Task.created_at))

            offset = (page - 1) * page_size
            query_stmt = query_stmt.offset(offset).limit(page_size)

            result = await pg_session.execute(query_stmt)
            rows = result.fetchall()

            data = []
            for row in rows:
                record = {
                    "stream_id": row.stream_id,
                    "namespace": row.namespace,
                    "scheduled_task_id": row.scheduled_task_id,
                    "payload": row.payload,
                    "priority": row.priority,
                    "delay": row.delay,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "trigger_time": row.trigger_time,
                    "source": row.source,
                    "metadata": row.task_metadata,
                    "task_name": row.task_name,
                    "status": row.status,
                    "result": row.result,
                    "error": row.error,
                    "started_at": row.started_at,
                    "completed_at": row.completed_at,
                    "retries": row.retries,
                    "duration": row.duration,
                    "consumer": row.consumer
                }
                data.append(record)

            return {
                "success": True,
                "data": data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "queue": queue,  
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"获取任务执行记录失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "total": 0,
                "page": page,
                "page_size": page_size
            }
