"""
限流器 - 兼容性导入

⚠️ 此文件保持向后兼容，将导入重定向到新的模块化结构。
原代码已被拆分到以下模块：
- jettask.rate_limit.qps_limiter: QPSRateLimiter 类
- jettask.rate_limit.concurrency_limiter: ConcurrencyRateLimiter 类
- jettask.rate_limit.task_limiter: TaskRateLimiter 类
- jettask.rate_limit.manager: RateLimiterManager 类

新的模块结构：
- qps_limiter.py: QPS限流器
- concurrency_limiter.py: 并发限流器
- task_limiter.py: 任务级限流器
- manager.py: 限流器管理器

使用示例：
    # 旧的导入方式（仍然可用）
    from jettask.rate_limit.limiter import RateLimiterManager, QPSRateLimiter

    # 新的导入方式（推荐）
    from jettask.rate_limit import RateLimiterManager, QPSRateLimiter
"""

from .config import RateLimitConfig, QPSLimit, ConcurrencyLimit
from .qps_limiter import QPSRateLimiter
from .concurrency_limiter import ConcurrencyRateLimiter
from .task_limiter import TaskRateLimiter
from .manager import RateLimiterManager

__all__ = [
    'RateLimitConfig',
    'QPSLimit',
    'ConcurrencyLimit',
    'QPSRateLimiter',
    'ConcurrencyRateLimiter',
    'TaskRateLimiter',
    'RateLimiterManager',
]
