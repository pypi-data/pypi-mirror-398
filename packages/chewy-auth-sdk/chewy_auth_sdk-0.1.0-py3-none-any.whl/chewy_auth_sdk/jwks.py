"""
JWKS (JSON Web Key Set) 管理和缓存

提供 Keycloak 公钥拉取和内存缓存功能
"""

import time
from typing import Dict, Optional
from threading import Lock

from jwt import PyJWKClient

from .settings import get_settings
from .exceptions import JWKSFetchError


class JWKSManager:
    """JWKS 管理器（单例模式）"""

    _instance: Optional["JWKSManager"] = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._clients: Dict[str, PyJWKClient] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._initialized = True

    def get_jwks_client(self, jwks_uri: Optional[str] = None) -> PyJWKClient:
        """
        获取 JWKS 客户端（带缓存）

        Args:
            jwks_uri: JWKS URI，如果不提供则从配置读取

        Returns:
            PyJWKClient: JWKS 客户端

        Raises:
            JWKSFetchError: JWKS 获取失败
        """
        settings = get_settings()

        # 确定 JWKS URI
        if jwks_uri is None:
            jwks_uri = settings.KEYCLOAK_JWKS_URI

        if not jwks_uri:
            raise JWKSFetchError("JWKS URI is not configured")

        # 检查缓存是否过期
        now = time.time()
        if jwks_uri in self._cache_timestamps:
            cache_age = now - self._cache_timestamps[jwks_uri]
            if cache_age < settings.CACHE_TTL:
                # 缓存有效，直接返回
                return self._clients[jwks_uri]

        # 缓存过期或不存在，重新创建客户端
        try:
            with self._lock:
                # 双重检查（防止并发创建）
                if jwks_uri in self._cache_timestamps:
                    cache_age = now - self._cache_timestamps[jwks_uri]
                    if cache_age < settings.CACHE_TTL:
                        return self._clients[jwks_uri]

                # 创建新的 JWKS 客户端
                client = PyJWKClient(
                    jwks_uri,
                    cache_keys=True,
                    max_cached_keys=16,
                    cache_jwk_set=True,
                    lifespan=settings.CACHE_TTL,
                )

                # 更新缓存
                self._clients[jwks_uri] = client
                self._cache_timestamps[jwks_uri] = now

                return client

        except Exception as e:
            raise JWKSFetchError(f"Failed to create JWKS client: {str(e)}")

    def clear_cache(self, jwks_uri: Optional[str] = None):
        """
        清除缓存

        Args:
            jwks_uri: 要清除的 JWKS URI，如果为 None 则清除所有缓存
        """
        with self._lock:
            if jwks_uri is None:
                self._clients.clear()
                self._cache_timestamps.clear()
            else:
                self._clients.pop(jwks_uri, None)
                self._cache_timestamps.pop(jwks_uri, None)


# 全局单例
_jwks_manager: Optional[JWKSManager] = None


def get_jwks_manager() -> JWKSManager:
    """获取 JWKS 管理器单例"""
    global _jwks_manager
    if _jwks_manager is None:
        _jwks_manager = JWKSManager()
    return _jwks_manager


def get_jwks_client(jwks_uri: Optional[str] = None) -> PyJWKClient:
    """
    获取 JWKS 客户端（便捷方法）

    Args:
        jwks_uri: JWKS URI

    Returns:
        PyJWKClient: JWKS 客户端
    """
    manager = get_jwks_manager()
    return manager.get_jwks_client(jwks_uri)


def clear_jwks_cache(jwks_uri: Optional[str] = None):
    """
    清除 JWKS 缓存（便捷方法）

    Args:
        jwks_uri: 要清除的 JWKS URI
    """
    manager = get_jwks_manager()
    manager.clear_cache(jwks_uri)
