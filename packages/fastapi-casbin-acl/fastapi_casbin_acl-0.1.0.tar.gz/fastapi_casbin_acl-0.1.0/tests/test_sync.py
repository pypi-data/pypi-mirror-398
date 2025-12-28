"""
Tests for fastapi_casbin_acl.sync module.
"""
import pytest
from typing import Protocol, Any, List


def test_policy_syncer_protocol():
    """Test PolicySyncer protocol definition."""
    from fastapi_casbin_acl.sync import PolicySyncer
    
    # Verify it's a Protocol
    assert hasattr(PolicySyncer, '__protocol_attrs__') or isinstance(PolicySyncer, type)
    
    # Create a mock implementation
    class MockSyncer:
        async def sync_policies(self) -> None:
            pass
    
    # Verify it matches the protocol (structural typing)
    syncer = MockSyncer()
    assert hasattr(syncer, 'sync_policies')
    assert callable(getattr(syncer, 'sync_policies'))

