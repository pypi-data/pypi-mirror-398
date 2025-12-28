"""
Tests for fastapi_casbin_acl.router.__init__ module.
"""
import pytest
from fastapi_casbin_acl.router import casbin_router


def test_router_import():
    """Test that casbin_router can be imported."""
    assert casbin_router is not None
    assert hasattr(casbin_router, 'routes')

