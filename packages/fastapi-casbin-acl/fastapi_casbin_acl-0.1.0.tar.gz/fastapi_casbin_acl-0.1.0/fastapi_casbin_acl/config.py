from typing import Optional
from pydantic import BaseModel, Field


class ACLConfig(BaseModel):
    """
    Global configuration for the ACL system.
    """

    default_model: str = Field(
        default="abac",
        description="Default model name to use for permission checks. "
        "Built-in models: 'rbac', 'abac'. Custom models can be registered via ModelRegistry.",
    )
    external_model_path: Optional[str] = Field(
        default=None,
        description="Path to a custom Casbin model file. "
        "If provided, it will be registered with name 'external'.",
    )
    admin_role: Optional[str] = Field(
        default=None, description="Role name that bypasses ownership checks"
    )
