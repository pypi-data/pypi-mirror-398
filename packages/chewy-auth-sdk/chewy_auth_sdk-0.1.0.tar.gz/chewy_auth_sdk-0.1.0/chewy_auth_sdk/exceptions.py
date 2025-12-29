"""
统一异常定义

所有 ChewyAuth SDK 的异常都继承自 ChewyAuthException
"""


class ChewyAuthException(Exception):
    """ChewyAuth SDK 基础异常"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ConfigurationError(ChewyAuthException):
    """配置错误"""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class TokenValidationError(ChewyAuthException):
    """Token 校验失败（基础类）"""

    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class TokenExpiredError(TokenValidationError):
    """Token 已过期"""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenError(TokenValidationError):
    """Token 无效"""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)


class InvalidSignatureError(TokenValidationError):
    """签名无效"""

    def __init__(self, message: str = "Token signature verification failed"):
        super().__init__(message)


class InvalidIssuerError(TokenValidationError):
    """Issuer 不匹配"""

    def __init__(self, message: str = "Token issuer is invalid"):
        super().__init__(message)


class InvalidAudienceError(TokenValidationError):
    """Audience 不匹配"""

    def __init__(self, message: str = "Token audience is invalid"):
        super().__init__(message)


class JWKSFetchError(ChewyAuthException):
    """JWKS 获取失败"""

    def __init__(self, message: str):
        super().__init__(f"Failed to fetch JWKS: {message}", status_code=500)
