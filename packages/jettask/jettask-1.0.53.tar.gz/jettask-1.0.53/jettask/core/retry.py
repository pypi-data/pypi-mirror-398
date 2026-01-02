"""
高性能任务重试机制
"""

import asyncio
import time
import random
from typing import Optional, List, Type, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """重试策略"""
    FIXED = "fixed"  
    LINEAR = "linear"  
    EXPONENTIAL = "exponential"  
    RANDOM_JITTER = "random_jitter"  


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3  
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL  
    base_delay: float = 1.0  
    max_delay: float = 60.0  
    exponential_base: float = 2.0  
    jitter: bool = True  
    jitter_range: float = 0.1  
    
    retryable_exceptions: Optional[List[Type[Exception]]] = None
    non_retryable_exceptions: Optional[List[Type[Exception]]] = None
    retry_predicate: Optional[Callable[[Exception], bool]] = None
    
    def should_retry(self, exception: Exception) -> bool:
        if self.non_retryable_exceptions:
            for exc_type in self.non_retryable_exceptions:
                if isinstance(exception, exc_type):
                    return False
        
        if self.retry_predicate:
            return self.retry_predicate(exception)
        
        if self.retryable_exceptions:
            for exc_type in self.retryable_exceptions:
                if isinstance(exception, exc_type):
                    return True
            return False
        
        return True
    
    def calculate_delay(self, attempt: int) -> float:
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        elif self.strategy == RetryStrategy.RANDOM_JITTER:
            delay = self.base_delay * (self.exponential_base ** (attempt - 1))
            if self.jitter:
                jitter = random.uniform(-self.jitter_range, self.jitter_range) * delay
                delay += jitter
        else:
            delay = self.base_delay
        
        return min(delay, self.max_delay)


class LocalRetryManager:
    """本地重试管理器 - 高性能实现"""
    
    def __init__(self):
        self._retry_tasks: Dict[str, Dict[str, Any]] = {}
        self._delayed_retries: List[tuple[float, str, Dict]] = []
        self._lock = asyncio.Lock()
        self._running = True
        self._process_task = None
        
    async def start(self):
        if not self._process_task:
            self._process_task = asyncio.create_task(self._process_delayed_retries())
    
    async def stop(self):
        self._running = False
        if self._process_task:
            await self._process_task
    
    async def schedule_retry(
        self, 
        task_id: str,
        task_func: Callable,
        args: tuple,
        kwargs: dict,
        config: RetryConfig,
        attempt: int,
        last_exception: Exception
    ) -> Optional[Any]:
        
        if attempt > config.max_retries:
            logger.error(f"Task {task_id} exceeded max retries ({config.max_retries})")
            raise last_exception
        
        delay = config.calculate_delay(attempt)
        
        if delay <= 0.1:  
            logger.info(f"Immediately retrying task {task_id}, attempt {attempt}/{config.max_retries}")
            return await self._execute_with_retry(
                task_id, task_func, args, kwargs, config, attempt
            )
        else:
            execute_at = time.time() + delay
            logger.info(f"Scheduling retry for task {task_id}, attempt {attempt}/{config.max_retries}, delay {delay:.2f}s")
            
            async with self._lock:
                task_info = {
                    'task_id': task_id,
                    'task_func': task_func,
                    'args': args,
                    'kwargs': kwargs,
                    'config': config,
                    'attempt': attempt,
                    'execute_at': execute_at
                }
                
                left, right = 0, len(self._delayed_retries)
                while left < right:
                    mid = (left + right) // 2
                    if self._delayed_retries[mid][0] <= execute_at:
                        left = mid + 1
                    else:
                        right = mid
                self._delayed_retries.insert(left, (execute_at, task_id, task_info))
            
            future = asyncio.Future()
            task_info['future'] = future
            return await future
    
    async def _execute_with_retry(
        self,
        task_id: str,
        task_func: Callable,
        args: tuple,
        kwargs: dict,
        config: RetryConfig,
        attempt: int
    ) -> Any:
        try:
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(*args, **kwargs)
            else:
                result = task_func(*args, **kwargs)
            
            logger.debug(f"Task {task_id} succeeded on attempt {attempt}")
            return result
            
        except Exception as e:
            if config.should_retry(e) and attempt < config.max_retries:
                return await self.schedule_retry(
                    task_id, task_func, args, kwargs, 
                    config, attempt + 1, e
                )
            else:
                logger.error(f"Task {task_id} failed after {attempt} attempts: {e}")
                raise
    
    async def _process_delayed_retries(self):
        while self._running:
            try:
                current_time = time.time()
                tasks_to_execute = []
                
                async with self._lock:
                    while self._delayed_retries and self._delayed_retries[0][0] <= current_time:
                        _, task_id, task_info = self._delayed_retries.pop(0)
                        tasks_to_execute.append(task_info)
                
                if tasks_to_execute:
                    execute_tasks = []
                    for task_info in tasks_to_execute:
                        task = asyncio.create_task(
                            self._execute_delayed_retry(task_info)
                        )
                        execute_tasks.append(task)
                    
                    await asyncio.gather(*execute_tasks, return_exceptions=True)
                
                async with self._lock:
                    if self._delayed_retries:
                        next_wake = self._delayed_retries[0][0]
                        sleep_time = max(0.01, min(0.1, next_wake - time.time()))
                    else:
                        sleep_time = 0.1
                
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in retry processor: {e}")
                await asyncio.sleep(0.1)
    
    async def _execute_delayed_retry(self, task_info: Dict[str, Any]):
        future = task_info.get('future')
        try:
            result = await self._execute_with_retry(
                task_info['task_id'],
                task_info['task_func'],
                task_info['args'],
                task_info['kwargs'],
                task_info['config'],
                task_info['attempt']
            )
            if future and not future.done():
                future.set_result(result)
        except Exception as e:
            if future and not future.done():
                future.set_exception(e)


_retry_manager = None


def get_retry_manager() -> LocalRetryManager:
    global _retry_manager
    if _retry_manager is None:
        _retry_manager = LocalRetryManager()
    return _retry_manager


async def retry_task(
    task_func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    config: RetryConfig = None,
    task_id: str = None
) -> Any:
    if kwargs is None:
        kwargs = {}
    
    if config is None:
        config = RetryConfig()
    
    if task_id is None:
        task_id = f"task_{id(task_func)}_{time.time()}"
    
    manager = get_retry_manager()
    
    await manager.start()
    
    return await manager._execute_with_retry(
        task_id, task_func, args, kwargs, config, 1
    )