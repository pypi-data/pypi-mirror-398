"""
执行器核心逻辑

从AsyncioExecutor提取的核心执行逻辑
职责:
1. 任务执行
2. Pipeline管理
3. 限流控制
4. 统计收集
"""

import asyncio
import logging
import time
import os
from enum import Enum
from typing import Dict, Optional, TYPE_CHECKING
from collections import defaultdict, deque

from ..utils.traceback_filter import filter_framework_traceback
from ..utils.task_logger import TaskContextManager, configure_task_logging
from ..utils.serializer import dumps_str
from ..exceptions import RetryableError
from ..core.enums import TaskStatus
from ..utils.rate_limit.limiter import RateLimiterManager, ConcurrencyRateLimiter
from ..config.lua_scripts import LUA_SCRIPT_BATCH_SEND_EVENT
if TYPE_CHECKING:
    from ..core.app import Jettask

logger = logging.getLogger('app')


class ExecutionMode(Enum):
    """执行模式"""
    SINGLE_PROCESS = "single_process"  
    MULTI_PROCESS = "multi_process"    
    AUTO = "auto"                      

UPDATE_MAX_OFFSET_LUA = """
local hash_key = KEYS[1]
local field = KEYS[2]
local new_value = tonumber(ARGV[1])

local current = redis.call('HGET', hash_key, field)
if current == false or tonumber(current) < new_value then
    redis.call('HSET', hash_key, field, new_value)
    return 1
else
    return 0
end
"""


