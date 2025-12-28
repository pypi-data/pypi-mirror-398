"""
FastAPI dependency for permission checking.

This module provides the permission_required dependency factory that integrates
Casbin permission checking into FastAPI routes.
"""

import inspect
from typing import Callable, Any, Optional

from fastapi import Request, Depends
from fastapi.routing import APIRoute

from .enforcer import acl
from .resource import ResourceGetter, OwnerGetter
from .exceptions import Forbidden, Unauthorized


def permission_required(
    *,
    get_subject: Callable[..., Any],
    resource: Optional[ResourceGetter] = None,
    action: str,
    owner_getter: Optional[OwnerGetter] = None,
    model: str = "abac",
) -> Callable:
    """
    Factory for the permission dependency.

    :param get_subject: Callable dependency that returns the subject (user ID/username).
    :param resource: Optional ResourceGetter to retrieve the resource object for ABAC.
    :param action: The action being performed (e.g. "read", "write").
    :param owner_getter: Optional OwnerGetter to extract owner from resource object.
                        If not provided, will try to use resource_obj.get_owner_sub() method.
                        This allows different resources to use different owner extraction strategies.
    :param model: The permission model to use (e.g., "rbac", "abac", or custom model name).
                  Default is "abac".

    Example:
        # Using RBAC model (no ownership check)
        @app.get("/users")
        async def list_users(
            _: None = Depends(permission_required(
                get_subject=get_user,
                action="read",
                model="rbac"
            ))
        ):
            ...

        # Using ABAC model with ownership check
        @app.get("/orders/{order_id}")
        async def get_order(
            order_id: int,
            _: None = Depends(permission_required(
                get_subject=get_user,
                resource=get_order_resource,
                action="read",
                owner_getter=get_order_owner,
                model="abac"
            ))
        ):
            ...

        # Using custom model
        @app.post("/admin/settings")
        async def update_settings(
            _: None = Depends(permission_required(
                get_subject=get_user,
                action="write",
                model="custom_admin"
            ))
        ):
            ...
    """

    async def _dependency(request: Request, sub: str = Depends(get_subject)):
        # 1. Check Authentication
        if sub is None:
            raise Unauthorized("User not authenticated")

        # Ensure subject is a string for Casbin
        sub_str = str(sub)

        # 2. Resolve Object (Resource Path)
        # Try to get the route path format (e.g. /items/{id})
        # This aligns with Casbin keyMatch2
        route = request.scope.get("route")
        if route and isinstance(route, APIRoute):
            obj_str = route.path_format
        else:
            # Fallback to raw path
            obj_str = request.url.path

        # 3. Determine if this model uses ownership (ABAC-style)
        # ABAC models expect 4 args: (sub, obj, act, owner)
        # RBAC models expect 3 args: (sub, obj, act)
        is_abac_model = model == "abac" or "abac" in model.lower()

        # 4. Resolve Owner / Attributes (ABAC)
        owner = ""
        if is_abac_model and resource:
            # Call the resource getter
            # It accepts request and returns the object
            resource_obj = resource(request)

            # If the resource getter is async (not strictly in protocol but good to support)
            if inspect.isawaitable(resource_obj):
                resource_obj = await resource_obj

            if resource_obj:
                # Extract owner using flexible strategy
                if owner_getter:
                    # Use custom owner_getter if provided
                    owner_field = owner_getter(resource_obj, request)
                elif hasattr(resource_obj, "get_owner_sub"):
                    # Fall back to model's get_owner_sub method if available
                    owner_field = resource_obj.get_owner_sub()
                else:
                    # No owner extraction method available
                    owner_field = None

                # Convert owner to string, or use empty string if None
                # Empty string means RBAC-only check (no ownership requirement)
                if owner_field is not None:
                    owner = str(owner_field)

        # 5. Enforce Policy
        if is_abac_model:
            # ABAC model: pass owner parameter
            if not acl.enforce(model, sub_str, obj_str, action, owner):
                raise Forbidden("Permission denied")
        else:
            # RBAC model: no owner parameter
            if not acl.enforce(model, sub_str, obj_str, action):
                raise Forbidden("Permission denied")

    return _dependency
