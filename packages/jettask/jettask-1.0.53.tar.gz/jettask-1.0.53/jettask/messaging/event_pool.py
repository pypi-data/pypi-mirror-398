"""
EventPool - 事件池核心实现

负责：
1. 任务队列管理和消息分发
2. 消费者管理和生命周期控制
3. 优先级队列处理
4. 离线Worker恢复机制

核心组件集成：
- MessageSender/Reader: 消息发送和读取（通过container）
- QueueRegistry: 队列注册管理
- Worker ID: 直接使用 app.worker_id（在 App._start 中生成）
"""

from ..utils.serializer import dumps_str, loads_str
import time
import threading
import logging
import asyncio
import json
from collections import defaultdict, deque, Counter
from typing import List, Optional, TYPE_CHECKING, Union
import traceback
import redis
from redis import asyncio as aioredis

from jettask.db.connector import get_sync_redis_client, get_async_redis_client

from ..utils.helpers import get_hostname
import os
from jettask.config.lua_scripts import LUA_SCRIPT_BATCH_SEND_EVENT

if TYPE_CHECKING:
    from ..core.task import Task
    from ..core.app import Jettask

logger = logging.getLogger('app')

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

class EventPool(object):
    STATE_MACHINE_NAME = "STATE_MACHINE"
    TIMEOUT = 60 * 5

    def __init__(
        self,
        redis_client: redis.StrictRedis,
        async_redis_client: Optional[aioredis.StrictRedis] = None,
        task_event_queues=None,
        tasks: dict = None,
        queue_registry=None,  
        offline_recovery=None,  
        queues: list = None,
        redis_url: str = None,
        consumer_config: dict = None,
        redis_prefix: str = None,
        app: Optional["Jettask"] = None,
        worker_id: str = None,
    ) -> None:
        self.redis_client = redis_client

        self._async_redis_client = async_redis_client  
        self._binary_redis_client = None
        self._async_binary_redis_client = None

        self._redis_url = redis_url or 'redis://localhost:6379/0'
        self.redis_prefix = redis_prefix or 'jettask'
        self.app = app  
        self.worker_id = worker_id  
        self.task_event_queues = task_event_queues  

        self.tasks = tasks
        from jettask.utils.queue_matcher import separate_wildcard_and_static_queues

        self.wildcard_patterns, static_queues = separate_wildcard_and_static_queues(queues or [])
        self.queues = static_queues  
        self.wildcard_mode = len(self.wildcard_patterns) > 0  
        
        self.consumer_config = consumer_config or {}
        self.consumer_config['queues'] = queues or []
        self.consumer_config['redis_prefix'] = redis_prefix or 'jettask'
        self.consumer_config['redis_url'] = redis_url or 'redis://localhost:6379/0'

        self.queue_registry = queue_registry
        self.offline_recovery = offline_recovery

        self.prefixed_queues = {}


        self._broadcast_message_tracker = {}

        self.solo_routing_tasks = {}
        self.solo_running_state = {}
        self.solo_urgent_retry = {}
        self.batch_routing_tasks = {}
        self.task_scheduler = {}
        self.running_task_state_mappings = {}
        self.delay_tasks = []
        self.solo_agg_task = {}
        self.rlock = threading.RLock()
        self._claimed_message_ids = set()  
        self._stop_reading = False  
        self._queue_stop_flags = {queue: False for queue in (queues or [])}  


    async def record_group_info_async(self, queue: str, task_name: str, group_name: str, consumer_name: str):
        if not self.worker_id:
            logger.warning("Cannot record group info: worker_id not initialized")
            return
        try:
            if self.app and hasattr(self.app, 'worker_state'):
                await self.app.worker_state.record_group_info(
                    worker_id=self.worker_id,
                    queue=queue,
                    task_name=task_name,
                    group_name=group_name,
                    consumer_name=consumer_name,
                    redis_prefix=self.redis_prefix
                )
            else:
                logger.warning("Cannot record group info: worker_state not available")

        except Exception as e:
            logger.error(f"Error recording task group info: {e}", exc_info=True)

    def _put_task(self, event_queue: Union[deque, asyncio.Queue], task, urgent: bool = False):
        if isinstance(event_queue, deque):
            if urgent:
                event_queue.appendleft(task)
            else:
                event_queue.append(task)
        elif isinstance(event_queue, asyncio.Queue):
            pass
    
    async def _async_put_task(self, event_queue: asyncio.Queue, task, urgent: bool = False):
        await event_queue.put(task)

    def init_routing(self):
        for queue in self.queues:
            self.solo_agg_task[queue] = defaultdict(list)
            self.solo_routing_tasks[queue] = defaultdict(list)
            self.solo_running_state[queue]  = defaultdict(bool)
            self.batch_routing_tasks[queue]  = defaultdict(list)
            self.task_scheduler[queue] = defaultdict(int)
            self.running_task_state_mappings[queue] = defaultdict(dict)
            
    def get_prefixed_queue_name(self, queue: str) -> str:
        return f"{self.redis_prefix}:QUEUE:{queue}"

    @property
    def async_redis_client(self):
        if self._async_redis_client is None:
            self._async_redis_client = get_async_redis_client(
                self._redis_url, decode_responses=True, socket_timeout=None
            )
        return self._async_redis_client

    @property
    def binary_redis_client(self):
        if self._binary_redis_client is None:
            self._binary_redis_client = get_sync_redis_client(
                self._redis_url, decode_responses=False, socket_timeout=None
            )
        return self._binary_redis_client

    @property
    def async_binary_redis_client(self):
        if self._async_binary_redis_client is None:
            self._async_binary_redis_client = get_async_redis_client(
                self._redis_url, decode_responses=False, socket_timeout=None
            )
        return self._async_binary_redis_client

    def get_redis_client(self, asyncio: bool = False, binary: bool = False):
        if binary:
            return self.async_binary_redis_client if asyncio else self.binary_redis_client
        return self.async_redis_client if asyncio else self.redis_client

    def _batch_send_event_sync(self, prefixed_queue, messages: List[dict], pipe):
        lua_args = [self.redis_prefix.encode() if isinstance(self.redis_prefix, str) else self.redis_prefix]

        for message in messages:
            if 'data' in message:
                data = message['data'] if isinstance(message['data'], bytes) else dumps_str(message['data'])
            else:
                data = dumps_str(message)
            lua_args.append(data)

        client = self.get_redis_client(asyncio=False, binary=True)

        results = client.eval(
            LUA_SCRIPT_BATCH_SEND_EVENT,
            1,  
            prefixed_queue,  
            *lua_args  
        )

        return [r.decode('utf-8') if isinstance(r, bytes) else r for r in results]

    async def _batch_send_event(self, prefixed_queue, messages: List[dict], pipe):
        lua_args = [self.redis_prefix.encode() if isinstance(self.redis_prefix, str) else self.redis_prefix]

        for message in messages:
            if 'data' in message:
                data = message['data'] if isinstance(message['data'], bytes) else dumps_str(message['data'])
            else:
                data = dumps_str(message)
            lua_args.append(data)

        client = self.get_redis_client(asyncio=True, binary=True)

        results = await client.eval(
            LUA_SCRIPT_BATCH_SEND_EVENT,
            1,  
            prefixed_queue,  
            *lua_args  
        )

        return [r.decode('utf-8') if isinstance(r, bytes) else r for r in results]
    
    def is_urgent(self, routing_key):
        is_urgent = self.solo_urgent_retry.get(routing_key, False)
        if is_urgent == True:
            del self.solo_urgent_retry[routing_key]
        return is_urgent
    
    async def scan_priority_queues(self, base_queue: str) -> list:
        pattern = f"{self.redis_prefix}:QUEUE:{base_queue}:*"
        
        try:
            from jettask.messaging.registry import QueueRegistry
            registry = QueueRegistry(
                redis_client=self.redis_client,
                async_redis_client=self.async_redis_client,
                redis_prefix=self.redis_prefix
            )
            
            priority_queue_names = await registry.get_priority_queues_for_base(base_queue)
            priority_queues = set(priority_queue_names)
            
            if not priority_queues:
                all_queues = await registry.get_all_queues()
                for queue in all_queues:
                    if queue.startswith(f"{base_queue}:"):
                        priority_queues.add(queue)
            
            priority_queues.add(base_queue)
            
            sorted_queues = []
            for q in priority_queues:
                if ':' in q:
                    base, priority = q.rsplit(':', 1)
                    if base == base_queue and priority.isdigit():
                        sorted_queues.append((int(priority), q))
                    else:
                        sorted_queues.append((float('inf'), q))  
                else:
                    sorted_queues.append((float('inf'), q))  
            
            sorted_queues.sort(key=lambda x: x[0])
            return [q[1] for q in sorted_queues]
            
        except Exception as e:
            import traceback
            logger.error(f"Error scanning priority queues for {base_queue}: {e}\n{traceback.format_exc()}")
            return [base_queue]  
    
    async def _ensure_consumer_group_and_record_info(
        self,
        prefixed_queue: str,
        task_name: str,
        consumer_name: str,
        base_group_name: str
    ) -> str:
        actual_queue_name = prefixed_queue.replace(f"{self.redis_prefix}:QUEUE:", "")

        group_name = base_group_name

        try:
            await self.async_redis_client.xgroup_create(
                name=prefixed_queue,
                groupname=group_name,
                id="0",
                mkstream=True
            )
            logger.debug(f"Created consumer group {group_name} for queue {prefixed_queue}")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group {group_name} already exists for queue {prefixed_queue}")
            else:
                logger.warning(f"Error creating consumer group {group_name} for {prefixed_queue}: {e}")

        await self.record_group_info_async(
            actual_queue_name, task_name, group_name, consumer_name
        )

        return group_name

    async def get_priority_queues_direct(self, base_queue: str) -> list:
        from jettask.messaging.registry import QueueRegistry
        registry = QueueRegistry(self.redis_client, self.async_redis_client, self.redis_prefix)

        priority_queue_names = await registry.get_priority_queues_for_base(base_queue)
        priority_queues = []

        for pq_name in priority_queue_names:
            if ':' in pq_name and pq_name.rsplit(':', 1)[1].isdigit():
                prefixed_pq = f"{self.redis_prefix}:QUEUE:{pq_name}"
                priority = int(pq_name.rsplit(':', 1)[1])
                priority_queues.append((priority, prefixed_pq))

        priority_queues.sort(key=lambda x: x[0])

        base_prefixed = f"{self.redis_prefix}:QUEUE:{base_queue}"
        return [base_prefixed] + [q[1] for q in priority_queues]
  
    
    @classmethod
    def separate_by_key(cls, lst):
        groups = {}
        for item in lst:
            key = item[0]['routing_key']
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        result = []
        group_values = list(groups.values())
        while True:
            exists_data = False
            for values in group_values:
                try:
                    result.append(values.pop(0))
                    exists_data = True
                except:
                    pass
            if not exists_data:
                break
        return result
    
    async def _unified_task_checker(self, event_queue: asyncio.Queue, checker_type: str = 'solo_agg'):
        last_solo_running_state = defaultdict(dict)
        last_wait_time = defaultdict(int)
        queue_batch_tasks = defaultdict(list)
        left_queue_batch_tasks = defaultdict(list)
        
        delay_tasks = getattr(self, 'delay_tasks', []) if checker_type == 'delay' else []
        
        while True:
            has_work = False
            current_time = time.time()
            
            if checker_type == 'delay':
                put_count = 0
                need_del_index = []
                for i in range(len(delay_tasks)):
                    schedule_time = delay_tasks[i][0]
                    task = delay_tasks[i][1]
                    if schedule_time <= current_time:
                        try:
                            await self._async_put_task(event_queue, task)
                            need_del_index.append(i)
                            put_count += 1
                            has_work = True
                        except IndexError:
                            pass
                for i in need_del_index:
                    del delay_tasks[i]
                    
            elif checker_type == 'solo_agg':
                for queue in self.queues:
                    for agg_key, tasks in self.solo_agg_task[queue].items():
                        if not tasks:
                            continue
                            
                        has_work = True
                        need_del_index = []
                        need_lock_routing_keys = []
                        sort_by_tasks = self.separate_by_key(tasks)
                        max_wait_time = 5
                        max_records = 3
                        
                        for index, (routing, task) in enumerate(sort_by_tasks):
                            routing_key = routing['routing_key']
                            max_records = routing.get('max_records', 1)
                            max_wait_time = routing.get('max_wait_time', 0)
                            
                            with self.rlock:
                                if self.solo_running_state[queue].get(routing_key, 0) > 0:
                                    continue
                                    
                            if len(queue_batch_tasks[queue] + left_queue_batch_tasks[queue]) >= max_records:
                                break 
                                
                            task["routing"] = routing

                            if self.is_urgent(routing_key):
                                left_queue_batch_tasks[queue].append(task)
                            else:
                                queue_batch_tasks[queue].append(task)
                            need_lock_routing_keys.append(routing_key)
                            need_del_index.append(index)

                        for routing_key, count in Counter(need_lock_routing_keys).items():
                            with self.rlock:
                                self.solo_running_state[queue][routing_key] = count
                                
                        if last_solo_running_state[queue] != self.solo_running_state[queue]:
                            last_solo_running_state[queue] = self.solo_running_state[queue].copy()
                            
                        tasks = [task for index, task in enumerate(sort_by_tasks) if index not in need_del_index]
                        self.solo_agg_task[queue][agg_key] = tasks
                        
                        if (len(queue_batch_tasks[queue] + left_queue_batch_tasks[queue]) >= max_records or 
                            (last_wait_time[queue] and last_wait_time[queue] < current_time - max_wait_time)):
                            for task in queue_batch_tasks[queue]:
                                await self._async_put_task(event_queue, task)
                            for task in left_queue_batch_tasks[queue]:
                                await self._async_put_task(event_queue, task)    
                            queue_batch_tasks[queue] = []
                            left_queue_batch_tasks[queue] = []
                            last_wait_time[queue] = 0
                        elif last_wait_time[queue] == 0:
                            last_wait_time[queue] = current_time
            
            sleep_time = self._get_optimal_sleep_time(has_work, checker_type)
            await asyncio.sleep(sleep_time)
    
    def _get_optimal_sleep_time(self, has_work: bool, checker_type: str) -> float:
        if checker_type == 'delay':
            return 0.001 if has_work else 1.0
        elif has_work:
            return 0.001  
        else:
            return 0.01   
    
    
    async def async_check_solo_agg_tasks(self, event_queue: asyncio.Queue):
        await self._unified_task_checker(event_queue, checker_type='solo_agg')
    
    async def check_solo_agg_tasks(self, event_queue: asyncio.Queue):
        await self._unified_task_checker(event_queue, checker_type='solo_agg')
    
    def check_sole_tasks(self, event_queue: Union[deque, asyncio.Queue]):
        agg_task_mappings = {queue:  defaultdict(list) for queue in self.queues}
        agg_wait_task_mappings = {queue:  defaultdict(float) for queue in self.queues}
        task_max_wait_time_mapping = {}
        make_up_for_index_mappings = {queue:  defaultdict(int) for queue in self.queues} 
        while True:
            put_count = 0
            for queue in self.queues:
                agg_task = agg_task_mappings[queue]
                for routing_key, tasks in self.solo_routing_tasks[queue].items():
                    schedule_time = self.task_scheduler[queue][routing_key]
                    if tasks:
                        for task in tasks:
                            prev_routing = task[0]
                            if agg_key:= prev_routing.get('agg_key'):
                                if not self.running_task_state_mappings[queue][agg_key]:
                                    self.solo_running_state[queue][routing_key] = False
                                    break 
                    if (
                        schedule_time <= time.time()
                        and self.solo_running_state[queue][routing_key] == False
                    ) :
                            try:
                                routing, task = tasks.pop(0)
                            except IndexError:
                                continue
                            task["routing"] = routing
                            
                            agg_key = routing.get('agg_key')
                            if agg_key is not None:
                                start_time = agg_wait_task_mappings[queue][agg_key]
                                if not start_time:
                                    agg_wait_task_mappings[queue][agg_key] = time.time()
                                    start_time = agg_wait_task_mappings[queue][agg_key]
                                agg_task[agg_key].append(task)
                                max_wait_time = routing.get('max_wait_time', 3)
                                task_max_wait_time_mapping[agg_key] = max_wait_time
                                if len(agg_task[agg_key])>=routing.get('max_records', 100) or time.time()-start_time>=max_wait_time:
                                    logger.debug(f'{agg_key=} {len(agg_task[agg_key])} 已满，准备发车！{routing.get("max_records", 100)} {time.time()-start_time} {max_wait_time}')
                                    for task in agg_task[agg_key]:
                                        task['routing']['version'] = 1
                                        self.running_task_state_mappings[queue][agg_key][task['event_id']] = time.time()
                                        self._put_task(event_queue, task, urgent=self.is_urgent(routing_key))
                                    agg_task[agg_key] = []
                                    make_up_for_index_mappings[queue][agg_key] = 0 
                                    agg_wait_task_mappings[queue][agg_key] = 0
                            else:
                                self._put_task(event_queue, task, urgent=self.is_urgent(routing_key))
                            self.solo_running_state[queue][routing_key] = True
                            put_count += 1
                for agg_key in agg_task.keys():
                    if not agg_task[agg_key]:
                        continue
                    start_time = agg_wait_task_mappings[queue][agg_key]
                    max_wait_time = task_max_wait_time_mapping[agg_key]
                    if make_up_for_index_mappings[queue][agg_key]>= len(agg_task[agg_key])-1:
                        make_up_for_index_mappings[queue][agg_key] = 0
                    routing = agg_task[agg_key][make_up_for_index_mappings[queue][agg_key]]['routing']
                    routing_key = routing['routing_key']
                    self.solo_running_state[queue][routing_key] = False
                    make_up_for_index_mappings[queue][agg_key] += 1
                    if time.time()-start_time>=max_wait_time:
                        logger.debug(f'{agg_key=} {len(agg_task[agg_key])}被迫发车！ {time.time()-start_time} {max_wait_time}')
                        for task in agg_task[agg_key]:
                            task['routing']['version'] = 1
                            self.running_task_state_mappings[queue][agg_key][task['event_id']] = time.time()
                            self._put_task(event_queue, task, urgent=self.is_urgent(routing_key))
                        agg_task[agg_key] = []
                        make_up_for_index_mappings[queue][agg_key] = 0
                        agg_wait_task_mappings[queue][agg_key] = 0
            if not put_count:
                time.sleep(0.001)
            elif put_count < 5:
                time.sleep(0.0005)  
                
    async def check_batch_tasks(self, event_queue: asyncio.Queue):
        await asyncio.sleep(0.1)

    async def check_delay_tasks(self, event_queue: asyncio.Queue):
        await self._unified_task_checker(event_queue, checker_type='delay')

    def _handle_redis_error(self, error: Exception, consecutive_errors: int, queue: str = None) -> tuple[bool, int]:
        if isinstance(error, redis.exceptions.ConnectionError):
            logger.error(f'Redis连接错误: {error}')
            logger.error(traceback.format_exc())
            consecutive_errors += 1
            if consecutive_errors >= 5:
                logger.error(f'连续连接失败{consecutive_errors}次，重新创建连接')
                return True, 0
            return False, consecutive_errors
            
        elif isinstance(error, redis.exceptions.ResponseError):
            if "NOGROUP" in str(error) and queue:
                logger.warning(f'队列 {queue} 或消费者组不存在')
                return False, consecutive_errors
            else:
                logger.error(f'Redis错误: {error}')
                logger.error(traceback.format_exc())
                consecutive_errors += 1
                return False, consecutive_errors
        else:
            logger.error(f'意外错误: {error}')
            logger.error(traceback.format_exc())
            consecutive_errors += 1
            return False, consecutive_errors

    def _process_message_common(self, event_id: str, event_data: dict, queue: str, event_queue, is_async: bool = False, consumer_name: str = None, group_name: str = None):
        if event_id in self._claimed_message_ids:
            logger.debug(f"跳过已认领的消息 {event_id}")
            return event_id
        
        actual_event_id = event_id  
        parsed_event_data = None  
        
        if 'data' in event_data or b'data' in event_data:
            data_field = event_data.get('data') or event_data.get(b'data')
            if data_field:
                try:
                    if isinstance(data_field, bytes):
                        parsed_data = loads_str(data_field)
                    else:
                        parsed_data = data_field
                    if 'event_id' in parsed_data:
                        actual_event_id = parsed_data['event_id']
                    parsed_event_data = parsed_data
                except (ValueError, UnicodeDecodeError):
                    pass  
        
        final_event_data = parsed_event_data if parsed_event_data is not None else event_data
        
        routing = final_event_data.get("routing")
        
        actual_queue = final_event_data.get('queue', queue)

        if not group_name:
            prefixed_queue = self.get_prefixed_queue_name(queue)
            group_name = prefixed_queue

        offset = None
        if 'offset' in final_event_data:
            try:
                offset = int(final_event_data['offset'])
            except (ValueError, TypeError):
                pass
        elif 'offset' in event_data or b'offset' in event_data:
            offset_field = event_data.get('offset') or event_data.get(b'offset')
            if offset_field:
                try:
                    offset = int(offset_field)
                    final_event_data['offset'] = offset
                except (ValueError, TypeError):
                    pass

        task_item = {
            "queue": actual_queue,  
            "event_id": actual_event_id,
            "event_data": final_event_data,  
            "consumer": consumer_name,  
            "group_name": group_name,  
        }
        
        push_flag = True
        if routing:
            if agg_key := routing.get('agg_key'):
                self.solo_agg_task[queue][agg_key].append(
                    [routing, task_item]
                )
                push_flag = False
        
        if push_flag:
            if is_async:
                return ('async_put', task_item)
            else:
                self._put_task(event_queue, task_item)
        
        return event_id
    
    async def _execute_recovery_for_queue(self, queue: str, log_prefix: str = "Recovery") -> int:
        from jettask.utils.queue_matcher import find_matching_tasks
        task_names = find_matching_tasks(queue, self.app._tasks_by_queue, self.wildcard_mode)

        if not task_names:
            logger.debug(f"[{log_prefix}] No tasks found for queue {queue}")
            return 0

        total_recovered = 0

        for task_name in task_names:
            recovery_key = f"recovery_{task_name}"
            recovery = getattr(self, recovery_key, None)

            if not recovery:
                from jettask.worker.lifecycle import WorkerManager
                recovery = WorkerManager(
                    redis_client=self.redis_client,
                    async_redis_client=self.async_binary_redis_client,
                    redis_prefix=self.redis_prefix,
                    queue_formatter=lambda q: f"{self.redis_prefix}:QUEUE:{q}",
                    queue_registry=self.queue_registry,
                    app=self.app,
                    tasks=self.tasks,
                    task_event_queues=self.task_event_queues,
                    worker_id=self.worker_id
                )
                setattr(self, recovery_key, recovery)

            base_queue = queue.split(':')[0]

            try:
                current_consumer = self.get_consumer_name(base_queue)
            except Exception as e:
                logger.warning(f"[{log_prefix}] Failed to get consumer for queue {queue}: {e}")
                continue

            def get_event_queue_by_task(tn: str):
                if self.task_event_queues:
                    return self.task_event_queues.get(tn)
                return None

            try:
                recovered = await recovery.recover_offline_workers(
                    task_name=task_name,
                    event_queue=None,  
                    event_queue_callback=get_event_queue_by_task  
                )
                total_recovered += recovered

                if recovered > 0:
                    logger.debug(f"[{log_prefix}] Recovered {recovered} messages for task {task_name} on queue {queue}")
            except Exception as e:
                logger.error(f"[{log_prefix}] Error recovering task {task_name} on queue {queue}: {e}")
                continue

        return total_recovered

    async def handle_worker_offline_event(self, worker_id: str, queues: list = None):
        try:
            logger.debug(f"[Recovery Event] Received offline event for worker {worker_id}")
            
            if not queues:
                if self.app and hasattr(self.app, 'worker_state'):
                    worker_info = await self.app.worker_state.get_worker_info(worker_id)
                    if worker_info:
                        queues_str = worker_info.get('queues', '')
                        queues = queues_str.split(',') if queues_str else []
                else:
                    logger.warning(f"[Recovery Event] WorkerManager not available, cannot get worker info for {worker_id}")
                    return

            if not queues:
                logger.warning(f"[Recovery Event] No queues found for worker {worker_id}, skipping recovery")
                return

            if not self.task_event_queues:
                logger.warning(f"[Recovery Event] No task_event_queues available, recovered messages will not be executed")

            for queue in queues:
                if not queue.strip():
                    continue

                logger.debug(f"[Recovery Event] Triggering recovery for worker {worker_id} on queue {queue}")

                try:
                    recovered = await self._execute_recovery_for_queue(queue, log_prefix="Recovery Event")

                    if recovered > 0:
                        logger.debug(f"[Recovery Event] Recovered {recovered} messages from worker {worker_id} on queue {queue}")
                    else:
                        logger.debug(f"[Recovery Event] No messages to recover from worker {worker_id} on queue {queue}")
                except Exception as e:
                    logger.warning(f"[Recovery Event] Failed to recover queue {queue}: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Recovery Event] Error handling offline event for worker {worker_id}: {e}", exc_info=True)

    async def _perform_self_recovery(self, queues: set, event_queue: dict):
        logger.debug("[Recovery Self] Starting self-recovery for current worker...")

        current_worker_id = self.worker_id

        if not current_worker_id:
            logger.debug("[Recovery Self] No worker_id available, skipping self-recovery")
            return

        worker_key = f"{self.redis_prefix}:WORKER:{current_worker_id}"
        logger.debug(f"[Recovery Self] Checking pending messages for worker: {current_worker_id}")

        def get_event_queue_by_task(task_name: str):
            if event_queue:
                return event_queue.get(task_name)
            return None

        total_recovered = 0

        for queue in queues:
            try:
                base_queue = queue
                if ':' in queue and queue.rsplit(':', 1)[-1].isdigit():
                    base_queue = queue.rsplit(':', 1)[0]

                current_consumer = None
                for _ in range(5):
                    try:
                        current_consumer = self.get_consumer_name(base_queue)
                        if current_consumer:
                            if base_queue != queue:
                                priority_suffix = queue.rsplit(':', 1)[-1]
                                current_consumer = f"{current_consumer}:{priority_suffix}"
                            break
                    except:
                        pass
                    await asyncio.sleep(0.1)

                if not current_consumer:
                    logger.warning(f"[Recovery Self] Cannot get consumer for queue {queue}, skipping")
                    continue

                stream_key = f"{self.redis_prefix}:QUEUE:{queue}"

                worker_data = await self.async_redis_client.hgetall(worker_key)
                if not worker_data:
                    logger.debug(f"[Recovery Self] Worker {current_worker_id} has no data")
                    continue

                decoded_worker_data = {}
                for k, v in worker_data.items():
                    key = k.decode('utf-8') if isinstance(k, bytes) else k
                    value = v.decode('utf-8') if isinstance(v, bytes) else v
                    decoded_worker_data[key] = value

                group_infos = []
                for key, value in decoded_worker_data.items():
                    if key.startswith('group_info:'):
                        try:
                            group_info = json.loads(value)
                            if group_info.get('queue') == base_queue:
                                group_infos.append(group_info)
                        except Exception as e:
                            logger.error(f"[Recovery Self] Error parsing group_info: {e}")

                if not group_infos:
                    logger.debug(f"[Recovery Self] No group_info for queue {queue}")
                    continue

                for group_info in group_infos:
                    try:
                        task_name = group_info.get('task_name')
                        group_name = group_info.get('group_name')

                        if not task_name or not group_name:
                            continue

                        offline_consumer_name = group_info.get('consumer_name')

                        pending_info = await self.async_binary_redis_client.xpending(stream_key, group_name)
                        if not pending_info or pending_info.get('pending', 0) == 0:
                            continue

                        detailed_pending = await self.async_binary_redis_client.xpending_range(
                            stream_key, group_name,
                            min='-', max='+', count=100,
                            consumername=offline_consumer_name
                        )

                        if not detailed_pending:
                            continue

                        logger.debug(
                            f"[Recovery Self] Found {len(detailed_pending)} pending messages "
                            f"for worker {current_worker_id}, queue {queue}, task {task_name}"
                        )

                        message_ids = [msg['message_id'] for msg in detailed_pending]
                        claimed_messages = await self.async_binary_redis_client.xclaim(
                            stream_key, group_name, current_consumer,
                            min_idle_time=0,  
                            message_ids=message_ids
                        )

                        if claimed_messages:
                            logger.debug(
                                f"[Recovery Self] Claimed {len(claimed_messages)} messages "
                                f"from {offline_consumer_name} to {current_consumer}"
                            )

                            task_event_queue = get_event_queue_by_task(task_name)
                            if task_event_queue:
                                for msg_id, msg_data in claimed_messages:
                                    if isinstance(msg_id, bytes):
                                        msg_id = msg_id.decode('utf-8')

                                    data_field = msg_data.get(b'data') or msg_data.get('data')
                                    if data_field:
                                        try:
                                            import msgpack
                                            parsed_data = msgpack.unpackb(data_field, raw=False)
                                            parsed_data['_task_name'] = task_name
                                            parsed_data['queue'] = queue

                                            task_item = {
                                                'queue': queue,
                                                'event_id': msg_id,
                                                'event_data': parsed_data,
                                                'consumer': current_consumer,
                                                'group_name': group_name
                                            }

                                            await task_event_queue.put(task_item)
                                            total_recovered += 1
                                        except Exception as e:
                                            logger.error(f"[Recovery Self] Error processing message: {e}")
                            else:
                                logger.warning(f"[Recovery Self] No event_queue for task {task_name}")

                    except Exception as e:
                        logger.error(f"[Recovery Self] Error recovering group {group_info}: {e}", exc_info=True)

            except Exception as e:
                logger.error(f"[Recovery Self] Error recovering queue {queue}: {e}", exc_info=True)

        if total_recovered > 0:
            logger.debug(f"[Recovery Self] Self-recovery completed: recovered {total_recovered} messages")
        else:
            logger.debug("[Recovery Self] Self-recovery completed: no pending messages found")

    async def _update_read_offset(self, queue: str, group_name: str, offset: int):
        try:
            if offset is None:
                return

            read_offset_key = f"{self.redis_prefix}:READ_OFFSETS"

            task_name = group_name.split(':')[-1]

            field = f"{queue}:{task_name}"

            await self.async_redis_client.eval(
                UPDATE_MAX_OFFSET_LUA,
                2,  
                read_offset_key,  
                field,  
                offset  
            )
            logger.debug(f"Updated read offset for {field}: {offset}")
        except Exception as e:
            logger.error(f"Error updating read offset: {e}")


    async def _initial_queue_discovery(self):
        if not self.wildcard_mode:
            return

        try:
            logger.debug("[QueueDiscovery] Performing initial queue discovery...")

            queue_members = await self.async_redis_client.smembers(
                self._queue_registry_key.encode()
            )

            discovered_queues = set()
            for queue_bytes in queue_members:
                queue_name = queue_bytes.decode('utf-8') if isinstance(queue_bytes, bytes) else str(queue_bytes)
                discovered_queues.add(queue_name)

            if not discovered_queues:
                logger.warning("[QueueDiscovery] QUEUE_REGISTRY is empty, initializing from existing data...")

                await self.queue_registry.initialize_from_existing_data()
                discovered_queues = await self.queue_registry.get_all_queues()

            logger.debug(f"[QueueDiscovery] Initial discovery found {len(discovered_queues)} queues: {discovered_queues}")

            self._discovered_queues = discovered_queues
            self.queues = [q for q in discovered_queues if q != '*']

            self.consumer_config['queues'] = self.queues

        except Exception as e:
            logger.error(f"[QueueDiscovery] Initial discovery failed: {e}", exc_info=True)
            self._discovered_queues = set()
            self.queues = []


    async def _check_queues_with_messages(
        self,
        all_queues: list,
        check_backlog: dict,
        group_name: str
    ) -> list:
        queues_with_messages = []

        try:
            queue_offsets_key = f"{self.redis_prefix}:QUEUE_OFFSETS"
            read_offsets_key = f"{self.redis_prefix}:READ_OFFSETS"

            pipe = self.async_redis_client.pipeline()

            for q in all_queues:
                actual_queue = q.replace(f"{self.redis_prefix}:QUEUE:", "")
                pipe.hget(queue_offsets_key, actual_queue)

            task_name = group_name.split(':')[-1]

            for q in all_queues:
                actual_queue = q.replace(f"{self.redis_prefix}:QUEUE:", "")
                field = f"{actual_queue}:{task_name}"
                pipe.hget(read_offsets_key, field)

            results = await pipe.execute()

            half_len = len(all_queues)
            for i, q in enumerate(all_queues):
                if check_backlog.get(q, True):
                    queues_with_messages.append(q)
                    logger.debug(f"Queue {q} needs to read pending messages, skipping offset check")
                    continue

                sent_offset = results[i]  
                read_offset = results[half_len + i]  

                sent = int(sent_offset) if sent_offset else 0
                read = int(read_offset) if read_offset else 0

                if sent > read:
                    queues_with_messages.append(q)
                    logger.debug(f"Queue {q} has {sent - read} unread messages (sent={sent}, read={read})")

            if not queues_with_messages:
                logger.debug("No queues have unread messages, will wait for new messages")

        except Exception as e:
            logger.debug(f"Failed to check queue offsets: {e}")
            queues_with_messages = all_queues

        return queues_with_messages

    async def _ensure_group_info_for_all_queues(
        self,
        all_queues: list,
        task_name: str,
        consumer_name: str,
        group_name: str
    ):
        for queue in all_queues:
            await self._ensure_consumer_group_and_record_info(
                queue, task_name, consumer_name, group_name
            )

        logger.debug(f"Restored group_info for {len(all_queues)} queues for task {task_name}")

    async def _initialize_queue_for_task(
        self,
        queue_name: str,
        task_name: str,
        consumer_name: str,
        lastid: dict,
        check_backlog: dict,
        base_group_name: str
    ):
        await self._ensure_consumer_group_and_record_info(
            queue_name, task_name, consumer_name, base_group_name
        )

        lastid[queue_name] = "0"
        check_backlog[queue_name] = True

        logger.debug(f"Initialized queue {queue_name} for task {task_name}")

    async def _initialize_all_queues_for_task(
        self,
        all_queues: list,
        task_name: str,
        consumer_name: str,
        lastid: dict,
        check_backlog: dict,
        base_group_name: str
    ) -> list:
        for queue in all_queues:
            await self._initialize_queue_for_task(
                queue, task_name, consumer_name, lastid, check_backlog, base_group_name
            )

        logger.debug(f"Initialized {len(all_queues)} queues for task {task_name}")

        return all_queues

    async def _read_messages_from_queues(
        self,
        all_queues: list,
        check_backlog: dict,
        group_name: str,
        lastid: dict,
        task_name: str,
        messages_needed: int
    ) -> list:
        messages = []

        queues_with_messages = await self._check_queues_with_messages(
            all_queues, check_backlog, group_name
        )

        if not queues_with_messages:
            return messages

        for q in queues_with_messages:
            if messages_needed <= 0:
                break  

            q_bytes = q.encode() if isinstance(q, str) else q
            if check_backlog.get(q, True):
                myid = lastid.get(q, "0-0")
            else:
                myid = ">"
            myid_bytes = myid.encode() if isinstance(myid, str) else myid

            try:
                q_messages = await self.async_binary_redis_client.xreadgroup(
                    groupname=group_name,
                    consumername=self.worker_id,
                    streams={q_bytes: myid_bytes},
                    count=messages_needed,  
                    block=100  
                )
                logger.debug(f'{group_name=} {q_bytes=} {self.worker_id=} {q_messages=}')
                if q_messages:
                    messages.extend(q_messages)
                    messages_read = len(q_messages[0][1]) if q_messages else 0
                    messages_needed -= messages_read

                    if messages_read > 0 and messages_needed > 0:
                        break  

            except Exception as e:
                if "NOGROUP" in str(e):
                    logger.warning(f"NOGROUP error for queue {q}, recreating consumer group...")
                    try:
                        await self._initialize_queue_for_task(
                            q, task_name, self.worker_id, lastid, check_backlog, base_group_name=group_name
                        )

                        if q not in all_queues:
                            all_queues.append(q)
                            logger.debug(f"Re-added queue {q} to all_queues after NOGROUP recovery")
                    except Exception as recreate_error:
                        logger.error(f"Failed to recreate consumer group for {q}: {recreate_error}")
                else:
                    logger.debug(f"Error reading from queue {q}: {e}")
                continue

        return messages

    async def _report_delivered_offsets(self, messages: list, group_name: str):
        try:
            from jettask.utils.stream_backlog import report_delivered_offset
            for msg in messages:
                stream_name = msg[0]
                if isinstance(stream_name, bytes):
                    stream_name = stream_name.decode('utf-8')
                queue_name = stream_name.replace(f"{self.redis_prefix}:STREAM:", "")
                await report_delivered_offset(
                    self.async_redis_client,
                    self.redis_prefix,
                    queue_name,
                    group_name,
                    [msg]
                )
        except Exception as e:
            logger.debug(f"Failed to report delivered offset: {e}")

    async def listen_event_by_task(self, task_obj: "Task", queue_name: str, prefetch_multiplier: int):
        check_backlog = {}  
        lastid = {}  
        consecutive_errors = 0
        max_consecutive_errors = 5

        task_name = task_obj.name

        task_event_queue = self.task_event_queues.get(task_name)
        if not task_event_queue:
            logger.error(f"No event queue found for task {task_name}")
            return


        all_queues = []
        prefixed_queue = queue_name 

        group_name = f"{prefixed_queue}:{task_name}"


        last_priority_update = 0

        while not self._stop_reading:
            current_time = time.time()
            if current_time - last_priority_update >= 1:  
                new_all_queues = await self.get_priority_queues_direct(queue_name)
                if new_all_queues != all_queues:

                    new_queues = set(new_all_queues) - set(all_queues)
                    if new_queues:
                        for new_queue in new_queues:
                            await self._initialize_queue_for_task(
                                new_queue, task_name, self.worker_id, lastid, check_backlog, group_name
                            )

                    all_queues = new_all_queues
                last_priority_update = current_time


            current_queue_size = task_event_queue.qsize() if hasattr(task_event_queue, 'qsize') else 0
            if current_queue_size >= prefetch_multiplier:
                await asyncio.sleep(0.01)  
                continue

            messages_needed = prefetch_multiplier - current_queue_size

            if messages_needed <= 0:
                await asyncio.sleep(0.01)
                continue

            messages = await self._read_messages_from_queues(
                all_queues, check_backlog, group_name, lastid, task_name, messages_needed
            )

            if not messages:
                await asyncio.sleep(0.2)
                continue


            try:
                consecutive_errors = 0

                await self._report_delivered_offsets(messages, group_name)
                
                skip_message_ids = []
                
                max_offsets_per_queue = {}
                
                for message in messages:
                    stream_name = message[0]
                    if isinstance(stream_name, bytes):
                        stream_name = stream_name.decode('utf-8')
                    
                    if len(message[1]) == 0:
                        check_backlog[stream_name] = False
                    
                    for event in message[1]:
                        event_id = event[0]
                        lastid[stream_name] = event_id
                        if isinstance(event_id, bytes):
                            event_id = event_id.decode('utf-8')
                        event_data = event[1]
                        
                        should_process = True
                        
                        try:
                            if b'data' in event_data or 'data' in event_data:
                                data_field = event_data.get(b'data') or event_data.get('data')
                                
                                parsed_data = loads_str(data_field)

                            
                                target_tasks = parsed_data.get('_target_tasks', None)
                                if target_tasks and task_name not in target_tasks:
                                    should_process = False
                                
                                if should_process:
                                    parsed_data['_task_name'] = task_name
                                    
                                    offset_field = event_data.get(b'offset') or event_data.get('offset')
                                    message_offset = None
                                    if offset_field:
                                        if isinstance(offset_field, bytes):
                                            offset_field = offset_field.decode('utf-8')
                                        parsed_data['offset'] = offset_field
                                        try:
                                            message_offset = int(offset_field)
                                        except (ValueError, TypeError):
                                            pass
                                    
                                    event_data.clear()
                                    for key, value in parsed_data.items():
                                        event_data[key] = value
                                    
                                    if message_offset is not None:
                                        actual_queue_name = stream_name.replace(f"{self.redis_prefix}:QUEUE:", "")
                                        if actual_queue_name not in max_offsets_per_queue:
                                            max_offsets_per_queue[actual_queue_name] = message_offset
                                        else:
                                            max_offsets_per_queue[actual_queue_name] = max(max_offsets_per_queue[actual_queue_name], message_offset)
                                    
                                    logger.debug(f"Task {task_name} will process message {event_id}")
                            else:
                                should_process = False
                        except Exception as e:
                            logger.error(f"Task {task_name}: Error parsing message data: {e}")
                        
                        if should_process:
                            actual_queue = event_data.get('queue', queue_name)

                            result = self._process_message_common(
                                event_id, event_data, actual_queue, task_event_queue,
                                is_async=True, consumer_name=self.worker_id, group_name=group_name
                            )
                            if isinstance(result, tuple) and result[0] == 'async_put':
                                await self._async_put_task(task_event_queue, result[1])
                                logger.debug(f"Put task {event_id} into task_event_queue")
                        else:
                            skip_message_ids.append(event_id)
                        
                
                if skip_message_ids:
                    group_name_bytes = group_name.encode() if isinstance(group_name, str) else group_name
                    for q in all_queues:
                        q_bytes = q.encode() if isinstance(q, str) else q
                        try:
                            await self.async_binary_redis_client.xack(q_bytes, group_name_bytes, *skip_message_ids)
                        except:
                            pass  
                    logger.debug(f"Task {task_name} batch ACKed {len(skip_message_ids)} skipped messages")

                if max_offsets_per_queue:
                    for queue_name, max_offset in max_offsets_per_queue.items():
                        asyncio.create_task(self._update_read_offset(queue_name, group_name, max_offset))
                    logger.debug(f"Updated read offsets for {len(max_offsets_per_queue)} queues")
                    
            except Exception as e:
                error_msg = str(e)
                import traceback
                traceback.print_exc()
                logger.error(f"Error in task listener {task_name}: {e}")
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Too many errors for task {task_name}, restarting...")
                    consecutive_errors = 0
                await asyncio.sleep(min(consecutive_errors, 5))


    async def _listen_task(self, task_obj: "Task", prefetch_multiplier: int):
        if task_obj.is_wildcard_queue:
            await self._listen_task_with_wildcard(task_obj, prefetch_multiplier)
        else:
            await self._start_single_queue_listener(task_obj, task_obj.queue, prefetch_multiplier)

    async def _start_single_queue_listener(self, task_obj: "Task", queue_name: str, prefetch_multiplier: int):
        task_name = task_obj.name

        await self._register_queue_for_task(queue_name, task_name)

        logger.debug(f"[Task: {task_name}] 开始监听队列: {queue_name}")

        await self.listen_event_by_task(
            task_obj,
            queue_name,
            prefetch_multiplier
        )

    async def _listen_task_with_wildcard(self, task_obj: "Task", prefetch_multiplier: int):
        task_name = task_obj.name
        wildcard_pattern = task_obj.queue

        logger.debug(f"[Task: {task_name}] 开始监听通配符队列: {wildcard_pattern}")

        monitored_queues = set()

        discovery_interval = 5.0  

        while not self._stop_reading:
            try:
                matched_queues = await self.queue_registry.discover_matching_queues(wildcard_pattern)

                new_queues = matched_queues - monitored_queues

                if new_queues:
                    logger.debug(f"[Task: {task_name}] 发现新队列: {list(new_queues)}")

                    for queue_name in new_queues:
                        listen_task = asyncio.create_task(
                            self._start_single_queue_listener(
                                task_obj,
                                queue_name,
                                prefetch_multiplier
                            )
                        )
                        self._background_tasks.append(listen_task)
                        monitored_queues.add(queue_name)

                        logger.debug(f"[Task: {task_name}] 已为队列 {queue_name} 启动监听")

                await asyncio.sleep(discovery_interval)

            except asyncio.CancelledError:
                logger.debug(f"[Task: {task_name}] 通配符队列监听已取消")
                break
            except Exception as e:
                logger.error(f"[Task: {task_name}] 通配符队列监听出错: {e}", exc_info=True)
                await asyncio.sleep(discovery_interval)

    async def _register_queue_for_task(self, queue: str, task_name: str):
        if queue not in self.queues:
            self.queues.append(queue)
            self.queues.sort()

            self._queue_stop_flags[queue] = False

            try:
                if self.worker_id and self.app and hasattr(self.app, 'worker_state'):
                    await self.app.worker_state.update_worker_field(
                        self.worker_id,
                        'queues',
                        ','.join(sorted(self.queues))
                    )
                    logger.debug(f"[Task: {task_name}] 新增队列 {queue}，当前总队列: {self.queues}")
            except Exception as e:
                logger.error(f"[Task: {task_name}] 更新 worker queues 字段失败: {e}", exc_info=True)


    async def listening_event(self, prefetch_multiplier: int = 1):
        if not self.task_event_queues:
            raise RuntimeError("task_event_queues not initialized")

        if not isinstance(self.task_event_queues, dict):
            raise TypeError(f"task_event_queues must be a dict[str, asyncio.Queue], got {type(self.task_event_queues)}")


        self._background_tasks = []

        if not self.tasks:
            raise RuntimeError("No tasks configured for EventPool")

        tasks = []

        if not self.worker_id:
            raise RuntimeError("Worker ID not initialized, cannot start listeners")

        for task_name, task_obj in self.tasks.items():
            if not task_obj:
                logger.warning(f"Task {task_name} has no task object, skipping...")
                continue

            if not task_obj.queue:
                logger.warning(f"Task {task_name} has no queue configured, skipping...")
                continue

            logger.debug(f"为任务 {task_name} 启动监听，队列模式: {task_obj.queue}, worker_id: {self.worker_id}")

            task = asyncio.create_task(
                self._listen_task(
                    task_obj=task_obj,
                    prefetch_multiplier=prefetch_multiplier
                )
            )
            tasks.append(task)
            self._background_tasks.append(task)



        recovery_task = asyncio.create_task(
            self.offline_recovery.start(recovery_interval=30.0)
        )
        self._background_tasks.append(recovery_task)
        logger.debug("[Recovery] Started offline worker recovery loop")

        cleanup_task = asyncio.create_task(
            self.offline_recovery.start_cleanup_task(cleanup_interval=86400.0)
        )
        self._background_tasks.append(cleanup_task)
        logger.debug("[Cleanup] Started offline worker cleanup task")

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.debug("listening_event tasks cancelled, cleaning up...")

            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
            if self._background_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self._background_tasks, return_exceptions=True),
                        timeout=0.2
                    )
                except asyncio.TimeoutError:
                    logger.debug("Some background tasks did not complete in time")
            raise

    def read_pending(self, groupname: str, queue: str, asyncio: bool = False):
        client = self.get_redis_client(asyncio, binary=True)
        prefixed_queue = self.get_prefixed_queue_name(queue)
        return client.xpending(prefixed_queue, groupname)

    def ack(self, queue, event_id, asyncio: bool = False):
        client = self.get_redis_client(asyncio, binary=True)
        prefixed_queue = self.get_prefixed_queue_name(queue)
        result = client.xack(prefixed_queue, prefixed_queue, event_id)
        if event_id in self._claimed_message_ids:
            self._claimed_message_ids.remove(event_id)
        return result
    def _safe_redis_operation(self, operation, *args, max_retries=3, **kwargs):
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Redis操作失败，已重试{max_retries}次: {e}")
                    raise

                logger.warning(f"Redis操作失败，第{attempt + 1}次重试: {e}")
                time.sleep(min(2 ** attempt, 5))  
    
    def cleanup(self):
        self._stop_reading = True

        if hasattr(self, 'offline_recovery') and self.offline_recovery:
            if hasattr(self.offline_recovery, 'stop_recovery'):
                self.offline_recovery.stop_recovery()
            if hasattr(self.offline_recovery, 'stop_cleanup'):
                self.offline_recovery.stop_cleanup()

        logger.debug("EventPool cleanup completed")