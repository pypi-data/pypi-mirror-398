"""
Tests for fastapi_casbin_acl.router module.
"""
import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
import casbin
import os
from fastapi_casbin_acl.enforcer import acl
from fastapi_casbin_acl.config import ACLConfig
from fastapi_casbin_acl.router import casbin_router


@pytest.fixture
async def setup_acl_for_router():
    """Setup ACL for router tests."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)
    config = ACLConfig(default_model="abac")
    await acl.init(adapter=adapter, config=config)
    yield acl
    acl._enforcers = {}
    acl._adapters = {}
    acl._config = None
    acl._initialized = False


@pytest.fixture
async def app_with_router(setup_acl_for_router):
    """Create FastAPI app with casbin router."""
    app = FastAPI()
    app.include_router(casbin_router)
    return app


@pytest.fixture
async def client(app_with_router):
    """Create test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_router), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_policies(client):
    """Test listing all policies."""
    response = await client.get("/policies")
    assert response.status_code == 200
    data = response.json()
    assert "policies" in data
    assert isinstance(data["policies"], list)


@pytest.mark.asyncio
async def test_create_policy(client):
    """Test creating a new policy."""
    policy_data = {"sub": "test_user", "obj": "/test", "act": "read"}
    response = await client.post("/policies", json=policy_data)
    assert response.status_code == 201
    data = response.json()
    assert data["sub"] == "test_user"
    assert data["obj"] == "/test"
    assert data["act"] == "read"


