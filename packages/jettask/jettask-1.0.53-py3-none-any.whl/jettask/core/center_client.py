"""
TaskCenter API 客户端

这个类是一个纯粹的 API 客户端，用于与 TaskCenter API 进行通信。
所有方法都是异步的，支持实时查询。
"""
import logging
from typing import Optional, Dict, Any, List
import aiohttp

logger = logging.getLogger(__name__)


class TaskCenterClient:
    """
    TaskCenter API 客户端

    这是一个轻量级的 HTTP 客户端，专门用于与 TaskCenter API 进行通信。

    特点：
    - 纯异步接口，所有方法都返回协程
    - 无状态设计，每次调用都是实时查询
    - 自动管理 HTTP 会话
    - 完整的错误处理和日志记录

    使用示例：
        ```python
        # 初始化客户端
        client = TaskCenterClient(task_center_url="http://localhost:8001")

        # 获取命名空间列表
        namespaces = await client.get_namespace_list()

        # 获取特定命名空间
        namespace = await client.get_namespace("default")

        # 获取统计信息
        stats = await client.get_namespace_statistics("default")

        # 使用完毕后关闭
        await client.close()
        ```

    或使用上下文管理器：
        ```python
        async with TaskCenterClient("http://localhost:8001") as client:
            namespaces = await client.get_namespace_list()
        ```
    """

    def __init__(self, task_center_url: str, api_key: Optional[str] = None):
        self.task_center_url = task_center_url.rstrip('/')
        self._base_api_url = f"{self.task_center_url}/api/task/v1"
        self._session: Optional[aiohttp.ClientSession] = None
        self._api_key = api_key

        logger.info(f"TaskCenter 客户端初始化: {self.task_center_url}")
        if api_key:
            logger.info("API 密钥已配置，将使用鉴权模式")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            logger.debug("创建新的 HTTP 会话")
        return self._session

    def _get_headers(self) -> Dict[str, str]:
        headers = {}
        if self._api_key:
            headers['X-API-Key'] = self._api_key
        return headers

    async def get_namespace_list(
        self,
        page: int = 1,
        page_size: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        url = f"{self._base_api_url}/namespaces/"
        params = {
            'page': page,
            'page_size': page_size
        }
        if is_active is not None:
            params['is_active'] = is_active

        logger.debug(f"获取命名空间列表: page={page}, page_size={page_size}, is_active={is_active}")

        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.debug(f"成功获取 {len(data)} 个命名空间")
                    return data
                else:
                    error_text = await resp.text()
                    logger.error(f"获取命名空间列表失败: HTTP {resp.status}, {error_text}")
                    raise ValueError(f"获取命名空间列表失败: HTTP {resp.status}")
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"获取命名空间列表失败: {e}")
            raise

    async def get_namespace(self, namespace_name: str) -> Dict[str, Any]:
        url = f"{self._base_api_url}/{namespace_name}/"

        logger.debug(f"获取命名空间详情: {namespace_name}")

        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"成功获取命名空间 '{namespace_name}' 的详细信息")
                    return data
                elif resp.status == 404:
                    logger.error(f"命名空间 '{namespace_name}' 不存在")
                    raise ValueError(f"命名空间 '{namespace_name}' 不存在")
                else:
                    error_text = await resp.text()
                    logger.error(f"获取命名空间失败: HTTP {resp.status}, {error_text}")
                    raise ValueError(f"获取命名空间失败: HTTP {resp.status}")
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {e}")
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"获取命名空间失败: {e}")
            raise

    async def get_namespace_statistics(self, namespace_name: str) -> Dict[str, Any]:
        url = f"{self._base_api_url}/{namespace_name}/statistics"

        logger.debug(f"获取命名空间统计信息: {namespace_name}")

        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"成功获取命名空间 '{namespace_name}' 的统计信息")
                    return data
                elif resp.status == 404:
                    logger.error(f"命名空间 '{namespace_name}' 不存在")
                    raise ValueError(f"命名空间 '{namespace_name}' 不存在")
                else:
                    error_text = await resp.text()
                    logger.error(f"获取统计信息失败: HTTP {resp.status}, {error_text}")
                    raise ValueError(f"获取统计信息失败: HTTP {resp.status}")
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {e}")
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise

    async def create_namespace(self, namespace_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self._base_api_url}/namespaces/"

        logger.debug(f"创建命名空间: {namespace_data.get('name')}")

        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.post(url, json=namespace_data, headers=headers) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    logger.info(f"成功创建命名空间 '{namespace_data.get('name')}'")
                    return data
                elif resp.status == 400:
                    error_text = await resp.text()
                    logger.error(f"创建命名空间失败: {error_text}")
                    raise ValueError(f"创建命名空间失败: {error_text}")
                else:
                    error_text = await resp.text()
                    logger.error(f"创建命名空间失败: HTTP {resp.status}, {error_text}")
                    raise ValueError(f"创建命名空间失败: HTTP {resp.status}")
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {e}")
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"创建命名空间失败: {e}")
            raise

    async def update_namespace(
        self,
        namespace_name: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = f"{self._base_api_url}/{namespace_name}/"

        logger.debug(f"更新命名空间: {namespace_name}")

        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.put(url, json=update_data, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"成功更新命名空间 '{namespace_name}'")
                    return data
                elif resp.status == 404:
                    logger.error(f"命名空间 '{namespace_name}' 不存在")
                    raise ValueError(f"命名空间 '{namespace_name}' 不存在")
                elif resp.status == 400:
                    error_text = await resp.text()
                    logger.error(f"更新命名空间失败: {error_text}")
                    raise ValueError(f"更新命名空间失败: {error_text}")
                else:
                    error_text = await resp.text()
                    logger.error(f"更新命名空间失败: HTTP {resp.status}, {error_text}")
                    raise ValueError(f"更新命名空间失败: HTTP {resp.status}")
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {e}")
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"更新命名空间失败: {e}")
            raise

    async def delete_namespace(self, namespace_name: str) -> Dict[str, Any]:
        url = f"{self._base_api_url}/{namespace_name}/"

        logger.debug(f"删除命名空间: {namespace_name}")

        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.delete(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"成功删除命名空间 '{namespace_name}'")
                    return data
                elif resp.status == 404:
                    logger.error(f"命名空间 '{namespace_name}' 不存在")
                    raise ValueError(f"命名空间 '{namespace_name}' 不存在")
                elif resp.status == 400:
                    error_text = await resp.text()
                    logger.error(f"删除命名空间失败: {error_text}")
                    raise ValueError(f"删除命名空间失败: {error_text}")
                else:
                    error_text = await resp.text()
                    logger.error(f"删除命名空间失败: HTTP {resp.status}, {error_text}")
                    raise ValueError(f"删除命名空间失败: HTTP {resp.status}")
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {e}")
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"删除命名空间失败: {e}")
            raise

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("HTTP 会话已关闭")

    async def __aenter__(self):
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        await self.close()

    def __repr__(self) -> str:
        return f"<TaskCenterClient url='{self.task_center_url}'>"




__all__ = ['TaskCenterClient']
