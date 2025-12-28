"""
FastAPI router for Casbin policy CRUD operations.

This router provides a REST API for managing Casbin policies and role bindings.
It is optional and can be included in the FastAPI application if needed.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..enforcer import acl
from ..exceptions import ACLNotInitialized


# Request/Response models
class PolicyCreate(BaseModel):
    """Request model for creating a policy."""
    sub: str = Field(..., description="Subject (user or role)")
    obj: str = Field(..., description="Object (resource path)")
    act: str = Field(..., description="Action (e.g., read, write, delete)")


class PolicyResponse(BaseModel):
    """Response model for a policy."""
    sub: str
    obj: str
    act: str


class RoleBindingCreate(BaseModel):
    """Request model for creating a role binding."""
    user: str = Field(..., description="User identifier")
    role: str = Field(..., description="Role name")


class RoleBindingResponse(BaseModel):
    """Response model for a role binding."""
    user: str
    role: str


class PolicyListResponse(BaseModel):
    """Response model for listing policies."""
    policies: List[PolicyResponse]


class RoleListResponse(BaseModel):
    """Response model for listing roles."""
    roles: List[str]


# Router
casbin_router = APIRouter(prefix="/policies", tags=["Casbin Policy"])


def _ensure_initialized():
    """Dependency to ensure ACL is initialized."""
    try:
        _ = acl.config
        _ = acl.enforcer
    except ACLNotInitialized:
        raise HTTPException(
            status_code=500,
            detail="ACL system is not initialized. Call await acl.init() first."
        )


@casbin_router.get("", response_model=PolicyListResponse)
async def list_policies(_: None = Depends(_ensure_initialized)):
    """
    List all policies.
    
    Returns all policy rules (p) from the Casbin model.
    """
    try:
        policies = acl.enforcer.get_policy()
        policy_list = [
            PolicyResponse(sub=p[0], obj=p[1], act=p[2])
            for p in policies
        ]
        return PolicyListResponse(policies=policy_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list policies: {str(e)}")


@casbin_router.post("", response_model=PolicyResponse, status_code=201)
async def create_policy(
    policy: PolicyCreate,
    _: None = Depends(_ensure_initialized)
):
    """
    Create a new policy.
    
    Adds a policy rule to the Casbin model.
    """
    try:
        # Add policy using async method
        added = await acl.enforcer.add_policy(policy.sub, policy.obj, policy.act)
        if not added:
            raise HTTPException(
                status_code=400,
                detail="Policy already exists or failed to add"
            )
        return PolicyResponse(sub=policy.sub, obj=policy.obj, act=policy.act)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")


@casbin_router.delete("", status_code=204)
async def delete_policy(
    policy: PolicyCreate,
    _: None = Depends(_ensure_initialized)
):
    """
    Delete a policy.
    
    Removes a policy rule from the Casbin model.
    """
    try:
        removed = await acl.enforcer.remove_policy(policy.sub, policy.obj, policy.act)
        if not removed:
            raise HTTPException(status_code=404, detail="Policy not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete policy: {str(e)}")


# Role management endpoints
@casbin_router.get("/roles/{user}", response_model=RoleListResponse)
async def get_user_roles(
    user: str,
    _: None = Depends(_ensure_initialized)
):
    """
    Get all roles for a user.
    
    Returns the list of roles assigned to the specified user.
    """
    try:
        roles = await acl.enforcer.get_roles_for_user(user)
        return RoleListResponse(roles=roles if roles else [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user roles: {str(e)}")


@casbin_router.post("/roles", response_model=RoleBindingResponse, status_code=201)
async def create_role_binding(
    binding: RoleBindingCreate,
    _: None = Depends(_ensure_initialized)
):
    """
    Create a role binding.
    
    Assigns a role to a user.
    """
    try:
        added = await acl.enforcer.add_role_for_user(binding.user, binding.role)
        if not added:
            raise HTTPException(
                status_code=400,
                detail="Role binding already exists or failed to add"
            )
        return RoleBindingResponse(user=binding.user, role=binding.role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create role binding: {str(e)}")


@casbin_router.delete("/roles", status_code=204)
async def delete_role_binding(
    binding: RoleBindingCreate,
    _: None = Depends(_ensure_initialized)
):
    """
    Delete a role binding.
    
    Removes a role assignment from a user.
    """
    try:
        removed = await acl.enforcer.delete_role_for_user(binding.user, binding.role)
        if not removed:
            raise HTTPException(status_code=404, detail="Role binding not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete role binding: {str(e)}")

