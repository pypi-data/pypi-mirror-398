"""批量缓冲区管理器

负责收集任务数据和ACK信息，批量写入数据库并ACK。
支持 INSERT 和 UPDATE 两种操作类型。
"""

import time
import asyncio
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class BatchBuffer:
    """批量缓冲区管理器

    负责：
    1. 收集任务数据和ACK信息
    2. 判断是否应该刷新（批量大小或超时）
    3. 批量写入数据库并ACK
    4. 自动定时刷新机制
    """

    def __init__(
        self,
        max_size: int = 1000,
        max_delay: float = 5.0,
        operation_type: str = 'insert',  
        redis_client_getter=None  
    ):
        self.max_size = max_size
        self.max_delay = max_delay
        self.operation_type = operation_type
        self.redis_client_getter = redis_client_getter

        self.records: List[Dict[str, Any]] = []
        self.contexts: List[Any] = []  

        self.last_flush_time = time.time()
        self.flush_lock = asyncio.Lock()

        self.total_flushed = 0
        self.flush_count = 0

        self._auto_flush_task: Optional[asyncio.Task] = None
        self._running = False
        self._db_manager = None

    async def add(self, record: dict, context: Any = None):
        if self.operation_type == 'insert' and record.get('queue') == 'TASK_CHANGES':
            logger.debug(f"跳过 TASK_CHANGES 队列的 INSERT 操作: {record.get('stream_id')}")
            if context and hasattr(context, 'ack'):
                try:
                    context.ack()
                    logger.debug(f"  ✓ 已确认 TASK_CHANGES 消息: {record.get('stream_id')}")
                except Exception as e:
                    logger.error(f"  ✗ 确认 TASK_CHANGES 消息失败: {e}")
            return

        self.records.append(record)
        if context:
            self.contexts.append(context)

    def should_flush(self) -> bool:
        if not self.records:
            return False

        if len(self.records) >= self.max_size:
            logger.debug(
                f"[{self.operation_type.upper()}] 缓冲区已满 "
                f"({len(self.records)}/{self.max_size})，触发刷新"
            )
            return True

        elapsed = time.time() - self.last_flush_time
        if elapsed >= self.max_delay:
            logger.debug(
                f"[{self.operation_type.upper()}] 缓冲区超时 "
                f"({elapsed:.1f}s >= {self.max_delay}s)，触发刷新"
            )
            return True

        return False

    async def flush(self, db_manager):
        if not self.records:
            return 0

        records_to_process = self.records.copy()
        contexts_to_process = self.contexts.copy()
        count = len(records_to_process)

        self.records.clear()
        self.contexts.clear()
        self.last_flush_time = time.time()

        start_time = time.time()

        try:
            logger.info(f"[{self.operation_type.upper()}] 开始批量刷新 {count} 条记录...")

            if self.operation_type == 'update' and self.redis_client_getter:
                await self._batch_fetch_task_info_from_redis(records_to_process)

            if self.operation_type == 'insert':
                await db_manager.batch_insert_tasks(records_to_process)
                logger.info(f"  ✓ 批量插入 {count} 条任务记录")
            else:  
                await db_manager.batch_update_tasks(records_to_process)
                logger.info(f"  ✓ 批量更新 {count} 条任务状态")
            if contexts_to_process:
                ctx_groups = {}
                for ctx in contexts_to_process:
                    if hasattr(ctx, 'event_id') and hasattr(ctx, 'acks'):
                        group_key = (ctx.queue, ctx.group_name)
                        if group_key not in ctx_groups:
                            ctx_groups[group_key] = {'ctx': ctx, 'event_ids': []}
                        ctx_groups[group_key]['event_ids'].append(ctx.event_id)

                total_acked = 0
                for group_key, group_data in ctx_groups.items():
                    ctx = group_data['ctx']
                    event_ids = group_data['event_ids']
                    try:
                        ctx.acks(event_ids)
                        total_acked += len(event_ids)
                        logger.debug(
                            f"  ✓ ACK {len(event_ids)} 条消息 "
                            f"(queue={group_key[0]}, group={group_key[1]})"
                        )
                    except Exception as e:
                        logger.error(
                            f"  ✗ ACK 失败 (queue={group_key[0]}, group={group_key[1]}): {e}"
                        )

                if total_acked > 0:
                    logger.info(f"  ✓ 批量确认 {total_acked} 条消息")

            self.total_flushed += count
            self.flush_count += 1
            elapsed = time.time() - start_time

            logger.info(
                f"[{self.operation_type.upper()}] ✓ 批量刷新完成! "
                f"本次: {count}条, "
                f"耗时: {elapsed:.3f}s, "
                f"总计: {self.total_flushed}条 ({self.flush_count}次刷新)"
            )

            return count

        except Exception as e:
            logger.error(
                f"[{self.operation_type.upper()}] ✗ 批量刷新失败: {e}",
                exc_info=True
            )
            logger.error(f"  ✗ 丢失 {count} 条记录")
            raise

    def get_stats(self) -> dict:
        return {
            'operation_type': self.operation_type,
            'current_size': len(self.records),
            'max_size': self.max_size,
            'total_flushed': self.total_flushed,
            'flush_count': self.flush_count,
            'avg_per_flush': self.total_flushed // self.flush_count if self.flush_count > 0 else 0
        }

    async def _auto_flush_loop(self):
        logger.info(f"[{self.operation_type.upper()}] 启动自动刷新任务，检查间隔: {self.max_delay}s")

        while self._running:
            try:
                await asyncio.sleep(self.max_delay)

                if self.should_flush():
                    logger.debug(
                        f"[{self.operation_type.upper()}] 自动刷新触发，"
                        f"缓冲区大小: {len(self.records)}"
                    )
                    await self.flush(self._db_manager)

            except asyncio.CancelledError:
                logger.info(f"[{self.operation_type.upper()}] 自动刷新任务被取消")
                break
            except Exception as e:
                logger.error(
                    f"[{self.operation_type.upper()}] 自动刷新任务出错: {e}",
                    exc_info=True
                )

    async def start_auto_flush(self, db_manager):
        if self._auto_flush_task is not None and not self._auto_flush_task.done():
            logger.warning(f"[{self.operation_type.upper()}] 自动刷新任务已在运行")
            return

        self._db_manager = db_manager
        self._running = True
        self._auto_flush_task = asyncio.create_task(self._auto_flush_loop())
        logger.info(f"[{self.operation_type.upper()}] 自动刷新任务已启动")

    async def stop_auto_flush(self):
        self._running = False

        if self._auto_flush_task is not None and not self._auto_flush_task.done():
            self._auto_flush_task.cancel()
            try:
                await self._auto_flush_task
            except asyncio.CancelledError:
                pass
            logger.info(f"[{self.operation_type.upper()}] 自动刷新任务已停止")

        if self.records and self._db_manager:
            logger.info(f"[{self.operation_type.upper()}] 执行最终刷新，剩余 {len(self.records)} 条记录")
            await self.flush(self._db_manager)
    async def _batch_fetch_task_info_from_redis(self, records: List[Dict[str, Any]]):
        if not records or not self.redis_client_getter:
            return

        from .consumer import _parse_task_info

        redis_client = self.redis_client_getter()
        if not redis_client:
            logger.error("无法获取 Redis 客户端")
            return

        task_ids = [record['task_id'] for record in records if 'task_id' in record]
        if not task_ids:
            return

        logger.info(f"  ⏳ 使用 pipeline 批量获取 {len(task_ids)} 个任务信息...")

        try:
            pipeline = redis_client.pipeline()
            for task_id in task_ids:
                pipeline.hgetall(task_id)

            results = await pipeline.execute()

            valid_count = 0
            for record, task_info in zip(records, results):
                if not task_info:
                    logger.warning(f"  ⚠ 无法找到任务状态信息: {record.get('task_id')}")
                    continue

                parsed_info = _parse_task_info(task_info)
                record.update(parsed_info)
                valid_count += 1

            logger.info(f"  ✓ 成功获取 {valid_count}/{len(task_ids)} 个任务信息")

        except Exception as e:
            logger.error(f"  ✗ 批量获取任务信息失败: {e}", exc_info=True)
