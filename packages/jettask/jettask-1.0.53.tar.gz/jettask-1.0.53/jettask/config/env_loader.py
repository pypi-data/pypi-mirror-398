#!/usr/bin/env python3
"""
环境变量加载器

提供统一的环境变量加载和管理功能
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class EnvLoader:
    """环境变量加载器

    功能：
    1. 从.env文件加载环境变量
    2. 支持多个.env文件按优先级加载
    3. 提供类型安全的环境变量获取方法
    4. 支持默认值

    使用示例：
        # 基本使用
        loader = EnvLoader()
        loader.load_env_file('.env')
        redis_url = loader.get('JETTASK_REDIS_URL')

        # 加载多个文件（后加载的覆盖先加载的）
        loader = EnvLoader()
        loader.load_env_file('.env')
        loader.load_env_file('.env.local', override=True)

        # 类型转换
        max_conn = loader.get_int('JETTASK_MAX_CONNECTIONS', default=200)
        debug = loader.get_bool('DEBUG', default=False)

        # 批量获取配置
        config = loader.get_config_dict('JETTASK_')
    """

    def __init__(self, auto_load: bool = False):
        self._loaded_files = []

        if auto_load:
            self.auto_load()

    def auto_load(self, search_paths: list = None) -> bool:
        if search_paths is None:
            search_paths = [Path.cwd()]

        env = os.environ.get('ENVIRONMENT', os.environ.get('ENV', 'development'))

        env_files = [
            '.env',
            f'.env.{env}',
            '.env.local',
        ]

        loaded_any = False
        for search_path in search_paths:
            search_path = Path(search_path)
            for env_file in env_files:
                file_path = search_path / env_file
                if file_path.exists():
                    self.load_env_file(str(file_path), override=True)
                    loaded_any = True

        return loaded_any

    def load_env_file(self, file_path: str, override: bool = True) -> bool:
        path = Path(file_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Environment file not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        logger.info(f"Loading environment variables from: {path}")

        success = load_dotenv(str(path), override=override)

        if success:
            self._loaded_files.append(str(path))
            logger.info(f"✓ Loaded environment variables from: {path}")
        else:
            logger.warning(f"Failed to load environment variables from: {path}")

        return success

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return os.environ.get(key, default)

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        value = os.environ.get(key)
        if value is None:
            return default

        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Environment variable {key}='{value}' cannot be converted to int")

    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        value = os.environ.get(key)
        if value is None:
            return default

        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Environment variable {key}='{value}' cannot be converted to float")

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        value = os.environ.get(key)
        if value is None:
            return default

        value_lower = value.lower().strip()

        if value_lower in ('true', '1', 'yes', 'on', 'enabled'):
            return True
        elif value_lower in ('false', '0', 'no', 'off', 'disabled'):
            return False
        else:
            raise ValueError(
                f"Environment variable {key}='{value}' cannot be converted to bool. "
                f"Valid values: true/false, 1/0, yes/no, on/off, enabled/disabled"
            )

    def get_list(self, key: str, separator: str = ',', default: Optional[list] = None) -> Optional[list]:
        value = os.environ.get(key)
        if value is None:
            return default or []

        return [item.strip() for item in value.split(separator) if item.strip()]

    def get_dict(self, key: str, default: Optional[dict] = None) -> Optional[dict]:
        value = os.environ.get(key)
        if value is None:
            return default or {}

        try:
            import json
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Environment variable {key}='{value}' is not valid JSON: {e}")

    def get_config_dict(self, prefix: str = '') -> Dict[str, str]:
        config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):]
                config[config_key] = value

        return config

    def require(self, key: str) -> str:
        value = os.environ.get(key)
        if value is None:
            raise ValueError(
                f"Required environment variable '{key}' is not set. "
                f"Please set it in your environment or .env file."
            )
        return value

    def set(self, key: str, value: Any, override: bool = True) -> None:
        if override or key not in os.environ:
            os.environ[key] = str(value)

    def clear_all(self, prefix: str = '') -> int:
        keys_to_remove = [key for key in os.environ.keys() if key.startswith(prefix)]
        for key in keys_to_remove:
            del os.environ[key]

        return len(keys_to_remove)

    def get_loaded_files(self) -> list:
        return self._loaded_files.copy()

    def __repr__(self) -> str:
        return f"EnvLoader(loaded_files={len(self._loaded_files)})"


_global_loader = None


def get_env_loader() -> EnvLoader:
    global _global_loader
    if _global_loader is None:
        _global_loader = EnvLoader()
    return _global_loader


def load_env(file_path: str = None, override: bool = True) -> EnvLoader:
    loader = get_env_loader()

    if file_path:
        loader.load_env_file(file_path, override=override)
    else:
        loader.auto_load()

    return loader
