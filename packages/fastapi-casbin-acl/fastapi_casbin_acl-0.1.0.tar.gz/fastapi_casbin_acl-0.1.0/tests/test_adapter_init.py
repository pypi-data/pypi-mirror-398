"""
Tests for fastapi_casbin_acl.adapter.__init__ module.
"""
import pytest
from fastapi_casbin_acl.adapter import CasbinRule, SQLModelAdapter


def test_adapter_imports():
    """Test that adapter module exports are available."""
    assert CasbinRule is not None
    assert SQLModelAdapter is not None


def test_adapter_casbin_rule_import():
    """Test CasbinRule can be imported from adapter."""
    from fastapi_casbin_acl.adapter import CasbinRule
    assert CasbinRule.__name__ == "CasbinRule"


def test_adapter_sqlmodel_adapter_import():
    """Test SQLModelAdapter can be imported from adapter."""
    from fastapi_casbin_acl.adapter import SQLModelAdapter
    assert SQLModelAdapter.__name__ == "SQLModelAdapter"

