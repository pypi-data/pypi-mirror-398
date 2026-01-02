"""
异步延迟队列 - 基于 asyncio 和 heapq 的高效延迟任务存储

核心特性：
1. 纯数据结构：只负责存储和检索，不执行任务
2. 高性能：插入/删除都是 O(log n)
3. 线程安全：在 asyncio 事件循环内安全使用
4. 支持取消：可以取消指定任务
"""

import heapq
import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger('app')


class AsyncDelayQueue:
    """
    异步延迟队列 - 纯数据结构

    使用最小堆（heapq）管理延迟任务，提供添加、获取到期任务、取消等操作。
    不主动执行任务，由外部（如 TaskExecutor.run()）主动调用 get_expired_tasks() 获取。
    """

    def __init__(self):
        self.heap = []  
        self._counter = 0  
        self._task_map: Dict[str, int] = {}  

        logger.debug("AsyncDelayQueue initialized")

    def put(self, task_data: Dict, delay: float) -> str:
        exec_time = time.time() + delay
        task_id = task_data.get('event_id', f'task_{self._counter}')

        self._counter += 1
        heapq.heappush(self.heap, (exec_time, self._counter, task_id, task_data))
        self._task_map[task_id] = self._counter

        logger.debug(
            f"[DelayQueue] Added task {task_id}, delay={delay:.3f}s, "
            f"exec_time={exec_time:.3f}, queue_size={len(self.heap)}"
        )
        return task_id

    def get_expired_tasks(self) -> List[Dict]:
        current_time = time.time()
        expired_tasks = []

        while self.heap:
            exec_time, counter, task_id, task_data = self.heap[0]

            if exec_time > current_time:
                break

            heapq.heappop(self.heap)

            if task_id not in self._task_map:
                logger.debug(f"[DelayQueue] Task {task_id} was cancelled, skipping")
                continue

            self._task_map.pop(task_id, None)

            expired_tasks.append(task_data)

        if expired_tasks:
            logger.info(
                f"[DelayQueue] Retrieved {len(expired_tasks)} expired tasks, "
                f"remaining={len(self.heap)}"
            )

        return expired_tasks

    def cancel(self, task_id: str) -> bool:
        if task_id not in self._task_map:
            return False

        self._task_map.pop(task_id)
        logger.debug(f"[DelayQueue] Cancelled task {task_id}")
        return True

    def get_next_expire_time(self) -> Optional[float]:
        if not self.heap:
            return None

        for exec_time, counter, task_id, task_data in self.heap:
            if task_id in self._task_map:
                return exec_time

        return None

    def size(self) -> int:
        return len(self.heap)

    def active_size(self) -> int:
        return len(self._task_map)

    def is_empty(self) -> bool:
        return len(self._task_map) == 0

    def clear(self):
        self.heap.clear()
        self._task_map.clear()
        logger.debug("[DelayQueue] Cleared all tasks")


__all__ = ['AsyncDelayQueue']
