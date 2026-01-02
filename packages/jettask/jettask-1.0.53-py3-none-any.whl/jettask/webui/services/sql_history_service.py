"""
SQL 历史查询服务

提供 SQL WHERE 条件的历史记录管理、模糊搜索和使用统计功能
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc, func
from sqlalchemy.dialects.postgresql import insert

from jettask.db.models import SQLHistory
from jettask.utils.task_logger import get_task_logger

logger = get_task_logger(__name__)


class SQLHistoryService:
    """SQL 历史查询服务"""

    @classmethod
    async def search(
        cls,
        pg_session: AsyncSession,
        namespace: str,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        try:
            conditions = [SQLHistory.namespace == namespace]

            if category:
                conditions.append(SQLHistory.category == category)

            if keyword and keyword.strip():
                keyword_pattern = f"%{keyword.strip()}%"
                conditions.append(
                    or_(
                        SQLHistory.where_clause.ilike(keyword_pattern),
                        SQLHistory.alias.ilike(keyword_pattern)
                    )
                )

            stmt = select(SQLHistory).where(
                and_(*conditions)
            ).order_by(
                desc(SQLHistory.usage_count),
                desc(SQLHistory.created_at)
            ).limit(limit)

            result = await pg_session.execute(stmt)
            rows = result.scalars().all()

            return [row.to_dict() for row in rows]

        except Exception as e:
            logger.error(f"搜索 SQL 历史失败: {e}", exc_info=True)
            return []

    @classmethod
    async def save_or_update(
        cls,
        pg_session: AsyncSession,
        namespace: str,
        where_clause: str,
        alias: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        if not where_clause or not where_clause.strip():
            return None

        where_clause = where_clause.strip()

        try:
            now = datetime.now(timezone.utc)

            stmt = insert(SQLHistory).values(
                namespace=namespace,
                where_clause=where_clause,
                alias=alias,
                category='user',
                usage_count=1,
                created_at=now,
                last_used_at=now
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=['namespace', 'where_clause'],
                set_={
                    'usage_count': SQLHistory.usage_count + 1,
                    'last_used_at': now,
                    'alias': func.coalesce(stmt.excluded.alias, SQLHistory.alias)
                }
            ).returning(SQLHistory)

            result = await pg_session.execute(stmt)
            row = result.scalar_one_or_none()
            await pg_session.commit()

            if row:
                logger.debug(f"SQL 历史记录已保存/更新: {where_clause[:50]}...")
                return row.to_dict()

            return None

        except Exception as e:
            logger.error(f"保存 SQL 历史失败: {e}", exc_info=True)
            await pg_session.rollback()
            return None

    @classmethod
    async def increment_usage(
        cls,
        pg_session: AsyncSession,
        history_id: int
    ) -> bool:
        try:
            stmt = update(SQLHistory).where(
                SQLHistory.id == history_id
            ).values(
                usage_count=SQLHistory.usage_count + 1,
                last_used_at=datetime.now(timezone.utc)
            )

            result = await pg_session.execute(stmt)
            await pg_session.commit()

            if result.rowcount > 0:
                logger.debug(f"SQL 历史记录使用次数已更新: id={history_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"更新使用次数失败: {e}", exc_info=True)
            await pg_session.rollback()
            return False

    @classmethod
    async def delete_history(
        cls,
        pg_session: AsyncSession,
        history_id: int
    ) -> bool:
        try:
            stmt = delete(SQLHistory).where(
                and_(
                    SQLHistory.id == history_id,
                    SQLHistory.category == 'user'
                )
            )

            result = await pg_session.execute(stmt)
            await pg_session.commit()

            if result.rowcount > 0:
                logger.info(f"SQL 历史记录已删除: id={history_id}")
                return True

            logger.warning(f"无法删除 SQL 历史记录（不存在或为系统内置）: id={history_id}")
            return False

        except Exception as e:
            logger.error(f"删除 SQL 历史失败: {e}", exc_info=True)
            await pg_session.rollback()
            return False

    @classmethod
    async def copy_system_templates(
        cls,
        pg_session: AsyncSession,
        target_namespace: str,
        template_namespace: str = 'default'
    ) -> int:
        try:
            stmt = select(SQLHistory).where(
                and_(
                    SQLHistory.namespace == template_namespace,
                    SQLHistory.category == 'system'
                )
            )
            result = await pg_session.execute(stmt)
            templates = result.scalars().all()

            if not templates:
                logger.warning(f"模板命名空间 '{template_namespace}' 中没有系统内置查询")
                return 0

            now = datetime.now(timezone.utc)
            copied_count = 0

            for template in templates:
                stmt = insert(SQLHistory).values(
                    namespace=target_namespace,
                    where_clause=template.where_clause,
                    alias=template.alias,
                    category='system',
                    usage_count=0,
                    created_at=now,
                    last_used_at=now
                )

                stmt = stmt.on_conflict_do_nothing(
                    index_elements=['namespace', 'where_clause']
                )

                result = await pg_session.execute(stmt)
                if result.rowcount > 0:
                    copied_count += 1

            await pg_session.commit()

            logger.info(
                f"从命名空间 '{template_namespace}' 复制了 {copied_count} 条系统内置查询到 '{target_namespace}'"
            )

            return copied_count

        except Exception as e:
            logger.error(f"复制系统内置查询失败: {e}", exc_info=True)
            await pg_session.rollback()
            return 0

    @classmethod
    async def cleanup_old_records(
        cls,
        pg_session: AsyncSession,
        namespace: str,
        days: int = 90,
        max_records: int = 1000
    ) -> int:
        try:
            deleted_count = 0

            cutoff_date = datetime.now(timezone.utc) - timezone.timedelta(days=days)
            stmt = delete(SQLHistory).where(
                and_(
                    SQLHistory.namespace == namespace,
                    SQLHistory.category == 'user',
                    SQLHistory.last_used_at < cutoff_date
                )
            )
            result = await pg_session.execute(stmt)
            deleted_count += result.rowcount

            count_stmt = select(func.count(SQLHistory.id)).where(
                and_(
                    SQLHistory.namespace == namespace,
                    SQLHistory.category == 'user'
                )
            )
            count_result = await pg_session.execute(count_stmt)
            total_count = count_result.scalar() or 0

            if total_count > max_records:
                keep_stmt = select(SQLHistory.id).where(
                    and_(
                        SQLHistory.namespace == namespace,
                        SQLHistory.category == 'user'
                    )
                ).order_by(
                    desc(SQLHistory.usage_count),
                    desc(SQLHistory.last_used_at)
                ).limit(max_records)

                keep_result = await pg_session.execute(keep_stmt)
                keep_ids = [row[0] for row in keep_result.fetchall()]

                if keep_ids:
                    delete_stmt = delete(SQLHistory).where(
                        and_(
                            SQLHistory.namespace == namespace,
                            SQLHistory.category == 'user',
                            ~SQLHistory.id.in_(keep_ids)
                        )
                    )
                    result = await pg_session.execute(delete_stmt)
                    deleted_count += result.rowcount

            await pg_session.commit()

            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 条旧的 SQL 历史记录")

            return deleted_count

        except Exception as e:
            logger.error(f"清理 SQL 历史失败: {e}", exc_info=True)
            await pg_session.rollback()
            return 0