@pytest.mark.asyncio
async def test_create_duplicate_policy(client):
    """Test creating a duplicate policy returns 400."""
    policy_data = {"sub": "test_user", "obj": "/test", "act": "read"}
    # Create first time
    await client.post("/policies", json=policy_data)
    # Try to create again
    response = await client.post("/policies", json=policy_data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_policy(client):
    """Test deleting a policy."""
    # First create a policy
    policy_data = {"sub": "delete_user", "obj": "/delete", "act": "write"}
    await client.post("/policies", json=policy_data)

    # Then delete it - use params or content for DELETE
    response = await client.request("DELETE", "/policies", json=policy_data)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_nonexistent_policy(client):
    """Test deleting a non-existent policy returns 404."""
    policy_data = {"sub": "nonexistent", "obj": "/nonexistent", "act": "read"}
    response = await client.request("DELETE", "/policies", json=policy_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_roles(client):
    """Test getting roles for a user."""
    # charlie has admin role in policy.csv
    response = await client.get("/policies/roles/charlie")
    assert response.status_code == 200
    data = response.json()
    assert "roles" in data
    assert isinstance(data["roles"], list)


@pytest.mark.asyncio
async def test_create_role_binding(client):
    """Test creating a role binding."""
    binding_data = {"user": "new_user", "role": "editor"}
    response = await client.post("/policies/roles", json=binding_data)
    assert response.status_code == 201
    data = response.json()
    assert data["user"] == "new_user"
    assert data["role"] == "editor"


@pytest.mark.asyncio
async def test_create_duplicate_role_binding(client):
    """Test creating a duplicate role binding returns 400."""
    binding_data = {"user": "duplicate_user", "role": "editor"}
    # Create first time
    await client.post("/policies/roles", json=binding_data)
    # Try to create again
    response = await client.post("/policies/roles", json=binding_data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_role_binding(client):
    """Test deleting a role binding."""
    # First create a role binding
    binding_data = {"user": "delete_user", "role": "viewer"}
    await client.post("/policies/roles", json=binding_data)

    # Then delete it
    response = await client.request("DELETE", "/policies/roles", json=binding_data)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_nonexistent_role_binding(client):
    """Test deleting a non-existent role binding returns 404."""
    binding_data = {"user": "nonexistent", "role": "role"}
    response = await client.request("DELETE", "/policies/roles", json=binding_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_router_uninitialized_acl():
    """Test router endpoints fail when ACL is not initialized."""
    # Reset ACL
    acl._enforcers = {}
    acl._adapters = {}
    acl._config = None
    acl._initialized = False

    app = FastAPI()
    app.include_router(casbin_router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/policies")
        assert response.status_code == 500
        assert "not initialized" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_router_list_policies_exception_handling(setup_acl_for_router, monkeypatch):
    """Test list_policies exception handling."""
    app = FastAPI()
    app.include_router(casbin_router)

    # Mock enforcer.get_policy to raise exception
    def mock_get_policy():
        raise Exception("Mock error")

    monkeypatch.setattr(acl.enforcer, "get_policy", mock_get_policy)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/policies")
        assert response.status_code == 500
        assert "Failed to list policies" in response.json()["detail"]


@pytest.mark.asyncio
async def test_router_create_policy_exception_handling(setup_acl_for_router, monkeypatch):
    """Test create_policy exception handling."""
    app = FastAPI()
    app.include_router(casbin_router)

    # Mock enforcer.add_policy to raise exception
    async def mock_add_policy(*args):
        raise Exception("Mock error")

    monkeypatch.setattr(acl.enforcer, "add_policy", mock_add_policy)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        policy_data = {"sub": "test", "obj": "/test", "act": "read"}
        response = await client.post("/policies", json=policy_data)
        assert response.status_code == 500
        assert "Failed to create policy" in response.json()["detail"]


@pytest.mark.asyncio
async def test_router_delete_policy_exception_handling(setup_acl_for_router, monkeypatch):
    """Test delete_policy exception handling."""
    app = FastAPI()
    app.include_router(casbin_router)

    # Mock enforcer.remove_policy to raise exception
    async def mock_remove_policy(*args):
        raise Exception("Mock error")

    monkeypatch.setattr(acl.enforcer, "remove_policy", mock_remove_policy)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        policy_data = {"sub": "test", "obj": "/test", "act": "read"}
        response = await client.request("DELETE", "/policies", json=policy_data)
        assert response.status_code == 500
        assert "Failed to delete policy" in response.json()["detail"]


@pytest.mark.asyncio
async def test_router_get_user_roles_exception_handling(setup_acl_for_router, monkeypatch):
    """Test get_user_roles exception handling."""
    app = FastAPI()
    app.include_router(casbin_router)

    # Mock enforcer.get_roles_for_user to raise exception
    async def mock_get_roles_for_user(*args):
        raise Exception("Mock error")

    monkeypatch.setattr(acl.enforcer, "get_roles_for_user", mock_get_roles_for_user)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/policies/roles/testuser")
        assert response.status_code == 500
        assert "Failed to get user roles" in response.json()["detail"]


@pytest.mark.asyncio
async def test_router_create_role_binding_exception_handling(
    setup_acl_for_router, monkeypatch
):
    """Test create_role_binding exception handling."""
    app = FastAPI()
    app.include_router(casbin_router)

    # Mock enforcer.add_role_for_user to raise exception
    async def mock_add_role_for_user(*args):
        raise Exception("Mock error")

    monkeypatch.setattr(acl.enforcer, "add_role_for_user", mock_add_role_for_user)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        binding_data = {"user": "test", "role": "role"}
        response = await client.post("/policies/roles", json=binding_data)
        assert response.status_code == 500
        assert "Failed to create role binding" in response.json()["detail"]


@pytest.mark.asyncio
async def test_router_delete_role_binding_exception_handling(
    setup_acl_for_router, monkeypatch
):
    """Test delete_role_binding exception handling."""
    app = FastAPI()
    app.include_router(casbin_router)

    # Mock enforcer.delete_role_for_user to raise exception
    async def mock_delete_role_for_user(*args):
        raise Exception("Mock error")

    monkeypatch.setattr(acl.enforcer, "delete_role_for_user", mock_delete_role_for_user)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        binding_data = {"user": "test", "role": "role"}
        response = await client.request("DELETE", "/policies/roles", json=binding_data)
        assert response.status_code == 500
        assert "Failed to delete role binding" in response.json()["detail"]
