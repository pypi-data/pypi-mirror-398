#!/usr/bin/env python
"""
配置管理模块
使用 Nacos 作为配置中心
支持定时刷新和配置变更监听
"""
import os
import json
import yaml
import threading
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional
from dotenv import load_dotenv
from nacos import NacosClient
import logging




logger = logging.getLogger(__name__)


class NacosConfigLoader:
    """Nacos 配置加载器类，支持定时刷新和配置监听"""
    
    def __init__(self, refresh_interval: int = 30):
        self.nacos_config = None 
        
        self.nacos_group = None
        self.nacos_data_id = None
        self.local_dev_mode = None
        self.service_info = None
        
        self.refresh_interval = refresh_interval
        self.refresh_thread = None
        self.stop_refresh = threading.Event()
        self.last_refresh_time = None
        self.config_version = 0
        
        self.change_listeners: List[Callable[[Dict[str, Any]], None]] = []
        
        self.nacos_client = None
        
        self._config_lock = threading.RLock()
        
        self._initialized = False
        self._config = None
    
    @property
    def config(self) -> dict:
        with self._config_lock:
            if not self._initialized:
                self._lazy_init()
            return self._config
    
    def _lazy_init(self):
        if self._initialized:
            return
        
        logger.info("第一次访问配置，开始初始化...")
        
        self._init_config()
        
        self._config = self._load_config()
        
        if not self.local_dev_mode and self.refresh_interval > 0:
            self.start_refresh_thread()
        
        self._initialized = True
        logger.info("配置初始化完成")
    
    def _init_config(self):
        try:
            logger.info("初始化 Nacos 配置...")
            load_dotenv()

            nacos_server = os.getenv('NACOS_SERVER')
            nacos_namespace = os.getenv('NACOS_NAMESPACE')
            nacos_data_id = os.getenv('NACOS_DATA_ID')

            missing_configs = []
            if not nacos_server:
                missing_configs.append('NACOS_SERVER')
            if not nacos_namespace:
                missing_configs.append('NACOS_NAMESPACE')
            if not nacos_data_id:
                missing_configs.append('NACOS_DATA_ID')

            if missing_configs:
                error_msg = f"缺少必需的Nacos配置环境变量: {', '.join(missing_configs)}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            nacos_username = os.getenv('NACOS_USERNAME')  
            nacos_password = os.getenv('NACOS_PASSWORD')  

            self.nacos_config = {
                'server_addresses': nacos_server,
                'namespace': nacos_namespace,
                'username': nacos_username,
                'password': nacos_password
            }

            self.nacos_group = os.getenv('NACOS_GROUP', 'DEFAULT_GROUP')
            self.nacos_data_id = nacos_data_id
            self.local_dev_mode = os.getenv('LOCAL_DEV_MODE', 'false').lower() == 'true'

            self.service_info = {
                'name': os.getenv('SERVICE_NAME'),
                'domain': os.getenv('SERVICE_DOMAIN'),
                'port': int(os.getenv('SERVICE_PORT')) if os.getenv('SERVICE_PORT') else None
            }

            logger.info(f"Nacos配置验证通过: server={nacos_server}, namespace={nacos_namespace}, group={self.nacos_group}, data_id={nacos_data_id}")

            if not self.nacos_client:
                self.nacos_client = NacosClient(
                    self.nacos_config['server_addresses'],
                    namespace=self.nacos_config['namespace'],
                    username=self.nacos_config['username'],
                    password=self.nacos_config['password']
                )
                logger.info(f"Nacos客户端初始化成功: {self.nacos_config['server_addresses']}")
        except ValueError as e:
            raise
        except Exception as e:
            logger.error(f"初始化配置失败: {e}", exc_info=True)
            raise
    
    def _load_config(self):
        try:
            config = self._load_from_nacos()
            self.last_refresh_time = datetime.now()
            self.config_version += 1
            logger.info(f"配置加载成功，版本: {self.config_version}")
            return config
        except Exception as e:
            logger.error(f"从 Nacos 加载配置失败: {e}")
            if not hasattr(self, '_config'):
                raise
            logger.warning("配置刷新失败，保持现有配置")
            return self._config
    
    def _load_from_nacos(self):
        
        if not self.nacos_client:
            raise ValueError("Nacos客户端未初始化")
        config_str = self.nacos_client.get_config(self.nacos_data_id, self.nacos_group)
        
        if not config_str:
            logger.warning(f"Nacos配置为空: {self.nacos_data_id}/{self.nacos_group}")
            return self._get_default_config()
        
        if self._is_properties_format(config_str):
            config = self._parse_properties(config_str)
        else:
            try:
                config = yaml.safe_load(config_str)
            except:
                try:
                    config = json.loads(config_str)
                except:
                    logger.error(f"无法解析配置格式: {config_str[:100]}...")
                    raise
        logger.debug(f"成功加载配置，包含 {len(config)} 个配置项")
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'PG_DB_HOST': 'localhost',
            'PG_DB_PORT': 5432,
            'PG_DB_USERNAME': 'jettask',
            'PG_DB_PASSWORD': '123456',
            'PG_DB_DATABASE': 'jettask',
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': 6379,
            'REDIS_DB': 0,
            'REDIS_PASSWORD': None
        }
    
    def _is_properties_format(self, config_str):
        lines = config_str.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                return '=' in line
        return False
    
    def _parse_properties(self, config_str):
        config = {}
        lines = config_str.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                parts = key.split('.')
                current = config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                final_value = value
                if value.lower() == 'true':
                    final_value = True
                elif value.lower() == 'false':
                    final_value = False
                elif value.isdigit():
                    final_value = int(value)
                elif self._is_float(value):
                    final_value = float(value)
                
                current[parts[-1]] = final_value
        
        return config
    
    def _is_float(self, value):
        try:
            float(value)
            return '.' in value
        except:
            return False
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def refresh(self) -> bool:
        if not self._initialized:
            logger.debug("配置尚未初始化，跳过刷新")
            return False
        
        try:
            logger.info("手动触发配置刷新")
            old_config = self._config.copy() if self._config else {}
            
            with self._config_lock:
                new_config = self._load_config()
                self._config = new_config
            
            if old_config != new_config:
                logger.info("配置已更新，通知监听器")
                self._notify_listeners(new_config)
                return True
            else:
                logger.debug("配置无变化")
                return False
        except Exception as e:
            logger.error(f"刷新配置失败: {e}")
            return False
    
    def start_refresh_thread(self):
        if self.refresh_thread and self.refresh_thread.is_alive():
            logger.warning("刷新线程已在运行")
            return
        
        self.stop_refresh.clear()
    
    def stop_refresh_thread(self):
        if self.refresh_thread and self.refresh_thread.is_alive():
            logger.info("正在停止配置刷新线程...")
            self.stop_refresh.set()
            self.refresh_thread.join(timeout=5)
            logger.info("配置刷新线程已停止")
    
    def _refresh_loop(self):
        logger.info("配置刷新循环已开始")
        
        while not self.stop_refresh.is_set():
            try:
                if self.stop_refresh.wait(self.refresh_interval):
                    break
                
                self.refresh()
                
            except Exception as e:
                logger.error(f"配置刷新循环异常: {e}")
                if self.stop_refresh.wait(10):
                    break
        
        logger.info("配置刷新循环已结束")
    
    def add_change_listener(self, listener: Callable[[Dict[str, Any]], None]):
        if listener not in self.change_listeners:
            self.change_listeners.append(listener)
            logger.info(f"添加配置变更监听器: {listener.__name__}")
    
    def remove_change_listener(self, listener: Callable[[Dict[str, Any]], None]):
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)
            logger.info(f"移除配置变更监听器: {listener.__name__}")
    
    def _notify_listeners(self, new_config: Dict[str, Any]):
        for listener in self.change_listeners:
            try:
                listener(new_config)
            except Exception as e:
                logger.error(f"配置变更监听器执行失败 {listener.__name__}: {e}")
    















    def get_namespace_configs(self, namespace_id: str, group: str = None) -> Optional[Dict[str, Any]]:
        if not self.nacos_config:
            logger.error("Nacos配置未初始化")
            return None

        try:
            temp_client = NacosClient(
                self.nacos_config['server_addresses'],
                namespace=namespace_id,
                username=self.nacos_config['username'],
                password=self.nacos_config['password']
            )

            target_group = group or self.nacos_group

            config_str = temp_client.get_config(self.nacos_data_id, target_group)

            if not config_str:
                logger.warning(f"命名空间 {namespace_id} 的配置为空")
                return {}

            if self._is_properties_format(config_str):
                config = self._parse_properties(config_str)
            else:
                try:
                    config = yaml.safe_load(config_str)
                except:
                    try:
                        config = json.loads(config_str)
                    except:
                        logger.error(f"无法解析命名空间 {namespace_id} 的配置格式")
                        return None

            logger.info(f"成功获取命名空间 {namespace_id} 的配置，包含 {len(config)} 个配置项")
            return config

        except Exception as e:
            logger.error(f"获取命名空间 {namespace_id} 配置异常: {e}", exc_info=True)
            return None
    
    def __del__(self):
        self.stop_refresh_thread()


config = NacosConfigLoader(refresh_interval=3)