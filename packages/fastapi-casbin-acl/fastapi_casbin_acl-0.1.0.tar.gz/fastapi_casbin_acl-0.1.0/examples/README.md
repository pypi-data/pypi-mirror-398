# FastAPI Casbin ACL 示例应用

这是一个完整的示例应用，展示了如何使用 `fastapi-casbin-acl` 构建带有权限控制的 Web 应用。

## 技术栈

- **FastAPI**: 现代、快速的 Web 框架
- **SQLModel**: 基于 SQLAlchemy 的 ORM，结合了 Pydantic 和 SQLAlchemy 的优势
- **aiosqlite**: 异步 SQLite 数据库驱动
- **Casbin**: 强大的访问控制库，支持 RBAC 和 ABAC

## 项目结构

```
examples/
├── __init__.py          # 包初始化文件
├── main.py              # FastAPI 应用主文件（包含前端页面）
├── database.py          # 数据库连接和会话管理
├── models.py            # SQLModel 数据模型
├── routes.py            # API 路由定义
├── run.py               # 便捷运行脚本
└── README.md            # 本文件
```

## 功能特性

### 1. 用户管理
- **列出所有用户** (`GET /api/users`) - 需要 `read` 权限
- **获取用户详情** (`GET /api/users/{user_id}`) - 需要 `read` 权限
- **创建新用户** (`POST /api/users`) - 需要 `write` 权限

### 2. 订单管理
- **列出所有订单** (`GET /api/orders`) - 需要 `read` 权限（RBAC）
- **创建新订单** (`POST /api/orders`) - 需要 `write` 权限（RBAC），订单自动关联到当前用户
- **获取订单详情** (`GET /api/orders/{id}`) - **ABAC**: 只有订单所有者或管理员可以访问
- **更新订单** (`PUT /api/orders/{id}`) - **ABAC**: 只有订单所有者或管理员可以更新
- **删除订单** (`DELETE /api/orders/{id}`) - **ABAC**: 只有订单所有者或管理员可以删除

## 权限模型

### 模型选择

本示例使用 **ABAC（基于属性的访问控制）** 模型，支持：
- **RBAC 功能**：基于角色的权限控制（如 admin、user 角色）
- **ABAC 功能**：基于资源所有者的权限控制（如订单所有者检查）

在 `permission_required` 中可以通过 `model` 参数指定使用的权限模型：

```python
# 使用 ABAC 模型（默认，支持所有权检查）
permission_required(..., model="abac")

# 使用 RBAC 模型（仅基于角色，不支持所有权检查）
permission_required(..., model="rbac")
```

### 标识符统一使用用户 ID

**重要**：本示例统一使用**用户 ID**（整数，转换为字符串）作为权限标识符，而不是 username。这确保了：
- Subject（用户标识）：`get_subject_from_user` 返回 `str(user.id)`
- Owner（资源所有者）：`Order.get_owner_sub()` 返回 `str(owner_id)`
- 策略定义：使用用户 ID（如 "1", "2", "3"）

### 角色定义
- **用户 ID 1** (alice): 管理员 (admin)
- **用户 ID 2** (bob): 普通用户 (user)
- **用户 ID 3** (charlie): 普通用户 (user)

### 权限策略

#### RBAC 策略（基于角色）
- `admin` 角色可以读取和写入用户 (`/api/users/*`)
- `user` 角色可以读取、写入和删除订单 (`/api/orders/*`)

**注意**：策略路径使用通配符 `/*` 来匹配带路径参数的路由：
- `/api/orders/*` 可以匹配 `/api/orders` 和 `/api/orders/{id}`
- `/api/users/*` 可以匹配 `/api/users` 和 `/api/users/{user_id}`

#### ABAC 策略（基于属性）
- 订单的访问控制基于 `owner_id` 属性
- 只有订单的所有者（`r.sub == r.owner`）或 `admin` 角色（`g(r.sub, "admin")`）可以访问、更新或删除订单
- Matcher 规则：`(p.sub == "" || p.sub == "*" || g(r.sub, p.sub)) && keyMatch2(r.obj, p.obj) && r.act == p.act && (r.owner == "" || r.sub == r.owner || g(r.sub, "admin"))`

## 核心设计

### 1. 认证与鉴权分离

示例采用了清晰的认证和鉴权分离设计：

```python
# 认证：获取用户对象
async def get_current_user(request: Request, session: AsyncSession) -> User | None:
    """从请求头获取用户对象"""
    user_id = int(request.headers.get("x-user-id"))
    # ... 查询用户 ...
    return user

# 鉴权：提取用户标识用于权限检查
async def get_subject_from_user(user: User) -> str | None:
    """返回用户 ID（字符串）用于 Casbin 权限检查"""
    return str(user.id)
```

### 2. 组合依赖：require_permission

提供了 `require_permission` 组合依赖，同时完成认证和权限检查：

