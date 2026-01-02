"""
认证API - 提供登录和token刷新功能
提供轻量级的路由入口，业务逻辑在 AuthService 中实现
"""
import logging
from fastapi import APIRouter, HTTPException, status
from jettask.webui.config import webui_config
from jettask.webui.utils.jwt_utils import JWTManager
from jettask.webui.services.auth_service import AuthService
from jettask.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    RefreshResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])

jwt_manager = JWTManager(
    secret_key=webui_config.jwt_secret_key,
    algorithm=webui_config.jwt_algorithm,
    access_token_expire_minutes=webui_config.jwt_access_token_expire_minutes,
    refresh_token_expire_days=webui_config.jwt_refresh_token_expire_days
)

auth_provider = webui_config.create_auth_provider()
if auth_provider:
    logger.info(f"认证提供者已初始化: {auth_provider}")
else:
    logger.info("认证提供者未配置，登录和刷新接口将不可用")



@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用户登录",
    description="""使用企业SSO token进行用户登录认证。

**认证流程**:
1. 前端用户在企业SSO系统登录，获得企业的access_token
2. 前端调用此接口，传入企业的access_token
3. 后端调用企业认证API验证token的有效性
4. 验证成功后，生成并返回JetTask的JWT token

**请求体参数**: token - 企业SSO系统颁发的access_token（必需）

**返回信息**: access_token（用于API调用）、refresh_token（用于刷新访问token）、token_type（固定为bearer）、expires_in（访问token过期时间，单位秒）

**使用场景**: Web UI用户登录、移动端用户认证、第三方系统集成

**注意**: 需要配置 JETTASK_REMOTE_TOKEN_VERIFY_URL 环境变量，否则此接口不可用""",
    responses={
        200: {
            "description": "登录成功，返回JWT token",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNzMwMzY3NjAwfQ.abc123",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNzMxMTQ5MjAwfQ.def456",
                        "token_type": "bearer",
                        "expires_in": 1800
                    }
                }
            }
        },
        401: {"description": "认证失败 - token无效或过期"},
        503: {"description": "服务未配置 - 未启用远程token验证服务"},
        500: {"description": "服务器内部错误"}
    }
)
async def login(request: LoginRequest):
    try:
        result = await AuthService.login(
            auth_provider=auth_provider,
            jwt_manager=jwt_manager,
            token=request.token,
            jwt_access_expire_minutes=webui_config.jwt_access_token_expire_minutes
        )

        return TokenResponse(**result)

    except ValueError as e:
        error_msg = str(e)

        if "未启用" in error_msg or "未配置" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg
            )

    except Exception as e:
        logger.error(f"登录过程发生异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录服务暂时不可用，请稍后重试"
        )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="刷新访问token",
    description="""使用refresh token获取新的access token，延长用户登录状态。

**工作原理**:
1. 客户端在access_token即将过期时调用此接口
2. 传入之前登录时获得的refresh_token
3. 后端验证refresh_token的有效性
4. 验证通过后，生成并返回新的access_token

**请求体参数**: refresh_token - 登录时返回的refresh_token（必需）

**返回信息**: access_token（新的访问token）、token_type（固定为bearer）、expires_in（访问token过期时间，单位秒）

**使用场景**: 前端自动续期、保持用户登录状态、避免频繁重新登录

**注意**: refresh_token有效期通常为7天，过期后需要重新登录""",
    responses={
        200: {
            "description": "刷新成功，返回新的access token",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNzMwMzY5NDAwfQ.xyz789",
                        "token_type": "bearer",
                        "expires_in": 1800
                    }
                }
            }
        },
        401: {"description": "认证失败 - refresh_token无效或过期"},
        500: {"description": "服务器内部错误"}
    }
)
async def refresh_token(request: RefreshRequest):
    try:
        result = AuthService.refresh_token(
            jwt_manager=jwt_manager,
            refresh_token=request.refresh_token,
            jwt_access_expire_minutes=webui_config.jwt_access_token_expire_minutes
        )

        return RefreshResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Token刷新过程发生异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token刷新服务暂时不可用，请稍后重试"
        )
