"""
数据库连接工具类

提供统一的 Redis 和 PostgreSQL 连接管理，避免代码重复。
所有数据库连接池均为全局单例，复用连接池以节省资源。

文件结构：
============================================================
1. 导入和全局配置 (第7-23行)
   - 第三方库导入
   - Logger 初始化

2. 全局变量 (第25-38行)
   - Redis 连接池缓存（同步/异步、文本/二进制）
   - PostgreSQL 引擎和会话工厂缓存

3. 工具类 (第41-83行)
   - InfiniteRetry: 无限重试策略

4. 自定义 Redis 连接池实现 (第85-453行)
   - IdleTrackingBlockingConnectionPool: 同步连接池（带空闲回收）
   - AsyncIdleTrackingBlockingConnectionPool: 异步连接池（带空闲回收）

5. 连接池获取函数 (第455-740行)
   - get_sync_redis_pool: 获取同步 Redis 连接池
   - get_async_redis_pool: 获取异步 Redis 连接池
   - get_async_redis_pool_for_pubsub: 获取 PubSub 专用连接池
   - get_pg_engine_and_factory: 获取 PostgreSQL 引擎和会话工厂

6. 配置和连接器类 (第742-1249行)
   - DBConfig: 数据库配置数据类
   - SyncRedisConnector: 同步 Redis 连接器
   - RedisConnector: 异步 Redis 连接器
   - PostgreSQLConnector: PostgreSQL 连接器
   - ConnectionManager: 统一连接管理器

7. 全局客户端实例管理 (第1251-1378行)
   - get_sync_redis_client: 获取全局同步 Redis 客户端
   - get_async_redis_client: 获取全局异步 Redis 客户端
   - clear_all_cache: 清理所有缓存

============================================================
"""

import os
import logging
import traceback
import socket
import time
import threading
import asyncio
from typing import Optional, Dict, Any, Union
from contextlib import asynccontextmanager, contextmanager
import redis as sync_redis
import redis.asyncio as redis
from redis.asyncio import BlockingConnectionPool
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)



class _PoolRegistry:
    """
    全局连接池注册表（单例模式）

    统一管理所有数据库连接池和客户端实例，避免全局变量分散
    """

    sync_redis_pools: Dict[str, sync_redis.ConnectionPool] = {}
    sync_binary_redis_pools: Dict[str, sync_redis.ConnectionPool] = {}
    async_redis_pools: Dict[str, redis.ConnectionPool] = {}
    async_binary_redis_pools: Dict[str, redis.ConnectionPool] = {}

    pg_engines: Dict[str, Any] = {}
    pg_session_factories: Dict[str, async_sessionmaker] = {}

    asyncpg_pools: Dict[str, Any] = {}

    sync_redis_clients: Dict[str, sync_redis.StrictRedis] = {}
    sync_binary_redis_clients: Dict[str, sync_redis.StrictRedis] = {}
    async_redis_clients: Dict[str, redis.StrictRedis] = {}
    async_binary_redis_clients: Dict[str, redis.StrictRedis] = {}

    @classmethod
    def clear_all(cls):
        cls.sync_redis_pools.clear()
        cls.sync_binary_redis_pools.clear()
        cls.async_redis_pools.clear()
        cls.async_binary_redis_pools.clear()
        cls.pg_engines.clear()
        cls.pg_session_factories.clear()
        cls.asyncpg_pools.clear()
        cls.sync_redis_clients.clear()
        cls.sync_binary_redis_clients.clear()
        cls.async_redis_clients.clear()
        cls.async_binary_redis_clients.clear()


_sync_redis_pools = _PoolRegistry.sync_redis_pools
_sync_binary_redis_pools = _PoolRegistry.sync_binary_redis_pools
_async_redis_pools = _PoolRegistry.async_redis_pools
_async_binary_redis_pools = _PoolRegistry.async_binary_redis_pools
_pg_engines = _PoolRegistry.pg_engines
_pg_session_factories = _PoolRegistry.pg_session_factories



class InfiniteRetry(Retry):
    """无限重试的 Retry 策略"""

    def __init__(self):
        super().__init__(
            ExponentialBackoff(cap=30, base=1),
            retries=-1  
        )

    def call_with_retry(self, do, fail):
        failures = 0
        backoff = self._backoff

        while True:
            try:
                return do()
            except Exception as error:
                failures += 1

                if failures == 1 or failures % 10 == 0:  
                    logger.warning(
                        f"Redis 连接失败 (第 {failures} 次), 将在 {backoff.compute(failures)} 秒后重试: {error}"
                    )

                fail(error)

                time.sleep(backoff.compute(failures))




