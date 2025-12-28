"""
FastAPI Casbin ACL - Access Control Layer for FastAPI applications.

This package provides a robust, production-ready infrastructure dependency
for permissions management with RBAC and ABAC support via Casbin.

Features:
- Multiple permission models: RBAC and ABAC out of the box
- Custom model support via ModelRegistry
- Per-route model selection
- Flexible owner extraction for ABAC
"""

from .enforcer import acl, AsyncEnforcerManager
from .config import ACLConfig
from .registry import ModelRegistry, model_registry
from .dependency import permission_required
from .resource import ResourceGetter, OwnerGetter
from .exceptions import (
    ACLException,
    ACLNotInitialized,
    ConfigError,
    Unauthorized,
    Forbidden,
)

__all__ = [
    # Core
    "acl",
    "AsyncEnforcerManager",
    # Configuration
    "ACLConfig",
    # Registry
    "ModelRegistry",
    "model_registry",
    # Dependency
    "permission_required",
    # Resource utilities
    "ResourceGetter",
    "OwnerGetter",
    # Exceptions
    "ACLException",
    "ACLNotInitialized",
    "ConfigError",
    "Unauthorized",
    "Forbidden",
]

__version__ = "0.1.0"
