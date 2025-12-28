# FastAPI Casbin ACL

A robust, production-ready FastAPI infrastructure dependency for permissions management, providing RBAC and ABAC support via Casbin.

## Features

- **Zero Business Logic Intrusion**: Decoupled from your business logic.
- **Strong Constraints, Few Conventions**: Enforces a consistent permission model (RBAC + ABAC).
- **Pluggable Authentication**: Works with any authentication system (JWT, OAuth2, Session) via dependency injection.
- **Casbin Lifecycle Management**: Centralized management of the Casbin Enforcer.
- **Async Support**: Fully compatible with FastAPI's async nature.
- **Multiple Model Support**: Support for multiple permission models (RBAC, ABAC, custom) with per-route model selection.
- **Model Registry**: Built-in model registry with automatic registration of built-in models.

## Installation

```bash
pip install fastapi-casbin-acl
```

## Quick Start

### 1. Initialize

In your startup logic (e.g., `main.py`):

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_casbin_acl.enforcer import acl
from fastapi_casbin_acl.config import ACLConfig
from fastapi_casbin_acl.adapter import SQLModelAdapter
from sqlalchemy.ext.asyncio import AsyncSession

# Example: Using SQLModel adapter
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database connection
    # ... your database setup ...
    
    # Initialize Casbin ACL
    adapter = SQLModelAdapter(AsyncSessionLocal)
    config = ACLConfig(default_model="abac")  # Default model: "abac" or "rbac"
    await acl.init(adapter=adapter, config=config)
    
    # Initialize policies (optional)
    # await init_policies()
    
    yield
    
    # Cleanup
    # ... your cleanup logic ...

app = FastAPI(lifespan=lifespan)
```

**Multiple Models Support**:

```python
# Initialize multiple models at once
await acl.init(
    adapter=adapter,
    models=["rbac", "abac"],  # Initialize both models
    config=config
)

# Or add models at runtime
await acl.init_model("custom_model", adapter=adapter)
```

### 2. Define Subject & Resource

Define how to get the current user (subject) and how to resolve resources (for ABAC).

```python
from fastapi import Request, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

