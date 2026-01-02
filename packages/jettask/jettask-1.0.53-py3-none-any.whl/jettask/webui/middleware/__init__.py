"""
WebUI 中间件模块
"""
from .namespace_middleware import NamespaceMiddleware
from .unified_auth_middleware import UnifiedAuthMiddleware

__all__ = ['NamespaceMiddleware',  'UnifiedAuthMiddleware']
