"""
测试 FastAPI Middleware
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch

from starlette.requests import Request
from starlette.datastructures import Headers

from chewy_auth_sdk.middleware.fastapi import (
    ChewyAuthMiddleware,
    ChewyAuthMiddlewareWithHeaderPassthrough,
)
from chewy_auth_sdk.token import AuthUser
from chewy_auth_sdk.exceptions import InvalidTokenError


class TestChewyAuthMiddleware:
    """测试 FastAPI 基础 Middleware"""

    @pytest.mark.asyncio
    @patch('chewy_auth_sdk.middleware.fastapi.verify_token')
    async def test_middleware_valid_token(self, mock_verify_token, sdk_configure):
        """测试有效 Token"""
        sdk_configure()
        
        mock_user = AuthUser(raw_claims={"sub": "user-123", "preferred_username": "testuser"})
        mock_verify_token.return_value = mock_user
        
        # 创建 Mock Request
        scope = {
            "type": "http",
            "headers": [(b"authorization", b"Bearer valid.token.here")],
        }
        request = Request(scope)
        
        # Mock call_next
        response = Mock()
        call_next = AsyncMock(return_value=response)
        
        middleware = ChewyAuthMiddleware(Mock())
        result = await middleware.dispatch(request, call_next)
        
        assert request.state.user == mock_user
        assert result == response
        mock_verify_token.assert_called_once_with("valid.token.here")

    @pytest.mark.asyncio
    async def test_middleware_no_token(self, sdk_configure):
        """测试无 Token"""
        sdk_configure()
        
        scope = {"type": "http", "headers": []}
        request = Request(scope)
        
        response = Mock()
        call_next = AsyncMock(return_value=response)
        
        middleware = ChewyAuthMiddleware(Mock())
        result = await middleware.dispatch(request, call_next)
        
        assert request.state.user is None
        assert result == response

    @pytest.mark.asyncio
    @patch('chewy_auth_sdk.middleware.fastapi.verify_token')
    async def test_middleware_invalid_token(self, mock_verify_token, sdk_configure):
        """测试无效 Token"""
        sdk_configure()
        
        mock_verify_token.side_effect = InvalidTokenError("Invalid token")
        
        scope = {
            "type": "http",
            "headers": [(b"authorization", b"Bearer invalid.token")],
        }
        request = Request(scope)
        
        middleware = ChewyAuthMiddleware(Mock())
        result = await middleware.dispatch(request, AsyncMock())
        
        assert result.status_code == 401
        body = json.loads(result.body)
        assert body["error"] == "Authentication failed"
        assert "Invalid token" in body["detail"]

    @pytest.mark.asyncio
    @patch('chewy_auth_sdk.middleware.fastapi.verify_token')
    async def test_middleware_expired_token(self, mock_verify_token, sdk_configure):
        """测试过期 Token"""
        from chewy_auth_sdk.exceptions import TokenExpiredError
        
        sdk_configure()
        
        mock_verify_token.side_effect = TokenExpiredError("Token expired")
        
        scope = {
            "type": "http",
            "headers": [(b"authorization", b"Bearer expired.token")],
        }
        request = Request(scope)
        
        middleware = ChewyAuthMiddleware(Mock())
        result = await middleware.dispatch(request, AsyncMock())
        
        assert result.status_code == 401
        body = json.loads(result.body)
        assert "expired" in body["detail"].lower()

    @pytest.mark.asyncio
    @patch('chewy_auth_sdk.middleware.fastapi.verify_token')
    async def test_middleware_exception_handling(self, mock_verify_token, sdk_configure):
        """测试异常处理"""
        sdk_configure()
        
        mock_verify_token.side_effect = Exception("Unexpected error")
        
        scope = {
            "type": "http",
            "headers": [(b"authorization", b"Bearer token")],
        }
        request = Request(scope)
        
        middleware = ChewyAuthMiddleware(Mock())
        result = await middleware.dispatch(request, AsyncMock())
        
        assert result.status_code == 500
        body = json.loads(result.body)
        assert "Unexpected error" in body["detail"]


class TestChewyAuthMiddlewareWithHeaderPassthrough:
    """测试 FastAPI Header 透传 Middleware"""

    @pytest.mark.asyncio
    async def test_header_passthrough_enabled(self, sdk_configure):
        """测试启用 Header 透传"""
        sdk_configure(ENABLE_HEADER_PASSTHROUGH=True)
        
        scope = {
            "type": "http",
            "headers": [
                (b"x-user-sub", b"user-123"),
                (b"x-user-name", b"testuser"),
                (b"x-user-roles", b'["admin", "user"]'),
            ],
        }
        request = Request(scope)
        
        response = Mock()
        call_next = AsyncMock(return_value=response)
        
        middleware = ChewyAuthMiddlewareWithHeaderPassthrough(Mock())
        result = await middleware.dispatch(request, call_next)
        
        assert request.state.user is not None
        assert request.state.user.sub == "user-123"
        assert request.state.user.username == "testuser"
        assert "admin" in request.state.user.roles
        assert "user" in request.state.user.roles

    @pytest.mark.asyncio
    async def test_header_passthrough_custom_headers(self, sdk_configure):
        """测试自定义 Header 名称"""
        sdk_configure(
            ENABLE_HEADER_PASSTHROUGH=True,
            HEADER_USER_SUB="X-Custom-Sub",
            HEADER_USER_NAME="X-Custom-Name",
            HEADER_USER_ROLES="X-Custom-Roles",
        )
        
        scope = {
            "type": "http",
            "headers": [
                (b"x-custom-sub", b"user-456"),
                (b"x-custom-name", b"customuser"),
                (b"x-custom-roles", b"moderator,admin"),
            ],
        }
        request = Request(scope)
        
        response = Mock()
        call_next = AsyncMock(return_value=response)
        
        middleware = ChewyAuthMiddlewareWithHeaderPassthrough(Mock())
        result = await middleware.dispatch(request, call_next)
        
        assert request.state.user.sub == "user-456"
        assert request.state.user.username == "customuser"
        assert "moderator" in request.state.user.roles

    @pytest.mark.asyncio
    async def test_header_passthrough_no_headers(self, sdk_configure):
        """测试没有透传 Header"""
        sdk_configure(ENABLE_HEADER_PASSTHROUGH=True)
        
        scope = {"type": "http", "headers": []}
        request = Request(scope)
        
        response = Mock()
        call_next = AsyncMock(return_value=response)
        
        middleware = ChewyAuthMiddlewareWithHeaderPassthrough(Mock())
        result = await middleware.dispatch(request, call_next)
        
        # 没有 header 也没有 JWT，user 应该是 None
        assert request.state.user is None

    @pytest.mark.asyncio
    @patch('chewy_auth_sdk.middleware.fastapi.verify_token')
    async def test_header_passthrough_disabled(self, mock_verify_token, sdk_configure):
        """测试禁用 Header 透传"""
        sdk_configure(ENABLE_HEADER_PASSTHROUGH=False)
        
        mock_user = AuthUser(raw_claims={"sub": "jwt-user"})
        mock_verify_token.return_value = mock_user
        
        scope = {
            "type": "http",
            "headers": [
                (b"x-user-sub", b"header-user"),
                (b"authorization", b"Bearer token"),
            ],
        }
        request = Request(scope)
        
        response = Mock()
        call_next = AsyncMock(return_value=response)
        
        middleware = ChewyAuthMiddlewareWithHeaderPassthrough(Mock())
        await middleware.dispatch(request, call_next)
        
        # 应该使用 JWT 而不是 Header
        assert request.state.user.sub == "jwt-user"

    @pytest.mark.asyncio
    async def test_header_passthrough_roles_json_array(self, sdk_configure):
        """测试 JSON 数组格式的角色"""
        sdk_configure(ENABLE_HEADER_PASSTHROUGH=True)
        
        scope = {
            "type": "http",
            "headers": [
                (b"x-user-sub", b"user-123"),
                (b"x-user-roles", b'["role1", "role2", "role3"]'),
            ],
        }
        request = Request(scope)
        
        response = Mock()
        call_next = AsyncMock(return_value=response)
        
        middleware = ChewyAuthMiddlewareWithHeaderPassthrough(Mock())
        await middleware.dispatch(request, call_next)
        
        assert request.state.user.roles == ["role1", "role2", "role3"]

    @pytest.mark.asyncio
    async def test_header_passthrough_roles_comma_separated(self, sdk_configure):
        """测试逗号分隔的角色"""
        sdk_configure(ENABLE_HEADER_PASSTHROUGH=True)
        
        scope = {
            "type": "http",
            "headers": [
                (b"x-user-sub", b"user-123"),
                (b"x-user-roles", b"role1,role2,role3"),
            ],
        }
        request = Request(scope)
        
        response = Mock()
        call_next = AsyncMock(return_value=response)
        
        middleware = ChewyAuthMiddlewareWithHeaderPassthrough(Mock())
        await middleware.dispatch(request, call_next)
        
        assert len(request.state.user.roles) == 3
        assert "role1" in request.state.user.roles
