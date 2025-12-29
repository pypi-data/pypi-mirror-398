"""
测试 Django Adapters
"""

import pytest
from unittest.mock import Mock

from chewy_auth_sdk.adapters.django import (
    require_auth,
    require_role,
    require_any_role,
    require_all_roles,
)
from chewy_auth_sdk.token import AuthUser


class TestRequireAuth:
    """测试 require_auth 装饰器"""

    def test_require_auth_success(self):
        """测试认证成功"""
        user = AuthUser(raw_claims={"sub": "user-123"})
        request = Mock()
        request.user = user
        
        @require_auth
        def my_view(request):
            return {"status": "ok"}
        
        result = my_view(request)
        assert result == {"status": "ok"}

    def test_require_auth_no_user(self):
        """测试无用户"""
        request = Mock()
        request.user = None
        
        @require_auth
        def my_view(request):
            return {"status": "ok"}
        
        result = my_view(request)
        assert result.status_code == 401

    def test_require_auth_invalid_user(self):
        """测试无效用户对象"""
        request = Mock()
        request.user = "not_an_authuser"
        
        @require_auth
        def my_view(request):
            return {"status": "ok"}
        
        result = my_view(request)
        assert result.status_code == 401

    def test_require_auth_empty_user(self):
        """测试空用户（sub 为空）"""
        request = Mock()
        request.user = AuthUser()
        
        @require_auth
        def my_view(request):
            return {"status": "ok"}
        
        result = my_view(request)
        assert result.status_code == 401


class TestRequireRole:
    """测试 require_role 装饰器"""

    def test_require_role_success(self):
        """测试拥有角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin"]}}
        )
        request = Mock()
        request.user = user
        
        @require_role("admin")
        def admin_view(request):
            return {"status": "ok"}
        
        result = admin_view(request)
        assert result == {"status": "ok"}

    def test_require_role_missing_role(self):
        """测试缺少角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["user"]}}
        )
        request = Mock()
        request.user = user
        
        @require_role("admin")
        def admin_view(request):
            return {"status": "ok"}
        
        result = admin_view(request)
        assert result.status_code == 403

    def test_require_role_not_authenticated(self):
        """测试未认证"""
        request = Mock()
        request.user = None
        
        @require_role("admin")
        def admin_view(request):
            return {"status": "ok"}
        
        result = admin_view(request)
        assert result.status_code == 401


class TestRequireAnyRole:
    """测试 require_any_role 装饰器"""

    def test_require_any_role_success(self):
        """测试拥有任一角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["moderator"]}}
        )
        request = Mock()
        request.user = user
        
        @require_any_role("admin", "moderator")
        def moderation_view(request):
            return {"status": "ok"}
        
        result = moderation_view(request)
        assert result == {"status": "ok"}

    def test_require_any_role_missing_all_roles(self):
        """测试缺少所有角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["user"]}}
        )
        request = Mock()
        request.user = user
        
        @require_any_role("admin", "moderator")
        def moderation_view(request):
            return {"status": "ok"}
        
        result = moderation_view(request)
        assert result.status_code == 403

    def test_require_any_role_not_authenticated(self):
        """测试未认证"""
        request = Mock()
        request.user = None
        
        @require_any_role("admin", "moderator")
        def moderation_view(request):
            return {"status": "ok"}
        
        result = moderation_view(request)
        assert result.status_code == 401


class TestRequireAllRoles:
    """测试 require_all_roles 装饰器"""

    def test_require_all_roles_success(self):
        """测试拥有所有角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin", "superuser", "moderator"]}}
        )
        request = Mock()
        request.user = user
        
        @require_all_roles("admin", "superuser")
        def super_admin_view(request):
            return {"status": "ok"}
        
        result = super_admin_view(request)
        assert result == {"status": "ok"}

    def test_require_all_roles_missing_some_roles(self):
        """测试缺少部分角色"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin"]}}
        )
        request = Mock()
        request.user = user
        
        @require_all_roles("admin", "superuser")
        def super_admin_view(request):
            return {"status": "ok"}
        
        result = super_admin_view(request)
        assert result.status_code == 403

    def test_require_all_roles_not_authenticated(self):
        """测试未认证"""
        request = Mock()
        request.user = None
        
        @require_all_roles("admin", "superuser")
        def super_admin_view(request):
            return {"status": "ok"}
        
        result = super_admin_view(request)
        assert result.status_code == 401
