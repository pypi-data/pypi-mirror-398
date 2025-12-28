"""
Async Enforcer Manager for Casbin.

This module provides a centralized manager for multiple Casbin AsyncEnforcer instances,
supporting different permission models for different routes/resources.
"""

import casbin
from typing import Any, Dict, List, Optional

from .config import ACLConfig
from .exceptions import ACLNotInitialized, ConfigError
from .registry import model_registry


class AsyncEnforcerManager:
    """
    Singleton manager for multiple Casbin AsyncEnforcer instances.

    This manager provides centralized access to Casbin AsyncEnforcer instances,
    supporting multiple permission models. Each model has its own enforcer instance,
    allowing different routes to use different permission models.

    Example:
        # Initialize with default models
        await acl.init(adapter)

        # Initialize with specific models
        await acl.init(adapter, models=['rbac', 'abac'])

        # Enforce using a specific model
        allowed = acl.enforce('rbac', user_id, '/api/users', 'read')

        # Enforce using ABAC model with owner check
        allowed = acl.enforce('abac', user_id, '/api/orders/{id}', 'read', owner_id)
    """

    _instance = None

    def __init__(self):
        self._enforcers: Dict[str, casbin.AsyncEnforcer] = {}
        self._adapters: Dict[str, Any] = {}
        self._config: Optional[ACLConfig] = None
        self._initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AsyncEnforcerManager, cls).__new__(cls)
        return cls._instance

    async def init(
        self,
        adapter: Any,
        models: Optional[List[str]] = None,
        config: Optional[ACLConfig] = None,
    ) -> None:
        """
        Initialize AsyncEnforcer instances for the specified models.

        :param adapter: Casbin async adapter (e.g. SQLModelAdapter). All models share the same adapter.
        :param models: List of model names to initialize. If None, initializes the default model from config.
        :param config: ACLConfig instance. If None, creates a default one.
        """
        # Create default config if not provided
        if config is None:
            config = ACLConfig()

        self._config = config

        # If external_model_path is provided, register it
        if config.external_model_path:
            model_registry.register("external", config.external_model_path)

        # Determine which models to initialize
        if models is None:
            # Initialize only the default model
            models_to_init = [config.default_model]
        else:
            models_to_init = models

        # Initialize enforcer for each model
        for model_name in models_to_init:
            await self._init_model(model_name, adapter)

        self._initialized = True

    async def _init_model(self, model_name: str, adapter: Any) -> None:
        """
        Initialize an enforcer for a specific model.

        :param model_name: Name of the model to initialize
        :param adapter: Casbin async adapter
        """
        # Skip if already initialized
        if model_name in self._enforcers:
            return

        # Get model path from registry
        model_path = model_registry.get_path(model_name)

        # Create enforcer
        enforcer = casbin.AsyncEnforcer(model_path, adapter)
        await enforcer.load_policy()

        self._enforcers[model_name] = enforcer
        self._adapters[model_name] = adapter

    async def init_model(self, model_name: str, adapter: Optional[Any] = None) -> None:
        """
        Initialize or reinitialize an enforcer for a specific model at runtime.

        This allows adding new models after the initial init() call.

        :param model_name: Name of the model to initialize
        :param adapter: Casbin async adapter. If None, uses the adapter from the first initialized model.
        """
        if adapter is None:
            if not self._adapters:
                raise ACLNotInitialized(
                    "No adapter available. Call init() first or provide an adapter."
                )
            # Use the first available adapter
            adapter = next(iter(self._adapters.values()))

        await self._init_model(model_name, adapter)

    def get_enforcer(self, model_name: str) -> casbin.AsyncEnforcer:
        """
        Get the AsyncEnforcer instance for a specific model.

        :param model_name: Name of the model
        :return: AsyncEnforcer instance
        :raises ACLNotInitialized: If the model has not been initialized
        """
        if model_name not in self._enforcers:
            available = ", ".join(self._enforcers.keys()) if self._enforcers else "none"
            raise ACLNotInitialized(
                f"Model '{model_name}' not initialized. "
                f"Available models: {available}. "
                f"Call await acl.init(adapter, models=['{model_name}']) first."
            )
        return self._enforcers[model_name]

    @property
    def enforcer(self) -> casbin.AsyncEnforcer:
        """
        Get the default AsyncEnforcer instance.

        This property provides backward compatibility and returns the enforcer
        for the default model specified in config.

        :return: AsyncEnforcer instance for the default model
        :raises ACLNotInitialized: If the enforcer has not been initialized
        """
        if not self._initialized or not self._config:
            raise ACLNotInitialized(
                "AsyncEnforcerManager is not initialized. Call await acl.init() first."
            )
        return self.get_enforcer(self._config.default_model)

    @property
    def config(self) -> ACLConfig:
        """
        Get the ACLConfig instance.

        :raises ACLNotInitialized: If the enforcer has not been initialized
        """
        if self._config is None:
            raise ACLNotInitialized(
                "AsyncEnforcerManager is not initialized. Call await acl.init() first."
            )
        return self._config

    def enforce(self, model_name: str, *args) -> bool:
        """
        Execute the Casbin enforce method using the specified model.

        Note: enforce is synchronous even in AsyncEnforcer as it operates on in-memory policies.

        :param model_name: Name of the model to use for enforcement
        :param args: Arguments to pass to enforce (sub, obj, act, ...)
        :return: True if access is allowed, False otherwise
        """
        enforcer = self.get_enforcer(model_name)
        return enforcer.enforce(*args)

    def is_model_initialized(self, model_name: str) -> bool:
        """
        Check if a model has been initialized.

        :param model_name: Name of the model
        :return: True if the model is initialized, False otherwise
        """
        return model_name in self._enforcers

    def list_initialized_models(self) -> List[str]:
        """
        List all initialized model names.

        :return: List of initialized model names
        """
        return list(self._enforcers.keys())

    async def load_policy(self, model_name: Optional[str] = None) -> None:
        """
        Reload policies from the adapter.

        :param model_name: Name of the model to reload. If None, reloads all models.
        """
        if model_name:
            enforcer = self.get_enforcer(model_name)
            await enforcer.load_policy()
        else:
            for enforcer in self._enforcers.values():
                await enforcer.load_policy()

    async def save_policy(self, model_name: Optional[str] = None) -> None:
        """
        Save policies to the adapter.

        :param model_name: Name of the model to save. If None, saves all models.
        """
        if model_name:
            enforcer = self.get_enforcer(model_name)
            await enforcer.save_policy()
        else:
            for enforcer in self._enforcers.values():
                await enforcer.save_policy()


# Global accessor
acl = AsyncEnforcerManager()
