"""
多进程执行器的子进程入口

职责：
1. 清理继承的父进程状态
2. 初始化子进程环境
3. 启动任务执行器
"""
import os
import gc
import sys
import signal
import asyncio
import logging
import multiprocessing
from typing import List, Dict
import time 

logger = None


class SubprocessInitializer:
    """子进程初始化器 - 负责清理和准备环境"""

    @staticmethod
    def cleanup_inherited_state():
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

        try:
            asyncio.set_event_loop_policy(None)
            asyncio.set_event_loop(None)
        except Exception:
            pass

        from jettask.db.connector import clear_all_cache
        clear_all_cache()

        gc.collect()

    @staticmethod
    def setup_logging(process_id: int, redis_prefix: str):
        import threading
        logging._lock = threading.RLock()

        root_logger = logging.getLogger()

        if hasattr(root_logger, '_lock'):
            root_logger._lock = threading.RLock()

        for handler in root_logger.handlers[:]:
            try:
                if hasattr(handler, 'lock'):
                    handler.lock = threading.RLock()
                handler.close()
            except:
                pass
            root_logger.removeHandler(handler)

        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            logger_obj = logging.getLogger(logger_name)

            if hasattr(logger_obj, '_lock'):
                logger_obj._lock = threading.RLock()

            if hasattr(logger_obj, 'handlers'):
                for handler in logger_obj.handlers[:]:
                    try:
                        if hasattr(handler, 'lock'):
                            handler.lock = threading.RLock()
                        handler.close()
                    except:
                        pass
                    logger_obj.removeHandler(handler)

                logger_obj.propagate = True

        formatter = logging.Formatter(
            fmt=f"%(asctime)s - %(levelname)s - [{redis_prefix}-P{process_id}] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        handler.createLock()

        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)

    @staticmethod
    def create_event_loop() -> asyncio.AbstractEventLoop:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


class MinimalApp:
    """
    最小化的 App 接口

    为子进程提供必要的接口，而不需要完整的 App 实例
    """
    def __init__(
        self,
        redis_client,
        async_redis_client,
        redis_url: str,
        redis_prefix: str,
        tasks: Dict,
        worker_id: str,
        worker_key: str
    ):
        self.redis = redis_client
        self.async_redis = async_redis_client
        self.redis_url = redis_url
        self.redis_prefix = redis_prefix
        self._tasks = tasks
        self.worker_id = worker_id
        self.worker_key = worker_key
        self._should_exit = False

        self._status_prefix = f"{redis_prefix}:STATUS:"
        self._result_prefix = f"{redis_prefix}:RESULT:"

        self._tasks_by_queue = {}
        for task_name, task in tasks.items():
            task_queue = task.queue or redis_prefix
            if task_queue not in self._tasks_by_queue:
                self._tasks_by_queue[task_queue] = []
            self._tasks_by_queue[task_queue].append(task_name)

        self.ep = None
        self.consumer_manager = None
        self.worker_state = None  

    def get_task_by_name(self, task_name: str):
        return self._tasks.get(task_name)

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

    def cleanup(self):
        pass


