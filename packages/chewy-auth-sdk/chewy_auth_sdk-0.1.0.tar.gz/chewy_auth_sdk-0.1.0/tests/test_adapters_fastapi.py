"""
测试 FastAPI Adapters
"""

import pytest
from unittest.mock import Mock
from fastapi import HTTPException

from chewy_auth_sdk.adapters.fastapi import (
    get_current_user,
    require_auth,
    require_role,
    require_any_role,
    require_all_roles,
    verify_token_dependency,
)
from chewy_auth_sdk.token import AuthUser


class TestGetCurrentUser:
    """测试 get_current_user dependency"""

    def test_get_current_user_success(self):
        """测试获取当前用户成功"""
        user = AuthUser(raw_claims={"sub": "user-123"})
        request = Mock()
        request.state.user = user
        
        result = get_current_user(request)
        assert result == user

    def test_get_current_user_none(self):
        """测试无用户"""
        request = Mock()
        request.state = Mock(spec=[])  # 没有 user 属性
        
        result = get_current_user(request)
        assert result is None


class TestRequireAuth:
    """测试 require_auth dependency"""

    def test_require_auth_success(self):
        """测试认证成功"""
        user = AuthUser(raw_claims={"sub": "user-123"})
        request = Mock()
        request.state.user = user
        
        result = require_auth(request)
        assert result == user

    def test_require_auth_no_user(self):
        """测试无用户"""
        request = Mock()
        request.state.user = None
        
        with pytest.raises(HTTPException) as exc_info:
            require_auth(request)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail

    def test_require_auth_invalid_user(self):
        """测试无效用户对象"""
        request = Mock()
        request.state.user = "not_an_authuser"
        
        with pytest.raises(HTTPException) as exc_info:
            require_auth(request)
        
        assert exc_info.value.status_code == 401

    def test_require_auth_empty_user(self):
        """测试空用户"""
        request = Mock()
        request.state.user = AuthUser()
        
        with pytest.raises(HTTPException) as exc_info:
            require_auth(request)
        
        assert exc_info.value.status_code == 401


class TestRequireRole:
    """测试 require_role dependency factory"""

    def test_require_role_success(self):
        """测试拥有角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin"]}}
        )
        request = Mock()
        request.state.user = user
        
        dependency = require_role("admin")
        result = dependency(request)
        assert result == user

    def test_require_role_missing_role(self):
        """测试缺少角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["user"]}}
        )
        request = Mock()
        request.state.user = user
        
        dependency = require_role("admin")
        
        with pytest.raises(HTTPException) as exc_info:
            dependency(request)
        
        assert exc_info.value.status_code == 403
        assert "admin" in exc_info.value.detail

    def test_require_role_not_authenticated(self):
        """测试未认证"""
        request = Mock()
        request.state.user = None
        
        dependency = require_role("admin")
        
        with pytest.raises(HTTPException) as exc_info:
            dependency(request)
        
        assert exc_info.value.status_code == 401


class TestRequireAnyRole:
    """测试 require_any_role dependency factory"""

    def test_require_any_role_success(self):
        """测试拥有任一角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["moderator"]}}
        )
        request = Mock()
        request.state.user = user
        
        dependency = require_any_role("admin", "moderator")
        result = dependency(request)
        assert result == user

    def test_require_any_role_missing_all_roles(self):
        """测试缺少所有角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["user"]}}
        )
        request = Mock()
        request.state.user = user
        
        dependency = require_any_role("admin", "moderator")
        
        with pytest.raises(HTTPException) as exc_info:
            dependency(request)
        
        assert exc_info.value.status_code == 403

    def test_require_any_role_not_authenticated(self):
        """测试未认证"""
        request = Mock()
        request.state.user = None
        
        dependency = require_any_role("admin", "moderator")
        
        with pytest.raises(HTTPException) as exc_info:
            dependency(request)
        
        assert exc_info.value.status_code == 401


class TestRequireAllRoles:
    """测试 require_all_roles dependency factory"""

    def test_require_all_roles_success(self):
        """测试拥有所有角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin", "superuser", "moderator"]}}
        )
        request = Mock()
        request.state.user = user
        
        dependency = require_all_roles("admin", "superuser")
        result = dependency(request)
        assert result == user

    def test_require_all_roles_missing_some_roles(self):
        """测试缺少部分角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin"]}}
        )
        request = Mock()
        request.state.user = user
        
        dependency = require_all_roles("admin", "superuser")
        
        with pytest.raises(HTTPException) as exc_info:
            dependency(request)
        
        assert exc_info.value.status_code == 403

    def test_require_all_roles_not_authenticated(self):
        """测试未认证"""
        request = Mock()
        request.state.user = None
        
        dependency = require_all_roles("admin", "superuser")
        
        with pytest.raises(HTTPException) as exc_info:
            dependency(request)
        
        assert exc_info.value.status_code == 401


class TestVerifyTokenDependency:
    """测试 verify_token_dependency"""

    def test_verify_token_dependency_no_credentials(self):
        """测试无凭证"""
        result = verify_token_dependency(None)
        assert result is None

    def test_verify_token_dependency_with_mock_credentials(self, sdk_configure):
        """测试使用 mock 凭证（实际验证会失败，因为 token 无效）"""
        sdk_configure()
        
        credentials = Mock()
        credentials.credentials = "invalid.token.here"
        
        # 由于 token 无效，应该返回 None
        result = verify_token_dependency(credentials)
        assert result is None
