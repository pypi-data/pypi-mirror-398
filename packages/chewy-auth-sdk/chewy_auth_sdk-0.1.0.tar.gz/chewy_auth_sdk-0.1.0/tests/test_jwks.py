"""
测试 JWKS 管理和缓存
"""

import pytest
import time
from unittest.mock import Mock, patch

from chewy_auth_sdk.jwks import (
    JWKSManager,
    get_jwks_manager,
    get_jwks_client,
    clear_jwks_cache,
)
from chewy_auth_sdk.exceptions import JWKSFetchError


class TestJWKSManager:
    """测试 JWKS 管理器"""

    def test_jwks_manager_singleton(self):
        """测试单例模式"""
        manager1 = JWKSManager()
        manager2 = JWKSManager()
        assert manager1 is manager2

    def test_get_jwks_manager(self):
        """测试获取管理器"""
        manager1 = get_jwks_manager()
        manager2 = get_jwks_manager()
        assert manager1 is manager2
        assert isinstance(manager1, JWKSManager)

    def test_clear_cache_all(self, sdk_configure):
        """测试清除所有缓存"""
        sdk_configure()
        manager = get_jwks_manager()
        
        # 模拟添加缓存
        manager._cache_timestamps["uri1"] = time.time()
        manager._cache_timestamps["uri2"] = time.time()
        
        manager.clear_cache()
        
        assert len(manager._cache_timestamps) == 0
        assert len(manager._clients) == 0

    def test_clear_cache_specific_uri(self, sdk_configure):
        """测试清除特定 URI 的缓存"""
        sdk_configure()
        manager = get_jwks_manager()
        
        # 模拟添加缓存
        manager._cache_timestamps["uri1"] = time.time()
        manager._cache_timestamps["uri2"] = time.time()
        
        manager.clear_cache("uri1")
        
        assert "uri1" not in manager._cache_timestamps
        assert "uri2" in manager._cache_timestamps

    def test_get_jwks_client_not_configured(self):
        """测试未配置时获取客户端"""
        from chewy_auth_sdk.exceptions import ConfigurationError
        
        manager = JWKSManager()
        
        with pytest.raises(ConfigurationError):
            manager.get_jwks_client()

    @patch('chewy_auth_sdk.jwks.PyJWKClient')
    def test_get_jwks_client_success(self, mock_pyjwk_client, sdk_configure):
        """测试成功获取客户端"""
        sdk_configure()
        
        mock_client = Mock()
        mock_pyjwk_client.return_value = mock_client
        
        manager = JWKSManager()
        manager._cache_timestamps.clear()  # 清除缓存
        manager._clients.clear()
        
        client = manager.get_jwks_client()
        
        assert client == mock_client
        mock_pyjwk_client.assert_called_once()

    @patch('chewy_auth_sdk.jwks.PyJWKClient')
    def test_get_jwks_client_cache_hit(self, mock_pyjwk_client, sdk_configure):
        """测试缓存命中"""
        settings = sdk_configure(CACHE_TTL=300)
        
        mock_client = Mock()
        mock_pyjwk_client.return_value = mock_client
        
        manager = JWKSManager()
        manager._cache_timestamps.clear()
        manager._clients.clear()
        
        # 第一次调用
        client1 = manager.get_jwks_client()
        
        # 第二次调用（应该使用缓存）
        client2 = manager.get_jwks_client()
        
        assert client1 is client2
        # 只创建一次
        assert mock_pyjwk_client.call_count == 1

    @patch('chewy_auth_sdk.jwks.PyJWKClient')
    def test_get_jwks_client_cache_expired(self, mock_pyjwk_client, sdk_configure):
        """测试缓存过期"""
        settings = sdk_configure(CACHE_TTL=1)
        
        mock_client = Mock()
        mock_pyjwk_client.return_value = mock_client
        
        manager = JWKSManager()
        manager._cache_timestamps.clear()
        manager._clients.clear()
        
        # 第一次调用
        manager.get_jwks_client()
        
        # 等待缓存过期
        time.sleep(2)
        
        # 第二次调用（缓存已过期）
        manager.get_jwks_client()
        
        # 应该创建两次
        assert mock_pyjwk_client.call_count == 2

    def test_get_jwks_client_missing_uri(self):
        """测试缺少 JWKS URI"""
        from chewy_auth_sdk.exceptions import ConfigurationError
        from chewy_auth_sdk.settings import reset_settings
        
        reset_settings()  # 确保未配置
        
        manager = JWKSManager()
        
        with pytest.raises((JWKSFetchError, ConfigurationError)):
            manager.get_jwks_client()


class TestJWKSHelperFunctions:
    """测试 JWKS 辅助函数"""

    @patch('chewy_auth_sdk.jwks.PyJWKClient')
    def test_get_jwks_client_function(self, mock_pyjwk_client, sdk_configure):
        """测试 get_jwks_client 函数"""
        sdk_configure()
        
        mock_client = Mock()
        mock_pyjwk_client.return_value = mock_client
        
        # 清除缓存
        manager = get_jwks_manager()
        manager.clear_cache()
        
        client = get_jwks_client()
        assert client == mock_client

    def test_clear_jwks_cache_function(self, sdk_configure):
        """测试 clear_jwks_cache 函数"""
        sdk_configure()
        
        manager = get_jwks_manager()
        manager._cache_timestamps["test_uri"] = time.time()
        
        clear_jwks_cache("test_uri")
        
        assert "test_uri" not in manager._cache_timestamps
