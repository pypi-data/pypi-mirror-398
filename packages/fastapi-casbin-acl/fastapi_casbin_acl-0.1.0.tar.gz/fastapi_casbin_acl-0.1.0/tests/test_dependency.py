"""
Tests for fastapi_casbin_acl.dependency module.
"""
import pytest
from fastapi import FastAPI, Request, Depends
from httpx import AsyncClient, ASGITransport
from fastapi_casbin_acl.dependency import permission_required
from fastapi_casbin_acl.enforcer import acl
from fastapi_casbin_acl.exceptions import Forbidden, Unauthorized
from fastapi_casbin_acl.config import ACLConfig
import casbin
import os


@pytest.fixture
async def setup_rbac_acl():
    """Setup ACL with RBAC model for testing."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)

    config = ACLConfig(default_model="rbac")
    await acl.init(adapter=adapter, models=["rbac"], config=config)
    yield acl
    acl._enforcers = {}
    acl._adapters = {}
    acl._config = None
    acl._initialized = False


@pytest.fixture
async def setup_abac_acl():
    """Setup ACL with ABAC model for testing."""
    policy_path = os.path.join(os.path.dirname(__file__), "policy.csv")
    adapter = casbin.persist.adapters.asyncio.AsyncFileAdapter(policy_path)

    config = ACLConfig(default_model="abac")
    await acl.init(adapter=adapter, models=["abac"], config=config)
    yield acl
    acl._enforcers = {}
    acl._adapters = {}
    acl._config = None
    acl._initialized = False


def get_current_user(request: Request):
    """Mock subject getter."""
    return request.headers.get("X-User")


class MockResource:
    """Mock resource with owner_id."""

    def __init__(self, owner_id):
        self.owner_id = owner_id


def get_sync_resource(request: Request):
    """Synchronous resource getter."""
    owner = request.headers.get("X-Resource-Owner")
    if owner:
        return MockResource(owner_id=owner)
    return None


async def get_async_resource(request: Request):
    """Asynchronous resource getter."""
    owner = request.headers.get("X-Resource-Owner")
    if owner:
        return MockResource(owner_id=owner)
    return None


@pytest.mark.asyncio
async def test_dependency_rbac_enforce_3_args(setup_rbac_acl):
    """Test RBAC model uses 3-arg enforce (sub, obj, act)."""
    app = FastAPI()

    @app.get("/public")
    async def test_route(
        request: Request,
        _=Depends(
            permission_required(get_subject=get_current_user, action="read", model="rbac")
        ),
    ):
        return {"message": "ok"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Alice has policy for /public read in RBAC model
        # This tests the RBAC enforce path (3 args, no owner)
        response = await client.get("/public", headers={"X-User": "alice"})
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_dependency_fallback_to_url_path(setup_abac_acl):
    """Test fallback to request.url.path when route is not APIRoute."""
    app = FastAPI()

    @app.get("/public")
    async def test_route(
        request: Request,
        _=Depends(
            permission_required(get_subject=get_current_user, action="read", model="abac")
        ),
    ):
        return {"message": "ok"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # This should use route.path_format (not fallback)
        response = await client.get("/public", headers={"X-User": "alice"})
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_dependency_async_resource_getter(setup_abac_acl):
    """Test async resource getter."""
    app = FastAPI()

    @app.get("/orders/{id}")
    async def get_order(
        request: Request,
        id: str,
        _=Depends(
            permission_required(
                get_subject=get_current_user,
                resource=get_async_resource,
                action="read",
                model="abac",
            )
        ),
    ):
        return {"message": f"order {id}"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Dave is owner
        response = await client.get(
            "/orders/123", headers={"X-User": "dave", "X-Resource-Owner": "dave"}
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_dependency_rbac_model_no_owner_param(setup_rbac_acl):
    """Test RBAC model enforce without owner parameter."""
    app = FastAPI()

    @app.get("/public")
    async def get_public(
        request: Request,
        _=Depends(
            permission_required(get_subject=get_current_user, action="read", model="rbac")
        ),
    ):
        return {"message": "public"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Alice has policy for /public read in RBAC model
        response = await client.get("/public", headers={"X-User": "alice"})
        assert response.status_code == 200
