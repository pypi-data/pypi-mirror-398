from typing import Protocol, Any, List

class PolicySyncer(Protocol):
    """
    Interface for policy synchronization.
    """
    async def sync_policies(self) -> None:
        ...

