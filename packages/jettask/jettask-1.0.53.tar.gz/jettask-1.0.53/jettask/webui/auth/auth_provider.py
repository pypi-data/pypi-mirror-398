"""
认证提供者抽象接口

定义了认证系统的标准接口，支持多种认证方式的实现：
- 本地认证（基于配置的用户名密码）
- 远程API认证（调用企业现有的认证服务）
- LDAP认证
- OAuth2认证
- 自定义认证
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AuthResult:
    """认证结果"""
    success: bool
    username: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None  
    error_message: Optional[str] = None


class AuthProvider(ABC):
    """
    认证提供者抽象基类

    所有认证实现都需要继承此类并实现 authenticate 方法
    """

    @abstractmethod
    async def verify_token(self, token: str) -> AuthResult:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(provider={self.get_provider_name()})>"
