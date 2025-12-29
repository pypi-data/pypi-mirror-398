"""
请求上下文管理

提供 request-scoped 用户对象访问（可选功能）
"""

from contextvars import ContextVar
from typing import Optional

from .token import AuthUser

# 使用 contextvars 实现 request-scoped 变量
_current_user: ContextVar[Optional[AuthUser]] = ContextVar(
    "current_user", default=None
)


def set_current_user(user: Optional[AuthUser]):
    """
    设置当前请求的用户对象

    Args:
        user: AuthUser 对象或 None
    """
    _current_user.set(user)


def get_current_user() -> Optional[AuthUser]:
    """
    获取当前请求的用户对象

    Returns:
        AuthUser 对象或 None（未认证）
    """
    return _current_user.get()


def clear_current_user():
    """清除当前请求的用户对象"""
    _current_user.set(None)


def require_auth() -> AuthUser:
    """
    获取当前用户对象，如果未认证则抛出异常

    Returns:
        AuthUser: 当前认证用户

    Raises:
        ValueError: 未认证时抛出
    """
    user = get_current_user()
    if user is None or not user:
        raise ValueError("Authentication required")
    return user


def require_role(role: str) -> AuthUser:
    """
    要求当前用户拥有指定角色

    Args:
        role: 角色名称

    Returns:
        AuthUser: 当前认证用户

    Raises:
        ValueError: 未认证或无权限时抛出
    """
    user = require_auth()
    if not user.has_role(role):
        raise ValueError(f"Role '{role}' is required")
    return user


def require_any_role(*roles: str) -> AuthUser:
    """
    要求当前用户拥有任一指定角色

    Args:
        *roles: 角色列表

    Returns:
        AuthUser: 当前认证用户

    Raises:
        ValueError: 未认证或无权限时抛出
    """
    user = require_auth()
    if not user.has_any_role(*roles):
        raise ValueError(f"One of roles {roles} is required")
    return user


def require_all_roles(*roles: str) -> AuthUser:
    """
    要求当前用户拥有所有指定角色

    Args:
        *roles: 角色列表

    Returns:
        AuthUser: 当前认证用户

    Raises:
        ValueError: 未认证或无权限时抛出
    """
    user = require_auth()
    if not user.has_all_roles(*roles):
        raise ValueError(f"All roles {roles} are required")
    return user
