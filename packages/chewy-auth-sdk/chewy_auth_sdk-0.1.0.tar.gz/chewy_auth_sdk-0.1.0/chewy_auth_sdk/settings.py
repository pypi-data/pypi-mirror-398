"""
SDK 全局配置管理

使用 dataclass + 单例模式管理全局配置
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChewyAuthSettings:
    """ChewyAuth SDK 全局配置"""

    # Keycloak 配置
    KEYCLOAK_ISSUER: str = ""
    KEYCLOAK_AUDIENCE: Optional[str] = None
    KEYCLOAK_JWKS_URI: Optional[str] = None  # 如果不提供，自动从 issuer 推导

    # 缓存配置
    CACHE_TTL: int = 300  # JWKS 缓存时间（秒）

    # Token 配置
    VERIFY_AUDIENCE: bool = True
    VERIFY_EXPIRATION: bool = True

    # 角色配置
    ROLES_CLAIM_PATH: str = "realm_access.roles"  # 角色在 JWT 中的路径

    # Header 透传配置（可选）
    ENABLE_HEADER_PASSTHROUGH: bool = False
    HEADER_USER_SUB: str = "X-User-Sub"
    HEADER_USER_NAME: str = "X-User-Name"
    HEADER_USER_ROLES: str = "X-User-Roles"

    # 内部状态
    _configured: bool = field(default=False, init=False, repr=False)

    def __post_init__(self):
        """初始化后处理"""
        # 如果没有提供 JWKS URI，从 issuer 推导
        if not self.KEYCLOAK_JWKS_URI and self.KEYCLOAK_ISSUER:
            self.KEYCLOAK_JWKS_URI = (
                f"{self.KEYCLOAK_ISSUER}/protocol/openid-connect/certs"
            )

    def validate(self):
        """验证配置是否完整"""
        from .exceptions import ConfigurationError

        if not self.KEYCLOAK_ISSUER:
            raise ConfigurationError(
                "KEYCLOAK_ISSUER is required. "
                "Please call configure(KEYCLOAK_ISSUER='...')"
            )

        if not self.KEYCLOAK_JWKS_URI:
            raise ConfigurationError(
                "KEYCLOAK_JWKS_URI could not be determined. "
                "Please provide KEYCLOAK_ISSUER or set KEYCLOAK_JWKS_URI explicitly."
            )

        self._configured = True

    @property
    def is_configured(self) -> bool:
        """是否已配置"""
        return self._configured and bool(self.KEYCLOAK_ISSUER)


# 全局单例配置
_settings: Optional[ChewyAuthSettings] = None


def configure(**kwargs) -> ChewyAuthSettings:
    """
    配置 ChewyAuth SDK

    Example:
        from chewy_auth_sdk.settings import configure

        configure(
            KEYCLOAK_ISSUER="https://kc.example.com/realms/demo",
            KEYCLOAK_AUDIENCE="account",
            CACHE_TTL=300,
        )

    Args:
        **kwargs: 配置参数

    Returns:
        ChewyAuthSettings: 配置对象

    Raises:
        ConfigurationError: 配置不完整或错误
    """
    global _settings

    # 创建或更新配置
    if _settings is None:
        _settings = ChewyAuthSettings(**kwargs)
    else:
        # 更新现有配置
        for key, value in kwargs.items():
            if hasattr(_settings, key):
                setattr(_settings, key, value)
            else:
                from .exceptions import ConfigurationError

                raise ConfigurationError(f"Unknown configuration key: {key}")

        # 重新初始化
        _settings.__post_init__()

    # 验证配置
    _settings.validate()

    return _settings


def get_settings() -> ChewyAuthSettings:
    """
    获取全局配置

    Returns:
        ChewyAuthSettings: 配置对象

    Raises:
        ConfigurationError: 未配置时抛出异常
    """
    from .exceptions import ConfigurationError

    if _settings is None or not _settings.is_configured:
        raise ConfigurationError(
            "ChewyAuth SDK is not configured. "
            "Please call configure() before using the SDK."
        )

    return _settings


def reset_settings():
    """重置配置（主要用于测试）"""
    global _settings
    _settings = None
