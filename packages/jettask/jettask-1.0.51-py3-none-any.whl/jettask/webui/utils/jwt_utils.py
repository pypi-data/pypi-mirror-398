"""
JWT Token 工具模块

提供JWT token的生成、验证和解析功能
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWTError

logger = logging.getLogger(__name__)


class JWTManager:
    """JWT Token管理器"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

        logger.info(
            f"JWT Manager initialized: "
            f"algorithm={algorithm}, "
            f"access_token_expire={access_token_expire_minutes}m, "
            f"refresh_token_expire={refresh_token_expire_days}d"
        )

    def create_access_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": subject,
            "type": "access",
            "exp": expire,
            "iat": now,
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Created access token for subject: {subject}, expires at: {expire}")
        return token

    def create_refresh_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": subject,
            "type": "refresh",
            "exp": expire,
            "iat": now,
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Created refresh token for subject: {subject}, expires at: {expire}")
        return token

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            if payload.get("type") != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None

            logger.debug(f"Token verified successfully for subject: {payload.get('sub')}")
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except PyJWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_signature": False, "verify_exp": False}
            )
            return payload
        except PyJWTError as e:
            logger.warning(f"Token decode failed: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        payload = self.verify_token(refresh_token, token_type="refresh")
        if not payload:
            logger.warning("Invalid refresh token")
            return None

        subject = payload.get("sub")
        if not subject:
            logger.warning("Refresh token missing subject")
            return None

        additional_claims = {
            k: v for k, v in payload.items()
            if k not in ["sub", "type", "exp", "iat"]
        }

        new_access_token = self.create_access_token(subject, additional_claims)
        logger.info(f"Refreshed access token for subject: {subject}")
        return new_access_token
