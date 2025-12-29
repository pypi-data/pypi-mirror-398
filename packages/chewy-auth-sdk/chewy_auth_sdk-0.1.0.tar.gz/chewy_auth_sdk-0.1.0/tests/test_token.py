"""
测试 Token 校验和 AuthUser 对象
"""

import pytest
import time
from typing import Dict, Any

from chewy_auth_sdk.token import AuthUser, verify_token, extract_token_from_header
from chewy_auth_sdk.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    InvalidSignatureError,
    InvalidIssuerError,
    InvalidAudienceError,
)


class TestAuthUser:
    """测试 AuthUser 对象"""

    def test_auth_user_from_claims(self):
        """测试从 claims 创建 AuthUser"""
        claims = {
            "sub": "user-123",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "given_name": "Test",
            "family_name": "User",
            "name": "Test User",
            "realm_access": {
                "roles": ["user", "admin"]
            }
        }
        user = AuthUser(raw_claims=claims)
        
        assert user.sub == "user-123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.given_name == "Test"
        assert user.family_name == "User"
        assert user.name == "Test User"
        assert user.roles == ["user", "admin"]

    def test_auth_user_with_username_fallback(self):
        """测试 username 的 fallback 逻辑"""
        claims = {
            "sub": "user-123",
            "username": "fallback_user"
        }
        user = AuthUser(raw_claims=claims)
        assert user.username == "fallback_user"

    def test_auth_user_empty_roles(self):
        """测试空角色列表"""
        claims = {
            "sub": "user-123",
            "preferred_username": "testuser"
        }
        user = AuthUser(raw_claims=claims)
        assert user.roles == []

    def test_auth_user_custom_roles_path(self, sdk_configure):
        """测试自定义角色路径"""
        sdk_configure(ROLES_CLAIM_PATH="custom.user_roles")
        
        claims = {
            "sub": "user-123",
            "custom": {
                "user_roles": ["role1", "role2"]
            }
        }
        user = AuthUser(raw_claims=claims)
        assert user.roles == ["role1", "role2"]

    def test_has_role(self):
        """测试 has_role 方法"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin", "user"]}}
        )
        assert user.has_role("admin") is True
        assert user.has_role("user") is True
        assert user.has_role("superadmin") is False

    def test_has_any_role(self):
        """测试 has_any_role 方法"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin", "user"]}}
        )
        assert user.has_any_role("admin", "superadmin") is True
        assert user.has_any_role("superadmin", "moderator") is False

    def test_has_all_roles(self):
        """测试 has_all_roles 方法"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "realm_access": {"roles": ["admin", "user"]}}
        )
        assert user.has_all_roles("admin", "user") is True
        assert user.has_all_roles("admin", "superadmin") is False

    def test_to_dict(self):
        """测试 to_dict 方法"""
        claims = {
            "sub": "user-123",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "realm_access": {"roles": ["admin"]}
        }
        user = AuthUser(raw_claims=claims)
        user_dict = user.to_dict()
        
        assert user_dict["sub"] == "user-123"
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["roles"] == ["admin"]
        assert "raw_claims" in user_dict

    def test_repr(self):
        """测试 __repr__ 方法"""
        user = AuthUser(
            raw_claims={"sub": "user-123", "preferred_username": "testuser"}
        )
        repr_str = repr(user)
        assert "user-123" in repr_str
        assert "testuser" in repr_str

    def test_bool_authenticated(self):
        """测试已认证用户的 bool 值"""
        user = AuthUser(raw_claims={"sub": "user-123"})
        assert bool(user) is True

    def test_bool_not_authenticated(self):
        """测试未认证用户的 bool 值"""
        user = AuthUser()
        assert bool(user) is False


class TestExtractTokenFromHeader:
    """测试从 Authorization header 提取 Token"""

    def test_extract_valid_bearer_token(self):
        """测试提取有效的 Bearer Token"""
        header = "Bearer eyJhbGciOiJSUzI1NiJ9.test.token"
        token = extract_token_from_header(header)
        assert token == "eyJhbGciOiJSUzI1NiJ9.test.token"

    def test_extract_token_case_insensitive(self):
        """测试 Bearer 大小写不敏感"""
        header = "bearer eyJhbGciOiJSUzI1NiJ9.test.token"
        token = extract_token_from_header(header)
        assert token == "eyJhbGciOiJSUzI1NiJ9.test.token"

    def test_extract_token_none_header(self):
        """测试 None header"""
        token = extract_token_from_header(None)
        assert token is None

    def test_extract_token_empty_header(self):
        """测试空 header"""
        token = extract_token_from_header("")
        assert token is None

    def test_extract_token_invalid_format(self):
        """测试无效格式"""
        token = extract_token_from_header("InvalidFormat")
        assert token is None

    def test_extract_token_wrong_scheme(self):
        """测试错误的 scheme"""
        token = extract_token_from_header("Basic dXNlcjpwYXNz")
        assert token is None

    def test_extract_token_too_many_parts(self):
        """测试太多部分"""
        token = extract_token_from_header("Bearer token extra parts")
        assert token is None


class TestVerifyToken:
    """测试 Token 校验（需要 mock JWKS）"""

    def test_verify_token_not_configured(self):
        """测试未配置时校验 Token"""
        from chewy_auth_sdk.exceptions import ConfigurationError
        
        with pytest.raises(ConfigurationError):
            verify_token("fake.token.here")

    def test_verify_token_invalid_format(self, sdk_configure):
        """测试无效格式的 Token"""
        sdk_configure()
        
        with pytest.raises(InvalidTokenError):
            verify_token("not.a.valid.jwt")

    def test_verify_token_empty(self, sdk_configure):
        """测试空 Token"""
        sdk_configure()
        
        with pytest.raises(InvalidTokenError):
            verify_token("")
