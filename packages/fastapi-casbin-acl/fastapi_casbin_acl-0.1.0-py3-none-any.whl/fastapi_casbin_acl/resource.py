from typing import Protocol, Any, TypeVar, Callable, Optional
from fastapi import Request

# Define a generic type for the resource for better type hinting if needed
T = TypeVar("T")

class ResourceGetter(Protocol):
    """
    Protocol for resource getters.
    A ResourceGetter is a callable that takes a FastAPI Request and returns a resource object (or None).
    It should NOT raise permission exceptions.
    """
    def __call__(self, request: Request) -> Any:
        ...


class OwnerGetter(Protocol):
    """
    Protocol for owner getters.
    An OwnerGetter is a callable that extracts the owner identifier from a resource object.
    It takes the resource object and optionally the request, and returns the owner identifier (usually a string).
    """
    def __call__(self, resource_obj: Any, request: Optional[Request] = None) -> Optional[str]:
        ...

