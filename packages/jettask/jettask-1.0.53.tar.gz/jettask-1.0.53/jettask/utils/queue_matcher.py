"""
队列通配符匹配工具

提供队列名称的通配符匹配功能，支持动态队列发现场景。
"""

import fnmatch
from typing import List, Dict, Set, Tuple


def is_wildcard_pattern(queue: str) -> bool:
    return '*' in queue or '?' in queue


def separate_wildcard_and_static_queues(queues: List[str]) -> Tuple[List[str], List[str]]:
    wildcard_patterns = []
    static_queues = []

    for queue in queues:
        if is_wildcard_pattern(queue):
            wildcard_patterns.append(queue)
        else:
            static_queues.append(queue)

    return wildcard_patterns, static_queues


def match_queue_to_pattern(queue: str, patterns: List[str]) -> str:
    for pattern in patterns:
        if fnmatch.fnmatch(queue, pattern):
            return pattern
    return None


def find_matching_tasks(
    queue: str,
    tasks_by_queue: Dict[str, List[str]],
    wildcard_mode: bool = False
) -> List[str]:
    task_names = tasks_by_queue.get(queue, [])

    if not task_names and wildcard_mode:
        for pattern, pattern_tasks in tasks_by_queue.items():
            if fnmatch.fnmatch(queue, pattern):
                task_names.extend(pattern_tasks)

    return task_names


def match_task_queue_to_patterns(
    task_queue: str,
    queue_patterns: List[str]
) -> bool:
    for queue_pattern in queue_patterns:
        if is_wildcard_pattern(queue_pattern):
            if fnmatch.fnmatch(task_queue, queue_pattern) or task_queue == queue_pattern:
                return True
        else:
            if task_queue == queue_pattern:
                return True

    return False


def discover_matching_queues(
    wildcard_patterns: List[str],
    all_queues: Set[str]
) -> Set[str]:
    matched_queues = set()

    for pattern in wildcard_patterns:
        for queue in all_queues:
            if fnmatch.fnmatch(queue, pattern):
                matched_queues.add(queue)

    return matched_queues
