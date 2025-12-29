"""
测试请求上下文管理
"""

import pytest
from chewy_auth_sdk.context import (
    set_current_user,
    get_current_user,
    clear_current_user,
    require_auth,
    require_role,
    require_any_role,
    require_all_roles,
)
from chewy_auth_sdk.token import AuthUser


class TestContextManagement:
    """测试上下文管理"""

    def test_set_and_get_current_user(self):
        """测试设置和获取当前用户"""
        user = AuthUser(raw_claims={"sub": "user-123", "preferred_username": "testuser"})
        set_current_user(user)
        
        current_user = get_current_user()
        assert current_user is not None
        assert current_user.sub == "user-123"
        assert current_user.username == "testuser"

    def test_get_current_user_default_none(self):
        """测试默认返回 None"""
        clear_current_user()  # 确保清空
        current_user = get_current_user()
        assert current_user is None

    def test_clear_current_user(self):
        """测试清除当前用户"""
        user = AuthUser(raw_claims={"sub": "user-123"})
        set_current_user(user)
        assert get_current_user() is not None
        
        clear_current_user()
        assert get_current_user() is None

    def test_set_current_user_none(self):
        """测试设置 None"""
        user = AuthUser(raw_claims={"sub": "user-123"})
        set_current_user(user)
        assert get_current_user() is not None
        
        set_current_user(None)
        assert get_current_user() is None


class TestRequireAuth:
    """测试 require_auth"""

    def test_require_auth_success(self, sdk_configure):
        """测试认证成功"""
        sdk_configure()
        user = AuthUser(raw_claims={"sub": "user-123"})
        set_current_user(user)
        
        authenticated_user = require_auth()
        assert authenticated_user.sub == "user-123"

    def test_require_auth_not_authenticated(self, sdk_configure):
        """测试未认证"""
        sdk_configure()
        clear_current_user()
        
        with pytest.raises(ValueError, match="Authentication required"):
            require_auth()

    def test_require_auth_none_user(self, sdk_configure):
        """测试用户为 None"""
        sdk_configure()
        set_current_user(None)
        
        with pytest.raises(ValueError, match="Authentication required"):
            require_auth()

    def test_require_auth_empty_user(self, sdk_configure):
        """测试空用户对象"""
        sdk_configure()
        empty_user = AuthUser()  # sub 为空
        set_current_user(empty_user)
        
        with pytest.raises(ValueError, match="Authentication required"):
            require_auth()


class TestRequireRole:
    """测试 require_role"""

    def test_require_role_success(self, sdk_configure):
        """测试拥有指定角色"""
        sdk_configure()
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin", "user"]}}
        )
        set_current_user(user)
        
        authenticated_user = require_role("admin")
        assert authenticated_user.sub == "user-123"

    def test_require_role_missing_role(self, sdk_configure):
        """测试缺少角色"""
        sdk_configure()
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["user"]}}
        )
        set_current_user(user)
        
        with pytest.raises(ValueError, match="Role 'admin' is required"):
            require_role("admin")

    def test_require_role_not_authenticated(self, sdk_configure):
        """测试未认证"""
        sdk_configure()
        clear_current_user()
        
        with pytest.raises(ValueError, match="Authentication required"):
            require_role("admin")


class TestRequireAnyRole:
    """测试 require_any_role"""

    def test_require_any_role_success(self, sdk_configure):
        """测试拥有任一角色"""
        sdk_configure()
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["user", "moderator"]}}
        )
        set_current_user(user)
        
        authenticated_user = require_any_role("admin", "moderator")
        assert authenticated_user.sub == "user-123"

    def test_require_any_role_missing_all_roles(self, sdk_configure):
        """测试缺少所有角色"""
        sdk_configure()
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["user"]}}
        )
        set_current_user(user)
        
        with pytest.raises(ValueError, match="One of roles .* is required"):
            require_any_role("admin", "moderator")

    def test_require_any_role_not_authenticated(self, sdk_configure):
        """测试未认证"""
        sdk_configure()
        clear_current_user()
        
        with pytest.raises(ValueError, match="Authentication required"):
            require_any_role("admin", "moderator")


class TestRequireAllRoles:
    """测试 require_all_roles"""

    def test_require_all_roles_success(self, sdk_configure):
        """测试拥有所有角色"""
        sdk_configure()
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin", "user", "moderator"]}}
        )
        set_current_user(user)
        
        authenticated_user = require_all_roles("admin", "user")
        assert authenticated_user.sub == "user-123"

    def test_require_all_roles_missing_some_roles(self, sdk_configure):
        """测试缺少部分角色"""
        sdk_configure()
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin"]}}
        )
        set_current_user(user)
        
        with pytest.raises(ValueError, match="All roles .* are required"):
            require_all_roles("admin", "user")

    def test_require_all_roles_not_authenticated(self, sdk_configure):
        """测试未认证"""
        sdk_configure()
        clear_current_user()
        
        with pytest.raises(ValueError, match="Authentication required"):
            require_all_roles("admin", "user")
