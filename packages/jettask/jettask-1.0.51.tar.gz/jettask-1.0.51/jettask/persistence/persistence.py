"""任务持久化模块

负责解析Redis Stream消息，并将任务数据批量插入PostgreSQL数据库。
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert

from jettask.db.models.task import Task
from jettask.db.models.task_metrics_minute import TaskMetricsMinute
from jettask.db.models.task_runs_metrics_minute import TaskRunsMetricsMinute

logger = logging.getLogger(__name__)


class TaskPersistence:
    """任务持久化处理器

    职责：
    - 解析Stream消息为任务信息
    - 批量插入任务到PostgreSQL的tasks表
    - 处理插入失败的降级策略
    """

    def __init__(
        self,
        async_session_local: sessionmaker,
        namespace_id: str,
        namespace_name: str
    ):
        self.AsyncSessionLocal = async_session_local
        self.namespace_id = namespace_id
        self.namespace_name = namespace_name


    async def batch_insert_tasks(self, tasks: List[Dict[str, Any]]) -> int:
        if not tasks:
            return 0

        logger.info(f"[BATCH INSERT] 批量插入 {len(tasks)} 条任务...")

        try:
            async with self.AsyncSessionLocal() as session:
                insert_data = []
                for record in tasks:
                    scheduled_task_id = record.get('scheduled_task_id')
                    trigger_time = record.get('trigger_time')

                    if isinstance(trigger_time, (int, float)):
                        trigger_time = datetime.fromtimestamp(trigger_time, timezone.utc)

                    insert_data.append({
                        'stream_id': record['stream_id'],
                        'queue': record['queue'],
                        'namespace': record['namespace'],
                        'scheduled_task_id': str(scheduled_task_id) if scheduled_task_id is not None else None,
                        'payload': record.get('payload', {}),
                        'priority': record.get('priority', 0),
                        'delay': record.get('delay', 0),
                        'trigger_time': trigger_time,
                        'source': record.get('source', 'redis_stream'),
                        'task_metadata': record.get('metadata', {})
                    })

                stmt = insert(Task).values(insert_data).on_conflict_do_nothing(
                    constraint='tasks_pkey'
                )

                await session.execute(stmt)

                await self._update_metrics_aggregation(session, insert_data)

                await session.commit()

                logger.info(f"[BATCH INSERT] ✓ 成功插入 {len(insert_data)} 条任务")
                return len(insert_data)

        except Exception as e:
            logger.error(f"[BATCH INSERT] ✗ 批量插入失败: {e}", exc_info=True)
            return 0

    async def batch_update_tasks(self, updates: List[Dict[str, Any]]) -> int:
        if not updates:
            return 0


        try:
            from sqlalchemy.dialects.postgresql import insert
            from ..db.models import TaskRun
            from ..utils.serializer import loads_str
            from datetime import datetime, timezone

            deduplicated = {}
            for record in updates:
                stream_id = record['stream_id']
                deduplicated[stream_id] = record

            unique_updates = list(deduplicated.values())

            if len(unique_updates) < len(updates):
                logger.info(
                    f"[BATCH UPDATE] 去重: {len(updates)} 条 → {len(unique_updates)} 条 "
                    f"(合并了 {len(updates) - len(unique_updates)} 条重复记录)"
                )

            async with self.AsyncSessionLocal() as session:
                upsert_data = []
                aggregation_data = []

                for record in unique_updates:
                    logger.debug(f"处理记录: {record}")
                    result = record.get('result')
                    if result and isinstance(result, bytes):
                        try:
                            result = loads_str(result)
                        except Exception:
                            result = result.decode('utf-8') if isinstance(result, bytes) else result

                    error = record.get('error')
                    if error and isinstance(error, bytes):
                        error = error.decode('utf-8')

                    trigger_time = record.get('trigger_time')
                    if trigger_time is None:
                        trigger_time = record.get('started_at')
                        logger.warning(f"Record missing trigger_time, using started_at as fallback: {record.get('stream_id')}")

                    started_at = record.get('started_at')
                    completed_at = record.get('completed_at')

                    if isinstance(trigger_time, (int, float)):
                        trigger_time_dt = datetime.fromtimestamp(trigger_time, timezone.utc)
                    else:
                        trigger_time_dt = trigger_time

                    if isinstance(started_at, (int, float)):
                        started_at_dt = datetime.fromtimestamp(started_at, timezone.utc)
                    else:
                        started_at_dt = started_at

                    if isinstance(completed_at, (int, float)):
                        completed_at_dt = datetime.fromtimestamp(completed_at, timezone.utc)
                    else:
                        completed_at_dt = completed_at

                    duration = None
                    if started_at and completed_at:
                        duration = completed_at - started_at

                    status = record.get('status')
                    if status and isinstance(status, bytes):
                        status = status.decode('utf-8')

                    consumer = record.get('consumer')
                    if consumer and isinstance(consumer, bytes):
                        consumer = consumer.decode('utf-8')

                    task_name = record.get('task_name')

                    upsert_record = {
                        'task_name': task_name,
                        'trigger_time': trigger_time_dt,
                        'stream_id': record['stream_id'],
                        'status': status,
                        'result': result,
                        'error': error,
                        'started_at': started_at_dt,
                        'completed_at': completed_at_dt,
                        'retries': record.get('retries', 0),
                        'duration': duration,
                        'consumer': consumer,
                        'updated_at': datetime.now(timezone.utc),
                    }
                    logger.debug(f"upsert_record: {upsert_record}")
                    upsert_data.append(upsert_record)

                    aggregation_record = {
                        'stream_id': record['stream_id'],
                        'task_name': task_name,
                        'status': status,
                        'started_at': started_at,
                        'completed_at': completed_at,
                        'retries': record.get('retries', 0),
                        'duration': duration,
                        'queue': record.get('queue'),
                        'namespace': record.get('namespace'),
                        'trigger_time': record.get('trigger_time'),  
                    }
                    aggregation_data.append(aggregation_record)

                logger.info(f"[BATCH UPDATE] 准备写入 {len(upsert_data)} 条记录")
    
                stmt = insert(TaskRun).values(upsert_data)

                from sqlalchemy import func
                stmt = stmt.on_conflict_do_update(
                    constraint='task_runs_pkey',  
                    set_={
                        'status': stmt.excluded.status,
                        'result': func.coalesce(stmt.excluded.result, TaskRun.result),
                        'error': func.coalesce(stmt.excluded.error, TaskRun.error),
                        'started_at': func.coalesce(stmt.excluded.started_at, TaskRun.started_at),
                        'completed_at': func.coalesce(stmt.excluded.completed_at, TaskRun.completed_at),
                        'retries': func.coalesce(stmt.excluded.retries, TaskRun.retries),
                        'duration': func.coalesce(stmt.excluded.duration, TaskRun.duration),
                        'consumer': func.coalesce(stmt.excluded.consumer, TaskRun.consumer),
                        'task_name': func.coalesce(stmt.excluded.task_name, TaskRun.task_name),
                        'updated_at': stmt.excluded.updated_at,
                    }
                )

                await session.execute(stmt)

                await self._update_task_runs_metrics_aggregation(session, aggregation_data)

                await session.commit()

                logger.info(f"[BATCH UPDATE] ✓ 成功更新 {len(upsert_data)} 条任务状态")
                return len(upsert_data)

        except Exception as e:
            logger.error(f"[BATCH UPDATE] ✗ 批量更新失败: {e}", exc_info=True)
            return 0

    async def _update_metrics_aggregation(self, session, tasks_data: List[Dict[str, Any]]) -> None:
        if not tasks_data:
            return

        logger.debug(f"Updating metrics aggregation for {len(tasks_data)} tasks")

        from collections import defaultdict

        metrics_map = defaultdict(int)

        for task in tasks_data:
            trigger_time = task.get('trigger_time')
            if not trigger_time:
                continue

            if isinstance(trigger_time, (int, float)):
                trigger_datetime = datetime.fromtimestamp(trigger_time, timezone.utc)
            elif isinstance(trigger_time, str):
                trigger_datetime = datetime.fromisoformat(trigger_time.replace('Z', '+00:00'))
            else:
                trigger_datetime = trigger_time

            time_bucket = trigger_datetime.replace(second=0, microsecond=0)

            key = (
                task['namespace'],
                task['queue'],
                time_bucket
            )

            metrics_map[key] += 1

        metrics_data = []
        for (namespace, queue, time_bucket), count in metrics_map.items():
            metrics_data.append({
                'namespace': namespace,
                'queue': queue,
                'time_bucket': time_bucket,
                'task_count': count,
                'updated_at': datetime.now(timezone.utc)
            })

        if not metrics_data:
            return

        stmt = insert(TaskMetricsMinute).values(metrics_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['namespace', 'queue', 'time_bucket'],
            set_={
                'task_count': TaskMetricsMinute.task_count + stmt.excluded.task_count,
                'updated_at': stmt.excluded.updated_at
            }
        )

        await session.execute(stmt)
        logger.debug(f"Updated {len(metrics_data)} metric entries in aggregation table")

    async def _update_task_runs_metrics_aggregation(
        self, session, tasks_data: List[Dict[str, Any]]
    ) -> None:
        if not tasks_data:
            return

        logger.debug(f"Updating task_runs metrics aggregation for {len(tasks_data)} tasks")

        from sqlalchemy import func

        metrics_map = {}

        for task in tasks_data:
            started_at = task.get('started_at')
            if not started_at:
                continue

            bucket_dt = datetime.fromtimestamp(started_at, tz=timezone.utc)
            time_bucket = bucket_dt.replace(second=0, microsecond=0)

            namespace = task.get('namespace') or 'default'

            queue = task.get('queue') or 'unknown'

            task_name = task.get('task_name') or 'unknown'

            key = (time_bucket, namespace, queue, task_name)

            if key not in metrics_map:
                metrics_map[key] = {
                    'total_count': 0,
                    'success_count': 0,
                    'failed_count': 0,
                    'retry_count': 0,
                    'total_duration': 0.0,
                    'max_duration': None,
                    'min_duration': None,
                    'total_delay': 0.0,
                    'max_delay': None,
                    'min_delay': None,
                    'running_concurrency': 0,
                }

            metrics = metrics_map[key]

            metrics['total_count'] += 1

            status = task.get('status')
            if status == 'success':
                metrics['success_count'] += 1
            elif status in ('failed', 'error'):
                metrics['failed_count'] += 1

            retries = task.get('retries') or 0
            metrics['retry_count'] += retries

            duration = task.get('duration')
            if duration is not None and duration > 0:
                metrics['total_duration'] += duration
                if metrics['max_duration'] is None or duration > metrics['max_duration']:
                    metrics['max_duration'] = duration
                if metrics['min_duration'] is None or duration < metrics['min_duration']:
                    metrics['min_duration'] = duration

            trigger_time = task.get('trigger_time')
            if trigger_time is not None and started_at is not None:
                delay = started_at - trigger_time
                if delay >= 0:  
                    metrics['total_delay'] += delay
                    if metrics['max_delay'] is None or delay > metrics['max_delay']:
                        metrics['max_delay'] = delay
                    if metrics['min_delay'] is None or delay < metrics['min_delay']:
                        metrics['min_delay'] = delay

            metrics['running_concurrency'] += 1

        if not metrics_map:
            return

        metrics_data = []
        for (time_bucket, namespace, queue, task_name), metrics in metrics_map.items():
            metrics_data.append({
                'time_bucket': time_bucket,
                'namespace': namespace,  
                'queue': queue,  
                'task_name': task_name,
                'total_count': metrics['total_count'],
                'success_count': metrics['success_count'],
                'failed_count': metrics['failed_count'],
                'retry_count': metrics['retry_count'],
                'total_duration': metrics['total_duration'],
                'max_duration': metrics['max_duration'],
                'min_duration': metrics['min_duration'],
                'total_delay': metrics['total_delay'],
                'max_delay': metrics['max_delay'],
                'min_delay': metrics['min_delay'],
                'running_concurrency': metrics['running_concurrency'],
                'updated_at': datetime.now(timezone.utc)
            })

        if not metrics_data:
            return

        stmt = insert(TaskRunsMetricsMinute).values(metrics_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['time_bucket', 'namespace', 'queue', 'task_name'],
            set_={
                'total_count': TaskRunsMetricsMinute.total_count + stmt.excluded.total_count,
                'success_count': TaskRunsMetricsMinute.success_count + stmt.excluded.success_count,
                'failed_count': TaskRunsMetricsMinute.failed_count + stmt.excluded.failed_count,
                'retry_count': TaskRunsMetricsMinute.retry_count + stmt.excluded.retry_count,
                'total_duration': TaskRunsMetricsMinute.total_duration + stmt.excluded.total_duration,
                'max_duration': func.greatest(
                    func.coalesce(TaskRunsMetricsMinute.max_duration, stmt.excluded.max_duration),
                    stmt.excluded.max_duration
                ),
                'min_duration': func.least(
                    func.coalesce(TaskRunsMetricsMinute.min_duration, stmt.excluded.min_duration),
                    stmt.excluded.min_duration
                ),
                'total_delay': TaskRunsMetricsMinute.total_delay + stmt.excluded.total_delay,
                'max_delay': func.greatest(
                    func.coalesce(TaskRunsMetricsMinute.max_delay, stmt.excluded.max_delay),
                    stmt.excluded.max_delay
                ),
                'min_delay': func.least(
                    func.coalesce(TaskRunsMetricsMinute.min_delay, stmt.excluded.min_delay),
                    stmt.excluded.min_delay
                ),
                'running_concurrency': func.greatest(
                    TaskRunsMetricsMinute.running_concurrency,
                    stmt.excluded.running_concurrency
                ),
                'updated_at': stmt.excluded.updated_at
            }
        )

        await session.execute(stmt)
        logger.debug(f"Updated {len(metrics_data)} task_runs metric entries in aggregation table")
