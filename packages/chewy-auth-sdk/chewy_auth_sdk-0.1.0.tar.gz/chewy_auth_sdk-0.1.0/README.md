# ChewyAuthSDK

**生产可用的 Python 统一认证 SDK**

统一 Keycloak JWT 校验逻辑，同时支持 Django 和 FastAPI。

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎯 核心特性

- ✅ **统一 Keycloak JWT 校验** - 基于 RS256 + JWKS
- ✅ **同时支持 Django 和 FastAPI** - 一套 SDK 适配两大框架
- ✅ **独立校验** - 无需 Gateway，无需 introspection API
- ✅ **高性能** - 本地 JWT 解析 + JWKS 缓存
- ✅ **完整透传 Claims** - 保留 Keycloak 原始用户信息
- ✅ **开箱即用** - 一行配置即可启用

---

## 📦 安装

```bash
# 基础安装（仅 JWT 校验）
pip install chewy-auth-sdk

# Django 项目
pip install chewy-auth-sdk[django]

# FastAPI 项目
pip install chewy-auth-sdk[fastapi]

# 同时支持 Django 和 FastAPI
pip install chewy-auth-sdk[all]
```

---

## 🚀 快速开始

### 1. 配置 SDK

在项目启动时配置一次即可：

```python
from chewy_auth_sdk import configure

configure(
    KEYCLOAK_ISSUER="https://keycloak.example.com/realms/your-realm",
    KEYCLOAK_AUDIENCE="account",  # 可选
    CACHE_TTL=300,  # JWKS 缓存时间（秒）
)
```

### 2. Django 集成

#### 2.1 添加 Middleware

在 `settings.py` 中添加：

```python
MIDDLEWARE += [
    "chewy_auth_sdk.middleware.django.ChewyAuthMiddleware",
]
```

#### 2.2 在视图中使用

```python
from django.http import JsonResponse

def my_view(request):
    # request.user 是 AuthUser 对象或 None
    if request.user is None:
        return JsonResponse({"error": "Not authenticated"}, status=401)
    
    return JsonResponse({
        "username": request.user.username,
        "email": request.user.email,
        "roles": request.user.roles,
    })
```

#### 2.3 使用装饰器进行权限控制

```python
from chewy_auth_sdk.adapters.django import require_auth, require_role

@require_auth
def protected_view(request):
    return JsonResponse({"message": "Authenticated user only"})

@require_role("admin")
def admin_view(request):
    return JsonResponse({"message": "Admin only"})
```

### 3. FastAPI 集成

#### 3.1 添加 Middleware

```python
from fastapi import FastAPI
from chewy_auth_sdk.middleware.fastapi import ChewyAuthMiddleware

app = FastAPI()
app.add_middleware(ChewyAuthMiddleware)
```

#### 3.2 在路由中使用

```python
from fastapi import Request, Depends, HTTPException
from chewy_auth_sdk.adapters.fastapi import get_current_user, require_auth
from chewy_auth_sdk import AuthUser

@app.get("/profile")
def get_profile(request: Request):
    # request.state.user 是 AuthUser 对象或 None
    user = request.state.user
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "username": user.username,
        "email": user.email,
        "roles": user.roles,
    }

# 使用 Dependency
@app.get("/me")
def get_me(user: AuthUser = Depends(require_auth)):
    return {"username": user.username}
```

#### 3.3 使用 Dependency 进行权限控制

```python
from chewy_auth_sdk.adapters.fastapi import require_role, require_any_role

@app.get("/admin")
def admin_endpoint(user: AuthUser = Depends(require_role("admin"))):
    return {"message": "Admin only"}

@app.get("/moderation")
def moderation_endpoint(
    user: AuthUser = Depends(require_any_role("admin", "moderator"))
):
    return {"message": "Admin or moderator"}
```

---

## 📚 核心概念

### AuthUser 对象

所有认证成功的请求都会得到一个 `AuthUser` 对象：

```python
class AuthUser:
    raw_claims: dict        # Keycloak 原始 claims（完整透传）
    sub: str                # 用户唯一标识
    username: str           # 用户名
    email: str | None       # 邮箱
    roles: list[str]        # 角色列表
    
    # 便捷方法
    def has_role(self, role: str) -> bool
    def has_any_role(self, *roles: str) -> bool
    def has_all_roles(self, *roles: str) -> bool
```

### Token 校验流程

1. **提取 Token** - 从 `Authorization: Bearer <token>` header 中提取
2. **获取公钥** - 从 Keycloak JWKS endpoint 获取（带缓存）
3. **校验签名** - 使用 RS256 算法校验
4. **校验 Claims** - 验证 `exp`、`iss`、`aud` 等
5. **构造用户对象** - 提取用户信息和角色

### 为什么不使用 Introspection？

❌ **不推荐 Introspection 的原因：**

- 每次请求都需要调用 Keycloak API（性能差）
- 增加 Keycloak 服务器负载
- 增加网络延迟
- 单点故障风险

✅ **推荐使用 JWT + JWKS：**

