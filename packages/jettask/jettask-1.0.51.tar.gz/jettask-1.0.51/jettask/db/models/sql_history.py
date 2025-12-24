"""
SQLHistory 模型

存储用户的 SQL WHERE 查询历史记录，支持模糊搜索和自动补全
"""
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Index
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from ..base import Base


class SQLHistory(Base):
    """
    SQL 查询历史表

    存储用户输入的 WHERE 条件，支持模糊搜索、使用统计和分类管理
    """
    __tablename__ = 'sql_history'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    namespace = Column(String(100), nullable=False, comment='命名空间')

    where_clause = Column(Text, nullable=False, comment='SQL WHERE 条件（不含 WHERE 关键字）')

    alias = Column(String(200), nullable=True, comment='查询别名（可选）')

    category = Column(
        String(20),
        nullable=False,
        default='user',
        comment='类别: system（系统内置，不可删除）/ user（用户历史，可删除）'
    )

    usage_count = Column(Integer, nullable=False, default=1, comment='使用次数')

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment='创建时间'
    )

    last_used_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment='最后使用时间'
    )

    __table_args__ = (
        Index('idx_sql_history_namespace_category', 'namespace', 'category'),
        Index('idx_sql_history_namespace_usage_created', 'namespace', 'usage_count', 'created_at'),
        Index('idx_sql_history_where_clause', 'where_clause'),
        Index('idx_sql_history_alias', 'alias'),
        Index('idx_sql_history_namespace_where_unique', 'namespace', 'where_clause', unique=True),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'namespace': self.namespace,
            'where_clause': self.where_clause,
            'alias': self.alias,
            'category': self.category,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
        }

    def __repr__(self) -> str:
        return f"<SQLHistory(id={self.id}, category='{self.category}', usage_count={self.usage_count})>"
