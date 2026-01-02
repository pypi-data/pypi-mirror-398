#!/usr/bin/env python
"""时间同步模块

提供与 Redis 服务器时间同步的功能，避免多个 worker 因系统时间不一致导致的限流问题。
在启动时一次性校准与 Redis 服务器的时间差，后续使用本地时间加上时间差来获得标准时间。
"""

import time
import logging
from typing import Optional
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class TimeSync:
    """时间同步类

    在初始化时与 Redis 服务器时间进行一次校准，计算时间差。
    后续所有时间获取都使用 本地时间 + 时间差 的方式，避免频繁访问 Redis。

    使用方式:
        # 初始化（异步）
        time_sync = TimeSync()
        await time_sync.sync(redis_client)

        # 获取标准时间
        now = time_sync.time()
    """

    def __init__(self):
        self._offset = 0.0  
        self._synced = False  
        self._sync_timestamp = 0.0  

    async def sync(self, redis_client: aioredis.Redis, retry: int = 3) -> bool:
        for attempt in range(retry):
            try:
                local_before = time.time()

                redis_time = await redis_client.time()

                local_after = time.time()

                network_delay = (local_after - local_before) / 2.0

                redis_timestamp = float(redis_time[0]) + float(redis_time[1]) / 1_000_000.0

                estimated_local_time = local_before + network_delay

                self._offset = redis_timestamp - estimated_local_time
                self._sync_timestamp = time.time()
                self._synced = True

                logger.debug(
                    f"时间同步成功: offset={self._offset:.6f}s, "
                    f"network_delay={network_delay*1000:.2f}ms, "
                    f"redis_time={redis_timestamp:.6f}, "
                    f"local_time={estimated_local_time:.6f}"
                )

                if abs(self._offset) > 1.0:
                    logger.warning(
                        f"本地时间与 Redis 服务器时间差异较大: {self._offset:.2f}s，"
                        f"建议检查系统时间配置"
                    )

                return True

            except Exception as e:
                logger.error(f"时间同步失败 (attempt {attempt + 1}/{retry}): {e}")
                if attempt < retry - 1:
                    await asyncio.sleep(0.1)

        logger.error("时间同步失败，使用本地时间")
        self._synced = False
        return False

    def time(self) -> float:
        if not self._synced:
            return time.time()

        return time.time() + self._offset

    def is_synced(self) -> bool:
        return self._synced

    def get_offset(self) -> float:
        return self._offset

    def get_sync_info(self) -> dict:
        return {
            'synced': self._synced,
            'offset': self._offset,
            'sync_timestamp': self._sync_timestamp,
            'time_since_sync': time.time() - self._sync_timestamp if self._synced else None,
        }


_global_time_sync: Optional[TimeSync] = None


def get_time_sync() -> TimeSync:
    global _global_time_sync
    if _global_time_sync is None:
        _global_time_sync = TimeSync()
    return _global_time_sync


async def init_time_sync(redis_client: aioredis.Redis) -> TimeSync:
    time_sync = get_time_sync()
    await time_sync.sync(redis_client)
    return time_sync


import asyncio
