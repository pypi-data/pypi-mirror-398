"""
认证模块

提供远程API认证方式的支持：
- 远程API认证（RemoteAuthProvider）
"""
from .auth_provider import AuthProvider, AuthResult
from .remote_auth_provider import RemoteAuthProvider

__all__ = [
    'AuthProvider',
    'AuthResult',
    'RemoteAuthProvider',
]
