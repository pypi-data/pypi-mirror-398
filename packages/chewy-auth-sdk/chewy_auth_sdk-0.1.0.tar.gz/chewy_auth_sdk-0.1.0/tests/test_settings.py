"""
测试 SDK 配置管理
"""

import pytest
from chewy_auth_sdk import configure, get_settings
from chewy_auth_sdk.settings import reset_settings, ChewyAuthSettings
from chewy_auth_sdk.exceptions import ConfigurationError


class TestChewyAuthSettings:
    """测试配置对象"""

    def test_default_values(self):
        """测试默认值"""
        settings = ChewyAuthSettings(KEYCLOAK_ISSUER="https://kc.example.com/realms/demo")
        assert settings.CACHE_TTL == 300
        assert settings.VERIFY_AUDIENCE is True
        assert settings.VERIFY_EXPIRATION is True
        assert settings.ROLES_CLAIM_PATH == "realm_access.roles"
        assert settings.ENABLE_HEADER_PASSTHROUGH is False

    def test_auto_jwks_uri_generation(self):
        """测试自动生成 JWKS URI"""
        settings = ChewyAuthSettings(KEYCLOAK_ISSUER="https://kc.example.com/realms/demo")
        assert settings.KEYCLOAK_JWKS_URI == "https://kc.example.com/realms/demo/protocol/openid-connect/certs"

    def test_manual_jwks_uri(self):
        """测试手动设置 JWKS URI"""
        custom_jwks = "https://custom.example.com/jwks"
        settings = ChewyAuthSettings(
            KEYCLOAK_ISSUER="https://kc.example.com/realms/demo",
            KEYCLOAK_JWKS_URI=custom_jwks
        )
        assert settings.KEYCLOAK_JWKS_URI == custom_jwks

    def test_validate_missing_issuer(self):
        """测试缺少 ISSUER 的验证"""
        settings = ChewyAuthSettings()
        with pytest.raises(ConfigurationError, match="KEYCLOAK_ISSUER is required"):
            settings.validate()

    def test_validate_success(self):
        """测试配置验证成功"""
        settings = ChewyAuthSettings(KEYCLOAK_ISSUER="https://kc.example.com/realms/demo")
        settings.validate()
        assert settings.is_configured is True


class TestConfigureFunction:
    """测试 configure 函数"""

    def test_configure_basic(self):
        """测试基础配置"""
        settings = configure(
            KEYCLOAK_ISSUER="https://kc.example.com/realms/demo",
            KEYCLOAK_AUDIENCE="account"
        )
        assert settings.KEYCLOAK_ISSUER == "https://kc.example.com/realms/demo"
        assert settings.KEYCLOAK_AUDIENCE == "account"
        assert settings.is_configured is True

    def test_configure_custom_values(self):
        """测试自定义配置值"""
        settings = configure(
            KEYCLOAK_ISSUER="https://kc.example.com/realms/demo",
            CACHE_TTL=600,
            VERIFY_AUDIENCE=False,
            ROLES_CLAIM_PATH="custom.roles"
        )
        assert settings.CACHE_TTL == 600
        assert settings.VERIFY_AUDIENCE is False
        assert settings.ROLES_CLAIM_PATH == "custom.roles"

    def test_configure_update_existing(self):
        """测试更新已有配置"""
        configure(KEYCLOAK_ISSUER="https://kc1.example.com/realms/demo")
        settings = configure(
            KEYCLOAK_ISSUER="https://kc2.example.com/realms/demo",
            CACHE_TTL=1000
        )
        assert settings.KEYCLOAK_ISSUER == "https://kc2.example.com/realms/demo"
        assert settings.CACHE_TTL == 1000

    def test_configure_invalid_key(self):
        """测试无效的配置键"""
        configure(KEYCLOAK_ISSUER="https://kc.example.com/realms/demo")
        with pytest.raises(ConfigurationError, match="Unknown configuration key"):
            configure(INVALID_KEY="value")

    def test_configure_header_passthrough(self):
        """测试 Header 透传配置"""
        settings = configure(
            KEYCLOAK_ISSUER="https://kc.example.com/realms/demo",
            ENABLE_HEADER_PASSTHROUGH=True,
            HEADER_USER_SUB="X-Custom-Sub",
            HEADER_USER_NAME="X-Custom-Name",
            HEADER_USER_ROLES="X-Custom-Roles"
        )
        assert settings.ENABLE_HEADER_PASSTHROUGH is True
        assert settings.HEADER_USER_SUB == "X-Custom-Sub"
        assert settings.HEADER_USER_NAME == "X-Custom-Name"
        assert settings.HEADER_USER_ROLES == "X-Custom-Roles"


class TestGetSettings:
    """测试 get_settings 函数"""

    def test_get_settings_not_configured(self):
        """测试未配置时获取设置"""
        with pytest.raises(ConfigurationError, match="ChewyAuth SDK is not configured"):
            get_settings()

    def test_get_settings_after_configure(self):
        """测试配置后获取设置"""
        configure(KEYCLOAK_ISSUER="https://kc.example.com/realms/demo")
        settings = get_settings()
        assert settings.KEYCLOAK_ISSUER == "https://kc.example.com/realms/demo"
        assert settings.is_configured is True

    def test_get_settings_returns_same_instance(self):
        """测试获取的是同一个实例"""
        configure(KEYCLOAK_ISSUER="https://kc.example.com/realms/demo")
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestResetSettings:
    """测试 reset_settings 函数"""

    def test_reset_settings(self):
        """测试重置配置"""
        configure(KEYCLOAK_ISSUER="https://kc.example.com/realms/demo")
        assert get_settings().is_configured is True

        reset_settings()

        with pytest.raises(ConfigurationError):
            get_settings()
