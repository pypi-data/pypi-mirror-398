"""
FastAPI Adapters and Helpers

提供 FastAPI 相关的便捷工具
"""

from typing import Optional

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..token import AuthUser, verify_token

# HTTP Bearer 安全方案（可选）
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(request: Request) -> Optional[AuthUser]:
    """
    FastAPI Dependency：获取当前用户

    Example:
        from fastapi import FastAPI, Depends
        from chewy_auth_sdk.adapters.fastapi import get_current_user

        app = FastAPI()

        @app.get("/profile")
        def get_profile(user: AuthUser = Depends(get_current_user)):
            if user is None:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return {"username": user.username}
    """
    return getattr(request.state, "user", None)


def require_auth(request: Request) -> AuthUser:
    """
    FastAPI Dependency：要求用户已认证

    Example:
        from fastapi import FastAPI, Depends
        from chewy_auth_sdk.adapters.fastapi import require_auth

        app = FastAPI()

        @app.get("/profile")
        def get_profile(user: AuthUser = Depends(require_auth)):
            return {"username": user.username}
    """
    user = getattr(request.state, "user", None)
    if user is None or not isinstance(user, AuthUser) or not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
    return user


def require_role(role: str):
    """
    FastAPI Dependency Factory：要求用户拥有指定角色

    Example:
        from fastapi import FastAPI, Depends
        from chewy_auth_sdk.adapters.fastapi import require_role

        app = FastAPI()

        @app.get("/admin")
        def admin_endpoint(user: AuthUser = Depends(require_role("admin"))):
            return {"message": "Welcome admin"}
    """

    def dependency(request: Request) -> AuthUser:
        user = require_auth(request)
        if not user.has_role(role):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{role}' is required",
            )
        return user

    return dependency


def require_any_role(*roles: str):
    """
    FastAPI Dependency Factory：要求用户拥有任一指定角色

    Example:
        from fastapi import FastAPI, Depends
        from chewy_auth_sdk.adapters.fastapi import require_any_role

        app = FastAPI()

        @app.get("/moderation")
        def moderation_endpoint(
            user: AuthUser = Depends(require_any_role("admin", "moderator"))
        ):
            return {"message": "Welcome"}
    """

    def dependency(request: Request) -> AuthUser:
        user = require_auth(request)
        if not user.has_any_role(*roles):
            raise HTTPException(
                status_code=403,
                detail=f"One of roles {roles} is required",
            )
        return user

    return dependency


def require_all_roles(*roles: str):
    """
    FastAPI Dependency Factory：要求用户拥有所有指定角色

    Example:
        from fastapi import FastAPI, Depends
        from chewy_auth_sdk.adapters.fastapi import require_all_roles

        app = FastAPI()

        @app.get("/super-admin")
        def super_admin_endpoint(
            user: AuthUser = Depends(require_all_roles("admin", "superuser"))
        ):
            return {"message": "Welcome super admin"}
    """

    def dependency(request: Request) -> AuthUser:
        user = require_auth(request)
        if not user.has_all_roles(*roles):
            raise HTTPException(
                status_code=403,
                detail=f"All roles {roles} are required",
            )
        return user

    return dependency


def verify_token_dependency(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[AuthUser]:
    """
    FastAPI Dependency：直接从 Bearer Token 校验并返回用户

    不依赖 Middleware，可单独使用

    Example:
        from fastapi import FastAPI, Depends
        from chewy_auth_sdk.adapters.fastapi import verify_token_dependency

        app = FastAPI()

        @app.get("/profile")
        def get_profile(user: AuthUser = Depends(verify_token_dependency)):
            if user is None:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return {"username": user.username}
    """
    if credentials is None:
        return None

    try:
        return verify_token(credentials.credentials)
    except Exception:
        return None
