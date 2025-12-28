"""
Tests for fastapi_casbin_acl.enforcer module.
"""
import pytest
import os
import casbin
from fastapi_casbin_acl.enforcer import acl, AsyncEnforcerManager
from fastapi_casbin_acl.config import ACLConfig
from fastapi_casbin_acl.exceptions import ACLNotInitialized, ConfigError


@pytest.fixture
def reset_acl():
    """Reset ACL singleton state before and after test."""
    # Reset before
    acl._enforcers = {}
    acl._adapters = {}
    acl._config = None
    acl._initialized = False
    yield
    # Reset after
    acl._enforcers = {}
    acl._adapters = {}
    acl._config = None
    acl._initialized = False


@pytest.mark.asyncio
async def test_init_with_default_config(reset_acl):
    """Test init with default config creation."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)

    # Call init without config - should create default
    await acl.init(adapter=adapter)

    assert acl._config is not None
    assert acl._initialized is True
    assert acl.config.default_model == "abac"  # Default is ABAC


@pytest.mark.asyncio
async def test_init_with_specific_models(reset_acl):
    """Test init with specific models list."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)

    # Initialize with both models
    await acl.init(adapter=adapter, models=["rbac", "abac"])

    assert acl.is_model_initialized("rbac")
    assert acl.is_model_initialized("abac")
    assert len(acl.list_initialized_models()) == 2


@pytest.mark.asyncio
async def test_init_with_external_model_path(reset_acl):
    """Test init registers external model when external_model_path is provided."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)

    # Use RBAC conf as external model
    from fastapi_casbin_acl.models import get_model_path
    external_path = get_model_path("rbac")
    config = ACLConfig(external_model_path=external_path, default_model="external")

    await acl.init(adapter=adapter, config=config)

    assert acl.is_model_initialized("external")


@pytest.mark.asyncio
async def test_get_enforcer_not_initialized(reset_acl):
    """Test get_enforcer raises ACLNotInitialized when model not initialized."""
    with pytest.raises(ACLNotInitialized, match="not initialized"):
        acl.get_enforcer("rbac")


@pytest.mark.asyncio
async def test_enforcer_property_not_initialized(reset_acl):
    """Test enforcer property raises ACLNotInitialized when not initialized."""
    with pytest.raises(ACLNotInitialized, match="not initialized"):
        _ = acl.enforcer


@pytest.mark.asyncio
async def test_config_property_not_initialized(reset_acl):
    """Test config property raises ACLNotInitialized when not initialized."""
    with pytest.raises(ACLNotInitialized, match="not initialized"):
        _ = acl.config


@pytest.mark.asyncio
async def test_load_policy(reset_acl):
    """Test load_policy method."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)
    config = ACLConfig(default_model="abac")

    await acl.init(adapter=adapter, config=config)

    # Load policy should not raise
    await acl.load_policy()

    # Verify policies are loaded
    enforcer = acl.get_enforcer("abac")
    policies = enforcer.get_policy()
    assert len(policies) > 0


@pytest.mark.asyncio
async def test_load_policy_specific_model(reset_acl):
    """Test load_policy for a specific model."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)

    await acl.init(adapter=adapter, models=["rbac", "abac"])

    # Load policy for specific model should not raise
    await acl.load_policy("rbac")


@pytest.mark.asyncio
async def test_save_policy(reset_acl):
    """Test save_policy method."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)
    config = ACLConfig(default_model="abac")

    await acl.init(adapter=adapter, config=config)

    # Save policy should not raise
    await acl.save_policy()


@pytest.mark.asyncio
async def test_enforce_method(reset_acl):
    """Test enforce method works correctly."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)
    config = ACLConfig(default_model="abac")

    await acl.init(adapter=adapter, config=config)

    # Test enforce - ABAC model requires 4 args (sub, obj, act, owner)
    assert acl.enforce("abac", "alice", "/public", "read", "") is True
    assert acl.enforce("abac", "eve", "/public", "read", "") is False


@pytest.mark.asyncio
async def test_enforce_rbac_model(reset_acl):
    """Test enforce method with RBAC model."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)

    await acl.init(adapter=adapter, models=["rbac"])

    # Test enforce - RBAC model requires 3 args (sub, obj, act)
    assert acl.enforce("rbac", "alice", "/public", "read") is True


@pytest.mark.asyncio
async def test_init_model_at_runtime(reset_acl):
    """Test init_model to add new model at runtime."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)

    # First init with ABAC only
    await acl.init(adapter=adapter, models=["abac"])
    assert not acl.is_model_initialized("rbac")

    # Add RBAC at runtime
    await acl.init_model("rbac")
    assert acl.is_model_initialized("rbac")


@pytest.mark.asyncio
async def test_singleton_pattern(reset_acl):
    """Test that AsyncEnforcerManager is a singleton."""
    manager1 = AsyncEnforcerManager()
    manager2 = AsyncEnforcerManager()

    assert manager1 is manager2
    assert manager1 is acl