```python
def require_permission(action: str, resource=None, owner_getter=None):
    """组合依赖：认证 + 鉴权，返回 User 对象"""
    def _dependency(
        user: User = Depends(get_current_user),
        _: None = Depends(permission_required(..., model="abac"))
    ) -> User:
        return user
    return _dependency
```

**使用示例**：
```python
# RBAC: 不需要资源
current_user: User = Depends(require_permission("read"))

# ABAC: 使用模型的 get_owner_sub 方法
current_user: User = Depends(require_permission("read", resource=get_order_resource))

# ABAC: 使用自定义 owner_getter（推荐）
current_user: User = Depends(
    require_permission("read", resource=get_order_resource, owner_getter=get_order_owner)
)
```

### 3. 灵活的 Owner 提取机制

支持两种方式从资源对象中提取 owner：

#### 方式 1：模型的 `get_owner_sub` 方法

在模型类上定义 `get_owner_sub` 方法：

```python
class Order(SQLModel, table=True):
    owner_id: int = Field(foreign_key="users.id")
    
    def get_owner_sub(self) -> str | None:
        """返回所有者的用户 ID（字符串）"""
        if self.owner_id is not None:
            return str(self.owner_id)
        return None
```

#### 方式 2：自定义 `owner_getter`（推荐）

定义专门的 owner 提取函数：

```python
def get_order_owner(order: Order, request: Request | None = None) -> str | None:
    """从订单对象中提取所有者用户 ID"""
    if hasattr(order, "get_owner_sub"):
        owner = order.get_owner_sub()
        if owner is not None:
            return owner
    if order.owner_id is not None:
        return str(order.owner_id)
    return None
```

**提取优先级**：
1. 如果提供了 `owner_getter`，优先使用
2. 否则尝试调用资源对象的 `get_owner_sub()` 方法
3. 如果都没有，返回 `None`（将使用 RBAC 检查）

## 安装和运行

### 1. 安装依赖

确保你已经安装了项目依赖：

```bash
# 在项目根目录
pip install -e .
# 或者
uv pip install -e .
```

### 2. 运行应用

```bash
# 方式 1: 使用 run.py
cd examples
python run.py

# 方式 2: 使用 uvicorn 直接运行
cd examples
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 方式 3: 使用 Python 运行
cd examples
python -m main
```

### 3. 访问应用

打开浏览器访问：http://localhost:8000

## 使用说明

### 前端界面

应用提供了一个完整的 HTML 前端界面，支持：

1. **用户管理**：
   - 获取用户列表
   - 获取用户详情（输入用户 ID）
   - 创建新用户

2. **订单管理**：
   - 获取订单列表
   - 获取订单详情（ABAC，输入订单 ID）
   - 创建新订单
   - 更新订单（ABAC，输入订单 ID）
   - 删除订单（ABAC，输入订单 ID）

3. **用户切换**：
   - 页面加载时自动获取用户列表
   - 下拉菜单显示用户信息（用户名和 ID）
   - 切换用户查看不同的权限效果

### API 调用示例

#### 1. 获取用户列表（需要 read 权限）

```bash
curl -X GET "http://localhost:8000/api/users" \
  -H "X-User-ID: 1"
```

#### 2. 获取用户详情（需要 read 权限）

```bash
curl -X GET "http://localhost:8000/api/users/2" \
  -H "X-User-ID: 1"
```

#### 3. 创建用户（需要 write 权限）

```bash
curl -X POST "http://localhost:8000/api/users" \
  -H "X-User-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dave",
    "email": "dave@example.com"
  }'
```

#### 4. 创建订单（需要 write 权限）

```bash
curl -X POST "http://localhost:8000/api/orders" \
  -H "X-User-ID: 2" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的订单",
    "description": "订单描述",
    "amount": 99.99
  }'
```

#### 5. 获取订单（ABAC: 只有所有者或管理员可以访问）

```bash
# 用户 ID 2 (bob) 可以访问自己的订单
curl -X GET "http://localhost:8000/api/orders/1" \
  -H "X-User-ID: 2"

# 用户 ID 1 (alice, 管理员) 可以访问任何订单
curl -X GET "http://localhost:8000/api/orders/1" \
  -H "X-User-ID: 1"

# 用户 ID 3 (charlie) 不能访问 bob 的订单（403 Forbidden）
curl -X GET "http://localhost:8000/api/orders/1" \
  -H "X-User-ID: 3"
```

#### 6. 更新订单（ABAC: 只有所有者或管理员可以更新）

```bash
curl -X PUT "http://localhost:8000/api/orders/1" \
  -H "X-User-ID: 2" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的标题",
    "status": "completed"
  }'
```

#### 7. 删除订单（ABAC: 只有所有者或管理员可以删除）

```bash
curl -X DELETE "http://localhost:8000/api/orders/1" \
  -H "X-User-ID: 2"
```

## 数据库

应用使用 SQLite 数据库（`example.db`），会在首次运行时自动创建。

数据库包含以下表：
- `users`: 用户表
- `orders`: 订单表
- `casbin_rule`: Casbin 策略规则表

## 代码说明

