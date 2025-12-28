import pytest
from fastapi import FastAPI, Depends, Request, status
from httpx import AsyncClient
from fastapi_casbin_acl.dependency import permission_required
from fastapi_casbin_acl.resource import ResourceGetter
from fastapi_casbin_acl.enforcer import acl


# Mock Subject Dependency
def get_current_user(request: Request):
    return request.headers.get("X-User")


# Mock Resource with get_owner_sub method for ABAC
class Order:
    def __init__(self, owner_id):
        self.owner_id = owner_id

    def get_owner_sub(self) -> str:
        """Return the owner identifier for ABAC checks."""
        return self.owner_id


def get_order_resource(request: Request):
    # Simulate fetching resource based on ID in path, but here we just return a mock
    # In real app: id = request.path_params['id']
    user_header = request.headers.get("X-Resource-Owner")
    if user_header:
        return Order(owner_id=user_header)
    return None


app = FastAPI()


# 1. RBAC Route
@app.get(
    "/public",
    dependencies=[
        Depends(
            permission_required(
                get_subject=get_current_user, action="read", model="abac"
            )
        )
    ],
)
def get_public():
    return {"message": "public"}


# 2. ABAC Route
# Matches policy: (r.sub == r.owner || p.sub == "admin")
# We don't have specific policies for /orders, so it relies purely on owner check or admin role.
@app.get(
    "/orders/{id}",
    dependencies=[
        Depends(
            permission_required(
                get_subject=get_current_user,
                resource=get_order_resource,
                action="read",
                model="abac",
            )
        )
    ],
)
def get_order(id: str):
    return {"message": f"order {id}"}


# Add exception handlers for the test app
from fastapi.responses import JSONResponse
from fastapi_casbin_acl.exceptions import Unauthorized, Forbidden


@app.exception_handler(Unauthorized)
def unauthorized_handler(request, exc):
    return JSONResponse(status_code=401, content={"message": "Unauthorized"})


@app.exception_handler(Forbidden)
def forbidden_handler(request, exc):
    return JSONResponse(status_code=403, content={"message": "Forbidden"})


@pytest.fixture
async def client():
    from httpx import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_rbac_allow(setup_acl, client):
    # Alice has policy for /public read
    response = await client.get("/public", headers={"X-User": "alice"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rbac_deny(setup_acl, client):
    # Eve has no policy
    response = await client.get("/public", headers={"X-User": "eve"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_abac_owner_allow(setup_acl, client):
    # Dave is owner of the order
    response = await client.get(
        "/orders/123", headers={"X-User": "dave", "X-Resource-Owner": "dave"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_abac_non_owner_deny(setup_acl, client):
    # Eve is not owner
    response = await client.get(
        "/orders/123", headers={"X-User": "eve", "X-Resource-Owner": "dave"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_abac_admin_allow(setup_acl, client):
    # Charlie has admin role (g, charlie, admin)
    # Admin bypasses ownership
    response = await client.get(
        "/orders/123", headers={"X-User": "charlie", "X-Resource-Owner": "dave"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_unauthorized_no_user(setup_acl, client):
    # No user header -> get_current_user returns None -> Unauthorized
    response = await client.get("/public")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthorized_handled(setup_acl, client):
    response = await client.get("/public")
    assert response.status_code == 401