class IdleTrackingBlockingConnectionPool(sync_redis.BlockingConnectionPool):
    """
    带空闲连接跟踪和自动回收的同步阻塞连接池

    核心机制：
    1. 在 get_connection() 时记录连接的获取时间戳
    2. 在 release() 时更新连接的最后使用时间戳
    3. 使用后台线程定期检查并关闭超过 max_idle_time 的空闲连接
    """

    def __init__(self, *args, max_idle_time: int = 300, idle_check_interval: int = 60, **kwargs):
        super().__init__(*args, **kwargs)

        self.max_idle_time = max_idle_time
        self.idle_check_interval = idle_check_interval

        self._connection_last_use: Dict[int, float] = {}
        self._connection_last_use_lock = threading.RLock()

        self._cleaner_thread = None
        self._stop_cleaner = threading.Event()

        if max_idle_time > 0 and idle_check_interval > 0:
            self._start_idle_cleaner()

    def get_connection(self, command_name=None, *keys, **options):
        max_retries = 3
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                conn = super().get_connection(command_name, *keys, **options)
                conn_id = id(conn)
                with self._connection_last_use_lock:
                    if conn_id not in self._connection_last_use:
                        self._connection_last_use[conn_id] = time.time()
                        logger.debug(f"连接 {conn_id} 首次获取")
                return conn
            except Exception as e:
                error_msg = str(e)
                last_error = e

                if "Buffer is closed" in error_msg or "Connection" in error_msg:
                    retry_count += 1
                    logger.warning(
                        f"Redis 连接错误 (第 {retry_count}/{max_retries} 次重试): {error_msg}"
                    )

                    try:
                        self.disconnect(inuse_connections=False)
                    except Exception as disconnect_error:
                        logger.debug(f"断开连接时发生错误: {disconnect_error}")

                    if retry_count < max_retries:
                        time.sleep(0.1 * retry_count)
                        continue

                raise

        if last_error:
            raise last_error

    def release(self, connection):
        conn_id = id(connection)
        current_time = time.time()
        with self._connection_last_use_lock:
            self._connection_last_use[conn_id] = current_time
            logger.debug(f"连接 {conn_id} 释放，更新最后使用时间: {current_time}")
        super().release(connection)

    def _start_idle_cleaner(self):
        self._cleaner_thread = threading.Thread(
            target=self._idle_cleaner_loop,
            name="SyncIdleConnectionCleaner",
            daemon=True
        )
        self._cleaner_thread.start()

    def _idle_cleaner_loop(self):
        while not self._stop_cleaner.wait(self.idle_check_interval):
            try:
                self._cleanup_idle_connections()
            except Exception as e:
                logger.error(f"清理空闲连接时出错: {e}")
                logger.debug(traceback.format_exc())

    def _cleanup_idle_connections(self):
        current_time = time.time()
        connections_to_keep = []
        connections_to_close = []

        connections_to_check = []
        with self._lock:
            initial_total = len(self._connections)
            initial_available = self.pool.qsize()
            initial_in_use = initial_total - initial_available

            while True:
                try:
                    conn = self.pool.get_nowait()
                    connections_to_check.append(conn)
                except:
                    break

        available_count = len(connections_to_check)
        logger.debug(f"检查 {available_count} 个可用连接")

        if available_count <= 2:
            with self._lock:
                for conn in connections_to_check:
                    self.pool.put(conn)
            logger.debug(f"可用连接数 {available_count} <= 2，跳过清理")
            return

        for conn in connections_to_check:
            if conn is None:
                connections_to_keep.append(conn)
                continue

            if hasattr(conn, '_is_pubsub_connection') and conn._is_pubsub_connection:
                logger.info(f"跳过 PubSub 连接清理: {id(conn)}")
                connections_to_keep.append(conn)
                continue

            conn_id = id(conn)
            with self._connection_last_use_lock:
                last_use = self._connection_last_use.get(conn_id, current_time)
                idle_time = current_time - last_use

            if idle_time > self.max_idle_time and len(connections_to_keep) + len(connections_to_check) - len(connections_to_close) > 2:
                connections_to_close.append((conn, conn_id, idle_time))
            else:
                connections_to_keep.append(conn)

        closed_count = 0
        for conn, conn_id, idle_time in connections_to_close:
            try:
                with self._connection_last_use_lock:
                    self._connection_last_use.pop(conn_id, None)

                conn.disconnect()

                with self._lock:
                    if conn in self._connections:
                        self._connections.remove(conn)

                closed_count += 1
                logger.debug(f"关闭空闲连接 {conn_id}，空闲时间: {idle_time:.1f}s")

            except Exception as e:
                logger.warning(f"断开连接 {conn_id} 失败: {e}")
                connections_to_keep.append(conn)
                with self._connection_last_use_lock:
                    self._connection_last_use[conn_id] = time.time()

        with self._lock:
            for conn in connections_to_keep:
                self.pool.put(conn)

        if closed_count > 0:
            with self._lock:
                final_total = len(self._connections)
                final_available = self.pool.qsize()
                final_in_use = final_total - final_available

    def _stop_idle_cleaner(self):
        if self._cleaner_thread and self._cleaner_thread.is_alive():
            self._stop_cleaner.set()
            self._cleaner_thread.join(timeout=5)

        with self._connection_last_use_lock:
            self._connection_last_use.clear()

    def disconnect(self, inuse_connections: bool = True):
        self._stop_idle_cleaner()
        super().disconnect(inuse_connections)


