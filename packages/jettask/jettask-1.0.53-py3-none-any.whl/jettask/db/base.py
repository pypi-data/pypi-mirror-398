"""
数据库基础配置

使用 SQLAlchemy 2.0 的异步API
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine = None
_async_session_factory = None


def get_engine(database_url: str, **kwargs):
    global _engine

    if _engine is None:
        if database_url and 'postgresql://' in database_url:
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')

        engine_kwargs = {
            'echo': kwargs.pop('echo', False),
            'pool_pre_ping': kwargs.pop('pool_pre_ping', True),
            'poolclass': kwargs.pop('poolclass', NullPool),  
        }
        engine_kwargs.update(kwargs)

        _engine = create_async_engine(database_url, **engine_kwargs)
        logger.info(f"数据库引擎已创建: {database_url.split('@')[-1]}")

    return _engine


def get_session_factory(database_url: str = None, **kwargs):
    global _async_session_factory

    if _async_session_factory is None:
        if database_url is None:
            raise ValueError("数据库URL未提供")

        engine = get_engine(database_url, **kwargs)
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _async_session_factory


def get_session(database_url: str = None, **kwargs):
    factory = get_session_factory(database_url, **kwargs)
    return factory()


async def init_db(database_url: str, **kwargs):
    from .models import Task, ScheduledTask, TaskExecutionHistory  

    engine = get_engine(database_url, **kwargs)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表已创建/更新")


async def drop_all(database_url: str, **kwargs):
    from .models import Task, ScheduledTask, TaskExecutionHistory  

    engine = get_engine(database_url, **kwargs)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.warning("所有数据库表已删除")
