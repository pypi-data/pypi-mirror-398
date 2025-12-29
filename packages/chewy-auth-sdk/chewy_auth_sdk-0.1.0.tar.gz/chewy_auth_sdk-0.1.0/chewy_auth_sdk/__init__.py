"""
ChewyAuthSDK - 生产可用的 Python 统一认证 SDK

统一 Keycloak JWT 校验逻辑，支持 Django 和 FastAPI
"""

__version__ = "0.1.0"

from .settings import configure, get_settings
from .token import AuthUser, verify_token
from .exceptions import (
    ChewyAuthException,
    ConfigurationError,
    TokenValidationError,
    TokenExpiredError,
    InvalidTokenError,
)

__all__ = [
    "configure",
    "get_settings",
    "AuthUser",
    "verify_token",
    "ChewyAuthException",
    "ConfigurationError",
    "TokenValidationError",
    "TokenExpiredError",
    "InvalidTokenError",
]