class AsyncIdleTrackingBlockingConnectionPool(redis.BlockingConnectionPool):
    """
    带空闲连接跟踪和自动回收的异步阻塞连接池

    核心机制：
    1. 在 get_connection() 时记录连接的获取时间戳
    2. 在 release() 时更新连接的最后使用时间戳
    3. 使用 asyncio.Task 定期检查并关闭超过 max_idle_time 的空闲连接
    """

    def __init__(self, *args, max_idle_time: int = 300, idle_check_interval: int = 60, **kwargs):
        kwargs.pop('max_idle_time', None)
        kwargs.pop('idle_check_interval', None)

        super().__init__(*args, **kwargs)

        self.max_idle_time = max_idle_time
        self.idle_check_interval = idle_check_interval

        self._connection_last_use: Dict[int, float] = {}
        self._connection_last_use_lock = None  

        self._cleaner_task = None
        self._stop_cleaner = None  


    async def get_connection(self, command_name=None, *keys, **options):
        await self._ensure_cleaner_task_started()

        max_retries = 3
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                conn = await super().get_connection(command_name, *keys, **options)
                conn_id = id(conn)

                if self._connection_last_use_lock is None:
                    self._connection_last_use_lock = asyncio.Lock()

                async with self._connection_last_use_lock:
                    if conn_id not in self._connection_last_use:
                        self._connection_last_use[conn_id] = time.time()
                        logger.debug(f"连接 {conn_id} 首次获取")
                return conn
            except Exception as e:
                error_msg = str(e)
                last_error = e

                if "Buffer is closed" in error_msg or "Connection" in error_msg:
                    retry_count += 1
                    logger.warning(
                        f"Redis 连接错误 (第 {retry_count}/{max_retries} 次重试): {error_msg}"
                    )

                    try:
                        await self.disconnect(inuse_connections=False)
                    except Exception as disconnect_error:
                        logger.debug(f"断开连接时发生错误: {disconnect_error}")

                    if retry_count < max_retries:
                        await asyncio.sleep(0.1 * retry_count)
                        continue

                raise

        if last_error:
            raise last_error

    async def release(self, connection):
        conn_id = id(connection)
        current_time = time.time()

        if self._connection_last_use_lock is None:
            self._connection_last_use_lock = asyncio.Lock()

        async with self._connection_last_use_lock:
            self._connection_last_use[conn_id] = current_time
            logger.debug(f"连接 {conn_id} 释放，更新最后使用时间: {current_time}")

        try:
            await super().release(connection)
        except KeyError:
            logger.debug(f"连接 {conn_id} 释放时不在连接池中，可能已被移除")
        except Exception as e:
            logger.warning(f"释放连接 {conn_id} 时发生错误: {e}")

    async def _ensure_cleaner_task_started(self):
        if self.max_idle_time > 0 and self.idle_check_interval > 0 and self._cleaner_task is None:
            if self._stop_cleaner is None:
                self._stop_cleaner = asyncio.Event()
            self._cleaner_task = asyncio.create_task(self._idle_cleaner_loop())

    async def _idle_cleaner_loop(self):
        while True:
            try:
                await asyncio.wait_for(
                    self._stop_cleaner.wait(),
                    timeout=self.idle_check_interval
                )
                break
            except asyncio.TimeoutError:
                try:
                    await self._cleanup_idle_connections()
                except Exception as e:
                    logger.error(f"清理空闲连接时出错: {e}")
                    logger.debug(traceback.format_exc())

    async def _cleanup_idle_connections(self):
        if self._connection_last_use_lock is None:
            return

        current_time = time.time()
        connections_to_keep = []
        connections_to_close = []

        async with self._lock:
            if not hasattr(self, '_available_connections'):
                return
            connections_to_check = list(self._available_connections)
            initial_available = len(self._available_connections)
            initial_in_use = len(self._in_use_connections) if hasattr(self, '_in_use_connections') else 0
            initial_total = initial_available + initial_in_use

        available_count = len(connections_to_check)
        logger.debug(f"检查 {available_count} 个可用连接")

        if available_count <= 2:
            logger.debug(f"可用连接数 {available_count} <= 2，跳过清理")
            return

        for conn in connections_to_check:
            if conn is None:
                connections_to_keep.append(conn)
                continue

            if hasattr(conn, '_is_pubsub_connection') and conn._is_pubsub_connection:
                logger.info(f"跳过 PubSub 连接清理: {id(conn)}")
                connections_to_keep.append(conn)
                continue

            conn_id = id(conn)
            async with self._connection_last_use_lock:
                last_use = self._connection_last_use.get(conn_id, current_time)
                idle_time = current_time - last_use

            if idle_time > self.max_idle_time and len(connections_to_keep) + len(connections_to_check) - len(connections_to_close) > 2:
                connections_to_close.append((conn, conn_id, idle_time))
            else:
                connections_to_keep.append(conn)

        closed_count = 0
        for conn, conn_id, idle_time in connections_to_close:
            try:
                async with self._connection_last_use_lock:
                    self._connection_last_use.pop(conn_id, None)

                await conn.disconnect()
            
                async with self._lock:
                    if hasattr(self, '_available_connections') and conn in self._available_connections:
                        self._available_connections.remove(conn)
                    if hasattr(self, '_in_use_connections') and conn in self._in_use_connections:
                        try:
                            self._in_use_connections.discard(conn)
                        except AttributeError:
                            self._in_use_connections.remove(conn)

                closed_count += 1
                logger.debug(f"关闭空闲连接 {conn_id}，空闲时间: {idle_time:.1f}s")

            except Exception as e:
                import traceback 
                traceback.print_exc()
                logger.warning(f"断开连接 {conn_id} 失败: {e}")
                logger.debug(traceback.format_exc())
                async with self._connection_last_use_lock:
                    self._connection_last_use[conn_id] = time.time()


    async def _stop_idle_cleaner(self):
        if self._cleaner_task and not self._cleaner_task.done():
            if self._stop_cleaner:
                self._stop_cleaner.set()
            try:
                await asyncio.wait_for(self._cleaner_task, timeout=5)
            except asyncio.TimeoutError:
                self._cleaner_task.cancel()

        if self._connection_last_use_lock:
            async with self._connection_last_use_lock:
                self._connection_last_use.clear()
        else:
            self._connection_last_use.clear()

    async def disconnect(self, inuse_connections: bool = True):
        await self._stop_idle_cleaner()
        await super().disconnect(inuse_connections)



