"""
测试 Django Middleware
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch

from chewy_auth_sdk.middleware.django import (
    ChewyAuthMiddleware,
    ChewyAuthMiddlewareWithHeaderPassthrough,
)
from chewy_auth_sdk.token import AuthUser
from chewy_auth_sdk.exceptions import TokenValidationError, InvalidTokenError


class TestChewyAuthMiddleware:
    """测试 Django 基础 Middleware"""

    def test_middleware_initialization(self, sdk_configure):
        """测试中间件初始化"""
        sdk_configure()
        
        get_response = Mock()
        middleware = ChewyAuthMiddleware(get_response)
        assert middleware.get_response == get_response

    def test_middleware_initialization_not_configured(self):
        """测试未配置时初始化中间件"""
        from chewy_auth_sdk.exceptions import ConfigurationError
        
        get_response = Mock()
        with pytest.raises(ConfigurationError):
            ChewyAuthMiddleware(get_response)

    @patch('chewy_auth_sdk.middleware.django.verify_token')
    def test_middleware_valid_token(self, mock_verify_token, sdk_configure):
        """测试有效 Token"""
        sdk_configure()
        
        # Mock verify_token 返回用户对象
        mock_user = AuthUser(raw_claims={"sub": "user-123", "preferred_username": "testuser"})
        mock_verify_token.return_value = mock_user
        
        # 创建 Mock Request
        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": "Bearer valid.token.here"}
        
        # 创建 Mock Response
        response = Mock()
        get_response = Mock(return_value=response)
        
        # 执行中间件
        middleware = ChewyAuthMiddleware(get_response)
        result = middleware(request)
        
        # 验证
        assert request.user == mock_user
        assert result == response
        mock_verify_token.assert_called_once_with("valid.token.here")

    def test_middleware_no_token(self, sdk_configure):
        """测试无 Token"""
        sdk_configure()
        
        request = Mock()
        request.META = {}
        
        response = Mock()
        get_response = Mock(return_value=response)
        
        middleware = ChewyAuthMiddleware(get_response)
        result = middleware(request)
        
        assert request.user is None
        assert result == response

    @patch('chewy_auth_sdk.middleware.django.verify_token')
    def test_middleware_invalid_token(self, mock_verify_token, sdk_configure):
        """测试无效 Token"""
        sdk_configure()
        
        # Mock verify_token 抛出异常
        mock_verify_token.side_effect = InvalidTokenError("Invalid token")
        
        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": "Bearer invalid.token"}
        
        middleware = ChewyAuthMiddleware(Mock())
        result = middleware(request)
        
        # 应该返回 401 错误
        assert result.status_code == 401
        data = json.loads(result.content)
        assert data["error"] == "Authentication failed"
        assert "Invalid token" in data["detail"]

    @patch('chewy_auth_sdk.middleware.django.verify_token')
    def test_middleware_expired_token(self, mock_verify_token, sdk_configure):
        """测试过期 Token"""
        from chewy_auth_sdk.exceptions import TokenExpiredError
        
        sdk_configure()
        
        mock_verify_token.side_effect = TokenExpiredError("Token expired")
        
        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": "Bearer expired.token"}
        
        middleware = ChewyAuthMiddleware(Mock())
        result = middleware(request)
        
        assert result.status_code == 401
        data = json.loads(result.content)
        assert "expired" in data["detail"].lower()

    @patch('chewy_auth_sdk.middleware.django.verify_token')
    def test_middleware_exception_handling(self, mock_verify_token, sdk_configure):
        """测试异常处理"""
        sdk_configure()
        
        mock_verify_token.side_effect = Exception("Unexpected error")
        
        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": "Bearer token"}
        
        middleware = ChewyAuthMiddleware(Mock())
        result = middleware(request)
        
        assert result.status_code == 500
        data = json.loads(result.content)
        assert "Unexpected error" in data["detail"]


class TestChewyAuthMiddlewareWithHeaderPassthrough:
    """测试 Django Header 透传 Middleware"""

    def test_header_passthrough_enabled(self, sdk_configure):
        """测试启用 Header 透传"""
        sdk_configure(ENABLE_HEADER_PASSTHROUGH=True)
        
        request = Mock()
        request.META = {
            "HTTP_X_USER_SUB": "user-123",
            "HTTP_X_USER_NAME": "testuser",
            "HTTP_X_USER_ROLES": '["admin", "user"]',
        }
        
        response = Mock()
        get_response = Mock(return_value=response)
        
        middleware = ChewyAuthMiddlewareWithHeaderPassthrough(get_response)
        result = middleware(request)
        
        assert request.user is not None
        assert request.user.sub == "user-123"
        assert request.user.username == "testuser"
        assert "admin" in request.user.roles
        assert "user" in request.user.roles

    def test_header_passthrough_custom_headers(self, sdk_configure):
        """测试自定义 Header 名称"""
        sdk_configure(
            ENABLE_HEADER_PASSTHROUGH=True,
            HEADER_USER_SUB="X-Custom-Sub",
            HEADER_USER_NAME="X-Custom-Name",
            HEADER_USER_ROLES="X-Custom-Roles",
        )
        
        request = Mock()
        request.META = {
            "HTTP_X_CUSTOM_SUB": "user-456",
            "HTTP_X_CUSTOM_NAME": "customuser",
            "HTTP_X_CUSTOM_ROLES": "moderator,admin",
        }
        
        response = Mock()
        get_response = Mock(return_value=response)
        
        middleware = ChewyAuthMiddlewareWithHeaderPassthrough(get_response)
        result = middleware(request)
        
        assert request.user.sub == "user-456"
        assert request.user.username == "customuser"
        assert "moderator" in request.user.roles

    def test_header_passthrough_no_headers(self, sdk_configure):
        """测试没有透传 Header 时回退到 JWT"""
        sdk_configure(ENABLE_HEADER_PASSTHROUGH=True)
        
        request = Mock()
        request.META = {}
        
        response = Mock()
        get_response = Mock(return_value=response)
        
        middleware = ChewyAuthMiddlewareWithHeaderPassthrough(get_response)
        
        # 由于没有 header 也没有 JWT，应该设置 user 为 None
        with patch.object(middleware.__class__.__bases__[0], '__call__', return_value=response):
            result = middleware(request)

    def test_header_passthrough_disabled(self, sdk_configure):
        """测试禁用 Header 透传"""
        sdk_configure(ENABLE_HEADER_PASSTHROUGH=False)
        
        request = Mock()
        request.META = {
            "HTTP_X_USER_SUB": "user-123",
            "HTTP_AUTHORIZATION": "Bearer token",
        }
        
        with patch('chewy_auth_sdk.middleware.django.verify_token') as mock_verify:
            mock_user = AuthUser(raw_claims={"sub": "jwt-user"})
            mock_verify.return_value = mock_user
            
            response = Mock()
            get_response = Mock(return_value=response)
            
            middleware = ChewyAuthMiddlewareWithHeaderPassthrough(get_response)
            middleware(request)
            
            # 应该使用 JWT 而不是 Header
            assert request.user.sub == "jwt-user"

    def test_header_passthrough_roles_json_array(self, sdk_configure):
        """测试 JSON 数组格式的角色"""
        sdk_configure(ENABLE_HEADER_PASSTHROUGH=True)
        
        request = Mock()
        request.META = {
            "HTTP_X_USER_SUB": "user-123",
            "HTTP_X_USER_ROLES": '["role1", "role2", "role3"]',
        }
        
        response = Mock()
        get_response = Mock(return_value=response)
        
        middleware = ChewyAuthMiddlewareWithHeaderPassthrough(get_response)
        middleware(request)
        
        assert request.user.roles == ["role1", "role2", "role3"]

    def test_header_passthrough_roles_comma_separated(self, sdk_configure):
        """测试逗号分隔的角色"""
        sdk_configure(ENABLE_HEADER_PASSTHROUGH=True)
        
        request = Mock()
        request.META = {
            "HTTP_X_USER_SUB": "user-123",
            "HTTP_X_USER_ROLES": "role1,role2,role3",
        }
        
        response = Mock()
        get_response = Mock(return_value=response)
        
        middleware = ChewyAuthMiddlewareWithHeaderPassthrough(get_response)
        middleware(request)
        
        assert len(request.user.roles) == 3
        assert "role1" in request.user.roles
