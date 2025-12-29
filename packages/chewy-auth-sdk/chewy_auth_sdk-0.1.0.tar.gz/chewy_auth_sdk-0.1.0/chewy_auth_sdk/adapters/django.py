"""
Django Adapters and Helpers

提供 Django 相关的便捷工具
"""

from functools import wraps
from typing import Callable

from django.http import JsonResponse

from ..token import AuthUser


def require_auth(view_func: Callable) -> Callable:
    """
    Django 视图装饰器：要求用户已认证

    Example:
        from chewy_auth_sdk.adapters.django import require_auth

        @require_auth
        def my_view(request):
            user = request.user
            return JsonResponse({"user": user.username})
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = getattr(request, "user", None)
        if user is None or not isinstance(user, AuthUser) or not user:
            return JsonResponse(
                {"error": "Authentication required"},
                status=401,
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def require_role(role: str) -> Callable:
    """
    Django 视图装饰器：要求用户拥有指定角色

    Example:
        from chewy_auth_sdk.adapters.django import require_role

        @require_role("admin")
        def admin_view(request):
            return JsonResponse({"message": "Welcome admin"})
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, "user", None)
            if user is None or not isinstance(user, AuthUser) or not user:
                return JsonResponse(
                    {"error": "Authentication required"},
                    status=401,
                )

            if not user.has_role(role):
                return JsonResponse(
                    {"error": f"Role '{role}' is required"},
                    status=403,
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_any_role(*roles: str) -> Callable:
    """
    Django 视图装饰器：要求用户拥有任一指定角色

    Example:
        from chewy_auth_sdk.adapters.django import require_any_role

        @require_any_role("admin", "moderator")
        def moderation_view(request):
            return JsonResponse({"message": "Welcome"})
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, "user", None)
            if user is None or not isinstance(user, AuthUser) or not user:
                return JsonResponse(
                    {"error": "Authentication required"},
                    status=401,
                )

            if not user.has_any_role(*roles):
                return JsonResponse(
                    {"error": f"One of roles {roles} is required"},
                    status=403,
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_all_roles(*roles: str) -> Callable:
    """
    Django 视图装饰器：要求用户拥有所有指定角色

    Example:
        from chewy_auth_sdk.adapters.django import require_all_roles

        @require_all_roles("admin", "superuser")
        def super_admin_view(request):
            return JsonResponse({"message": "Welcome super admin"})
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, "user", None)
            if user is None or not isinstance(user, AuthUser) or not user:
                return JsonResponse(
                    {"error": "Authentication required"},
                    status=401,
                )

            if not user.has_all_roles(*roles):
                return JsonResponse(
                    {"error": f"All roles {roles} are required"},
                    status=403,
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