def _get_socket_keepalive_options() -> Dict[int, int]:
    socket_keepalive_options = {}
    if hasattr(socket, 'TCP_KEEPIDLE'):
        socket_keepalive_options[socket.TCP_KEEPIDLE] = 1
    if hasattr(socket, 'TCP_KEEPINTVL'):
        socket_keepalive_options[socket.TCP_KEEPINTVL] = 3
    if hasattr(socket, 'TCP_KEEPCNT'):
        socket_keepalive_options[socket.TCP_KEEPCNT] = 5
    return socket_keepalive_options


def get_sync_redis_pool(
    redis_url: str,
    decode_responses: bool = True,
    max_connections: int = 200,
    socket_connect_timeout: int = 30,
    socket_timeout: int = 60,
    timeout: int = 60,
    health_check_interval: int = 30,
    max_idle_time: int = 10,
    idle_check_interval: int = 1,
    **pool_kwargs
) -> IdleTrackingBlockingConnectionPool:
    pool_cache = _sync_redis_pools if decode_responses else _sync_binary_redis_pools

    cache_key = f"{redis_url}:socket_timeout={socket_timeout}"

    if cache_key not in pool_cache:
        socket_keepalive_options = _get_socket_keepalive_options()

        infinite_retry = InfiniteRetry()
        print(f'{redis_url=}')
        pool = IdleTrackingBlockingConnectionPool.from_url(
            redis_url,
            decode_responses=decode_responses,
            max_connections=max_connections,
            timeout=timeout,  
            retry_on_timeout=True,
            retry_on_error=[ConnectionError, TimeoutError, OSError, BrokenPipeError],
            retry=infinite_retry,  
            socket_keepalive=True,
            socket_keepalive_options=socket_keepalive_options if socket_keepalive_options else None,
            health_check_interval=health_check_interval,  
            socket_connect_timeout=socket_connect_timeout,
            socket_timeout=socket_timeout,
            max_idle_time=max_idle_time,  
            idle_check_interval=idle_check_interval,
            **pool_kwargs
        )

        pool_cache[cache_key] = pool

        logger.debug(
            f"创建同步Redis阻塞连接池 (max={max_connections}, timeout={timeout}s, "
            f"health_check={health_check_interval}s, max_idle={max_idle_time}s): "
            f"{redis_url}, decode={decode_responses}"
        )

    return pool_cache[cache_key]


