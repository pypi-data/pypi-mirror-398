"""
时间处理工具函数
"""
import json
from datetime import datetime, timezone
from typing import Dict, Any, List


def parse_iso_datetime(time_str: str) -> datetime:
    if time_str.endswith('Z'):
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    else:
        dt = datetime.fromisoformat(time_str)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)

    return dt


def format_task_timestamps(task: Dict[str, Any], fields: List[str] = None) -> Dict[str, Any]:
    if fields is None:
        fields = ['created_at', 'started_at', 'completed_at']

    for field in fields:
        if task.get(field):
            if task[field].tzinfo is None:
                task[field] = task[field].replace(tzinfo=timezone.utc)
            task[field] = task[field].isoformat()

    return task


def parse_task_json_fields(task: Dict[str, Any], fields: List[str] = None) -> Dict[str, Any]:
    if fields is None:
        fields = ['task_data', 'result', 'metadata']

    for field in fields:
        if task.get(field) and isinstance(task[field], str):
            try:
                task[field] = json.loads(task[field])
            except:
                pass

    return task


def task_obj_to_dict(task_obj) -> Dict[str, Any]:
    task = {
        'id': task_obj.id,
        'queue_name': task_obj.queue_name,
        'task_name': task_obj.task_name,
        'task_data': task_obj.task_data,
        'priority': task_obj.priority,
        'retry_count': task_obj.retry_count,
        'max_retry': task_obj.max_retry,
        'status': task_obj.status,
        'result': task_obj.result,
        'error_message': task_obj.error_message,
        'created_at': task_obj.created_at,
        'started_at': task_obj.started_at,
        'completed_at': task_obj.completed_at,
        'worker_id': task_obj.worker_id,
        'execution_time': task_obj.execution_time,
        'duration': task_obj.duration,
        'metadata': task_obj.task_metadata,
        'next_sync_time': task_obj.next_sync_time,
        'sync_check_count': task_obj.sync_check_count
    }

    task = format_task_timestamps(task)

    task = parse_task_json_fields(task)

    return task
