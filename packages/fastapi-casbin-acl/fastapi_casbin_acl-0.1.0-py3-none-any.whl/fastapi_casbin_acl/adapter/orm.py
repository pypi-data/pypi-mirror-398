"""
SQLModel ORM models for Casbin policy storage.
"""
from typing import Optional
from sqlmodel import SQLModel, Field


class CasbinRule(SQLModel, table=True):
    """
    Casbin policy rule stored in database.
    
    This model follows the standard Casbin rule format:
    - ptype: "p" for policy, "g" for role definition
    - v0, v1, v2, ...: Policy values (sub, obj, act, etc.)
    
    Example policies:
    - p, alice, /orders, read
    - p, bob, /orders/*, write
    - g, charlie, admin
    
    Example records:
    - ptype="p", v0="alice", v1="/orders", v2="read"
    - ptype="g", v0="charlie", v1="admin"
    """
    __tablename__ = "casbin_rule"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    ptype: str = Field(max_length=16, description="Policy type: 'p' for policy, 'g' for role")
    v0: Optional[str] = Field(default=None, max_length=256, description="Subject (user/role)")
    v1: Optional[str] = Field(default=None, max_length=256, description="Object (resource)")
    v2: Optional[str] = Field(default=None, max_length=256, description="Action")
    v3: Optional[str] = Field(default=None, max_length=256, description="Additional field 1")
    v4: Optional[str] = Field(default=None, max_length=256, description="Additional field 2")
    v5: Optional[str] = Field(default=None, max_length=256, description="Additional field 3")