def get_async_redis_pool(
    redis_url: str,
    decode_responses: bool = True,
    max_connections: int = 200,
    socket_connect_timeout: int = 30,
    socket_timeout: Optional[int] = None,  
    socket_keepalive: bool = True,
    health_check_interval: int = 30,
    timeout: int = 60,
    max_idle_time: int = 10,
    idle_check_interval: int = 1,
    **pool_kwargs
) -> AsyncIdleTrackingBlockingConnectionPool:
    pool_cache = _async_redis_pools if decode_responses else _async_binary_redis_pools

    cache_key = f"{redis_url}:socket_timeout={socket_timeout}"


    if cache_key not in pool_cache:
        socket_keepalive_options = _get_socket_keepalive_options()

        infinite_retry = InfiniteRetry()

        pool_params = {
            'decode_responses': decode_responses,
            'max_connections': max_connections,
            'retry_on_timeout': True,
            'retry_on_error': [ConnectionError, TimeoutError, OSError, BrokenPipeError],
            'retry': infinite_retry,  
            'socket_keepalive': socket_keepalive,
            'health_check_interval': health_check_interval,
            'socket_connect_timeout': socket_connect_timeout,
            'max_idle_time': max_idle_time,  
            'idle_check_interval': idle_check_interval,
        }

        if socket_keepalive and socket_keepalive_options:
            pool_params['socket_keepalive_options'] = socket_keepalive_options

        pool_params['socket_timeout'] = socket_timeout

        pool_params.update(pool_kwargs)

        pool = AsyncIdleTrackingBlockingConnectionPool.from_url(
           redis_url,
            **pool_params
        )
        pool_cache[cache_key] = pool

        logger.debug(
            f"创建异步Redis阻塞连接池 (max={max_connections}, timeout={timeout}s, "
            f"health_check={health_check_interval}s, max_idle={max_idle_time}s): "
            f"{redis_url}, decode={decode_responses}"
        )

    return pool_cache[cache_key]


def get_dual_mode_async_redis_client(
    redis_url: str,
    max_connections: int = 200,
    **pool_kwargs
) -> tuple[redis.Redis, redis.Redis]:
    text_pool = get_async_redis_pool(
        redis_url=redis_url,
        decode_responses=True,
        max_connections=max_connections,
        **pool_kwargs
    )

    binary_pool = get_async_redis_pool(
        redis_url=redis_url,
        decode_responses=False,
        max_connections=max_connections,
        **pool_kwargs
    )

    text_client = redis.Redis(connection_pool=text_pool)
    binary_client = redis.Redis(connection_pool=binary_pool)

    return text_client, binary_client


def get_async_redis_pool_for_pubsub(
    redis_url: str,
    decode_responses: bool = True,
    max_connections: int = 10,
    health_check_interval: int = 60,
    **pool_kwargs
) -> redis.ConnectionPool:
    return get_async_redis_pool(
        redis_url=redis_url,
        decode_responses=decode_responses,
        max_connections=max_connections,
        socket_connect_timeout=30,
        socket_timeout=None,  
        socket_keepalive=True,
        health_check_interval=health_check_interval,
        **pool_kwargs
    )


def get_pg_engine_and_factory(
    dsn: str,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_recycle: int = 3600,
    echo: bool = False,
    **engine_kwargs
) -> tuple:
    print(f'{dsn=}')
    if dsn not in _pg_engines:
        engine = create_async_engine(
            dsn,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            echo=echo,
            **engine_kwargs
        )

        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        _pg_engines[dsn] = engine
        _pg_session_factories[dsn] = session_factory

        logger.debug(f"创建PostgreSQL引擎: {dsn}")

    return _pg_engines[dsn], _pg_session_factories[dsn]


