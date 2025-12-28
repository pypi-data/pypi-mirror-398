"""
Tests for fastapi_casbin_acl.adapter module.
"""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from fastapi_casbin_acl.adapter import CasbinRule, SQLModelAdapter
from fastapi_casbin_acl.adapter.orm import CasbinRule as ORMCasbinRule


@pytest.fixture
async def db_engine():
    """Create an in-memory SQLite database engine."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest.fixture
def adapter_factory(db_engine):
    """Create an adapter factory."""
    async_session = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    return async_session


@pytest.fixture
async def db_session(adapter_factory):
    """Create a database session for direct use."""
    async with adapter_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_casbin_rule_model():
    """Test CasbinRule ORM model."""
    rule = CasbinRule(
        ptype="p",
        v0="alice",
        v1="/orders",
        v2="read"
    )
    
    assert rule.ptype == "p"
    assert rule.v0 == "alice"
    assert rule.v1 == "/orders"
    assert rule.v2 == "read"
    assert rule.v3 is None
    assert rule.v4 is None
    assert rule.v5 is None


@pytest.mark.asyncio
async def test_casbin_rule_role():
    """Test CasbinRule for role definition."""
    rule = CasbinRule(
        ptype="g",
        v0="charlie",
        v1="admin"
    )
    
    assert rule.ptype == "g"
    assert rule.v0 == "charlie"
    assert rule.v1 == "admin"
    assert rule.v2 is None


@pytest.mark.asyncio
async def test_sqlmodel_adapter_init(adapter_factory):
    """Test SQLModelAdapter initialization."""
    adapter = SQLModelAdapter(adapter_factory)
    assert adapter._session_factory is not None


@pytest.mark.asyncio
async def test_sqlmodel_adapter_load_policy(adapter_factory, db_session):
    """Test SQLModelAdapter load_policy."""
    # Insert test data
    rule1 = CasbinRule(ptype="p", v0="alice", v1="/public", v2="read")
    rule2 = CasbinRule(ptype="g", v0="charlie", v1="admin")
    db_session.add(rule1)
    db_session.add(rule2)
    await db_session.commit()
    
    # Create adapter and load policy
    adapter = SQLModelAdapter(adapter_factory)
    
    # Create a mock model
    import casbin
    model = casbin.Model()
    model.add_def("r", "r", "sub, obj, act")
    model.add_def("p", "p", "sub, obj, act")
    model.add_def("g", "g", "_, _")
    model.add_def("e", "e", "some(where (p.eft == allow))")
    model.add_def("m", "m", "g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act")
    
    await adapter.load_policy(model)
    
    # Check policies were loaded
    assert len(model.model["p"]["p"].policy) > 0
    assert len(model.model["g"]["g"].policy) > 0


@pytest.mark.asyncio
async def test_sqlmodel_adapter_save_policy(adapter_factory, db_session):
    """Test SQLModelAdapter save_policy."""
    adapter = SQLModelAdapter(adapter_factory)
    
    # Create a mock model with policies
    import casbin
    model = casbin.Model()
    model.add_def("r", "r", "sub, obj, act")
    model.add_def("p", "p", "sub, obj, act")
    model.add_def("g", "g", "_, _")
    model.add_def("e", "e", "some(where (p.eft == allow))")
    model.add_def("m", "m", "g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act")
    
    # Add policies
    model.add_policy("p", "p", ["alice", "/public", "read"])
    model.add_policy("g", "g", ["charlie", "admin"])
    
    # Save policies (adapter uses session_factory internally)
    await adapter.save_policy(model)
    
    # Verify policies were saved (need to use a new session to check)
    from sqlalchemy import select
    async with adapter_factory() as session:
        result = await session.execute(select(CasbinRule))
        rules = result.scalars().all()
        assert len(rules) == 2


@pytest.mark.asyncio
async def test_sqlmodel_adapter_add_policy(adapter_factory, db_session):
    """Test SQLModelAdapter add_policy."""
    adapter = SQLModelAdapter(adapter_factory)
    
    result = await adapter.add_policy("p", "p", ["bob", "/orders", "write"])
    assert result is True
    
    # Verify policy was added
    from sqlalchemy import select
    result = await db_session.execute(
        select(CasbinRule).where(CasbinRule.ptype == "p")
    )
    rules = result.scalars().all()
    assert len(rules) == 1
    assert rules[0].v0 == "bob"
    assert rules[0].v1 == "/orders"
    assert rules[0].v2 == "write"


@pytest.mark.asyncio
async def test_sqlmodel_adapter_remove_policy(adapter_factory, db_session):
    """Test SQLModelAdapter remove_policy."""
    # Add a policy first
    rule = CasbinRule(ptype="p", v0="alice", v1="/public", v2="read")
    db_session.add(rule)
    await db_session.commit()
    
    adapter = SQLModelAdapter(adapter_factory)
    
    # Remove the policy
    result = await adapter.remove_policy("p", "p", ["alice", "/public", "read"])
    assert result is True
    
    # Verify policy was removed
    from sqlalchemy import select
    result = await db_session.execute(
        select(CasbinRule).where(CasbinRule.ptype == "p")
    )
    rules = result.scalars().all()
    assert len(rules) == 0


@pytest.mark.asyncio
async def test_sqlmodel_adapter_remove_policy_not_found(adapter_factory, db_session):
    """Test SQLModelAdapter remove_policy when policy doesn't exist."""
    adapter = SQLModelAdapter(adapter_factory)
    
    # Try to remove non-existent policy
    result = await adapter.remove_policy("p", "p", ["nonexistent", "/path", "read"])
    assert result is False


