
## 一、整体架构视图（逻辑架构）

```
┌─────────────────────────────────────────────────────────────┐
│                         Client / Frontend                   │
│                                                             │
│  - Web / Mobile / Service                                   │
│  - 携带 JWT / Token                                         │
└───────────────────────────────┬─────────────────────────────┘
                                │ HTTP Request
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Authentication Layer                    │   │
│  │                                                     │   │
│  │  - JWT Decode                                        │   │
│  │  - 获取 User Identity (sub, roles, claims)           │   │
│  └───────────────┬─────────────────────────────────────┘   │
│                  │ subject                                  │
│                  ▼                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           fastapi-casbin-acl (ACL Layer)             │   │
│  │                                                     │   │
│  │  permission_required                                 │   │
│  │   ├─ Subject Resolver (来自 Auth)                    │   │
│  │   ├─ Resource Getter (来自业务)                      │   │
│  │   ├─ Policy Enforcement (Casbin)                     │   │
│  │   └─ Decision (Allow / Deny)                         │   │
│  └───────────────┬─────────────────────────────────────┘   │
│                  │ allowed                                  │
│                  ▼                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Business Layer                        │   │
│  │                                                     │   │
│  │  - Controllers / Routers                             │   │
│  │  - Domain Logic                                      │   │
│  │  - ORM / Repository                                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                     │
│                                                             │
│  - User / Role / Policy Storage                             │
│  - Casbin Adapter (DB / Redis / File)                       │
│  - Business Data (Order / Project / etc.)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、fastapi-casbin-acl 在架构中的**准确定位**

### 一句话定位（非常重要）

> **fastapi-casbin-acl 是应用内部的 Access Control Layer（访问控制层），负责“授权决策”，而不是身份认证或业务逻辑。**

它的职责边界非常清晰：

| 能力             | 是否负责 |
| -------------- | ---- |
| 身份认证（JWT）      | ❌    |
| 用户管理           | ❌    |
| 角色管理 UI        | ❌    |
| 权限决策           | ✅    |
| RBAC / ABAC 执行 | ✅    |
| 接口 / 数据级鉴权     | ✅    |

---

## 三、fastapi-casbin-acl 的“上下游关系”

### 1️⃣ 上游依赖（它不控制，但强约束）

#### （1）认证系统（Authentication）

**提供给 ACL 的内容：**

* `sub`（用户唯一标识）
* 可选：角色 / claims

**形式：**

```python
get_subject = get_current_user_from_jwt
```

**架构约束：**

* fastapi-casbin-acl **不解析 JWT**
* 只消费“已认证的身份结果”

👉 **解耦 Auth 与 AuthZ**

---

#### （2）业务资源加载（Resource Getter）

**提供给 ACL 的内容：**

* 资源实例（如 Order）
* 或资源属性（owner_id / org_id）

**形式：**

```python
def get_order_resource(request) -> Order
```

**架构约束：**

* 只加载数据
* 不判断权限
* 不抛权限异常

👉 **事实与决策分离**

---

### 2️⃣ 下游依赖（ACL 直接控制）

#### （1）Casbin Policy & Model

fastapi-casbin-acl：

* 统一加载 Model
* 统一管理 Enforcer
* 统一执行 enforce

业务层：

* **不直接 import casbin**
* **不直接调用 enforce**

---

#### （2）业务路由（FastAPI Router）

业务代码通过：

```python
Depends(permission_required(...))
```

将**访问控制前置**到请求链路。

👉 ACL 是 **业务执行的“守门人”**

---

## 四、RBAC + ABAC 在架构中的协作关系

### RBAC（接口级）

```
User ──> Role ──> API Permission
```

* resource = None
* 只判断：sub / obj / act

```python
permission_required(
    obj="/orders",
    act="read"
)
```

---

### ABAC（数据级）

```
User ──> Role ──> API Permission
                 └─ Attribute Constraint
```

* resource != None
* 加载 owner / org / status
* matcher 中判断属性关系

```python
permission_required(
    obj="/orders/:id",
    act="read",
    resource=get_order_resource
)
```

---

## 五、fastapi-casbin-acl 为什么是“中枢而非服务”

从架构角色上看，它是：

* ❌ 不是独立微服务
* ❌ 不是 IAM
* ❌ 不是网关

而是：

> **Application 内的 Policy Enforcement Point（PEP）**

这也是为什么：

* 它以内嵌依赖存在
* 它靠近业务数据
* 它对性能敏感

---

## 六、你可以在架构文档中这样描述（可直接引用）

> fastapi-casbin-acl 作为应用内部的访问控制层，承接来自认证系统的用户身份信息，并结合业务层提供的资源属性，统一执行基于 Casbin 的 RBAC / ABAC 授权决策；其本身不管理用户、不解析身份、不包含业务逻辑，而是通过 FastAPI 依赖机制，对所有受控接口提供一致、可审计、可演进的权限约束。

