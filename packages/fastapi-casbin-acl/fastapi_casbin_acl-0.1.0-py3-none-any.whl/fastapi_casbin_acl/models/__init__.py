"""
Casbin model templates and loading utilities.

This module provides built-in model configurations for common access control patterns:
- rbac: Role-Based Access Control (API-level permissions)
- abac: Attribute-Based Access Control (data-level permissions with ownership)

Models are automatically registered with the ModelRegistry upon package import.
"""

import os
import importlib.resources
from typing import Optional


def get_model_path(model_name: str) -> str:
    """
    Get the path to the model template file for the given model name.

    :param model_name: The model name (e.g., 'rbac', 'abac')
    :return: Path to the model file
    :raises FileNotFoundError: If the model file is not found
    """
    model_filename = f"{model_name}.conf"

    # Try to load from package resources first
    try:
        model_path = str(
            importlib.resources.files("fastapi_casbin_acl.models").joinpath(
                model_filename
            )
        )
        if os.path.exists(model_path):
            return model_path
    except Exception:
        pass

    # Fallback to file system path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, model_filename)

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Casbin model file not found: {model_filename} "
            f"(searched at: {model_path})"
        )

    return model_path


def list_builtin_models() -> list[str]:
    """
    List all available built-in model names.

    :return: List of built-in model names
    """
    return ["rbac", "abac"]