async def get_asyncpg_pool(
    dsn: str,
    min_size: int = 2,
    max_size: int = 10,
    command_timeout: float = 60.0,
    timeout: float = 10.0,
    max_retries: int = 3,
    retry_delay: int = 5,
    **pool_kwargs
):
    import asyncpg  

    if dsn and '+asyncpg' in dsn:
        dsn = dsn.replace('+asyncpg', '')

    safe_dsn = _get_safe_pg_dsn(dsn)

    if dsn not in _PoolRegistry.asyncpg_pools:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"正在创建 asyncpg 连接池 (尝试 {attempt}/{max_retries}): {safe_dsn}")

                pool = await asyncpg.create_pool(
                    dsn,
                    min_size=min_size,
                    max_size=max_size,
                    command_timeout=command_timeout,
                    timeout=timeout,
                    **pool_kwargs
                )

                _PoolRegistry.asyncpg_pools[dsn] = pool
                logger.info(f"asyncpg 连接池创建成功: {safe_dsn} (min={min_size}, max={max_size})")
                break

            except Exception as e:
                logger.error(f"asyncpg 连接池创建失败 (尝试 {attempt}/{max_retries}): {safe_dsn}, 错误: {e}")

                if attempt < max_retries:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"asyncpg 连接池创建失败，已达到最大重试次数 ({max_retries})")
                    raise

    return _PoolRegistry.asyncpg_pools[dsn]


def _get_safe_pg_dsn(dsn: str) -> str:
    if not dsn:
        return "None"
    try:
        import re
        return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', dsn)
    except:
        return dsn


async def init_db_schema(db_url: str, metadata):
    if 'postgresql://' in db_url and '+asyncpg' not in db_url:
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')

    logger.info(f"正在初始化数据库表结构: {_get_safe_pg_dsn(db_url)}")

    engine, _ = get_pg_engine_and_factory(
        dsn=db_url,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        echo=False
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)
        logger.info("数据库表结构初始化完成")
    finally:
        await engine.dispose()



class DBConfig:
    """数据库配置基类"""

    @staticmethod
    def parse_redis_config(config: Union[str, Dict[str, Any]]) -> str:
        if isinstance(config, str):
            return config

        if isinstance(config, dict):
            if 'url' in config:
                return config['url']

            host = config.get('host', 'localhost')
            port = config.get('port', 6379)
            db = config.get('db', 0)
            password = config.get('password')

            if password:
                return f"redis://:{password}@{host}:{port}/{db}"
            else:
                return f"redis://{host}:{port}/{db}"

        raise ValueError(f"不支持的 Redis 配置格式: {type(config)}")

    @staticmethod
    def parse_pg_config(config: Union[str, Dict[str, Any]]) -> str:
        if isinstance(config, str):
            if config.startswith('postgresql://'):
                return config.replace('postgresql://', 'postgresql+asyncpg://', 1)
            elif config.startswith('postgresql+asyncpg://'):
                return config
            else:
                raise ValueError(f"不支持的 PostgreSQL URL 格式: {config}")

        if isinstance(config, dict):
            if 'url' in config:
                url = config['url']
                if url.startswith('postgresql://'):
                    return url.replace('postgresql://', 'postgresql+asyncpg://', 1)
                return url

            user = config.get('user', 'postgres')
            password = config.get('password', '')
            host = config.get('host', 'localhost')
            port = config.get('port', 5432)
            database = config.get('database', 'postgres')

            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

        raise ValueError(f"不支持的 PostgreSQL 配置格式: {type(config)}")


class SyncRedisConnector:
    """
    同步 Redis 连接管理器（使用全局单例连接池）

    使用示例:
        # 方式1: 直接使用
        connector = SyncRedisConnector("redis://localhost:6379/0")
        client = connector.get_client()
        client.set("key", "value")

        # 方式2: 上下文管理器
        with SyncRedisConnector("redis://localhost:6379/0") as client:
            client.set("key", "value")
    """

    def __init__(
        self,
        config: Union[str, Dict[str, Any]],
        decode_responses: bool = False,
        max_connections: int = 200,
        **pool_kwargs
    ):
        self.redis_url = DBConfig.parse_redis_config(config)
        self.decode_responses = decode_responses
        self.max_connections = max_connections
        self.pool_kwargs = pool_kwargs

        self._pool: sync_redis.ConnectionPool = get_sync_redis_pool(
            self.redis_url,
            decode_responses=self.decode_responses,
            max_connections=self.max_connections,
            **self.pool_kwargs
        )
        self._client: Optional[sync_redis.Redis] = None
        logger.debug(f"同步 Redis 连接器初始化: {self.redis_url}")

    def get_client(self) -> sync_redis.Redis:
        try:
            return sync_redis.Redis(connection_pool=self._pool)
        except Exception as e:
            logger.error(f"获取同步 Redis 客户端失败: {e}")
            traceback.print_exc()
            raise

    def close(self):
        pass

    def __enter__(self) -> sync_redis.Redis:
        self._client = self.get_client()
        return self._client

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            self._client.close()
            self._client = None


