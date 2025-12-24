#!/usr/bin/env python
"""
WebUI配置管理模块
提供统一的配置管理，所有配置的环境变量读取都在此处集中处理
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class WebUIConfig:
    """
    WebUI配置管理类（单例模式）

    所有配置的环境变量读取都在初始化时完成，
    后续使用配置直接从实例属性获取，不再重复读取环境变量。

    使用方式:
        from jettask.webui.config import webui_config

        # 获取配置
        redis_url = webui_config.redis_url
        pg_url = webui_config.pg_url
    """

    _instance: Optional['WebUIConfig'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        logger.info("正在初始化 WebUI 配置...")

        self._load_env_vars()

        self._validate_required_configs()

        self._initialized = True

        logger.info("WebUI 配置初始化完成")
        self._log_config_summary()

    def _load_env_vars(self):
        self.redis_url: Optional[str] = os.getenv('JETTASK_REDIS_URL')
        self.pg_url: Optional[str] = os.getenv('JETTASK_PG_URL')

        self.redis_prefix: str = os.getenv('JETTASK_REDIS_PREFIX', 'jettask')

        use_nacos_str = os.getenv('USE_NACOS', 'false')
        self.use_nacos: bool = use_nacos_str.lower() == 'true'

        if self.use_nacos:
            self.nacos_server: Optional[str] = os.getenv('NACOS_SERVER')
            self.nacos_namespace: Optional[str] = os.getenv('NACOS_NAMESPACE')
            self.nacos_data_id: Optional[str] = os.getenv('NACOS_DATA_ID')
            self.nacos_group: Optional[str] = os.getenv('NACOS_GROUP')
        else:
            self.nacos_server = None
            self.nacos_namespace = None
            self.nacos_data_id = None
            self.nacos_group = None

        self.api_host: str = os.getenv('JETTASK_API_HOST') or os.getenv('TASK_CENTER_API_HOST', '0.0.0.0')
        self.api_port: int = int(os.getenv('JETTASK_API_PORT') or os.getenv('TASK_CENTER_API_PORT', '8001'))

        self.base_url: str = os.getenv('TASK_CENTER_BASE_URL') or f"http://{self.api_host}:{self.api_port}"

        self.log_level: str = os.getenv('JETTASK_LOG_LEVEL', 'INFO').upper()

        self.api_key: Optional[str] = os.getenv('JETTASK_API_KEY')

        self.jwt_secret_key: str = os.getenv('JETTASK_JWT_SECRET', 'jettask-default-secret-change-in-production')
        self.jwt_algorithm: str = os.getenv('JETTASK_JWT_ALGORITHM', 'HS256')
        self.jwt_access_token_expire_minutes: int = int(os.getenv('JETTASK_JWT_ACCESS_EXPIRE', '30'))
        self.jwt_refresh_token_expire_days: int = int(os.getenv('JETTASK_JWT_REFRESH_EXPIRE', '7'))

        self.remote_token_verify_url: Optional[str] = os.getenv('JETTASK_REMOTE_TOKEN_VERIFY_URL')

        self.remote_token_method: str = os.getenv('JETTASK_REMOTE_TOKEN_METHOD', 'POST').upper()

        remote_token_headers_str = os.getenv('JETTASK_REMOTE_TOKEN_HEADERS', '{"Content-Type": "application/json"}')
        try:
            import json
            self.remote_token_headers: dict = json.loads(remote_token_headers_str)
        except json.JSONDecodeError:
            logger.warning(f"远程token验证请求头解析失败，使用默认值: {remote_token_headers_str}")
            self.remote_token_headers = {"Content-Type": "application/json"}

        self.remote_token_timeout: int = int(os.getenv('JETTASK_REMOTE_TOKEN_TIMEOUT', '10'))

        self.remote_token_field: str = os.getenv('JETTASK_REMOTE_TOKEN_FIELD', 'token')

        self.remote_token_location: str = os.getenv('JETTASK_REMOTE_TOKEN_LOCATION', 'body').lower()

        self.remote_token_success_field: str = os.getenv('JETTASK_REMOTE_TOKEN_SUCCESS_FIELD', 'success')
        self.remote_token_username_field: str = os.getenv('JETTASK_REMOTE_TOKEN_USERNAME_FIELD', 'data.username')
        self.remote_token_user_info_field: Optional[str] = os.getenv('JETTASK_REMOTE_TOKEN_USER_INFO_FIELD', 'data')

        remote_token_verify_ssl_str = os.getenv('JETTASK_REMOTE_TOKEN_VERIFY_SSL', 'true')
        self.remote_token_verify_ssl: bool = remote_token_verify_ssl_str.lower() == 'true'

    def _validate_required_configs(self):
        missing_configs = []

        if not self.redis_url:
            missing_configs.append('JETTASK_REDIS_URL')
        if not self.pg_url:
            missing_configs.append('JETTASK_PG_URL')


        if missing_configs:
            error_msg = f"缺少必需的环境变量: {', '.join(missing_configs)}"
            logger.error(error_msg)
            logger.error("=" * 60)
            logger.error("请通过以下方式之一提供配置:")
            logger.error("  1. 在 .env 文件中设置环境变量")
            logger.error("  2. 使用命令行: jettask api --use-nacos")
            logger.error("  3. 手动设置环境变量")
            logger.error("=" * 60)
            logger.error("示例 .env 文件:")
            logger.error("  JETTASK_REDIS_URL=redis://localhost:6379/0")
            logger.error("  JETTASK_PG_URL=postgresql://user:pass@localhost:5432/db")
            logger.error("=" * 60)
            raise ValueError(error_msg)

    def _log_config_summary(self):
        logger.info("=" * 60)
        logger.info("WebUI 配置摘要:")
        logger.info(f"  配置模式: {'Nacos' if self.use_nacos else '环境变量'}")
        logger.info(f"  Redis URL: {self._mask_url(self.redis_url)}")
        logger.info(f"  PostgreSQL URL: {self._mask_url(self.pg_url)}")
        logger.info(f"  Redis Prefix: {self.redis_prefix}")
        logger.info(f"  API Host: {self.api_host}")
        logger.info(f"  API Port: {self.api_port}")
        logger.info(f"  Log Level: {self.log_level}")

        if self.use_nacos:
            logger.info(f"  Nacos Server: {self.nacos_server}")
            logger.info(f"  Nacos Namespace: {self.nacos_namespace}")
            logger.info(f"  Nacos Data ID: {self.nacos_data_id}")
            logger.info(f"  Nacos Group: {self.nacos_group}")

        logger.info("=" * 60)

    @staticmethod
    def _mask_url(url: Optional[str]) -> str:
        if not url:
            return "未配置"

        import re
        masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', url)
        return masked

    def reload(self):
        logger.info("重新加载 WebUI 配置...")
        self._initialized = False
        self.__init__()

    @property
    def meta_database_url(self) -> str:
        if not self.pg_url:
            raise ValueError("PostgreSQL URL未配置")

        if 'postgresql://' in self.pg_url and '+asyncpg' not in self.pg_url:
            return self.pg_url.replace('postgresql://', 'postgresql+asyncpg://')

        return self.pg_url

    @property
    def sync_meta_database_url(self) -> str:
        if not self.pg_url:
            raise ValueError("PostgreSQL URL未配置")

        url = self.pg_url.replace('+asyncpg', '')
        return url

    def get_database_info(self) -> dict:
        import re

        result = {
            'raw_url': self.pg_url,
            'host': None,
            'port': None,
            'database': None,
            'username': None
        }

        if self.pg_url:
            match = re.match(
                r'postgresql(?:\+asyncpg)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)',
                self.pg_url
            )
            if match:
                username, _, host, port, database = match.groups()
                result.update({
                    'username': username,
                    'host': host,
                    'port': port or '5432',
                    'database': database
                })

        return result

    def create_auth_provider(self):
        from jettask.webui.auth import RemoteAuthProvider

        if not self.remote_token_verify_url:
            logger.info("远程token验证未配置，登录功能将不可用")
            return None

        logger.info(f"使用远程token验证提供者: {self.remote_token_verify_url}")
        return RemoteAuthProvider(
            verify_url=self.remote_token_verify_url,
            method=self.remote_token_method,
            headers=self.remote_token_headers,
            timeout=self.remote_token_timeout,
            token_field=self.remote_token_field,
            token_location=self.remote_token_location,
            success_field=self.remote_token_success_field,
            username_field=self.remote_token_username_field,
            user_info_field=self.remote_token_user_info_field,
            verify_ssl=self.remote_token_verify_ssl
        )

    def __repr__(self) -> str:
        return (
            f"<WebUIConfig("
            f"redis_url={self._mask_url(self.redis_url)}, "
            f"pg_url={self._mask_url(self.pg_url)}, "
            f"use_nacos={self.use_nacos}"
            f")>"
        )


webui_config = WebUIConfig()
