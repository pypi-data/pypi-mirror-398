"""
任务中心配置模块
明确区分：
1. 任务中心元数据库 - 存储命名空间、配置等管理数据
2. JetTask应用数据库 - 每个命名空间配置的Redis和PostgreSQL
"""
import os
from typing import Optional


class TaskCenterDatabaseConfig:
    """任务中心元数据库配置（用于存储命名空间等配置）"""

    def __init__(self):
        self._jettask_pg_url = os.getenv("JETTASK_PG_URL")

        if not self._jettask_pg_url:
            self.meta_db_host = os.getenv("TASK_CENTER_DB_HOST", "localhost")
            self.meta_db_port = int(os.getenv("TASK_CENTER_DB_PORT", "5432"))
            self.meta_db_user = os.getenv("TASK_CENTER_DB_USER", "jettask")
            self.meta_db_password = os.getenv("TASK_CENTER_DB_PASSWORD", "123456")
            self.meta_db_name = os.getenv("TASK_CENTER_DB_NAME", "jettask")
        else:
            import re
            match = re.match(r'postgresql\+?asyncpg?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)', self._jettask_pg_url)
            if match:
                self.meta_db_user, self.meta_db_password, self.meta_db_host, db_port, self.meta_db_name = match.groups()
                self.meta_db_port = int(db_port) if db_port else 5432
            else:
                self.meta_db_host = "localhost"
                self.meta_db_port = 5432
                self.meta_db_user = "jettask"
                self.meta_db_password = "123456"
                self.meta_db_name = "jettask"

        self.api_host = os.getenv("TASK_CENTER_API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("TASK_CENTER_API_PORT", "8001"))

        self.base_url = os.getenv("TASK_CENTER_BASE_URL", "http://localhost:8001")

    @property
    def meta_database_url(self) -> str:
        if self._jettask_pg_url:
            if 'postgresql://' in self._jettask_pg_url and '+asyncpg' not in self._jettask_pg_url:
                return self._jettask_pg_url.replace('postgresql://', 'postgresql+asyncpg://')
            return self._jettask_pg_url

        return f"postgresql+asyncpg://{self.meta_db_user}:{self.meta_db_password}@{self.meta_db_host}:{self.meta_db_port}/{self.meta_db_name}"
    
    @property
    def sync_meta_database_url(self) -> str:
        return f"postgresql://{self.meta_db_user}:{self.meta_db_password}@{self.meta_db_host}:{self.meta_db_port}/{self.meta_db_name}"
    
    @property
    def pg_url(self) -> str:
        return self.meta_database_url


task_center_config = TaskCenterDatabaseConfig()


def get_task_center_config() -> TaskCenterDatabaseConfig:
    return task_center_config