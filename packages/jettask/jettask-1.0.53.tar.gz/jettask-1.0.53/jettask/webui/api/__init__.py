"""
API v1 路由模块集合

路由结构：
- /api/v1/namespaces - 命名空间列表和创建（全局）
- /api/v1/{namespace} - 命名空间详情、更新、删除（命名空间下）
- /api/v1/{namespace}/statistics - 命名空间统计（命名空间下）
- /api/v1/{namespace}/queues - 队列管理（命名空间下的资源）
- /api/v1/{namespace}/queues/send - 任务发送（命名空间下的资源，已合并到 queues）
- /api/v1/{namespace}/sql-history - SQL 历史查询（命名空间下的资源）
- /api/v1/{namespace}/scheduled - 定时任务（命名空间下的资源）
- /api/v1/{namespace}/workers - Worker 监控（命名空间下的资源）
- /api/v1/{namespace}/settings - 设置（命名空间下的资源）
- /api/v1/{namespace}/alerts - 告警规则（命名空间下的资源）
- /api/v1/{namespace}/webhooks - Webhook 回调接收（命名空间下的资源）
- /api/v1/{namespace}/assets - 资产管理（命名空间下的资源）
"""
from fastapi import APIRouter

from .overview import router as overview_router                           
from .namespaces import global_router as namespaces_global_router         
from .namespaces import namespace_router as namespaces_namespace_router   
from .queues import router as queues_router                               
from .scheduled import router as scheduled_router                         
from .alerts import router as alerts_router                               
from .settings import router as settings_router                           
from .workers import router as workers_router                             
from .sql_history import router as sql_history_router                     
from .auth import router as auth_router                                   
from .webhooks import router as webhooks_router                           
from .assets import router as assets_router                               

api_router = APIRouter(prefix="/api/task/v1")

api_router.include_router(auth_router)               
api_router.include_router(namespaces_global_router)  
api_router.include_router(alerts_router)             

namespace_router = APIRouter(prefix="/{namespace}")

namespace_router.include_router(namespaces_namespace_router)  
namespace_router.include_router(overview_router)              
namespace_router.include_router(queues_router)                
namespace_router.include_router(sql_history_router)           
namespace_router.include_router(scheduled_router)             
namespace_router.include_router(workers_router)               
namespace_router.include_router(settings_router)              
namespace_router.include_router(webhooks_router)              
namespace_router.include_router(assets_router)                

api_router.include_router(namespace_router)

__all__ = ['api_router']