### 1. 数据库初始化 (`database.py`)

```python
# 使用 aiosqlite 创建异步 SQLite 引擎
engine = create_async_engine("sqlite+aiosqlite:///./example.db")
```

### 2. 数据模型 (`models.py`)

使用 SQLModel 定义数据模型，支持 `get_owner_sub` 方法用于 ABAC：

```python
class Order(SQLModel, table=True):
    owner_id: int = Field(foreign_key="users.id")
    
    def get_owner_sub(self) -> str | None:
        """返回所有者的用户 ID（字符串）"""
        if self.owner_id is not None:
            return str(self.owner_id)
        return None
```

### 3. 权限控制 (`routes.py`)

#### RBAC 示例（基于角色）

```python
@router.get("/users")
async def list_users(
    current_user: User = Depends(require_permission("read")),
):
    # 只有有 read 权限的用户可以访问
    ...
```

#### ABAC 示例（基于属性）

```python
@router.get("/orders/{id}")
async def get_order(
    current_user: User = Depends(
        require_permission("read", resource=get_order_resource, owner_getter=get_order_owner)
    ),
):
    # 只有订单所有者或管理员可以访问
    ...
```

### 4. ACL 初始化 (`main.py`)

```python
# 初始化 Casbin ACL
adapter = SQLModelAdapter(AsyncSessionLocal)
config = ACLConfig(default_model="abac")  # 设置默认模型为 ABAC
await acl.init(adapter=adapter, config=config)

# 如果需要同时支持多个模型，可以指定 models 参数：
# await acl.init(adapter=adapter, models=["rbac", "abac"], config=config)

# 初始化用户数据
await init_users()

# 初始化权限策略（使用用户 ID）
# 注意：init_policies 中使用 acl.get_enforcer("abac") 获取 ABAC 模型的 enforcer
await init_policies()
```

### 5. 权限策略配置

策略路径使用通配符 `/*` 来匹配带路径参数的路由：

```python
# 使用通配符匹配所有 /api/orders 下的路径
await enforcer.add_policy("admin", "/api/orders/*", "read")
await enforcer.add_policy("user", "/api/orders/*", "read")
```

这样可以同时匹配：
- `/api/orders`（列表路径）
- `/api/orders/{id}`（详情路径）

## 设计亮点

### 1. 认证与鉴权分离
- `get_current_user`: 负责认证，返回完整的 User 对象
- `get_subject_from_user`: 负责提取用户标识，返回用户 ID（字符串）
- `permission_required`: 负责权限检查

### 2. 组合依赖模式
- `require_permission`: 统一接口，同时完成认证和鉴权
- 路由中直接使用 `User` 对象，类型安全

### 3. 灵活的 Owner 提取
- 支持模型的 `get_owner_sub` 方法
- 支持自定义 `owner_getter` 函数
- 不同资源类型可以使用不同的提取策略

### 4. 统一的标识符
- 统一使用用户 ID（字符串）作为权限标识符
- Subject 和 Owner 格式一致，确保 ABAC 检查正确

## 扩展建议

1. **JWT 认证**: 将简单的 `X-User-ID` 请求头替换为 JWT token 认证
2. **更复杂的权限模型**: 添加更多角色和权限策略
3. **资源过滤**: 在列表接口中添加基于权限的资源过滤
4. **管理界面**: 添加权限策略管理界面
5. **单元测试**: 添加完整的测试用例
6. **多租户支持**: 添加租户隔离功能

## 注意事项

1. **用户标识符**: 本示例使用用户 ID（整数）作为权限标识符，请求头 `X-User-ID` 应传递用户 ID
2. **策略路径**: 使用通配符 `/*` 来匹配带路径参数的路由
3. **数据库文件**: 数据库文件 (`example.db`) 会在项目目录中创建
4. **权限策略**: 权限策略在应用启动时初始化，实际应用中应该从配置文件或管理界面加载
5. **生产环境**: 本示例使用简单的请求头来识别用户，生产环境应使用 JWT 或其他安全的认证机制

## 故障排除

### 问题：导入错误

如果遇到导入错误，确保你在正确的目录中运行应用，并且已经安装了所有依赖。

### 问题：数据库错误

如果遇到数据库相关错误，尝试删除 `example.db` 文件并重新运行应用。

### 问题：权限检查失败

1. 确保请求头中包含 `X-User-ID`，并且是有效的用户 ID（整数）
2. 检查用户是否有相应的角色和权限策略
3. 对于 ABAC 路由，确保订单的 `owner_id` 与当前用户 ID 匹配

### 问题：ABAC 权限检查失败

1. 确保 `Order.get_owner_sub()` 或 `owner_getter` 返回正确的用户 ID（字符串）
2. 确保策略路径使用通配符 `/*` 来匹配带参数的路由
3. 检查 matcher 规则是否正确配置

## 更多信息

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLModel 文档](https://sqlmodel.tiangolo.com/)
- [Casbin 文档](https://casbin.org/)
- [fastapi-casbin-acl 项目文档](../README.md)
