"""
Optional FastAPI router for Casbin policy management.
"""
from .policy import casbin_router

__all__ = ["casbin_router"]