class SubprocessRunner:
    """子进程运行器 - 负责实际执行任务"""

    def __init__(
        self,
        process_id: int,
        redis_url: str,
        redis_prefix: str,
        queues: List[str],
        tasks: Dict,
        concurrency: int,
        prefetch_multiplier: int,
        max_connections: int,
        consumer_config: Dict,
        worker_id: str,
        worker_key: str,
        local_concurrency: int = None
    ):
        self.process_id = process_id
        self.redis_url = redis_url
        self.redis_prefix = redis_prefix
        self.queues = queues
        self.tasks = tasks
        self.concurrency = concurrency
        self.prefetch_multiplier = prefetch_multiplier
        self.max_connections = max_connections
        self.consumer_config = consumer_config or {}
        self.worker_id = worker_id
        self.worker_key = worker_key
        self.local_concurrency = local_concurrency

        self.redis_client = None
        self.async_redis_client = None
        self.minimal_app = None
        self.event_pool = None
        self.executors = []
        self._should_exit = False

    def setup_signal_handlers(self):
        def signal_handler(signum, _frame):
            logger.debug(f"Process #{self.process_id} received signal {signum}")
            self._should_exit = True
            if self.minimal_app:
                self.minimal_app._should_exit = True
            if self.event_pool:
                self.event_pool._stop_reading = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def create_redis_connections(self):
        from jettask.db.connector import get_sync_redis_client, get_async_redis_client


        self.redis_client = get_sync_redis_client(
            redis_url=self.redis_url,
            decode_responses=True,
            max_connections=self.max_connections
        )

        self.async_redis_client = get_async_redis_client(
            redis_url=self.redis_url,
            decode_responses=True,
            max_connections=self.max_connections
        )

    async def initialize_components(self):
        from jettask.messaging.event_pool import EventPool
        from jettask.executor.task_executor import TaskExecutor
        from jettask.messaging.registry import QueueRegistry
        from jettask.worker.lifecycle import WorkerManager

        logger.debug(f"Process #{self.process_id}: Initializing components")

        task_event_queues = {task_name: asyncio.Queue() for task_name in self.tasks.keys()}
        logger.debug(f"Process #{self.process_id}: Created event queues for tasks: {list(task_event_queues.keys())}")

        self.minimal_app = MinimalApp(
            redis_client=self.redis_client,
            async_redis_client=self.async_redis_client,
            redis_url=self.redis_url,
            redis_prefix=self.redis_prefix,
            tasks=self.tasks,
            worker_id=self.worker_id,
            worker_key=self.worker_key
        )

        queue_registry = QueueRegistry(
            redis_client=self.redis_client,
            async_redis_client=self.async_redis_client,
            redis_prefix=self.redis_prefix
        )
        logger.debug(f"Process #{self.process_id}: Created QueueRegistry")

        from jettask.db.connector import get_async_redis_client
        async_binary_redis_client = get_async_redis_client(
            self.redis_url,
            decode_responses=False,
            socket_timeout=None
        )

        worker_manager = WorkerManager(
            redis_client=self.redis_client,
            async_redis_client=async_binary_redis_client,
            redis_prefix=self.redis_prefix,
            queue_formatter=lambda q: f"{self.redis_prefix}:QUEUE:{q}",
            queue_registry=queue_registry,
            app=self.minimal_app,
            tasks=self.tasks,
            task_event_queues=task_event_queues,
            worker_id=self.worker_id
        )
        self.minimal_app.worker_state = worker_manager
        logger.debug(f"Process #{self.process_id}: Created WorkerManager with recovery capabilities")

        await worker_manager.start_listener()
        logger.info(f"Process #{self.process_id}: Started PubSub listener for instant offline worker recovery")

        consumer_config = self.consumer_config.copy()
        consumer_config['redis_prefix'] = self.redis_prefix
        consumer_config['disable_heartbeat_process'] = True

        self.event_pool = EventPool(
            self.redis_client,
            self.async_redis_client,
            task_event_queues,  
            self.tasks,  
            queue_registry,  
            self.minimal_app.worker_state,  
            queues=self.queues,  
            redis_url=self.redis_url,
            consumer_config=consumer_config,
            redis_prefix=self.redis_prefix,
            app=self.minimal_app,
            worker_id=self.worker_id  
        )

        self.minimal_app.ep = self.event_pool

        self.event_pool.init_routing()

        listening_task = asyncio.create_task(
            self.event_pool.listening_event(self.prefetch_multiplier)
        )

        for task_name, task_queue in task_event_queues.items():
            executor = TaskExecutor(
                event_queue=task_queue,
                app=self.minimal_app,
                task_name=task_name,
                worker_id=self.worker_id,
                worker_state_manager=worker_manager,
                concurrency=self.concurrency,
                local_concurrency=self.local_concurrency
            )

            await executor.initialize()

            executor_task = asyncio.create_task(executor.run())
            self.executors.append((task_name, executor_task))
            logger.debug(f"Process #{self.process_id}: Started TaskExecutor for task '{task_name}'")

        return listening_task, [t for _, t in self.executors]

    async def run(self):
        logger.debug(f"Process #{self.process_id} starting (PID: {os.getpid()})")

        listening_task = None
        executor_tasks = []

        try:
            listening_task, executor_tasks = await self.initialize_components()

            await asyncio.gather(listening_task, *executor_tasks)

        except asyncio.CancelledError:
            logger.debug(f"Process #{self.process_id} cancelled")
        except Exception as e:
            logger.error(f"Process #{self.process_id} error: {e}", exc_info=True)
        finally:
            logger.debug(f"Process #{self.process_id} cleaning up")

            if listening_task and not listening_task.done():
                listening_task.cancel()

            for _task_name, task in self.executors:
                if not task.done():
                    task.cancel()

            try:
                all_tasks = [listening_task] + executor_tasks if listening_task else executor_tasks
                await asyncio.wait_for(
                    asyncio.gather(*all_tasks, return_exceptions=True),
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                pass

            if self.event_pool and hasattr(self.event_pool, 'cleanup'):
                try:
                    self.event_pool.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up EventPool: {e}")


            if self.minimal_app and hasattr(self.minimal_app, 'worker_state') and self.minimal_app.worker_state:
                try:
                    await self.minimal_app.worker_state.stop_listener()
                    logger.debug(f"Process #{self.process_id}: Stopped PubSub listener")
                except Exception as e:
                    logger.error(f"Error stopping WorkerManager listener: {e}")

            if self.async_redis_client:
                try:
                    await self.async_redis_client.aclose()
                except Exception as e:
                    logger.error(f"Error closing async Redis client: {e}")

            logger.debug(f"Process #{self.process_id} stopped")


def subprocess_main(
    process_id: int,
    redis_url: str,
    redis_prefix: str,
    queues: List[str],
    tasks: Dict,
    concurrency: int,
    prefetch_multiplier: int,
    max_connections: int,
    consumer_config: Dict,
    worker_id: str,
    worker_key: str,
    shutdown_event,
    local_concurrency: int = None
):
    
    try:
        initializer = SubprocessInitializer()
        initializer.cleanup_inherited_state()
        initializer.setup_logging(process_id, redis_prefix)

        global logger
        logger = logging.getLogger()
        logger.debug(f"Process #{process_id} starting in PID {os.getpid()}")
        runner = SubprocessRunner(
            process_id=process_id,
            redis_url=redis_url,
            redis_prefix=redis_prefix,
            queues=queues,
            tasks=tasks,
            concurrency=concurrency,
            prefetch_multiplier=prefetch_multiplier,
            max_connections=max_connections,
            consumer_config=consumer_config,
            worker_id=worker_id,
            worker_key=worker_key,
            local_concurrency=local_concurrency
        )
        runner.setup_signal_handlers()
        runner.create_redis_connections()
        loop = initializer.create_event_loop()

        try:
            if not shutdown_event.is_set():
                loop.run_until_complete(runner.run())
        except KeyboardInterrupt:
            logger.debug(f"Process #{process_id} received interrupt")
        except Exception as e:
            logger.error(f"Process #{process_id} fatal error: {e}", exc_info=True)
        finally:
            try:
                if worker_id:
                    from jettask.utils.rate_limit.concurrency_limiter import ConcurrencyRateLimiter
                    task_names = list(tasks.keys()) if tasks else []
                    ConcurrencyRateLimiter.cleanup_worker_locks(
                        redis_url=redis_url,
                        redis_prefix=redis_prefix,
                        worker_id=worker_id,
                        task_names=task_names
                    )
            except Exception as e:
                logger.error(f"Error during lock cleanup: {e}")

            try:
                loop.close()
            except:
                pass

            logger.debug(f"Process #{process_id} exited")
            sys.exit(0)
    except Exception as e:
        import traceback 
        traceback.print_exc()
        print(f"Subprocess #{process_id} fatal error during initialization: {e}", file=sys.stderr)
        sys.exit(1)

__all__ = ['subprocess_main']