class RedisConnector:
    """
    异步 Redis 连接管理器（支持双模式，使用全局单例连接池）

    双模式说明：
    - 文本模式（decode_responses=True）：返回字符串，用于普通操作
    - 二进制模式（decode_responses=False）：返回字节，用于 Stream 等需要原始数据的操作

    注意：两个模式使用独立的连接池，但都享受全局单例机制

    使用示例:
        # 方式1: 文本模式（默认）
        connector = RedisConnector("redis://localhost:6379/0")
        client = await connector.get_client()
        await client.set("key", "value")

        # 方式2: 二进制模式
        binary_client = await connector.get_client(binary_mode=True)
        messages = await binary_client.xreadgroup(...)

        # 方式3: 便捷方法
        messages = await connector.xreadgroup_binary(...)
    """

    def __init__(
        self,
        config: Union[str, Dict[str, Any]],
        decode_responses: bool = True,
        max_connections: int = 200,
        **pool_kwargs
    ):
        self.redis_url = DBConfig.parse_redis_config(config)
        self.decode_responses = decode_responses
        self.max_connections = max_connections
        self.pool_kwargs = pool_kwargs

        self._text_client: Optional[redis.Redis] = None
        self._binary_client: Optional[redis.Redis] = None
        logger.debug(f"异步 Redis 连接器初始化: {self.redis_url}")

    async def initialize(self):
        pass  

    async def get_client(self, binary_mode: bool = False) -> redis.Redis:
        try:
            if self._text_client is None:
                self._text_client, self._binary_client = get_dual_mode_async_redis_client(
                    redis_url=self.redis_url,
                    max_connections=self.max_connections,
                    **self.pool_kwargs
                )

            return self._binary_client if binary_mode else self._text_client
        except Exception as e:
            logger.error(f"获取 Redis 客户端失败: {e}")
            traceback.print_exc()
            raise

    async def xreadgroup_binary(self, *args, **kwargs):
        binary_client = await self.get_client(binary_mode=True)
        return await binary_client.xreadgroup(*args, **kwargs)

    async def xread_binary(self, *args, **kwargs):
        binary_client = await self.get_client(binary_mode=True)
        return await binary_client.xread(*args, **kwargs)

    async def close(self):
        pass

    async def __aenter__(self) -> redis.Redis:
        await self.initialize()
        self._client = await self.get_client()
        return self._client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.close()
            self._client = None


class PostgreSQLConnector:
    """
    PostgreSQL 连接管理器（使用全局单例引擎）

    使用示例:
        # 方式1: 直接使用
        connector = PostgreSQLConnector("postgresql://user:pass@localhost/db")
        session = await connector.get_session()

        # 方式2: 上下文管理器
        async with PostgreSQLConnector(config) as session:
            result = await session.execute(select(User))
    """

    def __init__(
        self,
        config: Union[str, Dict[str, Any]],
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        echo: bool = False,
        **engine_kwargs
    ):
        self.dsn = DBConfig.parse_pg_config(config)
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.echo = echo
        self.engine_kwargs = engine_kwargs

        self._engine, self._session_factory = get_pg_engine_and_factory(
            self.dsn,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_recycle=self.pool_recycle,
            echo=self.echo,
            **self.engine_kwargs
        )
        logger.debug(f"PostgreSQL 连接器初始化: {self.dsn}")

    async def initialize(self):
        pass

    async def get_session(self) -> AsyncSession:
        try:
            return self._session_factory()
        except Exception as e:
            logger.error(f"获取 PostgreSQL 会话失败: {e}")
            traceback.print_exc()
            raise

    @asynccontextmanager
    async def session_scope(self):
        session = await self.get_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self):
        pass

    async def __aenter__(self) -> AsyncSession:
        await self.initialize()
        return await self.get_session()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class ConnectionManager:
    """
    连接管理器 - 统一管理 Redis 和 PostgreSQL 连接

    使用示例:
        manager = ConnectionManager(
            redis_config="redis://localhost:6379/0",
            pg_config={"host": "localhost", "user": "admin", "password": "secret", "database": "mydb"}
        )

        # 获取 Redis 客户端
        redis_client = await manager.get_redis_client()

        # 获取 PostgreSQL 会话
        pg_session = await manager.get_pg_session()

        # 关闭所有连接
        await manager.close_all()
    """

    def __init__(
        self,
        redis_config: Optional[Union[str, Dict[str, Any]]] = None,
        pg_config: Optional[Union[str, Dict[str, Any]]] = None,
        redis_decode: bool = True,
        redis_max_connections: int = 50,
        pg_pool_size: int = 5,
        pg_max_overflow: int = 10,
    ):
        self._redis_connector: Optional[RedisConnector] = None
        self._pg_connector: Optional[PostgreSQLConnector] = None

        if redis_config:
            self._redis_connector = RedisConnector(
                redis_config,
                decode_responses=redis_decode,
                max_connections=redis_max_connections
            )

        if pg_config:
            self._pg_connector = PostgreSQLConnector(
                pg_config,
                pool_size=pg_pool_size,
                max_overflow=pg_max_overflow
            )

    async def get_redis_client(self, decode: bool = True) -> redis.Redis:
        if not self._redis_connector:
            raise ValueError("未配置 Redis 连接")

        if decode != self._redis_connector.decode_responses:
            temp_connector = RedisConnector(
                self._redis_connector.redis_url,
                decode_responses=decode
            )
            return await temp_connector.get_client()

        return await self._redis_connector.get_client()

    async def get_pg_session(self) -> AsyncSession:
        if not self._pg_connector:
            raise ValueError("未配置 PostgreSQL 连接")

        return await self._pg_connector.get_session()

    @asynccontextmanager
    async def pg_session_scope(self):
        if not self._pg_connector:
            raise ValueError("未配置 PostgreSQL 连接")

        async with self._pg_connector.session_scope() as session:
            yield session

    async def close_all(self):
        if self._redis_connector:
            await self._redis_connector.close()
        if self._pg_connector:
            await self._pg_connector.close()



