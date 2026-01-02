"""
多进程编排器

职责：
1. 启动和停止子进程
2. 监控子进程健康
3. 故障自动重启

注意：使用系统默认的 multiprocessing 启动模式（Linux上是fork，Windows/macOS上是spawn）。
- fork模式：子进程会继承父进程的状态，需要通过 cleanup_inherited_state() 清理
- spawn模式：子进程是全新的Python解释器，不会继承父进程状态，但需要所有对象可序列化
"""
import time
import os
import signal
import logging
import multiprocessing
from dataclasses import dataclass
from typing import Dict, List

logger = logging.getLogger('app')


@dataclass
class ProcessConfig:
    """进程配置"""
    process_id: int
    redis_url: str
    redis_prefix: str
    queues: List[str]
    tasks: Dict
    concurrency: int
    prefetch_multiplier: int
    max_connections: int
    consumer_config: Dict
    worker_id: str
    worker_key: str
    local_concurrency: int = None  


class ProcessOrchestrator:
    """
    进程编排器 - 只负责进程生命周期管理

    职责：
    1. 启动和停止子进程
    2. 监控子进程健康状态
    3. 自动重启失败的进程
    """

    def __init__(self, app, num_processes: int = 2, local_concurrency: int = None):
        self.app = app
        self.num_processes = num_processes
        self.local_concurrency = local_concurrency
        self.processes: Dict[int, multiprocessing.Process] = {}
        self.process_configs: Dict[int, ProcessConfig] = {}
        self.shutdown_event = multiprocessing.Event()

        self._monitor_interval = 1.0
        self._restart_delay = 2.0
        self._max_restart_attempts = 3
        self._restart_counts: Dict[int, int] = {}
        self._main_received_signal = False
        self._shutdown_called = False

        logger.debug(f"ProcessOrchestrator initialized with {num_processes} processes, local_concurrency={local_concurrency}")

    def _create_process_config(
        self,
        process_id: int,
        queues: List[str],
        tasks: List[str],
        prefetch_multiplier: int
    ) -> ProcessConfig:
        consumer_config = dict(self.app.consumer_config or {})
        consumer_config['disable_heartbeat_process'] = True
        new_task_items = {}
        for task_name in tasks:
            new_task_items[task_name] = self.app._tasks[task_name]
        tasks = new_task_items
        return ProcessConfig(
            process_id=process_id,
            redis_url=self.app.redis_url,
            redis_prefix=self.app.redis_prefix,
            queues=queues,
            tasks=tasks,
            concurrency=10000,  
            prefetch_multiplier=prefetch_multiplier,
            max_connections=self.app.max_connections,
            consumer_config=consumer_config,
            worker_id=getattr(self.app, 'worker_id', None),
            worker_key=getattr(self.app, 'worker_key', None),
            local_concurrency=self.local_concurrency
        )

    def _start_process(self, process_id: int, config: ProcessConfig) -> multiprocessing.Process:
        from .process_entry import subprocess_main
        process = multiprocessing.Process(
            target=subprocess_main,
            args=(
                config.process_id,
                config.redis_url,
                config.redis_prefix,
                config.queues,
                config.tasks,
                config.concurrency,
                config.prefetch_multiplier,
                config.max_connections,
                config.consumer_config,
                config.worker_id,
                config.worker_key,
                self.shutdown_event,
                config.local_concurrency
            ),
            name=f"JetTask-Worker-{process_id}"
        )
        process.start()


        logger.debug(f"Started process #{process_id} (PID: {process.pid})")
        return process

    def _restart_process(self, process_id: int):
        if self.shutdown_event.is_set():
            return

        restart_count = self._restart_counts.get(process_id, 0)
        if restart_count >= self._max_restart_attempts:
            logger.error(f"Process #{process_id} exceeded max restart attempts")
            return

        self._restart_counts[process_id] = restart_count + 1
        delay = self._restart_delay * (2 ** restart_count)

        logger.debug(
            f"Restarting process #{process_id} (attempt {restart_count + 1}) after {delay}s"
        )
        time.sleep(delay)

        config = self.process_configs[process_id]
        process = self._start_process(process_id, config)
        self.processes[process_id] = process

    def _monitor_processes(self) -> int:
        alive_count = 0

        for process_id, process in list(self.processes.items()):
            if process.is_alive():
                alive_count += 1
                self._restart_counts[process_id] = 0  
            else:
                exit_code = process.exitcode

                if self.shutdown_event.is_set():
                    logger.debug(f"Process #{process_id} stopped during shutdown")
                elif exit_code in (-15, -2):  
                    logger.debug(f"Process #{process_id} received termination signal")
                    self.shutdown_event.set()
                elif exit_code == 0:
                    if not self._main_received_signal:
                        all_stopped = all(not p.is_alive() for p in self.processes.values())
                        if all_stopped:
                            logger.debug("All processes stopped simultaneously")
                            self.shutdown_event.set()
                        else:
                            logger.warning(f"Process #{process_id} stopped unexpectedly")
                            self._restart_process(process_id)
                else:
                    logger.error(f"Process #{process_id} exited with code {exit_code}")
                    self._restart_process(process_id)

        return alive_count

    def start(
        self,
        queues: List[str],
        tasks: List[str],
        prefetch_multiplier: int = 100,
        worker_ids: list = None,
    ):
        logger.debug(f"Starting {self.num_processes} worker processes")



        try:
            for i, (worker_id, worker_key) in enumerate(worker_ids):
                config = self._create_process_config(i, queues, tasks, prefetch_multiplier)
                if worker_id:
                    config.worker_id = worker_id
                    config.worker_key = worker_key

                self.process_configs[i] = config
                process = self._start_process(i, config)
                self.processes[i] = process


            logger.debug(f"All {self.num_processes} processes started")

            while not self.shutdown_event.is_set():
                alive_count = self._monitor_processes()

                if alive_count == 0:
                    if self._main_received_signal or self.shutdown_event.is_set():
                        logger.debug("All processes stopped during shutdown")
                    else:
                        logger.error("All processes stopped unexpectedly")
                    break

                time.sleep(self._monitor_interval)

        except KeyboardInterrupt:
            logger.debug("Main process received KeyboardInterrupt")
            self._main_received_signal = True
            self.shutdown_event.set()
        except Exception as e:
            logger.error(f"ProcessOrchestrator error: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self):
        if self._shutdown_called:
            return
        self._shutdown_called = True

        logger.debug("Shutting down ProcessOrchestrator")

        self.shutdown_event.set()


        for process_id, process in self.processes.items():
            if process.is_alive():
                logger.debug(f"Force killing process #{process_id} (PID: {process.pid})")
                try:
                    os.kill(process.pid, signal.SIGKILL)
                except Exception as e:
                    logger.warning(f"Error killing process #{process_id}: {e}")
                    try:
                        process.kill()
                    except:
                        pass

        start_time = time.time()
        for process_id, process in self.processes.items():
            remaining = max(0, 1.0 - (time.time() - start_time))
            try:
                process.join(timeout=remaining)
            except:
                pass

            if process.is_alive():
                logger.warning(f"Process #{process_id} still alive after SIGKILL")

        self.processes.clear()
        self.process_configs.clear()
        self._restart_counts.clear()

        logger.debug("ProcessOrchestrator shutdown complete")


__all__ = ['ProcessOrchestrator', 'ProcessConfig']
