"""
JWT Token 校验和 AuthUser 对象

提供 Token 解析、校验和用户对象构建功能
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidTokenError as JWTInvalidTokenError,
    InvalidSignatureError as JWTInvalidSignatureError,
    InvalidIssuerError as JWTInvalidIssuerError,
    InvalidAudienceError as JWTInvalidAudienceError,
)

from .settings import get_settings
from .jwks import get_jwks_client
from .exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    InvalidSignatureError,
    InvalidIssuerError,
    InvalidAudienceError,
)


@dataclass
class AuthUser:
    """
    统一的认证用户对象

    完整透传 Keycloak 原始 claims，同时提供便捷访问属性
    """

    raw_claims: Dict[str, Any] = field(default_factory=dict)
    sub: str = ""
    username: str = ""
    email: Optional[str] = None
    roles: List[str] = field(default_factory=list)

    # 额外的便捷属性
    preferred_username: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    name: Optional[str] = None

    def __post_init__(self):
        """从 raw_claims 中提取常用字段"""
        if not self.raw_claims:
            return

        # 基础字段
        self.sub = self.raw_claims.get("sub", "")
        self.username = self.raw_claims.get(
            "preferred_username", self.raw_claims.get("username", "")
        )
        self.email = self.raw_claims.get("email")

        # 额外字段
        self.preferred_username = self.raw_claims.get("preferred_username")
        self.given_name = self.raw_claims.get("given_name")
        self.family_name = self.raw_claims.get("family_name")
        self.name = self.raw_claims.get("name")

        # 提取角色
        self.roles = self._extract_roles()

    def _extract_roles(self) -> List[str]:
        """
        从 raw_claims 中提取角色

        默认路径：realm_access.roles
        可通过配置修改
        """
        try:
            settings = get_settings()
            path = settings.ROLES_CLAIM_PATH
        except Exception:
            # 如果未配置，使用默认路径
            path = "realm_access.roles"

        # 解析路径（支持 dot notation）
        parts = path.split(".")
        current = self.raw_claims

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return []
            else:
                return []

        # 确保返回列表
        if isinstance(current, list):
            return current
        return []

    def has_role(self, role: str) -> bool:
        """检查用户是否拥有指定角色"""
        return role in self.roles

    def has_any_role(self, *roles: str) -> bool:
        """检查用户是否拥有任一指定角色"""
        return any(role in self.roles for role in roles)

    def has_all_roles(self, *roles: str) -> bool:
        """检查用户是否拥有所有指定角色"""
        return all(role in self.roles for role in roles)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "sub": self.sub,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "preferred_username": self.preferred_username,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "name": self.name,
            "raw_claims": self.raw_claims,
        }

    def __repr__(self) -> str:
        return f"AuthUser(sub={self.sub}, username={self.username}, roles={self.roles})"

    def __bool__(self) -> bool:
        """用户对象是否有效（是否已认证）"""
        return bool(self.sub)


def verify_token(token: str) -> AuthUser:
    """
    校验 JWT Token 并返回 AuthUser 对象

    Args:
        token: JWT Token 字符串

    Returns:
        AuthUser: 认证用户对象

    Raises:
        TokenExpiredError: Token 已过期
        InvalidTokenError: Token 无效
        InvalidSignatureError: 签名无效
        InvalidIssuerError: Issuer 不匹配
        InvalidAudienceError: Audience 不匹配
    """
    settings = get_settings()

    try:
        # 获取 JWKS 客户端
        jwks_client = get_jwks_client()

        # 获取签名密钥
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # 构建校验选项
        decode_options = {
            "verify_signature": True,
            "verify_exp": settings.VERIFY_EXPIRATION,
            "verify_aud": settings.VERIFY_AUDIENCE,
        }

        # 构建校验参数
        decode_kwargs = {
            "jwt": token,
            "key": signing_key.key,
            "algorithms": ["RS256"],
            "options": decode_options,
        }

        # 添加 issuer 校验
        if settings.KEYCLOAK_ISSUER:
            decode_kwargs["issuer"] = settings.KEYCLOAK_ISSUER

        # 添加 audience 校验
        if settings.VERIFY_AUDIENCE and settings.KEYCLOAK_AUDIENCE:
            decode_kwargs["audience"] = settings.KEYCLOAK_AUDIENCE

        # 解码并校验 Token
        claims = jwt.decode(**decode_kwargs)

        # 构建 AuthUser 对象
        return AuthUser(raw_claims=claims)

    except ExpiredSignatureError as e:
        raise TokenExpiredError(f"Token has expired: {str(e)}")

    except JWTInvalidSignatureError as e:
        raise InvalidSignatureError(f"Token signature verification failed: {str(e)}")

    except JWTInvalidIssuerError as e:
        raise InvalidIssuerError(f"Token issuer is invalid: {str(e)}")

    except JWTInvalidAudienceError as e:
        raise InvalidAudienceError(f"Token audience is invalid: {str(e)}")

    except JWTInvalidTokenError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")

    except Exception as e:
        raise InvalidTokenError(f"Token validation failed: {str(e)}")


def extract_token_from_header(authorization_header: Optional[str]) -> Optional[str]:
    """
    从 Authorization header 中提取 Token

    Args:
        authorization_header: Authorization header 值

    Returns:
        Token 字符串，如果无法提取则返回 None
    """
    if not authorization_header:
        return None

    # 支持 "Bearer <token>" 格式
    parts = authorization_header.split()
    if len(parts) != 2:
        return None

    scheme, token = parts
    if scheme.lower() != "bearer":
        return None

    return token
