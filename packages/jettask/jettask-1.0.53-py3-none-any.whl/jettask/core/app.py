import os

import time
from datetime import datetime
from ..utils.serializer import dumps, loads, dumps_str, loads_str
import signal

import asyncio
import logging
import contextlib
import importlib
import time 

from typing import List


from .message import TaskMessage
from .task import Task
from .enums import TaskStatus
from jettask.messaging.event_pool import EventPool
from ..executor.orchestrator import ProcessOrchestrator
from ..utils import gen_task_name
from ..scheduler import TaskScheduler
from ..exceptions import TaskTimeoutError, TaskExecutionError, TaskNotFoundError
from jettask.db.connector import get_sync_redis_client, get_async_redis_client

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    UVLOOP_AVAILABLE = True
except ImportError:
    UVLOOP_AVAILABLE = False

logger = logging.getLogger('app')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if UVLOOP_AVAILABLE:
    logger.debug("Using uvloop for better performance")
else:
    logger.debug("uvloop not available, using default asyncio event loop")


class Jettask(object):

    def __init__(self, redis_url: str = None, include: list = None, max_connections: int = None,
                 consumer_config: dict = None, tasks=None,
                 redis_prefix: str = None, scheduler_config: dict = None, pg_url: str = None,
                 task_center=None, 
                 heartbeat_interval: float = 5.0, heartbeat_timeout: float = 15.0,
                 scanner_interval: float = 2) -> None:
        self._tasks = tasks or {}
        self._task_queues = {}  
        self.asyncio = False
        self.include = include or []

        self.task_center = None  
        self._task_center_config = None
        self._original_redis_url = redis_url
        self._original_pg_url = pg_url

        self.redis_url = redis_url or os.environ.get('JETTASK_REDIS_URL')
        self.pg_url = pg_url or os.environ.get('JETTASK_PG_URL')
        self.max_connections = max_connections if max_connections is not None else int(os.environ.get('JETTASK_MAX_CONNECTIONS', '500'))
        self.redis_prefix = redis_prefix or os.environ.get('JETTASK_REDIS_PREFIX', 'jettask')

        if not self.redis_url:
            raise ValueError(
                "必须提供 redis_url 参数！\n\n"
                "请通过以下任一方式配置:\n"
                "  1. 初始化时传参:\n"
                "     app = Jettask(redis_url='redis://localhost:6379/0')\n\n"
                "  2. 设置环境变量:\n"
                "     export JETTASK_REDIS_URL='redis://localhost:6379/0'\n\n"
                "  3. 在 .env 文件中配置:\n"
                "     JETTASK_REDIS_URL=redis://localhost:6379/0\n"
            )

        self.consumer_config = consumer_config or {}
        self.scheduler_config = scheduler_config or {}

        if heartbeat_timeout <= heartbeat_interval * 2:
            raise ValueError(
                f"heartbeat_timeout ({heartbeat_timeout}s) 必须大于 heartbeat_interval ({heartbeat_interval}s) 的 2 倍！\n\n"
                f"当前配置会导致 worker 在正常心跳间隔内就被判定为超时。\n"
                f"建议配置：heartbeat_timeout >= heartbeat_interval * 3\n"
                f"例如：heartbeat_interval=5.0, heartbeat_timeout=15.0"
            )
        self.heartbeat_interval = heartbeat_interval  
        self.heartbeat_timeout = heartbeat_timeout    
        self.scanner_interval = scanner_interval      

        if task_center:
            self.mount_task_center(task_center)

        self.STATUS_PREFIX = f"{self.redis_prefix}:STATUS:"
        self.RESULT_PREFIX = f"{self.redis_prefix}:RESULT:"
        
        self._loads = loads
        self._dumps = dumps
        
        self.scheduler = None
        self._scheduler_db_url = None

        self._status_prefix = self.STATUS_PREFIX
        self._result_prefix = self.RESULT_PREFIX

        self.worker_state_manager = None

        self._worker_state = None


        self._cleanup_done = False
        self._should_exit = False
        self._worker_started = False
        self._handlers_registered = False

        self._registry = None
        self._registry_initialized = False

        self._pending_rate_limits = {}
   
    
    def _load_config_from_task_center(self):
        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                return False
            except RuntimeError:
                loop = asyncio.new_event_loop()
                if self.task_center:
                    if self.task_center._initialized:
                        config = self.task_center._config
                    else:
                        success = loop.run_until_complete(self.task_center.connect(asyncio=True))
                        if success:
                            config = self.task_center._config
                        else:
                            config = None
                else:
                    config = None
                loop.close()
            
            if config:
                redis_config = config.get('redis_config', {})
                pg_config = config.get('pg_config', {})
                if redis_config:
                    redis_host = redis_config.get('host', 'localhost')
                    redis_port = redis_config.get('port', 6379)
                    redis_password = redis_config.get('password')
                    redis_db = redis_config.get('db', 0)
                    
                    if redis_password:
                        self.redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
                    else:
                        self.redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
                    
                    logger.debug(f"从任务中心加载Redis配置: {redis_host}:{redis_port}/{redis_db}")
                
                if pg_config:
                    pg_host = pg_config.get('host', 'localhost')
                    pg_port = pg_config.get('port', 5432)
                    pg_user = pg_config.get('user', 'postgres')
                    pg_password = pg_config.get('password', '')
                    pg_database = pg_config.get('database', 'jettask')
                    
                    self.pg_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
                    logger.debug(f"从任务中心加载PostgreSQL配置: {pg_host}:{pg_port}/{pg_database}")
                
                self._task_center_config = config
                
                if self.task_center and self.task_center.redis_prefix != "jettask":
                    self.redis_prefix = self.task_center.redis_prefix
                    self.STATUS_PREFIX = f"{self.redis_prefix}:STATUS:"
                    self.RESULT_PREFIX = f"{self.redis_prefix}:RESULT:"
                
                if hasattr(self, '_redis'):
                    delattr(self, '_redis')
                if hasattr(self, '_async_redis'):
                    delattr(self, '_async_redis')
                if hasattr(self, '_ep'):
                    delattr(self, '_ep')
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.warning(f"从任务中心加载配置失败，使用手动配置: {e}")
            self.redis_url = self._original_redis_url
            self.pg_url = self._original_pg_url
    
    def mount_task_center(self, task_center):
        self.task_center = task_center
        
        if task_center and task_center._initialized:
            if task_center.redis_config:
                redis_url = task_center.get_redis_url()
                if redis_url:
                    self.redis_url = redis_url
                    
            if task_center.pg_config:
                pg_url = task_center.get_pg_url()
                if pg_url:
                    self.pg_url = pg_url
            
            self.redis_prefix = task_center.redis_prefix
            self.STATUS_PREFIX = f"{self.redis_prefix}:STATUS:"
            self.RESULT_PREFIX = f"{self.redis_prefix}:RESULT:"
            self.QUEUE_PREFIX = f"{self.redis_prefix}:QUEUE:"
            self.STREAM_PREFIX = f"{self.redis_prefix}:STREAM:"
            self.TASK_PREFIX = f"{self.redis_prefix}:TASK:"
            self.SCHEDULER_PREFIX = f"{self.redis_prefix}:SCHEDULED:"
            self.LOCK_PREFIX = f"{self.redis_prefix}:LOCK:"
            
            self._task_center_config = {
                'redis_config': task_center.redis_config,
                'pg_config': task_center.pg_config,
                'namespace_name': task_center.namespace_name,
                'version': task_center.version
            }
    
    
    def _setup_cleanup_handlers(self):
        if self._handlers_registered:
            return
        
        self._handlers_registered = True
        
        def signal_cleanup_handler(signum=None, frame=None):
            if self._cleanup_done:
                return
            if self._worker_started:
                logger.debug("Received shutdown signal, cleaning up...")
            self.cleanup()
            if signum:
                self._should_exit = True
        
        def atexit_cleanup_handler():
            if self._cleanup_done:
                return
            self.cleanup()
        
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_cleanup_handler)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, signal_cleanup_handler)
        
        import atexit
        atexit.register(atexit_cleanup_handler)
    
    def cleanup(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        
        if self._worker_started:
   
            
            if hasattr(self, 'ep') and self.ep:
                self.ep.cleanup()
            

        else:
            if hasattr(self, 'ep') and self.ep:
                self.ep.cleanup()


    @property
    def async_redis(self):
        if self.task_center and self.task_center.is_enabled and not self._task_center_config:
            self._load_config_from_task_center()

        return get_async_redis_client(
            redis_url=self.redis_url,
            decode_responses=True,
            max_connections=self.max_connections,
            socket_timeout=None  
        )

    @property
    def redis(self):

        return get_sync_redis_client(
            redis_url=self.redis_url,
            decode_responses=True,
            max_connections=self.max_connections
        )

    @property
    def binary_redis(self):
        return get_sync_redis_client(
            redis_url=self.redis_url,
            decode_responses=False,
            max_connections=self.max_connections
        )

    @property
    def async_binary_redis(self):
        return get_async_redis_client(
            redis_url=self.redis_url,
            decode_responses=False,
            max_connections=self.max_connections,
            socket_timeout=None
        )

    @property
    def worker_state(self):
        if self._worker_state is None:
            from jettask.worker.lifecycle import WorkerManager
            self._worker_state = WorkerManager(
                redis_client=self.redis,
                async_redis_client=self.async_redis,
                redis_prefix=self.redis_prefix
            )
            logger.debug("Initialized WorkerManager for app")
        return self._worker_state

    @property
    def ep(self):
        name = "_ep"
        if hasattr(self, name):
            ep = getattr(self, name)
        else:
            consumer_config = self.consumer_config.copy() if self.consumer_config else {}
            consumer_config['redis_prefix'] = self.redis_prefix


            task_event_queues = {}

            ep = EventPool(
                redis_client=self.redis,
                async_redis_client=None,  
                task_event_queues=task_event_queues,
                tasks=self._tasks,
                queue_registry=None,  
                offline_recovery=self.worker_state_manager,  
                redis_url=self.redis_url,
                consumer_config=consumer_config,
                redis_prefix=self.redis_prefix,
                app=self
            )
            setattr(self, name, ep)
        return ep

    @property
    def registry(self):
        if self._registry_initialized and self._registry:
            return self._registry

        from ..messaging.registry import QueueRegistry

        self._registry = QueueRegistry(
            redis_client=self.redis,  
            async_redis_client=self.async_redis,  
            redis_prefix=self.redis_prefix
        )

        self._registry_initialized = True
        return self._registry

    def clear(self):
        if hasattr(self, "process"):
            delattr(self, "process")
        if hasattr(self, "_ep"):
            delattr(self, "_ep")
        if hasattr(self, "_registry"):
            self._registry = None
            self._registry_initialized = False

    def get_task_by_name(self, name: str) -> Task:
        task = self._tasks.get(name)
        if task:
            return task
        
        if '.' not in name:
            for task_key, task_obj in self._tasks.items():
                if '.' in task_key:
                    _, func_name = task_key.rsplit('.', 1)
                    if func_name == name:
                        return task_obj
                elif task_key == name:
                    return task_obj
        
        return None

    def get_task_config(self, task_name: str) -> dict:
        task = self.get_task_by_name(task_name)
        if not task:
            return None

        return {
            'auto_ack': getattr(task, 'auto_ack', True),
            'queue': getattr(task, 'queue', None),
            'timeout': getattr(task, 'timeout', None),
            'max_retries': getattr(task, 'max_retries', 0),
            'retry_delay': getattr(task, 'retry_delay', None),
        }

    def include_module(self, modules: list):
        self.include += modules

    def _task_from_fun(
        self, fun, name=None, base=None, queue=None, bind=False, retry_config=None, rate_limit=None, auto_ack=True, **options
    ) -> Task:
        name = name or gen_task_name(fun.__name__, fun.__module__)
        base = base or Task


        if name not in self._tasks:
            run = staticmethod(fun)
            task: Task = type(
                fun.__name__,
                (base,),
                dict(
                    {
                        "app": self,
                        "name": name,
                        "run": run,
                        "queue": queue,
                        "retry_config": retry_config,  
                        "rate_limit": rate_limit,  
                        "auto_ack": auto_ack,  
                        "_decorated": True,
                        "__doc__": fun.__doc__,
                        "__module__": fun.__module__,
                        "__annotations__": fun.__annotations__,
                        "__wrapped__": run,
                    },
                    **options,
                ),
            )()
            task.bind_app(self)
            with contextlib.suppress(AttributeError):
                task.__qualname__ = fun.__qualname__
            self._tasks[task.name] = task

            if queue:
                self._task_queues[name] = queue

            if rate_limit:
                if isinstance(rate_limit, int) and rate_limit > 0:
                    self._register_rate_limit(name, rate_limit)
                elif hasattr(rate_limit, 'to_dict'):
                    self._register_rate_limit_config(name, rate_limit)
            else:
                from jettask.utils.rate_limit.limiter import RateLimiterManager

                RateLimiterManager.unregister_rate_limit_config(
                    redis_client=self.redis,
                    task_name=name,
                    redis_prefix=self.redis_prefix
                )
        else:
            task = self._tasks[name]
        return task

    def _register_rate_limit(self, task_name: str, qps_limit: int):
        from jettask.utils.rate_limit.config import QPSLimit

        config = QPSLimit(qps=qps_limit)
        self._pending_rate_limits[task_name] = config
        logger.debug(f"存储任务 {task_name} 的 QPS 限流配置，将在 start() 时注册")

    def _register_rate_limit_config(self, task_name: str, config):
        self._pending_rate_limits[task_name] = config
        logger.debug(f"存储任务 {task_name} 的限流配置，将在 start() 时注册")

    def _apply_pending_rate_limits(self):
        if not self._pending_rate_limits:
            return

        from jettask.utils.rate_limit.limiter import RateLimiterManager

        for task_name, config in self._pending_rate_limits.items():
            try:
                RateLimiterManager.register_rate_limit_config(
                    redis_client=self.redis,
                    task_name=task_name,
                    config=config,
                    redis_prefix=self.redis_prefix
                )
                logger.debug(f"已注册任务 {task_name} 的限流配置")
            except Exception as e:
                logger.error(f"注册任务 {task_name} 的限流配置失败: {e}")

        logger.debug(f"已注册 {len(self._pending_rate_limits)} 个任务的限流配置")

    def _get_queues_from_tasks(self, task_names: List[str]) -> List[str]:
        queues = []
        for task_name in task_names:
            if task_name not in self._task_queues:
                available_tasks = list(self._task_queues.keys())
                raise ValueError(
                    f"任务 '{task_name}' 不存在或未配置队列。\n"
                    f"已注册的任务: {', '.join(available_tasks) if available_tasks else '(无)'}"
                )

            queue = self._task_queues[task_name]

            if queue not in queues:
                queues.append(queue)

        logger.debug(f"从 {len(task_names)} 个任务获取到 {len(queues)} 个队列: {queues}")
        return queues

    def get_tasks_by_queue(self, queue_name: str) -> List[str]:
        return [task_name for task_name, queue in self._task_queues.items() if queue == queue_name]

    def task(
        self,
        name: str = None,
        queue: str = None,
        base: Task = None,
        max_retries: int = 0,
        retry_backoff: bool = True,  
        retry_backoff_max: float = 60,  
        retry_on_exceptions: tuple = None,  
        rate_limit: int = None,  
        auto_ack: bool = True,  
        *args,
        **kwargs,
    ):
        def _create_task_cls(fun):
            retry_config = None
            if max_retries > 0:
                retry_config = {
                    'max_retries': max_retries,
                    'retry_backoff': retry_backoff,
                    'retry_backoff_max': retry_backoff_max,
                }
                if retry_on_exceptions:
                    retry_config['retry_on_exceptions'] = [
                        exc if isinstance(exc, str) else exc.__name__
                        for exc in retry_on_exceptions
                    ]

            return self._task_from_fun(
                fun,
                name,
                base,
                queue,
                retry_config=retry_config,
                rate_limit=rate_limit,
                auto_ack=auto_ack,  
                *args,
                **kwargs
            )

        return _create_task_cls
    
    def include_router(self, router, prefix: str = None):
        from ..task.router import TaskRouter
        
        if not isinstance(router, TaskRouter):
            raise TypeError(f"Expected TaskRouter, got {type(router)}")
        
        tasks = router.get_tasks()
        
        for task_name, task_config in tasks.items():
            config = task_config.copy()
            
            if prefix:
                if config.get('name'):
                    config['name'] = f"{prefix}.{config['name']}"
                else:
                    config['name'] = f"{prefix}.{task_name}"
            
            func = config.pop('func')
            name = config.pop('name', task_name)
            queue = config.pop('queue', None)
            
            retry_config = {}
            if 'max_retries' in config:
                retry_config['max_retries'] = config.pop('max_retries', 0)
            if 'retry_delay' in config:
                retry_config['retry_backoff_max'] = config.pop('retry_delay', 60)
            
            self._task_from_fun(
                func,
                name=name,
                queue=queue,
                retry_config=retry_config if retry_config else None,
                **config
            )
    
    def send_tasks(self, messages: list, asyncio: bool = False):
        if asyncio:
            return self._send_tasks_async(messages)
        else:
            return self._send_tasks_sync(messages)

    def ack(self, ack_items: list):
        if not ack_items:
            return

        if not hasattr(self, '_executor_core') or not self._executor_core:
            logger.warning("ACK can only be called in worker context")
            return

        for item in ack_items:
            if isinstance(item, dict):
                queue = item['queue']
                event_id = item['event_id']
                group_name = item.get('group_name')
                offset = item.get('offset')
            elif isinstance(item, (tuple, list)):
                if len(item) >= 3:
                    queue, event_id, group_name = item[0], item[1], item[2]
                    offset = item[3] if len(item) > 3 else None
                elif len(item) == 2:
                    logger.error(
                        f"Invalid ACK item format: {item}. "
                        f"group_name is required. Use (queue, event_id, group_name) or ctx.acks([event_ids])"
                    )
                    continue
                else:
                    logger.error(f"Invalid ACK item format: {item}")
                    continue
            else:
                logger.error(f"Invalid ACK item type: {type(item)}")
                continue

            if not group_name:
                logger.error(
                    f"group_name is required for ACK. item={item}. "
                    f"Use ctx.acks([event_ids]) for automatic group_name injection."
                )
                continue

            self._executor_core.pending_acks.append((queue, event_id, group_name, offset))
            logger.debug(f"Added to pending_acks: queue={queue}, event_id={event_id}, group_name={group_name}")

        if len(self._executor_core.pending_acks) >= 100:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self._executor_core._flush_all_buffers())
            except RuntimeError:
                pass

    def _send_tasks_sync(self, messages: list):
        if not messages:
            return []

        results = []

        queue_messages = {}
        for msg in messages:
            if isinstance(msg, dict):
                msg = TaskMessage.from_dict(msg)
            elif not isinstance(msg, TaskMessage):
                raise ValueError(f"Invalid message type: {type(msg)}. Expected TaskMessage or dict")

            msg.validate()

            actual_queue = msg.queue
            if msg.priority is not None:
                actual_queue = f"{msg.queue}:{msg.priority}"
                msg.queue = actual_queue

            if actual_queue not in queue_messages:
                queue_messages[actual_queue] = []
            queue_messages[actual_queue].append(msg)

        for queue, queue_msgs in queue_messages.items():
            batch_results = self._send_batch_messages_sync(queue, queue_msgs)
            results.extend(batch_results)

        return results

    async def _send_tasks_async(self, messages: list):
        if not messages:
            return []

        results = []

        queue_messages = {}
        for msg in messages:
            if isinstance(msg, dict):
                msg = TaskMessage.from_dict(msg)
            elif not isinstance(msg, TaskMessage):
                raise ValueError(f"Invalid message type: {type(msg)}. Expected TaskMessage or dict")

            msg.validate()

            actual_queue = msg.queue
            if msg.priority is not None:
                actual_queue = f"{msg.queue}:{msg.priority}"
                msg.queue = actual_queue

            if actual_queue not in queue_messages:
                queue_messages[actual_queue] = []
            queue_messages[actual_queue].append(msg)

        for queue, queue_msgs in queue_messages.items():
            batch_results = await self._send_batch_messages_async(queue, queue_msgs)
            results.extend(batch_results)

        return results
    
    def _send_batch_messages_sync(self, queue: str, messages: list) -> list:
        from ..utils.serializer import dumps_str

        all_messages = []

        for msg in messages:
            msg_dict = msg.to_dict()

            if msg.delay and msg.delay > 0:
                current_time = time.time()
                msg_dict['execute_at'] = current_time + msg.delay
                msg_dict['is_delayed'] = 1

            all_messages.append(msg_dict)

        results = []

        if all_messages:
            batch_results = self.ep._batch_send_event_sync(
                self.ep.get_prefixed_queue_name(queue),
                [{'data': dumps_str(msg)} for msg in all_messages],
                self.ep.get_redis_client(asyncio=False, binary=True).pipeline()
            )
            results.extend(batch_results)

        return results

    async def _send_batch_messages_async(self, queue: str, messages: list) -> list:
        from ..utils.serializer import dumps_str

        all_messages = []

        for msg in messages:
            msg_dict = msg.to_dict()

            if msg.delay and msg.delay > 0:
                current_time = time.time()
                msg_dict['execute_at'] = current_time + msg.delay
                msg_dict['is_delayed'] = 1

            all_messages.append(msg_dict)

        results = []
        if all_messages:
            batch_results = await self.ep._batch_send_event(
                self.ep.get_prefixed_queue_name(queue),
                [{'data': dumps_str(msg)} for msg in all_messages],
                self.ep.get_redis_client(asyncio=True, binary=True).pipeline()
            )
            results.extend(batch_results)

        return results

    def _get_task_names_from_queue(self, queue: str, task_name: str = None) -> list:
        if task_name is not None:
            return [task_name]

        base_queue = queue.split(':')[0] if ':' in queue else queue

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            task_names = asyncio.create_task(self.registry.get_task_names_by_queue(base_queue))
            raise RuntimeError("Cannot call sync method from async context")
        except RuntimeError:
            task_names = asyncio.run(self.registry.get_task_names_by_queue(base_queue))

        return list(task_names) if task_names else []

    def get_result(self, event_id: str, queue: str, task_name: str = None,
                   delete: bool = False, asyncio: bool = False,
                   delayed_deletion_ex: int = None, wait: bool = False,
                   timeout: int = 300, poll_interval: float = 0.5):
        return_single = task_name is not None

        task_names = self._get_task_names_from_queue(queue, task_name)

        if not task_names:
            if asyncio:
                async def _return_empty_list():
                    return []
                return _return_empty_list()
            else:
                return []

        if asyncio:
            return self._get_results_async(event_id, queue, task_names, delete,
                                          delayed_deletion_ex, wait, timeout, poll_interval, return_single)
        else:
            return self._get_results_sync(event_id, queue, task_names, delete,
                                         delayed_deletion_ex, wait, timeout, poll_interval, return_single)

    def get_queue_position(self, event_id: str, queue: str, task_name: str = None, asyncio: bool = False):
        return_single = task_name is not None

        task_names = self._get_task_names_from_queue(queue, task_name)

        if not task_names:
            if asyncio:
                async def _return_empty_list():
                    return []
                return _return_empty_list()
            else:
                return []

        if asyncio:
            return self._get_queue_positions_async(event_id, queue, task_names, return_single)
        else:
            return self._get_queue_positions_sync(event_id, queue, task_names, return_single)

    def _get_queue_positions_sync(self, event_id: str, queue: str, task_names: list, return_single: bool):
        results = []

        prefixed_queue = f"{self.redis_prefix}:QUEUE:{queue}"

        try:
            stream_data = self.binary_redis.xrange(prefixed_queue, min=event_id, max=event_id, count=1)

            if not stream_data:
                for task_name in task_names:
                    results.append({
                        "task_name": task_name,
                        "error": "Task not found in stream"
                    })
                if return_single:
                    return results[0] if results else None
                return results

            message_id, message_data = stream_data[0]

            task_offset = None
            for key, value in message_data.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                if key == 'offset':
                    if isinstance(value, bytes):
                        task_offset = int(value.decode('utf-8'))
                    else:
                        task_offset = int(value)
                    break

            if task_offset is None:
                for task_name in task_names:
                    results.append({
                        "task_name": task_name,
                        "error": "Offset not found in task data"
                    })
                if return_single:
                    return results[0] if results else None
                return results

        except Exception as e:
            for task_name in task_names:
                results.append({
                    "task_name": task_name,
                    "error": f"Failed to read from stream: {str(e)}"
                })
            if return_single:
                return results[0] if results else None
            return results

        read_offsets_key = f"{self.redis_prefix}:READ_OFFSETS"
        task_offsets_key = f"{self.redis_prefix}:TASK_OFFSETS"

        base_queue = queue.split(':')[0] if ':' in queue else queue

        offset_keys = [f"{base_queue}:{task_name}" for task_name in task_names]

        try:
            pipeline = self.redis.pipeline()
            pipeline.hmget(read_offsets_key, offset_keys)
            pipeline.hmget(task_offsets_key, offset_keys)
            read_offsets_list, task_offsets_list = pipeline.execute()
        except Exception as e:
            for task_name in task_names:
                results.append({
                    "task_name": task_name,
                    "error": f"Failed to read offsets: {str(e)}"
                })
            if return_single:
                return results[0] if results else None
            return results

        for idx, task_name in enumerate(task_names):
            read_offset = read_offsets_list[idx]
            if read_offset is not None:
                read_offset = int(read_offset)

            task_ack_offset = task_offsets_list[idx]
            if task_ack_offset is not None:
                task_ack_offset = int(task_ack_offset)

            pending_read = (task_offset - read_offset) if read_offset is not None else None
            pending_consume = (task_offset - task_ack_offset) if task_ack_offset is not None else None

            results.append({
                "task_name": task_name,
                "task_offset": task_offset,
                "read_offset": read_offset,
                "task_ack_offset": task_ack_offset,
                "pending_read": pending_read,
                "pending_consume": pending_consume
            })

        if return_single:
            return results[0] if results else None
        return results

    async def _get_queue_positions_async(self, event_id: str, queue: str, task_names: list, return_single: bool):
        results = []

        prefixed_queue = f"{self.redis_prefix}:QUEUE:{queue}"

        try:
            stream_data = await self.async_binary_redis.xrange(prefixed_queue, min=event_id, max=event_id, count=1)

            if not stream_data:
                for task_name in task_names:
                    results.append({
                        "task_name": task_name,
                        "error": "Task not found in stream"
                    })
                if return_single:
                    return results[0] if results else None
                return results

            message_id, message_data = stream_data[0]

            task_offset = None
            for key, value in message_data.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                if key == 'offset':
                    if isinstance(value, bytes):
                        task_offset = int(value.decode('utf-8'))
                    else:
                        task_offset = int(value)
                    break

            if task_offset is None:
                for task_name in task_names:
                    results.append({
                        "task_name": task_name,
                        "error": "Offset not found in task data"
                    })
                if return_single:
                    return results[0] if results else None
                return results

        except Exception as e:
            for task_name in task_names:
                results.append({
                    "task_name": task_name,
                    "error": f"Failed to read from stream: {str(e)}"
                })
            if return_single:
                return results[0] if results else None
            return results

        read_offsets_key = f"{self.redis_prefix}:READ_OFFSETS"
        task_offsets_key = f"{self.redis_prefix}:TASK_OFFSETS"

        base_queue = queue.split(':')[0] if ':' in queue else queue

        offset_keys = [f"{base_queue}:{task_name}" for task_name in task_names]

        try:
            pipeline = self.async_redis.pipeline()
            pipeline.hmget(read_offsets_key, offset_keys)
            pipeline.hmget(task_offsets_key, offset_keys)
            read_offsets_list, task_offsets_list = await pipeline.execute()
        except Exception as e:
            for task_name in task_names:
                results.append({
                    "task_name": task_name,
                    "error": f"Failed to read offsets: {str(e)}"
                })
            if return_single:
                return results[0] if results else None
            return results

        for idx, task_name in enumerate(task_names):
            read_offset = read_offsets_list[idx]
            if read_offset is not None:
                read_offset = int(read_offset)

            task_ack_offset = task_offsets_list[idx]
            if task_ack_offset is not None:
                task_ack_offset = int(task_ack_offset)

            pending_read = (task_offset - read_offset) if read_offset is not None else None
            pending_consume = (task_offset - task_ack_offset) if task_ack_offset is not None else None

            results.append({
                "task_name": task_name,
                "task_offset": task_offset,
                "read_offset": read_offset,
                "task_ack_offset": task_ack_offset,
                "pending_read": pending_read,
                "pending_consume": pending_consume
            })

        if return_single:
            return results[0] if results else None
        return results

    def _build_task_key(self, task_name: str, queue: str, event_id: str):
        prefixed_queue = f"{self.redis_prefix}:QUEUE:{queue}"
        group_name = f"{prefixed_queue}:{task_name}"
        status_key = f"{event_id}:{group_name}"
        full_key = f"{self.redis_prefix}:TASK:{status_key}"
        return group_name, full_key

    @staticmethod
    def _decode_bytes(value):
        if value and isinstance(value, bytes):
            return value.decode('utf-8')
        return value

    @staticmethod
    def _is_task_completed(status):
        return status in [TaskStatus.COMPLETED.value, TaskStatus.SUCCESS.value]

    @staticmethod
    def _is_task_failed(status):
        return status in [TaskStatus.ERROR.value, TaskStatus.FAILED.value, "ERROR", "FAILED", "error", "failed"]

    def _get_results_sync(self, event_id: str, queue: str, task_names: list,
                         delete: bool, delayed_deletion_ex: int, wait: bool,
                         timeout: int, poll_interval: float, return_single: bool):
        results = []

        for task_name in task_names:
            try:
                _, full_key = self._build_task_key(task_name, queue, event_id)

                task_info = self._get_result_sync(full_key, event_id, delete, delayed_deletion_ex,
                                                  wait, timeout, poll_interval)

                if not task_info:
                    results.append({
                        "task_name": task_name,
                        "status": None,
                        "result": None
                    })
                else:
                    task_info["task_name"] = task_name
                    results.append(task_info)

            except Exception as e:
                results.append({
                    "task_name": task_name,
                    "status": "ERROR",
                    "result": None,
                    "error_msg": str(e)
                })

        if return_single:
            return results[0] if results else None
        return results

    async def _get_results_async(self, event_id: str, queue: str, task_names: list,
                                 delete: bool, delayed_deletion_ex: int, wait: bool,
                                 timeout: int, poll_interval: float, return_single: bool):
        results = []

        for task_name in task_names:
            try:
                _, full_key = self._build_task_key(task_name, queue, event_id)

                task_info = await self._get_result_async(full_key, event_id, delete, delayed_deletion_ex,
                                                         wait, timeout, poll_interval)

                if not task_info:
                    results.append({
                        "task_name": task_name,
                        "status": TaskStatus.PENDING.value,
                        "result": None
                    })
                else:
                    task_info["task_name"] = task_name
                    results.append(task_info)

            except Exception as e:
                results.append({
                    "task_name": task_name,
                    "status": "ERROR",
                    "result": None,
                    "error_msg": str(e)
                })

        if return_single:
            return results[0] if results else None
        return results

    def _get_result_sync(self, full_key: str, event_id: str, delete: bool, delayed_deletion_ex: int,
                         wait: bool = False, timeout: int = 300, poll_interval: float = 0.5):
        from ..exceptions import TaskTimeoutError, TaskExecutionError, TaskNotFoundError

        client = self.binary_redis
        start_time = time.time()

        while True:
            task_data = client.hgetall(full_key)

            if not task_data:
                if wait:
                    raise TaskNotFoundError(f"Task {event_id} not found")
                return None

            decoded_data = {}
            for key, value in task_data.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')

                if key.startswith('__'):
                    continue

                if isinstance(value, bytes):
                    if key == 'result':
                        try:
                            decoded_data[key] = loads_str(value)
                        except Exception:
                            decoded_data[key] = value
                    else:
                        try:
                            decoded_data[key] = value.decode('utf-8')
                        except Exception:
                            decoded_data[key] = value
                else:
                    decoded_data[key] = value

            if not wait:
                if delayed_deletion_ex is not None:
                    client.expire(full_key, delayed_deletion_ex)
                elif delete:
                    if self.task_center and self.task_center.is_enabled:
                        client.hset(full_key, "__pending_delete", "1")
                    else:
                        client.delete(full_key)
                return decoded_data

            status = decoded_data.get('status')

            if self._is_task_completed(status):
                if delayed_deletion_ex is not None:
                    client.expire(full_key, delayed_deletion_ex)
                elif delete:
                    if self.task_center and self.task_center.is_enabled:
                        client.hset(full_key, "__pending_delete", "1")
                    else:
                        client.delete(full_key)
                return decoded_data

            elif self._is_task_failed(status):
                error_msg = decoded_data.get('error_msg', 'Task execution failed')
                raise TaskExecutionError(event_id, error_msg)

            if time.time() - start_time > timeout:
                raise TaskTimeoutError(f"Task {event_id} timed out after {timeout} seconds")

            time.sleep(poll_interval)

    async def _get_result_async(self, full_key: str, event_id: str, delete: bool, delayed_deletion_ex: int,
                                wait: bool = False, timeout: int = 300, poll_interval: float = 0.5):

        client = self.async_binary_redis
        start_time = time.time()

        while True:
            task_data = await client.hgetall(full_key)

            if not task_data:
                if wait:
                    raise TaskNotFoundError(f"Task {event_id} not found")
                return None

            decoded_data = {}
            for key, value in task_data.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')

                if key.startswith('__'):
                    continue

                if isinstance(value, bytes):
                    if key == 'result':
                        try:
                            decoded_data[key] = loads_str(value)
                        except Exception:
                            decoded_data[key] = value
                    else:
                        try:
                            decoded_data[key] = value.decode('utf-8')
                        except Exception:
                            decoded_data[key] = value
                else:
                    decoded_data[key] = value

            if not wait:
                if delayed_deletion_ex is not None:
                    await client.expire(full_key, delayed_deletion_ex)
                elif delete:
                    if self.task_center and self.task_center.is_enabled:
                        await client.hset(full_key, "__pending_delete", "1")
                    else:
                        await client.delete(full_key)
                return decoded_data

            status = decoded_data.get('status')

            if self._is_task_completed(status):
                if delayed_deletion_ex is not None:
                    await client.expire(full_key, delayed_deletion_ex)
                elif delete:
                    if self.task_center and self.task_center.is_enabled:
                        await client.hset(full_key, "__pending_delete", "1")
                    else:
                        await client.delete(full_key)
                return decoded_data

            elif self._is_task_failed(status):
                error_msg = decoded_data.get('error_msg', 'Task execution failed')
                raise TaskExecutionError(event_id, error_msg)

            if time.time() - start_time > timeout:
                raise TaskTimeoutError(f"Task {event_id} timed out after {timeout} seconds")

            await asyncio.sleep(poll_interval)

    def register_router(self, router, prefix: str = None):
        from ..task.router import TaskRouter
        
        if not isinstance(router, TaskRouter):
            raise TypeError("router must be a TaskRouter instance")
        
        for task_name, task_config in router.get_tasks().items():
            if prefix:
                if task_config.get('name'):
                    task_config['name'] = f"{prefix}.{task_config['name']}"
                task_name = f"{prefix}.{task_name}"
            
            func = task_config.pop('func')
            name = task_config.pop('name', task_name)
            queue = task_config.pop('queue', None)
            
            task = self._task_from_fun(func, name, None, queue, **task_config)
            logger.debug(f"Registered task: {name} (queue: {queue or self.redis_prefix})")
        
        return self

    def _mount_module(self):
        for module in self.include:
            module = importlib.import_module(module)
            for attr_name in dir(module):
                obj = getattr(module, attr_name)
                if hasattr(obj, "app"):
                    self._tasks.update(getattr(obj, "app")._tasks)

    def _validate_tasks_for_executor(self, execute_type: str, queues: List[str]):
        if execute_type in ["asyncio", "multi_asyncio"]:
            return  
        
        incompatible_tasks = []
        for task_name, task in self._tasks.items():
            if task.queue not in queues:
                continue
                
            if asyncio.iscoroutinefunction(task.run):
                incompatible_tasks.append({
                    'name': task_name,
                    'queue': task.queue,
                    'type': 'async'
                })
        
        if incompatible_tasks:
            error_msg = f"\n错误：{execute_type} 执行器不能处理异步任务！\n"
            error_msg += "发现以下异步任务：\n"
            for task in incompatible_tasks:
                error_msg += f"  - {task['name']} (队列: {task['queue']})\n"
            error_msg += f"\n解决方案：\n"
            error_msg += f"1. 使用 asyncio 或 process 执行器\n"
            error_msg += f"2. 或者将这些任务改为同步函数（去掉 async/await）\n"
            error_msg += f"3. 或者将这些任务的队列从监听列表中移除\n"
            raise ValueError(error_msg)



    def _create_executor(self, concurrency: int, local_concurrency: int = None):
        orchestrator = ProcessOrchestrator(self, concurrency, local_concurrency=local_concurrency)

        self._current_executor = orchestrator

        def signal_handler(signum, frame):
            logger.debug(f"Main process received signal {signum}, initiating shutdown...")
            self._should_exit = True
            orchestrator.shutdown_event.set()
            raise KeyboardInterrupt()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        return orchestrator

    async def _cleanup_worker_v3(self, heartbeat_managers: list, executor, worker_ids: list):
        logger.debug("Shutting down workers...")


        if heartbeat_managers:
            logger.debug(f"Stopping {len(heartbeat_managers)} heartbeat tasks...")
            for i, heartbeat in enumerate(heartbeat_managers):
                try:
                    worker_id = worker_ids[i][0] if i < len(worker_ids) else f"worker_{i}"
                    logger.debug(f"Stopping heartbeat task for {worker_id}...")
                    await heartbeat.stop()
                except Exception as e:
                    logger.error(f"Error stopping heartbeat #{i}: {e}", exc_info=True)

        if executor:
            try:
                logger.debug("Shutting down executor...")
                executor.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down executor: {e}", exc_info=True)


        logger.debug(f"All {len(worker_ids)} workers shutdown complete")

    async def _start(self, tasks: List[str], concurrency: int = 1, prefetch_multiplier: int = 1, local_concurrency: int = None):
        heartbeat_managers = []
        executor = None
        worker_ids = []

        queues = self._get_queues_from_tasks(tasks)
        logger.debug(f"Tasks {tasks} -> Queues {queues}")

        try:
            from jettask.worker.heartbeat import HeartbeatManager

            for i in range(concurrency):
                heartbeat = await HeartbeatManager.create_and_start(
                    queue_registry=self.registry,  
                    worker_manager=self.worker_state,  
                    async_redis_client=self.async_redis,
                    redis_prefix=self.redis_prefix,
                    interval=self.heartbeat_interval,
                    heartbeat_timeout=self.heartbeat_timeout,
                    worker_state=self.worker_state
                )
                worker_ids.append((heartbeat.worker_id, heartbeat.worker_key))
                heartbeat_managers.append(heartbeat)

            executor = self._create_executor(concurrency, local_concurrency=local_concurrency)

            HeartbeatManager.start_global_timeout_scanner(
                scan_interval=self.scanner_interval,
                worker_manager=self.worker_state
            )
         


            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,  
                executor.start,
                queues,
                tasks,
                prefetch_multiplier,
                worker_ids
            )
        

        except KeyboardInterrupt:
            logger.debug("Worker interrupted by keyboard")
        except Exception as e:
            logger.error(f"Error in worker main loop: {e}", exc_info=True)
        finally:
            logger.debug("Stopping global worker timeout scanner...")
            await HeartbeatManager.stop_global_timeout_scanner()

            await self._cleanup_worker_v3(heartbeat_managers, executor, worker_ids)

    def start(
        self,
        tasks: List[str],
        concurrency: int = 1,
        prefetch_multiplier: int = 1,
        local_concurrency: int = None,
    ):

        if not tasks:
            raise ValueError(
                "必须指定 tasks 参数！\n"
                "示例: app.start(tasks=['task1', 'task2'], concurrency=4)"
            )

        self._worker_started = True

        if self.task_center and self.task_center.is_enabled and not self._task_center_config:
            self._load_config_from_task_center()

        logger.debug("正在注册待注册的限流配置...")
        self._apply_pending_rate_limits()

        self._setup_cleanup_handlers()


        asyncio.run(self._start(
            tasks=tasks,
            concurrency=concurrency,
            prefetch_multiplier=prefetch_multiplier,
            local_concurrency=local_concurrency,
        ))


    def get_task_info(self, event_id: str, asyncio: bool = False):
        client = self.get_redis_client(asyncio)
        key = f"{self.redis_prefix}:TASK:{event_id}"
        if asyncio:
            return client.hgetall(key)
        else:
            return client.hgetall(key)
    
    def get_task_status(self, event_id: str, asyncio: bool = False):
        if asyncio:
            return self._get_task_status_simple_async(event_id)
        else:
            client = self.redis
            key = f"{self.redis_prefix}:TASK:{event_id}"
            return client.hget(key, "status")

    async def _get_task_status_simple_async(self, event_id: str):
        key = f"{self.redis_prefix}:TASK:{event_id}"
        return await self.async_redis.hget(key, "status")

    def set_task_status(self, event_id: str, status: str, asyncio: bool = False):
        if asyncio:
            return self._set_task_status_async(event_id, status)
        else:
            client = self.redis
            key = f"{self.redis_prefix}:TASK:{event_id}"
            return client.hset(key, "status", status)
    
    async def _set_task_status_async(self, event_id: str, status: str):
        key = f"{self.redis_prefix}:TASK:{event_id}"
        return await self.async_redis.hset(key, "status", status)

    def set_task_status_by_batch(self, mapping: dict, asyncio: bool = False):
        if asyncio:
            return self._set_task_status_by_batch_async(mapping)
        else:
            pipeline = self.redis.pipeline()
            for event_id, status in mapping.items():
                key = f"{self.redis_prefix}:TASK:{event_id}"
                pipeline.hset(key, "status", status)
            return pipeline.execute()
    
    async def _set_task_status_by_batch_async(self, mapping: dict):
        pipeline = self.async_redis.pipeline()
        for event_id, status in mapping.items():
            key = f"{self.redis_prefix}:TASK:{event_id}"
            pipeline.hset(key, "status", status)
        return await pipeline.execute()

    def del_task_status(self, event_id: str, asyncio: bool = False):
        client = self.get_redis_client(asyncio)
        key = f"{self.redis_prefix}:TASK:{event_id}"
        return client.delete(key)

    def get_redis_client(self, asyncio: bool = False):
        return self.async_redis if asyncio else self.redis

    async def get_and_delayed_deletion(self, key: str, ex: int):
        result = await self.async_redis.hget(key, "result")
        await self.async_redis.expire(key, ex)
        return result

    
    async def _ensure_scheduler_initialized(self, db_url: str = None):
        if not self.scheduler:
            logger.debug("Auto-initializing scheduler...")
            if not db_url:
                db_url = self.pg_url or os.environ.get('JETTASK_PG_URL')
            if not db_url:
                raise ValueError(
                    "Database URL not provided. Please provide pg_url when initializing Jettask, "
                    "or set JETTASK_PG_URL environment variable\n"
                    "Example: app = Jettask(redis_url='...', pg_url='postgresql://...')\n"
                    "Or: export JETTASK_PG_URL='postgresql://user:password@localhost:5432/jettask'"
                )

            self._scheduler_db_url = db_url

            scheduler_config = self.scheduler_config.copy()
            scheduler_config.setdefault('scan_interval', 1.0)  
            scheduler_config.setdefault('batch_size', 100)
            scheduler_config.setdefault('lookahead_seconds', 3600)  

            self.scheduler = TaskScheduler(
                app=self,
                db_url=db_url,
                **scheduler_config
            )

            logger.debug("Scheduler initialized")
    
    async def start_scheduler(self):
        await self._ensure_scheduler_initialized()

        try:
            await self.scheduler.start(wait=True)
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            raise
    
    async def register_schedules(self, schedules):
        from ..scheduler.definition import Schedule
        from ..db.models import ScheduledTask, TaskType

        await self._ensure_scheduler_initialized()

        if isinstance(schedules, Schedule):
            schedules = [schedules]

        if not schedules:
            return 0

        namespace = 'default'
        if self.task_center and hasattr(self.task_center, 'namespace_name'):
            namespace = self.task_center.namespace_name
        elif self.redis_prefix and self.redis_prefix != 'jettask':
            namespace = self.redis_prefix

        tasks = []
        for schedule in schedules:
            if not isinstance(schedule, Schedule):
                raise ValueError(f"Expected Schedule, got {type(schedule)}")

            data = schedule.to_dict()
            task = ScheduledTask(
                scheduler_id=data['scheduler_id'],
                task_type=data['task_type'],  
                queue_name=data['queue'],
                namespace=namespace,
                task_args=data['task_args'],
                task_kwargs=data['task_kwargs'],
                interval_seconds=data.get('interval_seconds'),
                cron_expression=data.get('cron_expression'),
                next_run_time=data.get('next_run_time'),
                enabled=data['enabled'],
                priority=data['priority'],
                timeout=data['timeout'],
                max_retries=data['max_retries'],
                retry_delay=data['retry_delay'],
                description=data['description'],
                tags=data['tags'],
                metadata=data['metadata']
            )
            task._skip_if_exists = schedule.skip_if_exists
            tasks.append(task)

        from ..db.connector import get_pg_engine_and_factory

        _, session_factory = get_pg_engine_and_factory(
            dsn=self._scheduler_db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=False
        )
        session = session_factory()
        try:
            registered_count = 0
            for task in tasks:
                skip_if_exists = getattr(task, '_skip_if_exists', True)

                existing_task = await ScheduledTask.get_by_scheduler_id(session, task.scheduler_id)

                if existing_task:
                    if not skip_if_exists:
                        task.id = existing_task.id
                        await ScheduledTask.update_task(session, task)
                        await session.commit()
                        logger.debug(f"已更新定时任务: {task.scheduler_id} -> {task.queue_name}")
                    else:
                        logger.debug(f"定时任务已存在: {task.scheduler_id}")
                else:
                    await ScheduledTask.create(session, task)
                    await session.commit()
                    registered_count += 1
                    logger.debug(f"已注册定时任务: {task.scheduler_id} -> {task.queue_name}")

            return registered_count
        finally:
            await session.close()

    async def list_schedules(self, **filters):
        await self._ensure_scheduler_initialized()

        from ..db.connector import get_pg_engine_and_factory
        from ..db.models import ScheduledTask

        _, session_factory = get_pg_engine_and_factory(
            dsn=self._scheduler_db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=False
        )
        session = session_factory()
        try:
            return await ScheduledTask.list_tasks(session, **filters)
        finally:
            await session.close()

    async def remove_schedule(self, scheduler_id: str) -> bool:
        await self._ensure_scheduler_initialized()

        from ..db.connector import get_pg_engine_and_factory
        from ..db.models import ScheduledTask

        _, session_factory = get_pg_engine_and_factory(
            dsn=self._scheduler_db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=False
        )
        session = session_factory()
        try:
            task = await ScheduledTask.get_by_scheduler_id(session, scheduler_id)
            if not task:
                return False

            await ScheduledTask.delete_by_id(session, task.id)
            await session.commit()
            return True
        finally:
            await session.close()

    async def pause_schedule(self, scheduler_id: str) -> bool:
        await self._ensure_scheduler_initialized()

        from ..db.connector import get_pg_engine_and_factory
        from ..db.models import ScheduledTask

        _, session_factory = get_pg_engine_and_factory(
            dsn=self._scheduler_db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=False
        )
        session = session_factory()
        try:
            task = await ScheduledTask.get_by_scheduler_id(session, scheduler_id)
            if not task:
                return False

            task.enabled = False
            await ScheduledTask.update_task(session, task)
            await session.commit()
            return True
        finally:
            await session.close()

    async def resume_schedule(self, scheduler_id: str) -> bool:
        await self._ensure_scheduler_initialized()

        from ..db.connector import get_pg_engine_and_factory
        from ..db.models import ScheduledTask

        _, session_factory = get_pg_engine_and_factory(
            dsn=self._scheduler_db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=False
        )
        session = session_factory()
        try:
            task = await ScheduledTask.get_by_scheduler_id(session, scheduler_id)
            if not task:
                return False

            task.enabled = True
            await ScheduledTask.update_task(session, task)
            await session.commit()
            return True
        finally:
            await session.close()

