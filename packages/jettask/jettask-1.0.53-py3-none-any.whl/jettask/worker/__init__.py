"""
Worker 管理模块

提供 Worker 的创建、生命周期管理、状态监控等功能。

推荐使用接口:
    from jettask.worker import WorkerManager, HeartbeatManager

    # Worker 状态管理（包含 Worker ID 生成、注册、状态管理等）
    worker_manager = WorkerManager(redis, async_redis, 'jettask')
    worker_id = worker_manager.generate_worker_id('prefix')
    await worker_manager.register_worker(worker_id)

    # 心跳管理（协程驱动）
    heartbeat = HeartbeatManager.create_and_start(...)
"""

from .lifecycle import WorkerManager
from .heartbeat import HeartbeatManager

WorkerState = WorkerManager
WorkerStateManager = WorkerManager
WorkerRegistry = WorkerManager
WorkerScanner = WorkerManager  
OfflineWorkerRecovery = WorkerManager  

__all__ = [
    'WorkerManager',      
    'HeartbeatManager',   

    'WorkerState',
    'WorkerStateManager',
    'WorkerRegistry',
    'WorkerScanner',

    'OfflineWorkerRecovery',
]
