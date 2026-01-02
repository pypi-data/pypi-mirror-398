"""
队列统计API v2 - 支持消费者组和优先级队列
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from collections import defaultdict
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from jettask.config.constants import is_internal_consumer

logger = logging.getLogger(__name__)


class QueueStatsV2:
    """队列统计服务V2 - 支持消费者组详情"""
    
    def __init__(self, redis_client: redis.Redis, pg_session: Optional[AsyncSession] = None, redis_prefix: str = "default"):
        self.redis_client = redis_client
        self.pg_session = pg_session
        self.redis_prefix = redis_prefix
    
    async def get_queue_stats_grouped(self, time_filter: Optional[Dict[str, Any]] = None) -> List[dict]:
        flat_stats = await self.get_queue_stats_with_groups(time_filter)
        
        return await self._transform_to_grouped_format(flat_stats)
    
    async def get_queue_stats_with_groups(self, time_filter: Optional[Dict[str, Any]] = None) -> List[dict]:
        try:
            all_stats = await self._get_queue_structure_from_redis()
            
            if not all_stats:
                return []
            
            await self._enrich_with_db_stats(all_stats, time_filter)
            
            all_stats.sort(key=lambda x: (
                x['base_queue_name'],
                x['priority'] if x['priority'] is not None else 999,
                x['group_name'] or ''
            ))
            
            return all_stats
            
        except Exception as e:
            logger.error(f"获取队列统计信息失败: {e}")
            raise
    
    async def _get_queue_structure_from_redis(self) -> List[dict]:
        try:
            queue_pattern = f"{self.redis_prefix}:QUEUE:*"
            queue_keys = await self.redis_client.keys(queue_pattern)
            if not queue_keys:
                return []
            
            pipe = self.redis_client.pipeline()
            for queue_key in queue_keys:
                pipe.xinfo_groups(queue_key)
            
            try:
                groups_results = await pipe.execute()
            except redis.ResponseError:
                groups_results = []
                for queue_key in queue_keys:
                    try:
                        result = await self.redis_client.xinfo_groups(queue_key)
                        groups_results.append(result)
                    except redis.ResponseError:
                        groups_results.append([])
            all_stats = []
            for i, queue_key in enumerate(queue_keys):
                if isinstance(queue_key, bytes):
                    queue_key_str = queue_key.decode('utf-8')
                else:
                    queue_key_str = queue_key
                
                queue_name = queue_key_str.replace(f"{self.redis_prefix}:QUEUE:", "")
                
                base_queue_name = self._get_base_queue_name(queue_name)
                priority = self._extract_priority(queue_name)
                
                groups_info = groups_results[i] if i < len(groups_results) else []
                
                if groups_info:
                    for group in groups_info:
                        group_name = group.get('name', group.get(b'name', ''))
                        if isinstance(group_name, bytes):
                            group_name = group_name.decode('utf-8')
                        
                        if is_internal_consumer(group_name):
                            continue
                        
                        consumers_count = group.get('consumers', group.get(b'consumers', 0))
                        pending_count = group.get('pending', group.get(b'pending', 0))
                        
                        last_delivered_id = group.get('last-delivered-id', group.get(b'last-delivered-id', ''))
                        if isinstance(last_delivered_id, bytes):
                            last_delivered_id = last_delivered_id.decode('utf-8')
                        
                        if last_delivered_id == '0-0':
                            continue
                        
                        task_name = self._extract_task_name(group_name)
                        
                        stat_record = {
                            'base_queue_name': base_queue_name,
                            'full_queue_name': queue_name,
                            'priority': priority,
                            'queue_length': 0,  
                            'group_name': group_name,
                            'task_name': task_name,
                            'consumers': consumers_count,
                            'pending': pending_count,
                            'last_delivered_id': last_delivered_id,
                            'visible_messages': 0,  
                            'invisible_messages': pending_count,
                            'success_count': 0,  
                            'failed_count': 0,  
                            'success_rate': 0.0,
                            'processing_rate': 0.0,
                            'avg_execution_time': 0.0
                        }
                        
                        all_stats.append(stat_record)
                else:
                    stat_record = {
                        'base_queue_name': base_queue_name,
                        'full_queue_name': queue_name,
                        'priority': priority,
                        'queue_length': 0,  
                        'group_name': None,
                        'task_name': None,
                        'consumers': 0,
                        'pending': 0,
                        'last_delivered_id': None,
                        'visible_messages': 0,
                        'invisible_messages': 0,
                        'success_count': 0,
                        'failed_count': 0,
                        'success_rate': 0.0,
                        'processing_rate': 0.0,
                        'avg_execution_time': 0.0
                    }
                    all_stats.append(stat_record)
            
            return all_stats
            
        except Exception as e:
            logger.error(f"从Redis获取队列结构失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    async def _enrich_with_db_stats(self, stats: List[dict], time_filter: Optional[Dict[str, Any]] = None):
        if not self.pg_session or not stats:
            return
        
        try:
            unique_queues = list(set(stat['full_queue_name'] for stat in stats))
            unique_groups = list(set(stat['group_name'] for stat in stats if stat['group_name']))
            
            if not unique_queues:
                return
            
            time_clause = ""
            params = {
                'namespace': self.redis_prefix,
                'queues': unique_queues
            }
            
            if unique_groups:
                params['groups'] = unique_groups
            
            if time_filter:
                if 'start_time' in time_filter:
                    time_clause += " AND t.created_at >= :start_time"
                    params['start_time'] = time_filter['start_time']
                if 'end_time' in time_filter:
                    time_clause += " AND t.created_at <= :end_time"
                    params['end_time'] = time_filter['end_time']
            
            query = text(f"""
                WITH base_data AS (
                    -- 获取所有任务及其运行状态
                    SELECT
                        t.queue,
                        t.stream_id,
                        tr.consumer_group,
                        tr.status,
                        tr.duration,
                        tr.end_time,
                        CASE WHEN tr.stream_id IS NULL THEN 1 ELSE 0 END as is_unprocessed
                    FROM tasks t
                    LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
                        AND t.trigger_time = tr.trigger_time  -- 利用分区剪枝
                    WHERE t.namespace = :namespace
                        AND t.queue = ANY(:queues) {time_clause}
                ),
                group_stats AS (
                    -- 按队列和消费者组分组统计
                    SELECT 
                        queue,
                        consumer_group,
                        COUNT(DISTINCT stream_id) as total_tasks,
                        SUM(is_unprocessed) as unprocessed_count,
                        COUNT(DISTINCT CASE WHEN status IS NOT NULL THEN stream_id END) as processed_tasks,
                        COUNT(DISTINCT CASE WHEN status = 'pending' THEN stream_id END) as pending_in_runs,
                        COUNT(DISTINCT CASE WHEN status = 'success' THEN stream_id END) as success_count,
                        COUNT(DISTINCT CASE WHEN status = 'error' THEN stream_id END) as error_count,
                        AVG(CASE WHEN status = 'success' AND duration IS NOT NULL THEN duration END) as avg_execution_time,
                        COUNT(DISTINCT CASE WHEN status = 'success' AND end_time >= NOW() - INTERVAL '1 minute' THEN stream_id END) as recent_completed
                    FROM base_data
                    WHERE consumer_group IS NOT NULL
                    GROUP BY queue, consumer_group
                ),
                queue_totals AS (
                    -- 获取每个队列的总体统计（包括未处理的任务）
                    SELECT 
                        queue,
                        COUNT(DISTINCT stream_id) as queue_total_tasks,
                        SUM(is_unprocessed) as queue_unprocessed_tasks
                    FROM base_data
                    GROUP BY queue
                )
                -- 合并结果
                SELECT 
                    gs.queue,
                    gs.consumer_group,
                    COALESCE(qt.queue_total_tasks, gs.total_tasks) as total_tasks,
                    gs.processed_tasks,
                    COALESCE(qt.queue_unprocessed_tasks, 0) as unprocessed_tasks,
                    gs.pending_in_runs,
                    gs.success_count,
                    gs.error_count,
                    gs.avg_execution_time,
                    gs.recent_completed
                FROM group_stats gs
                LEFT JOIN queue_totals qt ON gs.queue = qt.queue
                
                UNION ALL
                
                -- 对于没有消费者组的队列，返回未处理任务的统计
                SELECT 
                    queue,
                    NULL as consumer_group,
                    queue_total_tasks as total_tasks,
                    0 as processed_tasks,
                    queue_unprocessed_tasks as unprocessed_tasks,
                    0 as pending_in_runs,
                    0 as success_count,
                    0 as error_count,
                    NULL as avg_execution_time,
                    0 as recent_completed
                FROM queue_totals
                WHERE queue_unprocessed_tasks > 0
            """)
            
            result = await self.pg_session.execute(query, params)
            db_stats = {}
            for row in result:
                if row.consumer_group:
                    key = f"{row.queue}|{row.consumer_group}"
                else:
                    key = f"{row.queue}|NONE"
                db_stats[key] = row
            
            for stat in stats:
                if stat['group_name']:
                    key = f"{stat['full_queue_name']}|{stat['group_name']}"
                else:
                    key = f"{stat['full_queue_name']}|NONE"
                
                if key in db_stats:
                    row = db_stats[key]
                    stat['queue_length'] = row.total_tasks or 0
                    stat['success_count'] = row.success_count or 0
                    stat['failed_count'] = row.error_count or 0
                    stat['avg_execution_time'] = float(row.avg_execution_time or 0)
                    stat['processing_rate'] = row.recent_completed or 0
                    
                    total = stat['success_count'] + stat['failed_count']
                    if total > 0:
                        stat['success_rate'] = round((stat['success_count'] / total) * 100, 2)
                    
                    unprocessed_tasks = row.unprocessed_tasks or 0  
                    pending_in_runs = row.pending_in_runs or 0      
                    redis_pending = stat['pending']                  
                    
                    stat['visible_messages'] = unprocessed_tasks + max(0, pending_in_runs - redis_pending)
                    
        except Exception as e:
            logger.error(f"从数据库补充统计信息失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    
    async def _get_active_workers_for_queue(self, base_queue_name: str) -> int:
        try:
            import time
            active_workers = 0
            
            worker_pattern = f"{self.redis_prefix}:WORKER:*"
            worker_keys = await self.redis_client.keys(worker_pattern)
            
            for worker_key in worker_keys:
                try:
                    worker_info = await self.redis_client.hgetall(worker_key)
                    if worker_info:
                        last_heartbeat = worker_info.get(b'last_heartbeat', worker_info.get('last_heartbeat'))
                        if last_heartbeat:
                            if isinstance(last_heartbeat, bytes):
                                last_heartbeat = last_heartbeat.decode('utf-8')
                            heartbeat_time = float(last_heartbeat)
                            if time.time() - heartbeat_time < 60:  
                                queues = worker_info.get(b'queues', worker_info.get('queues', ''))
                                if isinstance(queues, bytes):
                                    queues = queues.decode('utf-8')
                                if base_queue_name in queues:
                                    active_workers += 1
                except Exception:
                    continue
                    
            return active_workers
        except Exception as e:
            logger.warning(f"获取活跃workers失败: {e}")
            return 0
    
    async def _transform_to_grouped_format(self, flat_stats: List[dict]) -> List[dict]:
        grouped_data = {}
        
        for stat in flat_stats:
            base_queue_name = stat['base_queue_name']
            
            if base_queue_name not in grouped_data:
                grouped_data[base_queue_name] = {
                    'queue_name': base_queue_name,
                    'consumer_groups': [],
                    'consumer_groups_count': 0,
                    'total_length': 0,
                    'priority_queues': set(),  
                    'total_visible': 0,
                    'total_invisible': 0,
                    'total_success': 0,
                    'total_failed': 0,
                    'active_workers': 0  
                }
            
            if stat['group_name']:
                consumer_group = {
                    'group_name': stat['group_name'],
                    'task_name': stat['task_name'],
                    'queue_name': stat['full_queue_name'],  
                    'priority': stat['priority'],
                    'queue_length': stat['queue_length'],
                    'consumers': stat['consumers'],
                    'pending': stat['pending'],
                    'last_delivered_id': stat['last_delivered_id'],
                    'visible_messages': stat['visible_messages'],
                    'invisible_messages': stat['invisible_messages'],
                    'success_count': stat['success_count'],
                    'failed_count': stat['failed_count'],
                    'success_rate': stat['success_rate'],
                    'processing_rate': stat['processing_rate'],
                    'avg_execution_time': stat['avg_execution_time'],
                    'unique_key': f"{stat['group_name']}_{stat['full_queue_name']}"  
                }
                grouped_data[base_queue_name]['consumer_groups'].append(consumer_group)
                
                grouped_data[base_queue_name]['total_visible'] += stat['visible_messages']
                grouped_data[base_queue_name]['total_invisible'] += stat['invisible_messages']
                grouped_data[base_queue_name]['total_success'] += stat['success_count']
                grouped_data[base_queue_name]['total_failed'] += stat['failed_count']
            
            grouped_data[base_queue_name]['priority_queues'].add(stat['priority'])
            
            if base_queue_name not in grouped_data:
                grouped_data[base_queue_name]['calculated_queues'] = set()
            
            full_queue = stat['full_queue_name']
            if full_queue not in grouped_data[base_queue_name].get('calculated_queues', set()):
                grouped_data[base_queue_name]['total_length'] += stat['queue_length']
                grouped_data[base_queue_name].setdefault('calculated_queues', set()).add(full_queue)
        
        result = []
        for queue_data in grouped_data.values():
            queue_data.pop('calculated_queues', None)
            
            queue_data['priority_queues'] = sorted(list(queue_data['priority_queues']))
            queue_data['consumer_groups_count'] = len(queue_data['consumer_groups'])
            
            queue_data['active_workers'] = await self._get_active_workers_for_queue(queue_data['queue_name'])
            
            total_tasks = queue_data['total_success'] + queue_data['total_failed']
            if total_tasks > 0:
                queue_data['overall_success_rate'] = round(
                    (queue_data['total_success'] / total_tasks) * 100, 2
                )
            else:
                queue_data['overall_success_rate'] = 0.0
            
            result.append(queue_data)
        
        result.sort(key=lambda x: x['queue_name'])
        
        return result
    
    
    def _get_base_queue_name(self, queue_name: str) -> str:
        if ':' in queue_name:
            parts = queue_name.rsplit(':', 1)
            if parts[-1].isdigit():
                return parts[0]
        return queue_name
    
    def _extract_priority(self, queue_name: str) -> int:
        if ':' in queue_name:
            parts = queue_name.rsplit(':', 1)
            if parts[-1].isdigit():
                return int(parts[-1])
        return 0  
    
    def _extract_task_name(self, group_name: str) -> str:
        if ':' in group_name:
            parts = group_name.split(':')
            try:
                queue_idx = parts.index('QUEUE')
                if len(parts) > queue_idx + 2:
                    return parts[-1]
            except ValueError:
                pass
        return 'default'
    
    def _is_default_idle_group(self, group_name: str, base_queue_name: str) -> bool:
        if ':QUEUE:' in group_name:
            parts = group_name.split(':QUEUE:')
            if len(parts) == 2:
                queue_part = parts[1]
                if queue_part == base_queue_name or queue_part.startswith(f"{base_queue_name}:"):
                    if ':' not in queue_part.replace(f"{base_queue_name}:", ""):
                        return True
        return False