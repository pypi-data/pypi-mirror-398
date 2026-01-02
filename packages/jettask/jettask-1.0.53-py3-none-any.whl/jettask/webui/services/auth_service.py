"""
认证服务层 - 处理用户登录和Token刷新的核心业务逻辑
"""
import logging
from typing import Optional, Dict, Any
from jettask.webui.auth import AuthProvider, AuthResult
from jettask.webui.utils.jwt_utils import JWTManager

logger = logging.getLogger(__name__)


class AuthService:
    """
    认证服务类 - 封装认证相关的业务逻辑

    职责:
    1. 处理用户登录（验证企业SSO token并生成JWT）
    2. 处理Token刷新（使用refresh token获取新的access token）
    3. 统一的错误处理和日志记录
    """

    @staticmethod
    async def login(
        auth_provider: Optional[AuthProvider],
        jwt_manager: JWTManager,
        token: str,
        jwt_access_expire_minutes: int
    ) -> Dict[str, Any]:
        if not auth_provider:
            logger.warning("登录请求被拒绝 - 远程token验证未配置")
            raise ValueError(
                "登录功能未启用：未配置远程token验证服务。"
                "请联系管理员配置 JETTASK_REMOTE_TOKEN_VERIFY_URL 环境变量。"
            )

        logger.debug(f"开始验证企业SSO token（认证方式: {auth_provider.get_provider_name()}）")
        auth_result: AuthResult = await auth_provider.verify_token(token)

        if not auth_result.success:
            logger.warning(
                f"登录失败 - {auth_provider.get_provider_name()} token验证失败"
                f" - {auth_result.error_message}"
            )
            raise ValueError(auth_result.error_message or "Token验证失败")

        username = auth_result.username

        if not username:
            logger.error("认证成功但缺少用户名信息")
            raise ValueError("认证服务返回的用户信息不完整")

        logger.debug(f"为用户 {username} 生成JWT tokens")
        access_token = jwt_manager.create_access_token(username)
        refresh_token = jwt_manager.create_refresh_token(username)

        logger.info(
            f"用户登录成功: {username} "
            f"(认证方式: {auth_provider.get_provider_name()})"
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": jwt_access_expire_minutes * 60
        }

    @staticmethod
    def refresh_token(
        jwt_manager: JWTManager,
        refresh_token: str,
        jwt_access_expire_minutes: int
    ) -> Dict[str, Any]:
        logger.debug("开始刷新访问token")
        new_access_token = jwt_manager.refresh_access_token(refresh_token)

        if not new_access_token:
            logger.warning("Token刷新失败 - 无效或过期的刷新token")
            raise ValueError("无效或过期的刷新token，请重新登录")

        payload = jwt_manager.decode_token(refresh_token)
        username = payload.get('sub') if payload else 'unknown'
        logger.info(f"Token刷新成功: {username}")

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": jwt_access_expire_minutes * 60
        }