- 本地校验，性能高
- JWKS 缓存，减少网络请求
- 无需依赖 Keycloak 可用性
- 符合 OAuth2 / OIDC 标准最佳实践

---

## ⚙️ 高级配置

### 完整配置选项

```python
from chewy_auth_sdk import configure

configure(
    # Keycloak 配置（必填）
    KEYCLOAK_ISSUER="https://keycloak.example.com/realms/your-realm",
    
    # Audience 校验（可选）
    KEYCLOAK_AUDIENCE="account",  # 如果不提供，不校验 audience
    VERIFY_AUDIENCE=True,  # 是否校验 audience
    
    # JWKS 配置（可选，自动推导）
    KEYCLOAK_JWKS_URI=None,  # 默认：{ISSUER}/protocol/openid-connect/certs
    CACHE_TTL=300,  # JWKS 缓存时间（秒）
    
    # Token 校验（可选）
    VERIFY_EXPIRATION=True,  # 是否校验 token 过期时间
    
    # 角色提取（可选）
    ROLES_CLAIM_PATH="realm_access.roles",  # 角色在 JWT 中的路径
    
    # Header 透传（可选，不推荐）
    ENABLE_HEADER_PASSTHROUGH=False,  # 是否启用 Gateway header 透传
    HEADER_USER_SUB="X-User-Sub",
    HEADER_USER_NAME="X-User-Name",
    HEADER_USER_ROLES="X-User-Roles",
)
```

### Header 透传模式（可选）

如果你使用 Gateway 并希望透传用户信息，可以使用：

```python
# Django
MIDDLEWARE += [
    "chewy_auth_sdk.middleware.django.ChewyAuthMiddlewareWithHeaderPassthrough",
]

# FastAPI
from chewy_auth_sdk.middleware.fastapi import ChewyAuthMiddlewareWithHeaderPassthrough
app.add_middleware(ChewyAuthMiddlewareWithHeaderPassthrough)
```

### 自定义角色路径

如果你的角色不在 `realm_access.roles`，可以自定义：

```python
configure(
    KEYCLOAK_ISSUER="...",
    ROLES_CLAIM_PATH="resource_access.my-client.roles",  # 自定义路径
)
```

---

## 🧪 测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest
```

---

## 📖 架构说明

### 项目结构

```
ChewyAuthSDK/
├── chewy_auth_sdk/
│   ├── __init__.py          # 公共 API
│   ├── settings.py          # 全局配置管理
│   ├── exceptions.py        # 统一异常定义
│   ├── jwks.py              # JWKS 管理和缓存
│   ├── token.py             # JWT 校验和 AuthUser
│   ├── context.py           # 请求上下文（可选）
│   ├── middleware/
│   │   ├── django.py        # Django Middleware
│   │   └── fastapi.py       # FastAPI Middleware
│   └── adapters/
│       ├── django.py        # Django 装饰器和工具
│       └── fastapi.py       # FastAPI Dependency 和工具
├── pyproject.toml
└── README.md
```

### 设计原则

1. **职责分离** - 每个模块只做一件事
2. **框架无关** - 核心逻辑不依赖 Django/FastAPI
3. **易于扩展** - 可轻松支持新框架
4. **生产就绪** - 异常处理、缓存、性能优化

---

## 🚫 明确禁止

ChewyAuthSDK **只做 Token 校验**，**不实现**以下功能：

- ❌ 登录 / 跳转到 Keycloak
- ❌ Refresh Token 处理
- ❌ 用户信息存储（数据库）
- ❌ Keycloak Admin API 调用
- ❌ 强制依赖 Gateway

如需这些功能，请直接使用 Keycloak 官方库或其他专用工具。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 License

MIT License

---

## 🔗 相关链接

- [Keycloak 官方文档](https://www.keycloak.org/documentation)
- [OAuth 2.0 / OIDC 规范](https://oauth.net/2/)
- [JWT 介绍](https://jwt.io/)
- [Django 官方文档](https://www.djangoproject.com/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)

---

## ❓ FAQ

### Q: 为什么不使用 Keycloak Python Adapter？

A: Keycloak 官方 Python Adapter 主要面向 OIDC 登录流程，对于纯 API 认证（微服务）场景过于复杂。ChewyAuthSDK 专注于 JWT 校验，更轻量、更灵活。

### Q: 可以在生产环境使用吗？

A: 是的，ChewyAuthSDK 设计目标就是生产可用。包含完整的异常处理、缓存机制、性能优化。

### Q: 如何处理 Token 过期？

A: Token 过期会抛出 `TokenExpiredError`，Middleware 会返回 401。客户端应该刷新 Token 后重试。

### Q: 支持多个 Realm 吗？

A: 当前版本只支持单个 Realm。如需多 Realm，建议为每个服务独立配置 SDK。

### Q: 性能如何？

A: JWT 本地校验 + JWKS 缓存，单次请求耗时 < 1ms。JWKS 缓存默认 5 分钟，可自定义。

---

**Enjoy coding with ChewyAuthSDK! 🎉**
