"""
FastAPI Middleware for ChewyAuth

自动解析 Authorization header，校验 JWT Token，
并将 AuthUser 对象注入到 request.state.user
"""

import json
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..token import verify_token, extract_token_from_header, AuthUser
from ..exceptions import TokenValidationError, ConfigurationError
from ..context import set_current_user, clear_current_user


class ChewyAuthMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware for JWT Authentication

    使用方法：
        from fastapi import FastAPI
        from chewy_auth_sdk.middleware.fastapi import ChewyAuthMiddleware

        app = FastAPI()
        app.add_middleware(ChewyAuthMiddleware)

    行为：
        - 自动解析 Authorization header
        - 校验成功：request.state.user = AuthUser
        - 无 token：request.state.user = None
        - 校验失败：返回 401 JSON
    """

    async def dispatch(self, request: Request, call_next):
        # 清除之前的用户上下文
        clear_current_user()

        # 默认设置为 None（未认证）
        request.state.user = None

        # 提取 Token
        authorization = request.headers.get("Authorization")
        token = extract_token_from_header(authorization)

        if token:
            try:
                # 校验 Token
                user = verify_token(token)
                request.state.user = user

                # 设置上下文（可选）
                set_current_user(user)

            except TokenValidationError as e:
                # Token 校验失败，返回 401
                clear_current_user()
                return self._error_response(e.message, e.status_code)

            except Exception as e:
                # 其他异常，返回 500
                clear_current_user()
                return self._error_response(
                    f"Authentication failed: {str(e)}", 500
                )

        # 继续处理请求
        response = await call_next(request)

        # 清除用户上下文
        clear_current_user()

        return response

    def _error_response(self, message: str, status_code: int) -> JSONResponse:
        """返回错误响应"""
        return JSONResponse(
            {"error": "Authentication failed", "detail": message},
            status_code=status_code,
        )


class ChewyAuthMiddlewareWithHeaderPassthrough(ChewyAuthMiddleware):
    """
    FastAPI Middleware with Header Passthrough Support

    支持从 Gateway 透传的 header 中直接构造 AuthUser，跳过 JWT 解析

    使用方法：
        from fastapi import FastAPI
        from chewy_auth_sdk.middleware.fastapi import (
            ChewyAuthMiddlewareWithHeaderPassthrough
        )

        app = FastAPI()
        app.add_middleware(ChewyAuthMiddlewareWithHeaderPassthrough)

    配置：
        需要在 SDK 配置中启用：
        configure(
            ENABLE_HEADER_PASSTHROUGH=True,
            HEADER_USER_SUB="X-User-Sub",
            HEADER_USER_NAME="X-User-Name",
            HEADER_USER_ROLES="X-User-Roles",
        )
    """

    async def dispatch(self, request: Request, call_next):
        from ..settings import get_settings

        settings = get_settings()

        # 清除之前的用户上下文
        clear_current_user()

        # 默认设置为 None（未认证）
        request.state.user = None

        # 如果启用了 header 透传，优先使用
        if settings.ENABLE_HEADER_PASSTHROUGH:
            user = self._extract_user_from_headers(request)
            if user:
                request.state.user = user
                set_current_user(user)
                response = await call_next(request)
                clear_current_user()
                return response

        # 否则使用标准的 JWT 校验
        return await super().dispatch(request, call_next)

    def _extract_user_from_headers(self, request: Request) -> Optional[AuthUser]:
        """从 header 中提取用户信息"""
        from ..settings import get_settings

        settings = get_settings()

        # 提取 headers
        sub = request.headers.get(settings.HEADER_USER_SUB)
        username = request.headers.get(settings.HEADER_USER_NAME)
        roles_str = request.headers.get(settings.HEADER_USER_ROLES)

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