async def create_redis_client(
    config: Union[str, Dict[str, Any]],
    decode_responses: bool = True
) -> redis.Redis:
    connector = RedisConnector(config, decode_responses=decode_responses)
    return await connector.get_client()


async def create_pg_session(
    config: Union[str, Dict[str, Any]]
) -> AsyncSession:
    connector = PostgreSQLConnector(config)
    return await connector.get_session()



_sync_redis_clients = _PoolRegistry.sync_redis_clients
_sync_binary_redis_clients = _PoolRegistry.sync_binary_redis_clients
_async_redis_clients = _PoolRegistry.async_redis_clients
_async_binary_redis_clients = _PoolRegistry.async_binary_redis_clients

def get_sync_redis_client(
    redis_url: str,
    decode_responses: bool = True,
    max_connections: int = 1000,
    **pool_kwargs
) -> sync_redis.StrictRedis:
    pool_kwargs.pop('name', None)

    client_cache = _sync_redis_clients if decode_responses else _sync_binary_redis_clients

    socket_timeout_val = pool_kwargs.get('socket_timeout', 60)  
    cache_key = f"{redis_url}:socket_timeout={socket_timeout_val}"

    if cache_key not in client_cache:
        pool = get_sync_redis_pool(
            redis_url=redis_url,
            decode_responses=decode_responses,
            max_connections=max_connections,
            **pool_kwargs
        )

        client_cache[cache_key] = sync_redis.StrictRedis(connection_pool=pool)
        logger.debug(f"创建同步Redis客户端实例: {redis_url}, decode={decode_responses}, PID={os.getpid()}")

    return client_cache[cache_key]


def get_async_redis_client(
    redis_url: str,
    decode_responses: bool = True,
    max_connections: int = 1000,
    socket_timeout: Optional[int] = None,  
    **pool_kwargs
) -> redis.StrictRedis:
    pool_kwargs.pop('name', None)

    client_cache = _async_redis_clients if decode_responses else _async_binary_redis_clients

    cache_key = f"{redis_url}:socket_timeout={socket_timeout}"

    if cache_key not in client_cache:
        pool = get_async_redis_pool(
            redis_url=redis_url,
            decode_responses=decode_responses,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            **pool_kwargs
        )

        client_cache[cache_key] = redis.StrictRedis(connection_pool=pool)
        logger.debug(f"创建异步Redis客户端实例: {redis_url}, decode={decode_responses}, PID={os.getpid()}")

    return client_cache[cache_key]


def clear_all_cache():
    _PoolRegistry.clear_all()



__all__ = [
    'get_sync_redis_pool',
    'get_async_redis_pool',
    'get_async_redis_pool_for_pubsub',  
    'get_pg_engine_and_factory',
    'get_asyncpg_pool',  

    'init_db_schema',  

    'get_sync_redis_client',
    'get_async_redis_client',
    'get_dual_mode_async_redis_client',  

    'clear_all_cache',

    'DBConfig',

    'SyncRedisConnector',
    'RedisConnector',
    'PostgreSQLConnector',
    'ConnectionManager',

    'create_redis_client',
    'create_pg_session',
]
