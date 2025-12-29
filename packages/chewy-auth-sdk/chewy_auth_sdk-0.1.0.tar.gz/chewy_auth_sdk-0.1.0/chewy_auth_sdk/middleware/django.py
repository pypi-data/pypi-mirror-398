"""
Django Middleware for ChewyAuth

自动解析 Authorization header，校验 JWT Token，
并将 AuthUser 对象注入到 request.user
"""

import json
from typing import Callable, Optional

from django.http import JsonResponse, HttpRequest

from ..token import verify_token, extract_token_from_header, AuthUser
from ..exceptions import TokenValidationError, ConfigurationError
from ..context import set_current_user, clear_current_user


class ChewyAuthMiddleware:
    """
    Django Middleware for JWT Authentication

    使用方法：
        在 Django settings.py 中添加：
        MIDDLEWARE += ["chewy_auth_sdk.middleware.django.ChewyAuthMiddleware"]

    行为：
        - 自动解析 Authorization header
        - 校验成功：request.user = AuthUser
        - 无 token：request.user = None
        - 校验失败：直接返回 401 JSON
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

        # 验证配置
        try:
            from ..settings import get_settings

            get_settings()
        except ConfigurationError as e:
            raise ConfigurationError(
                f"ChewyAuth SDK is not configured. "
                f"Please call configure() in Django settings. Error: {str(e)}"
            )

    def __call__(self, request: HttpRequest):
        # 清除之前的用户上下文
        clear_current_user()

        # 默认设置为 None（未认证）
        request.user = None

        # 提取 Token
        authorization = request.META.get("HTTP_AUTHORIZATION")
        token = extract_token_from_header(authorization)

        if token:
            try:
                # 校验 Token
                user = verify_token(token)
                request.user = user

                # 设置上下文（可选）
                set_current_user(user)

            except TokenValidationError as e:
                # Token 校验失败，返回 401
                return self._error_response(e.message, e.status_code)

            except Exception as e:
                # 其他异常，返回 500
                return self._error_response(
                    f"Authentication failed: {str(e)}", 500
                )

        # 继续处理请求
        response = self.get_response(request)

        # 清除用户上下文
        clear_current_user()

        return response

    def _error_response(self, message: str, status_code: int) -> JsonResponse:
        """返回错误响应"""
        return JsonResponse(
            {"error": "Authentication failed", "detail": message},
            status=status_code,
        )


class ChewyAuthMiddlewareWithHeaderPassthrough(ChewyAuthMiddleware):
    """
    Django Middleware with Header Passthrough Support

    支持从 Gateway 透传的 header 中直接构造 AuthUser，跳过 JWT 解析

    使用方法：
        在 Django settings.py 中添加：
        MIDDLEWARE += [
            "chewy_auth_sdk.middleware.django.ChewyAuthMiddlewareWithHeaderPassthrough"
        ]

    配置：
        需要在 SDK 配置中启用：
        configure(
            ENABLE_HEADER_PASSTHROUGH=True,
            HEADER_USER_SUB="X-User-Sub",
            HEADER_USER_NAME="X-User-Name",
            HEADER_USER_ROLES="X-User-Roles",
        )
    """

    def __call__(self, request: HttpRequest):
        from ..settings import get_settings

        settings = get_settings()

        # 清除之前的用户上下文
        clear_current_user()

        # 默认设置为 None（未认证）
        request.user = None

        # 如果启用了 header 透传，优先使用
        if settings.ENABLE_HEADER_PASSTHROUGH:
            user = self._extract_user_from_headers(request)
            if user:
                request.user = user
                set_current_user(user)
                response = self.get_response(request)
                clear_current_user()
                return response

        # 否则使用标准的 JWT 校验
        return super().__call__(request)

    def _extract_user_from_headers(self, request: HttpRequest) -> Optional[AuthUser]:
        """从 header 中提取用户信息"""
        from ..settings import get_settings

        settings = get_settings()

        # 提取 headers
        sub = request.META.get(f"HTTP_{settings.HEADER_USER_SUB.upper().replace('-', '_')}")
        username = request.META.get(
            f"HTTP_{settings.HEADER_USER_NAME.upper().replace('-', '_')}"
        )
        roles_str = request.META.get(
            f"HTTP_{settings.HEADER_USER_ROLES.upper().replace('-', '_')}"
        )

        # 如果 sub 不存在，说明没有透传
        if not sub:
            return None

        # 解析角色
        roles = []
        if roles_str:
            try:
                roles = json.loads(roles_str)
                if not isinstance(roles, list):
                    roles = [roles_str]
            except json.JSONDecodeError:
                roles = roles_str.split(",")

        # 构造 AuthUser
        raw_claims = {
            "sub": sub,
            "preferred_username": username or "",
            "realm_access": {
                "roles": roles
            }
        }
        return AuthUser(raw_claims=raw_claims)
