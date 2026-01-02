"""
分析服务层
处理数据分析相关的业务逻辑
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """分析服务类"""
    
    def __init__(self, namespace_data_access):
        self.namespace_data_access = namespace_data_access
    
    async def get_namespaces(self) -> List[Dict[str, Any]]:
        return await self.namespace_data_access.get_all_namespaces()
    
    async def get_queue_stats(
        self,
        namespace: str
    ) -> List[Dict[str, Any]]:
        return await self.namespace_data_access.get_queue_stats(namespace)