"""PostgreSQL Consumer - 基于通配符队列的新实现

完全替换旧的 consumer.py 实现，使用 Jettask 通配符队列功能。
"""

import time
import logging
from datetime import datetime, timezone

from jettask import Jettask
from jettask.core.context import TaskContext
from jettask.db.connector import get_pg_engine_and_factory, DBConfig
from .buffer import BatchBuffer
from .persistence import TaskPersistence

logger = logging.getLogger(__name__)


def _decode_redis_field(value, field_type='str'):
    if not value:
        return None

    if isinstance(value, bytes):
        try:
            value = value.decode('utf-8')
        except Exception:
            return None

    try:
        if field_type == 'int':
            return int(value) if value else 0
        elif field_type == 'float':
            return float(value) if value else None
        else:  
            return value
    except (ValueError, TypeError):
        return None


def _extract_task_name_from_consumer(consumer: str) -> str:
    if not consumer:
        return None

    try:
        last_part = consumer.split('-')[-1]
        task_name = last_part.split(':')[0]
        return task_name if task_name else None
    except (IndexError, AttributeError):
        logger.warning(f"Failed to extract task_name from consumer: {consumer}")
        return None


def _parse_task_info(task_info: dict) -> dict:
    consumer = _decode_redis_field(task_info.get(b'consumer'), 'str')


    return {
        'retries': _decode_redis_field(task_info.get(b'retries'), 'int'),
        'trigger_time': _decode_redis_field(task_info.get(b'trigger_time_float'), 'float'),
        'started_at': _decode_redis_field(task_info.get(b'started_at'), 'float'),
        'completed_at': _decode_redis_field(task_info.get(b'completed_at'), 'float'),
        'consumer': consumer,
        'queue': _decode_redis_field(task_info.get(b'queue'), 'str'),  
        'status': _decode_redis_field(task_info.get(b'status'), 'str'),
        'result': task_info.get(b'result'),  
        'error': task_info.get(b'exception') or task_info.get(b'error'),  
    }


def _extract_event_id_from_task_id(task_id: str) -> str:
    if not task_id:
        return None

    parts = task_id.split(':')
    if len(parts) >= 3:
        return parts[2]  

    return None


def _extract_task_name_from_task_id(task_id: str) -> str:
    if not task_id:
        return None

    parts = task_id.split(':')
    if len(parts) >= 5:
        return parts[4]  

    return None


