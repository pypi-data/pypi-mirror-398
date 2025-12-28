import pytest
import os
import casbin
from fastapi_casbin_acl.enforcer import acl
from fastapi_casbin_acl.config import ACLConfig


@pytest.fixture(scope="function")
async def setup_acl():
    """
    Setup ACL with async file adapter for testing.
    """
    # Path to policy file
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")

    # Initialize ACL with AsyncFileAdapter
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)
    config = ACLConfig(default_model="abac")
    await acl.init(adapter=adapter, config=config)

    yield acl

    # Teardown: reset singleton state (re-init will overwrite on next test)
    acl._enforcers = {}
    acl._adapters = {}
    acl._config = None
    acl._initialized = False