@pytest.mark.asyncio
async def test_sqlmodel_adapter_remove_filtered_policy(adapter_factory, db_session):
    """Test SQLModelAdapter remove_filtered_policy."""
    # Add multiple policies
    rule1 = CasbinRule(ptype="p", v0="alice", v1="/public", v2="read")
    rule2 = CasbinRule(ptype="p", v0="alice", v1="/orders", v2="write")
    rule3 = CasbinRule(ptype="p", v0="bob", v1="/public", v2="read")
    db_session.add_all([rule1, rule2, rule3])
    await db_session.commit()
    
    adapter = SQLModelAdapter(adapter_factory)
    
    # Remove all policies for alice (field_index=0, field_values=["alice"])
    result = await adapter.remove_filtered_policy("p", "p", 0, "alice")
    assert result is True
    
    # Verify only alice's policies were removed
    from sqlalchemy import select
    result = await db_session.execute(
        select(CasbinRule).where(CasbinRule.ptype == "p")
    )
    rules = result.scalars().all()
    assert len(rules) == 1
    assert rules[0].v0 == "bob"


@pytest.mark.asyncio
async def test_sqlmodel_adapter_remove_policy_with_v3_v4_v5(adapter_factory, db_session):
    """Test remove_policy with v3, v4, v5 fields (lines 150, 152, 154)."""
    # Add policy with extended fields
    rule = CasbinRule(
        ptype="p",
        v0="user1",
        v1="/resource",
        v2="action",
        v3="field3",
        v4="field4",
        v5="field5"
    )
    db_session.add(rule)
    await db_session.commit()
    
    adapter = SQLModelAdapter(adapter_factory)
    
    # Remove policy matching all fields including v3, v4, v5
    result = await adapter.remove_policy("p", "p", ["user1", "/resource", "action", "field3", "field4", "field5"])
    assert result is True
    
    # Verify policy was removed
    from sqlalchemy import select
    result = await db_session.execute(
        select(CasbinRule).where(CasbinRule.ptype == "p")
    )
    rules = result.scalars().all()
    assert len(rules) == 0


@pytest.mark.asyncio
async def test_sqlmodel_adapter_remove_filtered_policy_no_match(adapter_factory, db_session):
    """Test remove_filtered_policy returns False when no match (line 206)."""
    adapter = SQLModelAdapter(adapter_factory)
    
    # Try to remove filtered policy that doesn't exist
    result = await adapter.remove_filtered_policy("p", "p", 0, "nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_sqlmodel_adapter_create_rule_with_many_fields(adapter_factory):
    """Test _create_rule handles more than 6 fields."""
    adapter = SQLModelAdapter(adapter_factory)
    
    # Create rule with more than 6 values (should be truncated)
    rule = adapter._create_rule("p", ["v0", "v1", "v2", "v3", "v4", "v5", "v6", "v7"])
    
    assert rule.ptype == "p"
    assert rule.v0 == "v0"
    assert rule.v1 == "v1"
    assert rule.v2 == "v2"
    assert rule.v3 == "v3"
    assert rule.v4 == "v4"
    assert rule.v5 == "v5"
    # v6 and v7 should be truncated


@pytest.mark.asyncio
async def test_sqlmodel_adapter_create_rule_with_few_fields(adapter_factory):
    """Test _create_rule handles fewer than 6 fields."""
    adapter = SQLModelAdapter(adapter_factory)
    
    # Create rule with fewer than 6 values (should be padded with None)
    rule = adapter._create_rule("p", ["v0", "v1"])
    
    assert rule.ptype == "p"
    assert rule.v0 == "v0"
    assert rule.v1 == "v1"
    assert rule.v2 is None
    assert rule.v3 is None
    assert rule.v4 is None
    assert rule.v5 is None

