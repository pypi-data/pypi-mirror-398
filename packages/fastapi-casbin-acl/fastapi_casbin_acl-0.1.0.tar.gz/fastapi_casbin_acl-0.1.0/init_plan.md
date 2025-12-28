# 一、总体设计目标（先定边界）

你要做的不是一个“工具函数”，而是一个 **FastAPI 权限基础设施依赖（Infrastructure Dependency）**。

### 这个依赖必须满足：

1. **零业务侵入**
    
2. **强约束、少约定**
    
3. **RBAC + ABAC 默认支持**
    
4. **可插拔认证方式（JWT / 其他）**
    
5. **与 Casbin 解耦但兼容**

6. **可复用、可约束、可演进、可审计。**

---

# 二、能力拆分：这个依赖到底提供什么？

从“使用者”的视角看，它只做三件事：

```text
1. 统一的权限模型约束
2. 一个 permission_required 依赖工厂
3. 一套 Casbin 生命周期管理机制
```

**不做的事（非常重要）：**

- 不负责用户体系
    
- 不负责 ORM
    
- 不负责业务资源定义
    
- 不绑定具体 JWT 实现
    

---

# 三、最终建议的「依赖包结构」

你可以将其作为一个独立 Python 包，例如：

```text
fastapi_casbin_acl/
├── __init__.py
├── config.py              # 全局配置与约定
├── enforcer.py            # Casbin Enforcer 生命周期
├── models.py              # 权限领域抽象（非 ORM）
├── dependency.py          # permission_required 核心
├── resource.py            # 资源加载协议
├── sync.py                # 策略同步接口（可选）
└── exceptions.py          # 权限异常定义
```

👉 **这是你原 `app/` 目录中权限相关内容的“上移抽象”**。

---

# 四、核心设计一：配置即能力（config.py）

### 设计原则

> **权限系统的变化应通过配置驱动，而不是修改业务代码**

### 示例结构

```python
# fastapi_casbin_acl/config.py

class ACLConfig:
    model_path: str
    enable_abac: bool = True
```

### 工程价值

- 多项目共享统一约束
    
- 防止每个项目“魔改 matcher”
    
- 为未来扩展（tenant / time）留入口
    

---

# 五、核心设计二：Enforcer 生命周期集中管理（enforcer.py）

### 设计原则（你已经认同）

> **Enforcer 是全局单例、集中管理、禁止业务层直接访问**

### 示例设计

```python
# fastapi_casbin_acl/enforcer.py

class EnforcerManager:
    def __init__(self, model_path: str, adapter):
        self.enforcer = casbin.Enforcer(model_path, adapter)

    def enforce(self, *args) -> bool:
        return self.enforcer.enforce(*args)
```

### 架构约束

- ❌ 禁止 `import casbin` 出现在业务项目
    
- ✅ 所有鉴权经由 `EnforcerManager`
    

---

# 六、核心设计三：资源加载协议（resource.py）

这是你整套 ABAC 设计中**最重要的抽象**。

### 明确一个协议，而不是一个实现

```python
from typing import Protocol
from fastapi import Request

class ResourceGetter(Protocol):
    def __call__(self, request: Request):
        ...
```

### 约束

- 输入：`Request`
    
- 输出：任意对象
    
- 禁止：抛权限异常
    

👉 **这是“事实提供者”，不是“决策者”**

---

# 七、核心设计四：permission_required 依赖工厂（dependency.py）

permission_required 通过“资源是否存在”自然区分接口级 RBAC 与数据级 ABAC，而无需引入额外模式或分支，是一种低心智负担、强约束、易扩展的工程化设计。

这是你整个依赖包的**唯一入口 API**。

### 对外暴露的使用方式（设计重点）

```python
Depends(
    permission_required(
        resource=get_order_resource,
        action="read"
    )
)
```

### 内部职责拆分（必须遵守）

```text
permission_required
 ├── 调用认证回调（获取 sub）
 ├── 解析接口资源（obj）
 ├── 调用 ResourceGetter（获取属性）
 ├── 构造 Casbin Request
 └── 执行 enforce
```

### 关键点（非常重要）

- action ≠ HTTP Method
    
- action 是**业务语义**（read / write / delete）

permission_required 通过“资源是否存在”自然区分接口级 RBAC 与数据级 ABAC，而无需引入额外模式或分支，是一种低心智负担、强约束、易扩展的工程化设计。

---

# 八、与认证系统的解耦设计（关键）

你的依赖**绝不能强依赖 JWT 实现**。

### 正确方式：注入用户解析函数

```python
def permission_required(
    *,
    get_subject: Callable,
    resource: ResourceGetter | None,
    action: str
):
    ...
    if resource is None:
        owner = None
    else:
        obj_instance = resource(request)
        owner = getattr(obj_instance, config.owner_field, None)
    ...

```

这样你可以支持：

- JWT
    
- OAuth2
    
- 内部服务鉴权
    
- 单元测试 mock
    

---

# 九、Casbin Model 的“模板化”设计

你可以内置一个**推荐模型**，但允许覆盖。

```ini
[request_definition]
r = sub, obj, act, owner

[matchers]
m = g(r.sub, p.sub) &&
    keyMatch2(r.obj, p.obj) &&
    r.act == p.act &&
    (r.sub == r.owner || p.sub == "admin")
```

### 架构原则

> **业务项目不直接编辑 matcher，只能通过配置选择模型**

---

# 十、集成到业务项目的标准流程（用户视角）

### 1️⃣ 安装依赖

```bash
pip install fastapi-casbin-acl
```

### 2️⃣ 初始化（启动时）

```python
acl.init(
    model_path="conf/casbin_model.conf",
    adapter=db_adapter
)
```

### 3️⃣ 路由中使用

```python
@router.get(
    "/orders/{order_id}",
    dependencies=[
        Depends(
            permission_required(
                get_subject=get_current_user,
                resource=get_order_resource,
                action="read"
            )
        )
    ]
)
def get_order(order_id: int):
    ...
```