class PostgreSQLConsumer:
    """PostgreSQL Consumer - 基于通配符队列

    核心特性：
    1. 使用 @app.task(queue='*') 监听所有队列
    2. 使用 @app.task(queue='TASK_CHANGES') 处理状态更新
    3. 批量 INSERT 和 UPDATE
    4. 自动队列发现（Jettask 内置）
    """

    def __init__(
        self,
        pg_config,  
        redis_config,  
        prefix: str = "jettask",
        namespace_id: str = None,
        namespace_name: str = None,
        batch_size: int = 1000,
        flush_interval: float = 5.0
    ):
        self.pg_config = pg_config
        self.redis_config = redis_config
        self.redis_prefix = prefix
        self.namespace_id = namespace_id
        self.namespace_name = namespace_name or "default"

        if isinstance(redis_config, dict):
            redis_url = redis_config.get('url') or redis_config.get('redis_url')
            if not redis_url:
                password = redis_config.get('password', '')
                host = redis_config.get('host', 'localhost')
                port = redis_config.get('port', 6379)
                db = redis_config.get('db', 0)
                redis_url = f"redis://"
                if password:
                    redis_url += f":{password}@"
                redis_url += f"{host}:{port}/{db}"
        else:
            redis_url = f"redis://"
            if hasattr(redis_config, 'password') and redis_config.password:
                redis_url += f":{redis_config.password}@"
            redis_url += f"{redis_config.host}:{redis_config.port}/{redis_config.db}"

        self.redis_url = redis_url
        logger.debug(f"构建 Redis URL: {redis_url}")

        self.async_engine = None
        self.AsyncSessionLocal = None
        self.db_manager = None

        self.app = Jettask(
            redis_url=redis_url,
            redis_prefix=prefix
        )

        self.insert_buffer = BatchBuffer(
            max_size=batch_size,
            max_delay=flush_interval,
            operation_type='insert'
        )

        self.update_buffer = BatchBuffer(
            max_size=batch_size // 2,  
            max_delay=flush_interval,
            operation_type='update',
            redis_client_getter=lambda: self.app.async_binary_redis  
        )

        self._register_tasks()

        self._running = False

        self._auto_flush_started = False

    async def _ensure_auto_flush_started(self):
        if not self._auto_flush_started:
            logger.info("[Worker进程] 启动缓冲区自动刷新任务...")
            await self.insert_buffer.start_auto_flush(self.db_manager)
            await self.update_buffer.start_auto_flush(self.db_manager)
            self._auto_flush_started = True
            logger.info("[Worker进程] ✓ 缓冲区自动刷新任务已启动")

    def _register_tasks(self):
        consumer = self  

        @self.app.task(queue='*', auto_ack=False, name=f'{self.namespace_name}._handle_persist_task')
        async def _handle_persist_task(ctx: TaskContext, *args, **kwargs):
            return await consumer._do_handle_persist_task(ctx, *args, **kwargs)

        @self.app.task(queue='TASK_CHANGES', auto_ack=False, name=f'{self.namespace_name}._handle_status_update')
        async def _handle_status_update(ctx: TaskContext, **kwargs):

            return await consumer._do_handle_status_update(ctx, **kwargs)

    async def _do_handle_persist_task(self, ctx: TaskContext, *args, **kwargs):
        await self._ensure_auto_flush_started()


        if ctx.queue == f'TASK_CHANGES':
            logger.debug(f"[持久化任务] 跳过 TASK_CHANGES 队列: {ctx.event_id}")
            ctx.acks([ctx.event_id])
            return

        try:

            metadata = ctx.metadata or {}

            trigger_time = metadata.get('trigger_time', time.time())
            if isinstance(trigger_time, (str, bytes)):
                trigger_time = float(trigger_time)

            priority = metadata.get('priority', 0)
            if priority and isinstance(priority, (str, bytes)):
                priority = int(priority)
            elif priority is None:
                priority = 0

            delay = metadata.get('delay', 0)
            if delay and isinstance(delay, (str, bytes)):
                delay = float(delay)
            elif delay is None:
                delay = 0

            scheduled_task_id = metadata.get('scheduled_task_id')

            payload = {
                'args': args,
                'kwargs': kwargs,
            }

            record = {
                'stream_id': ctx.event_id,
                'queue': ctx.queue.replace(f'{self.redis_prefix}:QUEUE:', ''),
                'payload': payload,
                'priority': priority,
                'delay': delay,
                'trigger_time': trigger_time,  
                'scheduled_task_id': scheduled_task_id,
                'namespace': self.namespace_name,
                'source': 'scheduler' if scheduled_task_id else 'redis_stream',
            }

            await self.insert_buffer.add(record, ctx)
            logger.debug(f"[持久化任务] 已添加到缓冲区，当前大小: {len(self.insert_buffer.records)}/{self.insert_buffer.max_size}")

            if self.insert_buffer.should_flush():
                logger.info(f"[持久化任务] 触发刷新，缓冲区大小: {len(self.insert_buffer.records)}")
                await self.insert_buffer.flush(self.db_manager)

            if self.update_buffer.should_flush():
                await self.update_buffer.flush(self.db_manager)

        except Exception as e:
            logger.error(f"持久化任务失败: {e}", exc_info=True)
            ctx.acks([ctx.event_id])

    async def _do_handle_status_update(self, ctx: TaskContext, **kwargs):

        await self._ensure_auto_flush_started()

        try:
            task_id = kwargs.get('task_id')
            if not task_id:
                logger.warning(f"TASK_CHANGES 消息缺少 task_id: {ctx.event_id}")
                ctx.acks([ctx.event_id])
                return

            event_id = _extract_event_id_from_task_id(task_id)
            if not event_id:
                logger.error(f"无效的 task_id 格式: {task_id}")
                ctx.acks([ctx.event_id])
                return

            task_name = _extract_task_name_from_task_id(task_id)

            update_record = {
                'task_id': task_id,
                'stream_id': event_id,
                'task_name': task_name,
                'namespace': self.namespace_name,  
            }

            await self.update_buffer.add(update_record, ctx)
            logger.debug(f"[状态更新] 已添加到缓冲区，当前大小: {len(self.update_buffer.records)}/{self.update_buffer.max_size}")

            if self.update_buffer.should_flush():
                logger.info(f"[状态更新] 触发刷新，缓冲区大小: {len(self.update_buffer.records)}")
                await self.update_buffer.flush(self.db_manager)

            if self.insert_buffer.should_flush():
                await self.insert_buffer.flush(self.db_manager)

        except Exception as e:
            logger.error(f"更新任务状态失败: {e}", exc_info=True)
            ctx.acks([ctx.event_id])

    async def start(self, concurrency: int = 4, prefetch_multiplier: int = 1):
        logger.info(f"Starting PostgreSQL consumer (wildcard queue mode)")
        logger.info(f"Namespace: {self.namespace_name} ({self.namespace_id or 'N/A'})")

        dsn = DBConfig.parse_pg_config(self.pg_config)

        self.async_engine, self.AsyncSessionLocal = get_pg_engine_and_factory(
            dsn,
            pool_size=50,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False
        )

        logger.debug(f"使用全局 PostgreSQL 连接池: {dsn[:50]}...")

        self.db_manager = TaskPersistence(
            async_session_local=self.AsyncSessionLocal,
            namespace_id=self.namespace_id,
            namespace_name=self.namespace_name
        )

        self._running = True


        self.app._worker_started = True

        if self.app.task_center and self.app.task_center.is_enabled and not self.app._task_center_config:
            self.app._load_config_from_task_center()

        logger.info("正在注册待注册的限流配置...")
        self.app._apply_pending_rate_limits()

        self.app._setup_cleanup_handlers()

        logger.info("=" * 60)
        logger.info(f"启动 PG Consumer (通配符队列模式)")
        logger.info("=" * 60)
        logger.info(f"命名空间: {self.namespace_name} ({self.namespace_id or 'N/A'})")
        logger.info(f"监听队列: * (所有队列) + TASK_CHANGES (状态更新)")
        logger.info(f"INSERT 批量: {self.insert_buffer.max_size} 条")
        logger.info(f"UPDATE 批量: {self.update_buffer.max_size} 条")
        logger.info(f"刷新间隔: {self.insert_buffer.max_delay} 秒")
        logger.info(f"并发数: {concurrency}")
        logger.info("=" * 60)

        try:

            task_names = list(self.app._tasks.keys())
            logger.info(f"已注册的任务: {task_names}")

            await self.app._start(
                tasks=task_names,  
                concurrency=concurrency,
                prefetch_multiplier=prefetch_multiplier
            )
        finally:
            await self.stop()

    async def stop(self):
        logger.info("停止 PG Consumer...")
        self._running = False

        try:
            await self.insert_buffer.stop_auto_flush()
            await self.update_buffer.stop_auto_flush()
            logger.info("✓ 缓冲区自动刷新任务已停止")
        except Exception as e:
            logger.error(f"停止自动刷新任务失败: {e}")


        insert_stats = self.insert_buffer.get_stats()
        update_stats = self.update_buffer.get_stats()

        logger.info("=" * 60)
        logger.info("PG Consumer 统计信息")
        logger.info("=" * 60)
        logger.info(f"INSERT: 总计 {insert_stats['total_flushed']} 条, "
                   f"刷新 {insert_stats['flush_count']} 次, "
                   f"平均 {insert_stats['avg_per_flush']} 条/次")
        logger.info(f"UPDATE: 总计 {update_stats['total_flushed']} 条, "
                   f"刷新 {update_stats['flush_count']} 次, "
                   f"平均 {update_stats['avg_per_flush']} 条/次")
        logger.info("=" * 60)

        logger.info("PG Consumer 已停止")
