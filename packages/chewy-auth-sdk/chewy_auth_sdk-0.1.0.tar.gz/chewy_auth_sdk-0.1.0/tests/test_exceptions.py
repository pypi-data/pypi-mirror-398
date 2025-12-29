"""
测试异常定义
"""

import pytest
from chewy_auth_sdk.exceptions import (
    ChewyAuthException,
    ConfigurationError,
    TokenValidationError,
    TokenExpiredError,
    InvalidTokenError,
    InvalidSignatureError,
    InvalidIssuerError,
    InvalidAudienceError,
    JWKSFetchError,
)


class TestChewyAuthException:
    """测试基础异常"""

    def test_exception_message(self):
        """测试异常消息"""
        exc = ChewyAuthException("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"

    def test_exception_status_code(self):
        """测试异常状态码"""
        exc = ChewyAuthException("Test error", status_code=400)
        assert exc.status_code == 400

    def test_exception_default_status_code(self):
        """测试默认状态码"""
        exc = ChewyAuthException("Test error")
        assert exc.status_code == 500


class TestConfigurationError:
    """测试配置错误"""

    def test_configuration_error(self):
        """测试配置错误"""
        exc = ConfigurationError("Invalid configuration")
        assert str(exc) == "Invalid configuration"
        assert exc.status_code == 500


class TestTokenValidationError:
    """测试 Token 验证错误"""

    def test_token_validation_error(self):
        """测试 Token 验证错误"""
        exc = TokenValidationError("Token is invalid")
        assert str(exc) == "Token is invalid"
        assert exc.status_code == 401


class TestTokenExpiredError:
    """测试 Token 过期错误"""

    def test_token_expired_error(self):
        """测试 Token 过期错误"""
        exc = TokenExpiredError()
        assert "expired" in str(exc).lower()
        assert exc.status_code == 401

    def test_token_expired_error_custom_message(self):
        """测试自定义消息"""
        exc = TokenExpiredError("Custom expired message")
        assert str(exc) == "Custom expired message"


class TestInvalidTokenError:
    """测试无效 Token 错误"""

    def test_invalid_token_error(self):
        """测试无效 Token 错误"""
        exc = InvalidTokenError()
        assert "invalid" in str(exc).lower()
        assert exc.status_code == 401

    def test_invalid_token_error_custom_message(self):
        """测试自定义消息"""
        exc = InvalidTokenError("Custom invalid message")
        assert str(exc) == "Custom invalid message"


class TestInvalidSignatureError:
    """测试签名无效错误"""

    def test_invalid_signature_error(self):
        """测试签名无效错误"""
        exc = InvalidSignatureError()
        assert "signature" in str(exc).lower()
        assert exc.status_code == 401


class TestInvalidIssuerError:
    """测试 Issuer 错误"""

    def test_invalid_issuer_error(self):
        """测试 Issuer 错误"""
        exc = InvalidIssuerError()
        assert "issuer" in str(exc).lower()
        assert exc.status_code == 401


class TestInvalidAudienceError:
    """测试 Audience 错误"""

    def test_invalid_audience_error(self):
        """测试 Audience 错误"""
        exc = InvalidAudienceError()
        assert "audience" in str(exc).lower()
        assert exc.status_code == 401


class TestJWKSFetchError:
    """测试 JWKS 获取错误"""

    def test_jwks_fetch_error(self):
        """测试 JWKS 获取错误"""
        exc = JWKSFetchError("Network error")
        assert "JWKS" in str(exc)
        assert "Network error" in str(exc)
        assert exc.status_code == 500