# 1. Subject Provider (Authentication)
async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Get current user from request (e.g., JWT token, session)"""
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return None
    
    # Query user from database
    # ... your user query logic ...
    return user

async def get_subject_from_user(user = Depends(get_current_user)) -> str | None:
    """Extract subject (user ID) for permission checking"""
    if user is None:
        return None
    return str(user.id)  # Return user ID as string

# 2. Resource Getter (Optional, for ABAC)
class Order:
    def __init__(self, id, owner_id):
        self.id = id
        self.owner_id = owner_id
    
    def get_owner_sub(self) -> str | None:
        """Return owner ID for ABAC ownership check"""
        return str(self.owner_id) if self.owner_id else None

async def get_order_resource(request: Request) -> Order | None:
    """Fetch resource from database based on path parameters"""
    order_id = request.path_params.get("id")
    if not order_id:
        return None
    
    # Query order from database
    # ... your order query logic ...
    return Order(id=order_id, owner_id="user_123")
```

### 3. Protect Routes

Use `permission_required` in your route dependencies.

#### RBAC (Interface Level)

```python
from fastapi_casbin_acl.dependency import permission_required

@app.get(
    "/dashboard",
    dependencies=[
        Depends(permission_required(
            get_subject=get_subject_from_user,
            action="read",
            model="rbac"  # Use RBAC model
        ))
    ]
)
async def dashboard():
    return {"data": "..."}
```

#### ABAC (Data Level)

Enforces that the user is the **owner** of the resource OR has the **admin** role.

```python
@app.get(
    "/orders/{id}",
    dependencies=[
        Depends(permission_required(
            get_subject=get_subject_from_user,
            resource=get_order_resource,  # Inject resource getter
            action="read",
            model="abac"  # Use ABAC model for ownership check
        ))
    ]
)
async def get_order(id: str):
    return {"order": id}
```

#### Custom Owner Getter

For more flexibility, you can provide a custom `owner_getter`:

```python
def get_order_owner(order: Order, request: Request | None = None) -> str | None:
    """Custom owner extraction logic"""
    if hasattr(order, "get_owner_sub"):
        return order.get_owner_sub()
    return str(order.owner_id) if order.owner_id else None

@app.put(
    "/orders/{id}",
    dependencies=[
        Depends(permission_required(
            get_subject=get_subject_from_user,
            resource=get_order_resource,
            owner_getter=get_order_owner,  # Custom owner getter
            action="write",
            model="abac"
        ))
    ]
)
async def update_order(id: str):
    return {"order": id, "status": "updated"}
```

## Model Management

### Built-in Models

The package provides two built-in models that are automatically registered:

- **`rbac`**: Role-Based Access Control (3 args: sub, obj, act)
- **`abac`**: Attribute-Based Access Control (4 args: sub, obj, act, owner)

### Model Registry

You can register custom models using the `ModelRegistry`:

```python
from fastapi_casbin_acl.registry import model_registry

# Register a custom model
model_registry.register("custom_model", "/path/to/custom.conf")

# List all registered models
models = model_registry.list_models()  # ['rbac', 'abac', 'custom_model']

# Get model path
path = model_registry.get_path("abac")
```

### Using Different Models per Route

You can use different permission models for different routes:

```python
# Route 1: Use RBAC model
@app.get("/public")
async def public_endpoint(
    _=Depends(permission_required(
        get_subject=get_subject_from_user,
        action="read",
        model="rbac"
    ))
):
    return {"message": "public"}

# Route 2: Use ABAC model
@app.get("/orders/{id}")
async def order_endpoint(
    _=Depends(permission_required(
        get_subject=get_subject_from_user,
        resource=get_order_resource,
        action="read",
        model="abac"
    ))
):
    return {"order": "..."}
```

## Configuration

You can customize the ACL behavior by passing a config object during initialization.

```python
from fastapi_casbin_acl.config import ACLConfig

config = ACLConfig(
    default_model="abac",           # Default model name (default: "abac")
    external_model_path="/path/to/custom.conf",  # Register external model
    admin_role="superuser"          # Change default admin role from 'admin'
)

await acl.init(adapter=adapter, config=config)
```

If `external_model_path` is provided, it will be automatically registered with the name `"external"`.

## Working with Enforcers

### Get Enforcer for Specific Model

```python
# Get enforcer for a specific model
enforcer = acl.get_enforcer("abac")

# Add policies
await enforcer.add_policy("admin", "/api/users/*", "read")
await enforcer.add_grouping_policy("user_1", "admin")

# Save policies
await acl.save_policy("abac")  # Save specific model
await acl.save_policy()        # Save all models
```

### Check Initialized Models

```python
# Check if a model is initialized
if acl.is_model_initialized("abac"):
    enforcer = acl.get_enforcer("abac")

# List all initialized models
models = acl.list_initialized_models()  # ['rbac', 'abac']
```

## Exception Handling

The dependency raises `Unauthorized` (401) or `Forbidden` (403) exceptions. You should handle them in your application.

```python
from fastapi.responses import JSONResponse
from fastapi_casbin_acl.exceptions import Unauthorized, Forbidden

@app.exception_handler(Unauthorized)
async def unauthorized_handler(request: Request, exc: Unauthorized):
    return JSONResponse(
        status_code=401,
        content={"detail": "Unauthorized: Please provide valid authentication"}
    )

@app.exception_handler(Forbidden)
async def forbidden_handler(request: Request, exc: Forbidden):
    return JSONResponse(
        status_code=403,
        content={"detail": "Permission Denied"}
    )
```

## Built-in Models

### ABAC Model (Default)

The package comes with a built-in Casbin model optimized for RBAC + ABAC:

```ini
[request_definition]
r = sub, obj, act, owner

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = (p.sub == "" || p.sub == "*" || g(r.sub, p.sub)) && keyMatch2(r.obj, p.obj) && r.act == p.act && (r.owner == "" || r.sub == r.owner || g(r.sub, "admin"))
```

- **RBAC**: When `owner` is empty (`""`), matches `sub`, `obj`, `act` against policy `p`. Supports wildcard policies (`p, *, /path/*, action`).
- **ABAC**: When `owner` is provided, checks if `r.sub == r.owner` (Resource Ownership). Requires a matching policy for the resource path.
- **Admin Override**: If `sub` has role `admin` (via `g, sub, admin`), access is allowed regardless of ownership.

### RBAC Model

The RBAC model is simpler and only supports role-based access control:

```ini
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = (p.sub == "" || p.sub == "*" || g(r.sub, p.sub)) && keyMatch2(r.obj, p.obj) && r.act == p.act
```

## Complete Example

See the `examples/` directory for a complete working example with:

- User and Order management
- RBAC and ABAC permission checks
- Database integration with SQLModel
- Frontend interface

To run the example:

```bash
cd examples
python run.py
# or
uvicorn main:app --reload
```

## API Reference

### `permission_required`

Factory function that creates a permission dependency.

**Parameters**:
- `get_subject`: Callable that returns the subject (user ID/username) for permission checking
- `resource`: Optional `ResourceGetter` to retrieve the resource object for ABAC
- `action`: The action being performed (e.g., "read", "write", "delete")
- `owner_getter`: Optional `OwnerGetter` to extract owner from resource object
- `model`: Model name to use (default: "abac"). Must be initialized before use.

**Returns**: FastAPI dependency function

### `ACLConfig`

Configuration class for ACL system.

**Fields**:
- `default_model`: Default model name (default: "abac")
- `external_model_path`: Optional path to external model file (registered as "external")
- `admin_role`: Role name that bypasses ownership checks (default: "admin")

### `ModelRegistry`

Registry for managing Casbin permission models.

**Methods**:
- `register(name, path)`: Register a new model
- `unregister(name)`: Unregister a model
- `get_path(name)`: Get path to model file
- `is_registered(name)`: Check if model is registered
- `list_models()`: List all registered model names

### `AsyncEnforcerManager`

Singleton manager for multiple Casbin AsyncEnforcer instances.

**Methods**:
- `init(adapter, models=None, config=None)`: Initialize enforcers
- `get_enforcer(model_name)`: Get enforcer for specific model
- `enforce(model_name, *args)`: Execute enforce with specific model
- `init_model(model_name, adapter=None)`: Initialize a model at runtime
- `is_model_initialized(model_name)`: Check if model is initialized
- `list_initialized_models()`: List all initialized models
- `load_policy(model_name=None)`: Reload policies
- `save_policy(model_name=None)`: Save policies

## License

MIT
