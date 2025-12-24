"""PostgreSQL Consumer 模块 - V4 重构版本

基于 Jettask 通配符队列的 PostgreSQL 消费者实现。

核心特性：
- 使用通配符队列 (*) 自动发现和监听所有队列
- 独立的 TASK_CHANGES 队列处理状态更新
- 批量 INSERT 和 UPDATE 提升性能
- 支持多命名空间管理

模块结构：
- consumer.py: PostgreSQL 消费者（通配符队列实现）
- manager.py: 统一的消费者管理器
- buffer.py: 批量缓冲区
- persistence.py: 任务持久化逻辑

使用示例：
    from jettask.persistence import PostgreSQLConsumer, UnifiedConsumerManager

    # 使用 Consumer 类（单命名空间）
    consumer = PostgreSQLConsumer(
        pg_config={'url': 'postgresql://...'},
        redis_config={'url': 'redis://...'},
        prefix='jettask',
        namespace_name='default'
    )
    await consumer.start()

    # 使用 UnifiedConsumerManager（多命名空间）
    manager = UnifiedConsumerManager(
        task_center_url='http://localhost:8001',
        check_interval=30
    )
    await manager.run()
"""

from .consumer import PostgreSQLConsumer
from .manager import UnifiedConsumerManager

__all__ = [
    'PostgreSQLConsumer',
    'UnifiedConsumerManager',
]
