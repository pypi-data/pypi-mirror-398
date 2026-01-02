"""
定时任务调度模块

本模块提供：
- TaskScheduler - 定时任务调度器，负责周期性扫描和触发任务
"""
import asyncio
import logging
from typing import Optional, List
from datetime import datetime, timezone
import time
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jettask.core.message import TaskMessage
from jettask.db.models import ScheduledTask, TaskType
from jettask.db.connector import get_pg_engine_and_factory, _get_safe_pg_dsn

logger = logging.getLogger('app')




class TaskScheduler:
    """
    定时任务调度器

    设计理念：
    1. 直接从数据库读取即将到期的任务（避免 Redis 中间层）
    2. 提前1小时获取任务，利用延迟任务功能（TaskMessage 的 delay 参数）
    3. 发送后立即更新数据库状态，防止重复发送
    4. 减少数据库查询频率，提高系统可维护性

    工作流程：
    1. 定期扫描数据库（默认30秒一次）
    2. 查找未来1小时内需要执行的任务
    3. 使用 TaskMessage + delay 发送到队列
    4. 更新任务状态（周期性任务计算下次执行时间，一次性任务禁用）
    """

    def __init__(
        self,
        app,
        db_url: str,
        scan_interval: float = 3.0,
        batch_size: int = 100,
        lookahead_seconds: int = 3600,  
        **kwargs  
    ):
        self.app = app
        self.db_url = db_url

        self.scan_interval = scan_interval
        self.batch_size = batch_size
        self.lookahead_seconds = lookahead_seconds

        _, self._session_factory = get_pg_engine_and_factory(
            dsn=db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=False
        )

        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        logger.info(
            f"TaskScheduler initialized: "
            f"scan_interval={scan_interval}s, "
            f"batch_size={batch_size}, "
            f"lookahead={lookahead_seconds}s, "
            f"db_url={_get_safe_pg_dsn(db_url)}"
        )

    async def start(self, wait: bool = False):
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._stop_event.clear()

        self._task = asyncio.create_task(self._run_loop())

        logger.info("TaskScheduler started")

        if wait:
            try:
                await self._task
            except asyncio.CancelledError:
                logger.info("Scheduler was cancelled")
            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                raise

    async def stop(self):
        if not self._running:
            logger.warning("Scheduler is not running")
            return

        logger.info("Stopping TaskScheduler...")

        self._running = False
        self._stop_event.set()

        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Scheduler task did not finish in time, cancelling...")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            except Exception as e:
                logger.error(f"Error while stopping scheduler: {e}", exc_info=True)

        logger.info("TaskScheduler stopped")

    async def _run_loop(self):
        logger.info("Scheduler loop started")

        try:
            while self._running:
                try:
                    await self._schedule_once()
                    print(f'{self.scan_interval=}')
                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(),
                            timeout=self.scan_interval
                        )
                        break
                    except asyncio.TimeoutError:
                        pass

                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                    await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")

        finally:
            logger.info("Scheduler loop exited")

    async def _schedule_once(self):
        start_time = time.time()
        logger.debug("开始调度检查...")  

        session = self._session_factory()
        try:
            async with session.begin():
                tasks = await ScheduledTask.get_ready_tasks(
                    session,
                    batch_size=self.batch_size,
                    lookahead_seconds=self.lookahead_seconds
                )

                if not tasks:
                    logger.debug("No tasks ready to schedule")
                    return 0

                logger.info(f"Found {len(tasks)} tasks ready to schedule (within {self.lookahead_seconds}s)")

                scheduled_count = 0
                failed_tasks = []

                for task in tasks:
                    try:
                        success = await self._send_task_with_delay(task)

                        if success:
                            scheduled_count += 1
                        else:
                            failed_tasks.append(task)

                    except Exception as e:
                        logger.error(
                            f"Error scheduling task {task.scheduler_id}: {e}",
                            exc_info=True
                        )
                        failed_tasks.append(task)

                await self._update_tasks_after_scheduling(session, tasks)

        finally:
            await session.close()

        duration = time.time() - start_time
        logger.info(
            f"Schedule cycle completed: "
            f"scheduled={scheduled_count}, "
            f"failed={len(failed_tasks)}, "
            f"duration={duration:.2f}s"
        )

        if failed_tasks:
            failed_ids = [t.scheduler_id for t in failed_tasks]
            logger.warning(f"Failed to schedule tasks: {failed_ids}")

        return scheduled_count

    async def _send_task_with_delay(self, task: ScheduledTask) -> bool:

        now = datetime.now(timezone.utc)
        delay = None

        if task.next_run_time:
            if task.next_run_time > now:
                delay = (task.next_run_time - now).total_seconds()
            else:
                delay = None

        msg = TaskMessage(
            queue=task.queue_name,
            args=task.task_args if task.task_args else [],
            kwargs=task.task_kwargs if task.task_kwargs else {},
            priority=task.priority,
            delay=delay,
            scheduled_task_id=task.id  
        )

        try:
            event_ids = await self.app.send_tasks([msg], asyncio=True)

            if event_ids:
                event_id = event_ids[0]

                if delay:
                    logger.info(
                        f"Scheduled task: scheduler_id={task.scheduler_id}, "
                        f"queue={task.queue_name}, "
                        f"event_id={event_id}, "
                        f"delay={delay:.1f}s"
                    )
                else:
                    logger.info(
                        f"Scheduled task (immediate): scheduler_id={task.scheduler_id}, "
                        f"queue={task.queue_name}, "
                        f"event_id={event_id}"
                    )
                return True
            else:
                logger.warning(f"Failed to send task {task.scheduler_id}: no event_id returned")
                return False

        except Exception as e:
            logger.error(f"Error sending task {task.scheduler_id}: {e}", exc_info=True)
            return False

    async def _update_tasks_after_scheduling(self, session: AsyncSession, tasks: List[ScheduledTask]):
        updates = []  
        once_task_ids = []  

        for task in tasks:
            if task.task_type == TaskType.ONCE.value:
                once_task_ids.append(task.id)
            else:
                last_run = task.next_run_time
                task.last_run_time = last_run
                next_run = task.calculate_next_run_time(from_time=last_run)
                next_trigger = task.calculate_trigger_time(next_run) if next_run else None

                updates.append((task.id, next_run, next_trigger, last_run))

        if updates:
            try:
                await ScheduledTask.batch_update_next_run_times(session, updates)
                logger.info(f"Updated {len(updates)} recurring tasks")
                for task_id, next_run, next_trigger, last_run in updates:
                    logger.info(
                        f"  Task {task_id}: next_run={next_run}, "
                        f"next_trigger={next_trigger}, last_run={last_run}"
                    )
            except Exception as e:
                logger.error(f"Failed to update recurring tasks: {e}", exc_info=True)

        if once_task_ids:
            try:
                await ScheduledTask.batch_disable_once_tasks(session, once_task_ids)
                logger.info(f"Disabled {len(once_task_ids)} once tasks")
            except Exception as e:
                logger.error(f"Failed to disable once tasks: {e}", exc_info=True)

    async def trigger_now(self, task_id: int) -> bool:
        session = self._session_factory()
        try:
            task = await ScheduledTask.get_by_id(session, task_id)
            if not task:
                logger.warning(f"Task {task_id} not found")
                return False

            msg = TaskMessage(
                queue=task.queue_name,
                args=task.task_args if task.task_args else [],
                kwargs=task.task_kwargs if task.task_kwargs else {},
                priority=task.priority,
                scheduled_task_id=task.id
            )

            try:
                event_ids = await self.app.send_tasks([msg], asyncio=True)

                if event_ids:
                    logger.info(
                        f"Manually triggered task {task.scheduler_id}: "
                        f"event_id={event_ids[0]}"
                    )
                    return True

            except Exception as e:
                logger.error(f"Error triggering task {task.scheduler_id}: {e}", exc_info=True)

            return False
        finally:
            await session.close()

    async def trigger_by_scheduler_id(self, scheduler_id: str) -> bool:
        session = self._session_factory()
        try:
            task = await ScheduledTask.get_by_scheduler_id(session, scheduler_id)
            if not task:
                logger.warning(f"Task with scheduler_id '{scheduler_id}' not found")
                return False

            return await self.trigger_now(task.id)
        finally:
            await session.close()


__all__ = ['TaskScheduler']
