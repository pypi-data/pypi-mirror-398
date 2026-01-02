"""
概览服务层
处理系统概览和健康检查相关的业务逻辑
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import logging
import time
import traceback
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from jettask.schemas import TimeRangeQuery
from jettask.db.connector import get_async_redis_client, get_pg_engine_and_factory
from jettask.webui.services.base_service import BaseService, TimeRangeResult

logger = logging.getLogger(__name__)



class OverviewService(BaseService):
    """概览服务类"""
    
    @staticmethod
    def get_root_info() -> Dict[str, Any]:
        return {
            "success": True,
            "data": {
                "service": "JetTask WebUI API",
                "version": "v1",
                "status": "running",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    @staticmethod
    def get_health_status() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    async def get_system_stats(namespace: str) -> Dict[str, Any]:
        import os
        redis_url = os.environ.get('JETTASK_REDIS_URL', 'redis://localhost:6379/0')
        redis_client = get_async_redis_client(redis_url, decode_responses=True)
        
        try:
            stats = {
                'namespace': namespace,
                'queues': 0,
                'tasks': 0,
                'delayed_tasks': 0,
                'workers': 0
            }
            
            from jettask.messaging.registry import QueueRegistry
            from jettask.task.task_registry import TaskRegistry
            from jettask.worker.lifecycle import WorkerManager as WorkerRegistry

            sync_redis_client = get_sync_redis_client(redis_url, decode_responses=True)

            queue_registry = QueueRegistry(
                redis_client=sync_redis_client,
                async_redis_client=redis_client,
                redis_prefix=namespace
            )

            task_registry = TaskRegistry(
                redis_client=None,
                async_redis_client=redis_client,
                redis_prefix=namespace
            )

            worker_registry = WorkerRegistry(
                redis_client=None,
                async_redis_client=redis_client,
                redis_prefix=namespace
            )

            stats['queues'] = await queue_registry.get_queue_count()

            stats['tasks'] = await task_registry.get_task_count_from_redis()

            stats['delayed_tasks'] = 0

            stats['workers'] = await worker_registry.get_worker_count()
            
            return stats
            
        finally:
            await redis_client.aclose()
    
    @staticmethod
    async def get_dashboard_stats(
        namespace: str,
        time_range: str = "24h",
        queues: Optional[str] = None
    ) -> Dict[str, Any]:
        import os

        pg_url = os.environ.get('JETTASK_PG_URL')
        if not pg_url:
            return {
                "success": True,
                "data": _get_empty_dashboard_stats()
            }

        end_time = datetime.now(timezone.utc)
        start_time = BaseService._parse_time_range(time_range, end_time)

        queue_filter, queue_list, queue_params = _build_queue_filter_and_params(queues)

        _, session_factory = get_pg_engine_and_factory(pg_url)
        async with session_factory() as session:
            stats_data = await _get_task_statistics(
                session, namespace, start_time, end_time,
                queue_filter, queue_params
            )
            
            throughput = await _calculate_throughput(
                session, namespace, queue_filter, queue_params
            )
            
            distribution_params = {
                'namespace': namespace,
                'start_time': start_time,
                'end_time': end_time,
                **queue_params
            }
            distribution_data = await _get_task_distribution(
                session, namespace, start_time, end_time,
                queue_filter, distribution_params
            )
            
            return {
                "success": True,
                "data": {
                    **stats_data,
                    "throughput": throughput,
                    "distribution": distribution_data
                }
            }
    
    @staticmethod
    async def get_top_queues(
        namespace: str,
        metric: str = "backlog",
        limit: int = 10,
        time_range: str = "24h",
        queues: Optional[str] = None
    ) -> Dict[str, Any]:
        if metric == "backlog":
            return await _get_top_backlog_queues(namespace, limit, time_range, queues)
        elif metric == "error":
            return await _get_top_error_queues(namespace, limit, time_range, queues)
        else:
            raise ValueError(f"不支持的指标类型: {metric}")
    
    @staticmethod
    async def get_dashboard_overview_stats(
        namespace: str,
        query: TimeRangeQuery
    ) -> Dict[str, Any]:
        import os

        pg_url = os.environ.get('JETTASK_PG_URL')
        if not pg_url:
            return _get_empty_overview_stats()

        time_range_result = BaseService._parse_time_range_query(query)

        queue_list = query.queues if hasattr(query, 'queues') and query.queues else None
        queue_filter, _, queue_params = _build_queue_filter_and_params(queue_list)

        _, session_factory = get_pg_engine_and_factory(pg_url)
        async with session_factory() as session:
            result = await _execute_overview_query(
                session, namespace, time_range_result,
                queue_filter, queue_params
            )
            
            return _format_overview_data(result, time_range_result.granularity)



def _build_queue_filter_and_params(queues: Optional[List[str]] = None):
    queue_list = []
    if queues:
        if isinstance(queues, str):
            queue_list = [q.strip() for q in queues.split(',') if q.strip()]
        elif isinstance(queues, list):
            queue_list = [q.strip() for q in queues if q and q.strip()]
        else:
            queue_list = []
    
    queue_filter = ""
    queue_params = {}
    
    if queue_list:
        queue_placeholders = ','.join([f':queue_{i}' for i in range(len(queue_list))])
        queue_filter = f"AND t.queue IN ({queue_placeholders})"
        
        for i, queue in enumerate(queue_list):
            queue_params[f'queue_{i}'] = queue
    
    return queue_filter, queue_list, queue_params


def _get_empty_dashboard_stats():
    return {
        "total_tasks": 0,
        "completed_tasks": 0,
        "failed_tasks": 0,
        "running_tasks": 0,
        "pending_tasks": 0,
        "success_rate": 0,
        "throughput": 0,
        "avg_processing_time": 0,
        "total_queues": 0,
        "distribution": [{'type': '暂无数据', 'value': 1, 'queue': '', 'status': 'empty'}]
    }


def _get_empty_overview_stats():
    return {
        "task_trend": [],
        "concurrency": [],
        "processing_time": [],
        "creation_latency": [],
        "granularity": "minute"
    }


async def _get_task_statistics(session, namespace, start_time, end_time, queue_filter, queue_params):
    stats_sql = text(f"""
        WITH task_stats AS (
            SELECT 
                t.stream_id,
                t.created_at,
                t.queue,
                tr.status,
                tr.execution_time,
                tr.end_time
            FROM tasks t
            LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
                AND t.trigger_time = tr.trigger_time  -- 利用分区剪枝
            WHERE t.namespace = :namespace
                AND t.created_at >= :start_time
                AND t.created_at <= :end_time
                {queue_filter}
        )
        SELECT 
            COUNT(DISTINCT stream_id) as total_tasks,
            COUNT(DISTINCT CASE WHEN status = 'success' THEN stream_id END) as completed_tasks,
            COUNT(DISTINCT CASE WHEN status = 'error' THEN stream_id END) as failed_tasks,
            COUNT(DISTINCT CASE WHEN status = 'running' THEN stream_id END) as running_tasks,
            COUNT(DISTINCT CASE WHEN status IS NULL OR status = 'pending' THEN stream_id END) as pending_tasks,
            COUNT(DISTINCT queue) as total_queues,
            AVG(CASE WHEN status = 'success' AND execution_time IS NOT NULL 
                THEN execution_time END) as avg_execution_time
        FROM task_stats
    """)
    
    all_params = {
        'namespace': namespace,
        'start_time': start_time,
        'end_time': end_time,
        **queue_params
    }
    
    result = await session.execute(stats_sql, all_params)
    row = result.first()
    
    if row:
        avg_execution_time = row.avg_execution_time or 0
        success_rate = round((row.completed_tasks / row.total_tasks * 100) if row.total_tasks > 0 else 0, 1)
        
        return {
            "total_tasks": row.total_tasks or 0,
            "completed_tasks": row.completed_tasks or 0,
            "failed_tasks": row.failed_tasks or 0,
            "running_tasks": row.running_tasks or 0,
            "pending_tasks": row.pending_tasks or 0,
            "success_rate": success_rate,
            "avg_processing_time": round(avg_execution_time * 1000 if avg_execution_time else 0, 1),
            "total_queues": row.total_queues or 0
        }
    
    return _get_empty_dashboard_stats()


async def _calculate_throughput(session, namespace, queue_filter, queue_params):
    recent_end_time = datetime.now(timezone.utc)
    throughput = 0
    
    time_windows = [
        (5, "最近5分钟"),
        (10, "最近10分钟"), 
        (30, "最近30分钟"),
        (60, "最近1小时")
    ]
    
    for window_minutes, window_desc in time_windows:
        recent_start_time = recent_end_time - timedelta(minutes=window_minutes)
        
        recent_query = text(f"""
            SELECT COUNT(DISTINCT t.stream_id) as recent_completed
            FROM tasks t
            LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
                AND t.trigger_time = tr.trigger_time  -- 利用分区剪枝
            WHERE t.namespace = :namespace
                AND tr.status = 'success'
                AND tr.end_time >= :recent_start_time
                AND tr.end_time <= :recent_end_time
                {queue_filter}
        """)
        
        throughput_params = {
            'namespace': namespace,
            'recent_start_time': recent_start_time,
            'recent_end_time': recent_end_time,
            **queue_params
        }
        
        recent_result = await session.execute(recent_query, throughput_params)
        recent_row = recent_result.first()
        recent_completed = recent_row.recent_completed if recent_row else 0
        
        if recent_completed >= 5:
            throughput = round(recent_completed / window_minutes, 1)
            logger.info(f"使用{window_desc}计算吞吐量: {recent_completed}个任务/{window_minutes}分钟 = {throughput}任务/分钟")
            break
        elif recent_completed > 0:
            throughput = round(recent_completed / window_minutes, 1)
    
    return throughput


async def _get_task_distribution(session, namespace, start_time, end_time, queue_filter, query_params):
    distribution_sql = text(f"""
        SELECT 
            t.queue,
            COUNT(DISTINCT t.stream_id) as count
        FROM tasks t
        WHERE t.namespace = :namespace
            AND t.created_at >= :start_time
            AND t.created_at <= :end_time
            {queue_filter}
        GROUP BY t.queue
        ORDER BY count DESC, t.queue
    """)
    
    distribution_result = await session.execute(distribution_sql, query_params)
    
    distribution_data = []
    for row in distribution_result.fetchall():
        if row.count > 0:
            distribution_data.append({
                'type': row.queue,
                'value': row.count,
                'queue': row.queue,
                'status': 'all'
            })
    
    if not distribution_data:
        distribution_data = [
            {'type': '暂无数据', 'value': 1, 'queue': '', 'status': 'empty'}
        ]
    
    return distribution_data


async def _get_top_backlog_queues(namespace, limit, time_range, queues):
    import os

    pg_url = os.environ.get('JETTASK_PG_URL')
    if not pg_url:
        return {"success": True, "data": []}

    end_time = datetime.now(timezone.utc)
    start_time = BaseService._parse_time_range(time_range, end_time)

    _, session_factory = get_pg_engine_and_factory(pg_url)
    async with session_factory() as session:
        return await _get_top_backlog_from_tasks(session, namespace, limit)


async def _get_top_backlog_from_tasks(session, namespace, limit):
    task_sql = text("""
        SELECT 
            t.queue,
            COUNT(DISTINCT t.stream_id) as backlog,
            CASE 
                WHEN COUNT(DISTINCT t.stream_id) > 1000 THEN 'critical'
                WHEN COUNT(DISTINCT t.stream_id) > 500 THEN 'warning'
                ELSE 'normal'
            END as status
        FROM tasks t
        LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
            AND t.trigger_time = tr.trigger_time  -- 利用分区剪枝
        WHERE t.namespace = :namespace
            AND (tr.stream_id IS NULL OR tr.status = 'pending')
            AND t.created_at > NOW() - INTERVAL '24 hour'
        GROUP BY t.queue
        ORDER BY backlog DESC
        LIMIT :limit
    """)
    
    result = await session.execute(task_sql, {
        'namespace': namespace,
        'limit': limit
    })
    
    backlog_queues = []
    for row in result.fetchall():
        backlog_queues.append({
            "queue": row.queue,
            "backlog": int(row.backlog),
            "status": row.status
        })
    
    return {"success": True, "data": backlog_queues}


async def _get_top_error_queues(namespace, limit, time_range, queues):
    import os

    pg_url = os.environ.get('JETTASK_PG_URL')
    if not pg_url:
        return {"success": True, "data": []}

    end_time = datetime.now(timezone.utc)
    start_time = BaseService._parse_time_range(time_range, end_time)

    _, session_factory = get_pg_engine_and_factory(pg_url)
    async with session_factory() as session:
        queue_list = []
        if queues:
            queue_list = [q.strip() for q in queues.split(',') if q.strip()]
        
        if queue_list:
            error_sql = text("""
                WITH queue_stats AS (
                    SELECT
                        t.queue,
                        COUNT(DISTINCT t.stream_id) as total,
                        COUNT(DISTINCT CASE WHEN tr.status = 'error' THEN t.stream_id END) as errors
                    FROM tasks t
                    LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
                        AND t.trigger_time = tr.trigger_time  -- 利用分区剪枝
                    WHERE t.namespace = :namespace
                        AND t.created_at >= :start_time
                        AND t.created_at <= :end_time
                        AND t.queue = ANY(:queues)
                    GROUP BY t.queue
                )
                SELECT 
                    queue,
                    errors,
                    total,
                    CASE 
                        WHEN total > 0 THEN ROUND(errors::numeric / total * 100, 1)
                        ELSE 0 
                    END as error_rate
                FROM queue_stats
                WHERE errors > 0
                ORDER BY error_rate DESC, errors DESC
                LIMIT :limit
            """)
            
            result = await session.execute(error_sql, {
                'namespace': namespace,
                'start_time': start_time,
                'end_time': end_time,
                'queues': queue_list,
                'limit': limit
            })
        else:
            error_sql = text("""
                WITH queue_stats AS (
                    SELECT
                        t.queue,
                        COUNT(DISTINCT t.stream_id) as total,
                        COUNT(DISTINCT CASE WHEN tr.status = 'error' THEN t.stream_id END) as errors
                    FROM tasks t
                    LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
                        AND t.trigger_time = tr.trigger_time  -- 利用分区剪枝
                    WHERE t.namespace = :namespace
                        AND t.created_at >= :start_time
                        AND t.created_at <= :end_time
                    GROUP BY t.queue
                )
                SELECT
                    queue,
                    errors,
                    total,
                    CASE
                        WHEN total > 0 THEN ROUND(errors::numeric / total * 100, 1)
                        ELSE 0
                    END as error_rate
                FROM queue_stats
                WHERE errors > 0
                ORDER BY error_rate DESC, errors DESC
                LIMIT :limit
            """)
            
            result = await session.execute(error_sql, {
                'namespace': namespace,
                'start_time': start_time,
                'end_time': end_time,
                'limit': limit
            })
        
        error_queues = []
        for row in result.fetchall():
            error_queues.append({
                "queue": row.queue,
                "errors": int(row.errors),
                "total": int(row.total),
                "error_rate": float(row.error_rate)
            })
        
        return {"success": True, "data": error_queues}


async def _execute_overview_query(session, namespace, time_range_result, queue_filter, queue_params):
    interval_seconds = time_range_result.interval_seconds
    
    sql = text(f"""
        WITH time_series AS (
            SELECT to_timestamp(FLOOR(EXTRACT(epoch FROM ts) / {interval_seconds}) * {interval_seconds}) AS time_bucket
            FROM generate_series(
                :start_time ::timestamptz,
                :end_time ::timestamptz + INTERVAL '{interval_seconds} seconds',
                INTERVAL '{interval_seconds} seconds'
            ) AS ts
        ),
        enqueue_counts AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM t.created_at) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                COUNT(DISTINCT t.stream_id) as enqueued
            FROM tasks t
            WHERE t.namespace = :namespace
                AND t.created_at >= :start_time
                AND t.created_at <= :end_time
                {queue_filter}
            GROUP BY time_bucket
        ),
        complete_counts AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM tr.end_time) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                COUNT(DISTINCT t.stream_id) as completed
            FROM task_runs tr
            JOIN tasks t ON tr.stream_id = t.stream_id
            WHERE t.namespace = :namespace
                AND tr.end_time >= :start_time
                AND tr.end_time <= :end_time
                AND tr.status = 'success'
                AND t.created_at >= :start_time
                AND t.created_at <= :end_time
                {queue_filter}
            GROUP BY time_bucket
        ),
        failed_counts AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM tr.end_time) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                COUNT(DISTINCT t.stream_id) as failed
            FROM task_runs tr
            JOIN tasks t ON tr.stream_id = t.stream_id
            WHERE t.namespace = :namespace
                AND tr.end_time >= :start_time
                AND tr.end_time <= :end_time
                AND tr.status = 'error'
                AND t.created_at >= :start_time
                AND t.created_at <= :end_time
                {queue_filter}
            GROUP BY time_bucket
        ),
        concurrency_data AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM tr.start_time) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                COUNT(DISTINCT t.stream_id) as concurrent_tasks
            FROM task_runs tr
            JOIN tasks t ON tr.stream_id = t.stream_id
            WHERE t.namespace = :namespace
                AND tr.start_time >= :start_time
                AND tr.start_time <= :end_time
                AND tr.start_time IS NOT NULL
                AND tr.end_time IS NOT NULL
                AND t.created_at >= :start_time
                AND t.created_at <= :end_time
                {queue_filter}
            GROUP BY time_bucket
        ),
        processing_time_data AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM tr.end_time) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                AVG(CASE WHEN tr.status = 'success' AND tr.execution_time > 0 
                    THEN tr.execution_time END) as avg_processing_time,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY 
                    CASE WHEN tr.status = 'success' AND tr.execution_time > 0 
                    THEN tr.execution_time END) as p50_processing_time,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY 
                    CASE WHEN tr.status = 'success' AND tr.execution_time > 0 
                    THEN tr.execution_time END) as p90_processing_time
            FROM task_runs tr
            JOIN tasks t ON tr.stream_id = t.stream_id
            WHERE t.namespace = :namespace
                AND tr.end_time >= :start_time
                AND tr.end_time <= :end_time
                AND tr.status = 'success'
                {queue_filter}
            GROUP BY time_bucket
        ),
        creation_latency_data AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM tr.start_time) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                AVG(EXTRACT(EPOCH FROM (tr.start_time - t.created_at))) as avg_creation_latency,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY 
                    EXTRACT(EPOCH FROM (tr.start_time - t.created_at))) as p50_creation_latency,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY 
                    EXTRACT(EPOCH FROM (tr.start_time - t.created_at))) as p90_creation_latency
            FROM task_runs tr
            JOIN tasks t ON tr.stream_id = t.stream_id
            WHERE t.namespace = :namespace
                AND tr.start_time >= :start_time
                AND tr.start_time <= :end_time
                AND tr.start_time IS NOT NULL
                {queue_filter}
            GROUP BY time_bucket
        )
        SELECT 
            ts.time_bucket,
            COALESCE(eq.enqueued, 0) as enqueued,
            COALESCE(cc.completed, 0) as completed,
            COALESCE(fc.failed, 0) as failed,
            COALESCE(cd.concurrent_tasks, 0) as concurrent_tasks,
            ROUND(ptd.avg_processing_time::numeric, 6) as avg_processing_time,
            ROUND(ptd.p50_processing_time::numeric, 6) as p50_processing_time,
            ROUND(ptd.p90_processing_time::numeric, 6) as p90_processing_time,
            ROUND(cld.avg_creation_latency::numeric, 3) as avg_creation_latency,
            ROUND(cld.p50_creation_latency::numeric, 3) as p50_creation_latency,
            ROUND(cld.p90_creation_latency::numeric, 3) as p90_creation_latency
        FROM time_series ts
        LEFT JOIN enqueue_counts eq ON ts.time_bucket = eq.time_bucket
        LEFT JOIN complete_counts cc ON ts.time_bucket = cc.time_bucket
        LEFT JOIN failed_counts fc ON ts.time_bucket = fc.time_bucket
        LEFT JOIN concurrency_data cd ON ts.time_bucket = cd.time_bucket
        LEFT JOIN processing_time_data ptd ON ts.time_bucket = ptd.time_bucket
        LEFT JOIN creation_latency_data cld ON ts.time_bucket = cld.time_bucket
        ORDER BY ts.time_bucket
    """)
    
    query_params = {
        'namespace': namespace,
        'start_time': time_range_result.start_time,
        'end_time': time_range_result.end_time,
        **queue_params
    }
    
    result = await session.execute(sql, query_params)
    return result.fetchall()


def _format_overview_data(rows, granularity):
    task_trend = []
    concurrency = []
    processing_time = []
    creation_latency = []
    
    end_index = len(rows) - 1
    
    for idx, row in enumerate(rows):
        time_str = row.time_bucket.isoformat()
        
        enqueued_val = row.enqueued if row.enqueued > 0 or idx == 0 or idx == end_index else None
        completed_val = row.completed if row.completed > 0 or idx == 0 or idx == end_index else None
        failed_val = row.failed if row.failed > 0 or idx == 0 or idx == end_index else None
        
        task_trend.extend([
            {'time': time_str, 'value': enqueued_val, 'metric': '入队速率'},
            {'time': time_str, 'value': completed_val, 'metric': '完成速率'},
            {'time': time_str, 'value': failed_val, 'metric': '失败数'}
        ])
        
        concurrency.append({
            'time': time_str,
            'value': row.concurrent_tasks or 0,
            'metric': '并发任务数'
        })
        
        _add_processing_time_data(processing_time, time_str, row, idx, end_index)
        
        _add_creation_latency_data(creation_latency, time_str, row, idx, end_index)
    
    return {
        "task_trend": task_trend,
        "concurrency": concurrency,
        "processing_time": processing_time,
        "creation_latency": creation_latency,
        "granularity": granularity
    }


def _add_processing_time_data(processing_time, time_str, row, idx, end_index):
    if row.avg_processing_time is not None:
        avg_time_val = round(float(row.avg_processing_time * 1000), 1)
    else:
        avg_time_val = None if idx != 0 and idx != end_index else 0
        
    if row.p50_processing_time is not None:
        p50_time_val = round(float(row.p50_processing_time * 1000), 1)
    else:
        p50_time_val = None if idx != 0 and idx != end_index else 0
        
    if row.p90_processing_time is not None:
        p90_time_val = round(float(row.p90_processing_time * 1000), 1)
    else:
        p90_time_val = None if idx != 0 and idx != end_index else 0
    
    processing_time.extend([
        {'time': time_str, 'value': avg_time_val, 'metric': '平均处理时间'},
        {'time': time_str, 'value': p50_time_val, 'metric': 'P50处理时间'},
        {'time': time_str, 'value': p90_time_val, 'metric': 'P90处理时间'}
    ])


def _add_creation_latency_data(creation_latency, time_str, row, idx, end_index):
    if row.avg_creation_latency is not None:
        avg_latency_val = round(float(row.avg_creation_latency), 3)
    else:
        avg_latency_val = None if idx != 0 and idx != end_index else 0
        
    if row.p50_creation_latency is not None:
        p50_latency_val = round(float(row.p50_creation_latency), 3)
    else:
        p50_latency_val = None if idx != 0 and idx != end_index else 0
        
    if row.p90_creation_latency is not None:
        p90_latency_val = round(float(row.p90_creation_latency), 3)
    else:
        p90_latency_val = None if idx != 0 and idx != end_index else 0
    
    creation_latency.extend([
        {'time': time_str, 'value': avg_latency_val, 'metric': '平均执行延时'},
        {'time': time_str, 'value': p50_latency_val, 'metric': 'P50执行延时'},
        {'time': time_str, 'value': p90_latency_val, 'metric': 'P90执行延时'}
    ])