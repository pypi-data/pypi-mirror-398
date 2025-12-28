"""
Model Registry for managing Casbin permission models.

This module provides a centralized registry for Casbin model configurations,
supporting both built-in models (rbac, abac) and user-defined external models.
"""

import os
import importlib.resources
from typing import Dict, List, Optional

from .exceptions import ConfigError


class ModelRegistry:
    """
    Registry for managing Casbin permission models.

    This class provides a centralized way to register, retrieve, and manage
    Casbin model configurations. Built-in models (rbac, abac) are automatically
    registered upon instantiation.

    Example:
        # Get the global registry instance
        from fastapi_casbin_acl import model_registry

        # List available models
        models = model_registry.list_models()  # ['rbac', 'abac']

        # Get path to a specific model
        path = model_registry.get_path('rbac')

        # Register a custom model
        model_registry.register('custom', '/path/to/custom.conf')
    """

    def __init__(self):
        self._models: Dict[str, str] = {}
        self._auto_register_builtin()

    def _auto_register_builtin(self) -> None:
        """
        Automatically register built-in models from the models directory.
        """
        builtin_models = ["rbac", "abac"]

        for model_name in builtin_models:
            model_filename = f"{model_name}.conf"

            # Try to load from package resources first
            model_path: Optional[str] = None
            try:
                resource_path = str(
                    importlib.resources.files("fastapi_casbin_acl.models").joinpath(
                        model_filename
                    )
                )
                if os.path.exists(resource_path):
                    model_path = resource_path
            except Exception:
                pass

            # Fallback to file system path
            if model_path is None:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                models_dir = os.path.join(current_dir, "models")
                fallback_path = os.path.join(models_dir, model_filename)
                if os.path.exists(fallback_path):
                    model_path = fallback_path

            if model_path:
                self._models[model_name] = model_path

    def register(self, name: str, path: str) -> None:
        """
        Register a new model with the given name and path.

        :param name: Unique name for the model
        :param path: Path to the Casbin model configuration file
        :raises ConfigError: If the model file does not exist
        """
        if not os.path.exists(path):
            raise ConfigError(f"Model file not found: {path}")

        self._models[name] = path

    def unregister(self, name: str) -> None:
        """
        Unregister a model by name.

        :param name: Name of the model to unregister
        :raises ConfigError: If the model is not registered
        """
        if name not in self._models:
            raise ConfigError(f"Model not registered: {name}")

        del self._models[name]

    def get_path(self, name: str) -> str:
        """
        Get the path to the model configuration file.

        :param name: Name of the model
        :return: Path to the model configuration file
        :raises ConfigError: If the model is not registered
        """
        if name not in self._models:
            available = ", ".join(self._models.keys()) if self._models else "none"
            raise ConfigError(
                f"Model not registered: '{name}'. Available models: {available}"
            )

        return self._models[name]

    def is_registered(self, name: str) -> bool:
        """
        Check if a model is registered.

        :param name: Name of the model
        :return: True if the model is registered, False otherwise
        """
        return name in self._models

    def list_models(self) -> List[str]:
        """
        List all registered model names.

        :return: List of registered model names
        """
        return list(self._models.keys())


# Global singleton instance
model_registry = ModelRegistry()