class ExecutorCore:
    """
    执行器核心逻辑

    从AsyncioExecutor提取的核心执行逻辑
    职责:
    1. 任务执行
    2. Pipeline管理
    3. 限流控制
    4. 统计收集
    """

    @staticmethod
    def _extract_trigger_time_from_event_id(event_id: str) -> float:
        try:
            timestamp_ms = event_id.split('-')[0]
            return float(timestamp_ms) / 1000.0  
        except (ValueError, IndexError, AttributeError):
            logger.warning(f"Failed to extract timestamp from event_id: {event_id}")
            return time.time()

    def __init__(self, app: "Jettask", task_name: str, concurrency: int = 100):
        self.app = app
        self.task_name = task_name
        self.concurrency = concurrency

        self.pipeline_config = {
            'ack': {'max_batch': 1000, 'max_delay': 0.05},
            'task_info': {'max_batch': 2000, 'max_delay': 0.1},
            'status': {'max_batch': 1000, 'max_delay': 0.15},
            'data': {'max_batch': 1000, 'max_delay': 0.15},
            'stats': {'max_batch': 5000, 'max_delay': 0.2}
        }

        self.pending_acks = []
        self.status_updates = []
        self.data_updates = []
        self.task_info_updates = {}
        self.stats_updates = []

        self.last_pipeline_flush = {
            'ack': time.time(),
            'task_info': time.time(),
            'status': time.time(),
            'data': time.time(),
            'stats': time.time()
        }

        self.batch_counter = 0
        self.pipeline_operation_count = 0

        self.prefix = self.app.ep.redis_prefix or 'jettask'
        self._status_prefix = self.app._status_prefix
        self._result_prefix = self.app._result_prefix
        self._prefixed_queue_cache = {}

        self.pending_cache = {}
        self.pending_cache_expire = 0

        self.rate_limiter_manager = None

        log_format = os.environ.get('JETTASK_LOG_FORMAT', 'text').lower()
        if log_format == 'json':
            configure_task_logging(format='json')
        else:
            format_string = os.environ.get('JETTASK_LOG_FORMAT_STRING')
            if format_string:
                configure_task_logging(format='text', format_string=format_string)

        logger.debug(f"ExecutorCore initialized for task {task_name}")

    def _get_prefixed_queue_cached(self, queue: str) -> str:
        if queue not in self._prefixed_queue_cache:
            self._prefixed_queue_cache[queue] = self.app.ep.get_prefixed_queue_name(queue)
        return self._prefixed_queue_cache[queue]

    async def get_pending_count_cached(self, queue: str) -> int:
        current_time = time.time()

        if (current_time - self.pending_cache_expire > 30 or
            queue not in self.pending_cache):
            try:
                pending_info = await self.app.ep.async_redis_client.xpending(queue, queue)
                self.pending_cache[queue] = pending_info.get("pending", 0)
                self.pending_cache_expire = current_time
            except Exception:
                self.pending_cache[queue] = 0

        return self.pending_cache.get(queue, 0)

    async def _quick_ack(self, queue: str, event_id: str, group_name: str = None,
                        offset: int = None):
        group_name = group_name or queue
        self.pending_acks.append((queue, event_id, group_name, offset))
        current_time = time.time()

        ack_config = self.pipeline_config['ack']
        time_since_flush = current_time - self.last_pipeline_flush['ack']

        should_flush = (
            len(self.pending_acks) >= ack_config['max_batch'] or
            (len(self.pending_acks) >= 50 and time_since_flush >= ack_config['max_delay'])
        )

        if should_flush:
            await self._flush_all_buffers()

    async def _flush_all_buffers(self):
        pipeline = self.app.ep.async_redis_client.pipeline()
        operations_count = 0

        if self.pending_acks:
            acks_by_queue_group = defaultdict(lambda: defaultdict(list))
            max_offsets = {}

            for item in self.pending_acks:
                if len(item) == 4:
                    queue, event_id, group_name, offset = item
                elif len(item) == 3:
                    queue, event_id, group_name = item
                    offset = None
                else:
                    queue, event_id = item
                    group_name = queue
                    offset = None

                prefixed_queue = self._get_prefixed_queue_cached(queue)
                acks_by_queue_group[prefixed_queue][group_name].append(event_id)

                if group_name and offset is not None:
                    key = (queue, group_name)
                    if key not in max_offsets or offset > max_offsets[key]:
                        max_offsets[key] = offset

            if max_offsets:
                task_offset_key = f"{self.prefix}:TASK_OFFSETS"
                for (queue, group_name), offset in max_offsets.items():
                    task_name = group_name.split(':')[-1]
                    task_field = f"{queue}:{task_name}"
                    pipeline.eval(UPDATE_MAX_OFFSET_LUA, 2, task_offset_key, task_field, offset)
                    operations_count += 1

            for prefixed_queue, groups in acks_by_queue_group.items():
                for group_name, event_ids in groups.items():
                    stream_key = prefixed_queue.encode() if isinstance(prefixed_queue, str) else prefixed_queue
                    group_key = group_name.encode() if isinstance(group_name, str) else group_name
                    batch_bytes = [b.encode() if isinstance(b, str) else b for b in event_ids]
                    pipeline.xack(stream_key, group_key, *batch_bytes)
                    operations_count += 1

            self.pending_acks.clear()
        task_change_events = []
        if self.task_info_updates:
            for event_key, updates in self.task_info_updates.items():
                if event_key.endswith('_handle_status_update') or \
                    event_key.endswith('_handle_persist_task'):
                    continue  
                key = f"{self.prefix}:TASK:{event_key}"
                key_bytes = key.encode() 
                if updates:
                    encoded_updates = {k.encode(): v.encode() if isinstance(v, str) else v
                                     for k, v in updates.items()}
                    pipeline.hset(key_bytes, mapping=encoded_updates)
                    pipeline.expire(key_bytes, 3600)
                    operations_count += 2
                    task_change_events.append(key)

            if task_change_events:
                self._send_task_changes_with_offset(task_change_events, pipeline)

            self.task_info_updates.clear()

        if hasattr(self, 'stats_updates') and self.stats_updates:
            self.stats_updates.clear()

        if operations_count > 0:
            try:
                results = await pipeline.execute()

                if isinstance(results, Exception):
                    logger.error(f"Pipeline execution error: {results}")
                else:
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"Pipeline operation {i} error: {result}")

                logger.debug(f"Unified pipeline executed {operations_count} operations")
                self.pipeline_operation_count += operations_count

            except Exception as e:
                import traceback
                logger.error(f"Pipeline flush error: {traceback.format_exc()}")

        current_time = time.time()
        for key in self.last_pipeline_flush:
            self.last_pipeline_flush[key] = current_time

    async def _collect_stats_async(self, queue: str, success: bool,
                                   processing_time: float, total_latency: float):
        try:
            if hasattr(self.app, 'consumer_manager') and self.app.consumer_manager:
                if hasattr(self, 'stats_updates'):
                    self.stats_updates.append({
                        'queue': queue,
                        'field': 'success_count' if success else 'error_count',
                        'value': 1
                    })
                    self.stats_updates.append({
                        'queue': queue,
                        'field': 'total_processing_time',
                        'value': int(processing_time * 1000)
                    })

                    if len(self.stats_updates) >= self.pipeline_config['stats']['max_batch']:
                        asyncio.create_task(self._flush_all_buffers())
        except Exception:
            pass

    async def execute_task(self, event_id: str, event_data: dict, queue: str,
                          routing: dict = None, consumer: str = None,
                          group_name: str = None, **kwargs):
        status = "success"
        exception = None
        error_msg = None
        ret = None
        task = None
        args = ()
        kwargs_inner = {}

        status_key = f"{event_id}:{group_name}"
        task_name = event_data.get("_task_name") or event_data.get("name")

        if not task_name:
            logger.error(f"No _task_name in event_data for event {event_id}")
            return

        async with TaskContextManager(
            event_id=event_id,
            task_name=task_name,
            queue=queue,
            worker_id=consumer
        ):
            trigger_time_float = self._extract_trigger_time_from_event_id(event_id)
            
            try:
                execution_start_time = time.time()

                if kwargs.get('_recovery'):
                    logger.debug(f"Processing recovered message {event_id}")

                if event_data.get('is_delayed') and 'execute_at' in event_data:
                    execute_at = float(event_data['execute_at'])
                    if execute_at > time.time():
                        logger.debug(f"Task {event_id} delayed until {execute_at}")
                        return


                task = self.app.get_task_by_name(task_name)
                retry_config = task.retry_config or {}
                max_retries = retry_config.get('max_retries', 0)
                if not task:
                    exception = f"{task_name=} {queue=} 未绑定任何task"
                    logger.error(exception)

                    offset = self._extract_offset(event_data)
                    await self._quick_ack(queue, event_id, group_name, offset)

                    current_time = time.time()
                    duration = current_time - trigger_time_float

                    self.task_info_updates[status_key] = {
                        "status": TaskStatus.ERROR.value,
                        "exception": exception,
                        "started_at": str(execution_start_time),
                        "completed_at": str(current_time),
                        "duration": str(duration),
                        "consumer": consumer,
                        "trigger_time_float": str(trigger_time_float),
                        "queue": str(queue)
                    }
                    await self._flush_all_buffers()
                    return

                self.pedding_count = await self.get_pending_count_cached(queue)

                args = event_data.get("args", ()) or ()
                kwargs_inner = event_data.get("kwargs", {}) or {}


                scheduled_task_id = event_data.get('scheduled_task_id')
                priority = event_data.get('priority')
                delay = event_data.get('delay')

                metadata = {
                    'priority': priority,
                    'delay': delay,
                    'trigger_time': trigger_time_float,
                    'scheduled_task_id': scheduled_task_id,
                    'group_name': group_name,
                    'queue': queue,
                }

                if "event_type" in event_data and "customer_data" in event_data:
                    args = (event_data["event_type"], event_data["customer_data"])
                    extra_kwargs = {k: v for k, v in event_data.items()
                                  if k not in ["event_type", "customer_data", "_broadcast",
                                             "_target_tasks", "_timestamp", "trigger_time",
                                             "name", "_task_name"]}
                    kwargs_inner.update(extra_kwargs)

                result = task.on_before(
                    event_id=event_id,
                    pedding_count=self.pedding_count,
                    args=args,
                    kwargs=kwargs_inner,
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if result and result.reject:
                    self.task_info_updates[status_key] = {
                        "status": TaskStatus.REJECTED.value,
                        "consumer": consumer,
                        "started_at": str(execution_start_time),
                        "completed_at": str(time.time()),
                        "error_msg": "Task rejected by on_before",
                        "trigger_time_float": str(trigger_time_float),
                        "queue": str(queue)
                    }
                    await self._flush_all_buffers()
                    return

                self.task_info_updates[status_key] = {
                    "status": TaskStatus.RUNNING.value,
                    "consumer": consumer,
                    "started_at": str(execution_start_time),
                    "trigger_time_float": str(trigger_time_float),
                    "queue": str(queue)
                }

                current_retry = 0
                last_exception = None

                while current_retry <= max_retries:
                    try:
                        if current_retry > 0:
                            logger.debug(f"Retry attempt {current_retry}/{max_retries} for task {event_id}")

                        clean_kwargs = {k: v for k, v in kwargs_inner.items()
                                      if not k.startswith('_')}

                        task_result = task(
                            event_id,
                            trigger_time_float,         
                            queue,
                            group_name,           
                            scheduled_task_id,    
                            metadata,             
                            *args,
                            **clean_kwargs
                        )
                        if asyncio.iscoroutine(task_result):
                            ret = await task_result
                        else:
                            ret = task_result

                        result = task.on_success(
                            event_id=event_id,
                            args=args,
                            kwargs=clean_kwargs,
                            result=ret,
                        )
                        if asyncio.iscoroutine(result):
                            await result

                        task_config = self.app.get_task_config(task_name)
                        auto_ack = task_config.get('auto_ack', True) if task_config else True
                        if auto_ack:
                            offset = self._extract_offset(event_data)
                            await self._quick_ack(queue, event_id, group_name, offset)

                        break

                    except SystemExit:
                        logger.debug('Task interrupted by system exit, leaving message pending for recovery')
                        status = TaskStatus.ERROR.value
                        exception = "System exit"
                        error_msg = "Task interrupted by shutdown"
                        break

                    except Exception as e:
                        last_exception = e
                        current_retry += 1

                        should_retry = False
                        if current_retry <= max_retries:
                            retry_on_exceptions = retry_config.get('retry_on_exceptions')

                            if retry_on_exceptions:
                                exc_type_name = type(e).__name__
                                should_retry = exc_type_name in retry_on_exceptions
                            else:
                                should_retry = True

                        if should_retry:
                            if isinstance(e, RetryableError) and e.retry_after is not None:
                                delay = e.retry_after
                            else:
                                retry_backoff = retry_config.get('retry_backoff', True)
                                if retry_backoff:
                                    base_delay = 1.0
                                    delay = min(base_delay * (2 ** (current_retry - 1)),
                                              retry_config.get('retry_backoff_max', 60))
                                else:
                                    delay = 1.0

                            logger.info(f'任务执行失败 (尝试 {current_retry}/{max_retries}): {str(e)}，将在 {delay:.2f}s 后重试')
                            await asyncio.sleep(delay)
                            continue
                        else:
                            if max_retries > 0:
                                logger.error(f'任务在 {current_retry-1} 次重试后失败: {str(e)}')
                            else:
                                logger.error(f'任务执行失败: {str(e)}')

                            status = TaskStatus.ERROR.value
                            exception = filter_framework_traceback()
                            error_msg = str(e)
                            logger.error(exception)

                            offset = self._extract_offset(event_data)
                            await self._quick_ack(queue, event_id, group_name, offset)
                            break

            finally:
                completed_at = time.time()
                execution_time = max(0, completed_at - execution_start_time)
                total_latency = max(0, completed_at - trigger_time_float)


                task_info = {
                    "completed_at": str(completed_at),
                    "execution_time": execution_time,
                    "duration": total_latency,
                    "consumer": consumer,
                    'status': status,
                    'retries': current_retry,
                    "trigger_time_float": str(trigger_time_float),
                    "queue": str(queue)
                }

                if ret:
                    task_info["result"] = ret if isinstance(ret, str) else dumps_str(ret)

                if exception:
                    task_info["exception"] = exception
                if error_msg:
                    task_info["error_msg"] = error_msg

                if status_key in self.task_info_updates:
                    self.task_info_updates[status_key].update(task_info)
                else:
                    self.task_info_updates[status_key] = task_info

                if task:
                    if 'clean_kwargs' not in locals():
                        clean_kwargs = {k: v for k, v in kwargs_inner.items()
                                      if not k.startswith('_') and not k.startswith('__')}

                    result = task.on_end(
                        event_id=event_id,
                        args=args,
                        kwargs=clean_kwargs,
                        result=ret,
                        pedding_count=self.pedding_count,
                    )
                    if asyncio.iscoroutine(result):
                        await result

                if routing:
                    agg_key = routing.get("agg_key")
                    routing_key = routing.get("routing_key")
                    if routing_key and agg_key:
                        if queue in self.app.ep.solo_running_state and routing_key in self.app.ep.solo_running_state[queue]:
                            self.app.ep.solo_running_state[queue][routing_key] -= 1
                    try:
                        if result and result.urgent_retry:
                            self.app.ep.solo_urgent_retry[routing_key] = True
                    except:
                        pass
                    if result and result.delay:
                        self.app.ep.task_scheduler[queue][routing_key] = time.time() + result.delay

                self.batch_counter -= 1

    def _extract_offset(self, event_data: dict) -> Optional[int]:
        if isinstance(event_data, dict):
            offset = event_data.get('offset')
            if offset is not None:
                try:
                    return int(offset)
                except (ValueError, TypeError):
                    pass
        return None

    def _send_task_changes_with_offset(self, task_ids: list, pipeline):
        from jettask.utils.serializer import dumps_str

        stream_key = f"{self.prefix}:QUEUE:TASK_CHANGES".encode()
        lua_args = [self.prefix.encode() if isinstance(self.prefix, str) else self.prefix]

        for task_id in task_ids:
            message_data = {'kwargs': {'task_id': task_id}}
            data = dumps_str(message_data)
            lua_args.append(data)

        pipeline.eval(
            LUA_SCRIPT_BATCH_SEND_EVENT,
            1,  
            stream_key,  
            *lua_args  
        )
        logger.debug(f"已添加 {len(task_ids)} 条 TASK_CHANGES 消息到 pipeline")

    async def cleanup(self):
        logger.debug("ExecutorCore cleaning up...")

        if self.rate_limiter_manager:
            try:
                await self.rate_limiter_manager.stop_all()
                logger.debug("Rate limiter manager stopped and locks released")
            except Exception as e:
                logger.error(f"Error stopping rate limiter manager: {e}")

        try:
            await asyncio.wait_for(self._flush_all_buffers(), timeout=0.5)
            logger.debug("Buffers flushed successfully")
        except asyncio.TimeoutError:
            logger.warning("Buffer flush timeout")
        except Exception as e:
            logger.error(f"Error flushing buffers: {e}")



__all__ = ['ExecutorCore', 'ExecutionMode', 'UPDATE_MAX_OFFSET_LUA']
