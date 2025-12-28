"""Middleware loader for declarative agent configuration.

Dynamically loads FunctionMiddleware instances from import paths.
Supports both class instantiation and factory functions.
"""
from __future__ import annotations

import importlib
import logging
from typing import Sequence

from agent_framework import FunctionMiddleware

LOGGER = logging.getLogger("agentic_ai.middleware_loader")


def load_middleware(path: str) -> FunctionMiddleware:
    """Load a middleware from an import path.

    Supports two formats:
    - module:ClassName - Instantiates a class with no arguments
    - module:factory_func - Calls a factory function that returns middleware

    Args:
        path: Import path in format "module:name" or "module.submodule:name"

    Returns:
        Instantiated FunctionMiddleware

    Raises:
        ValueError: If path format is invalid or target is not a middleware
        ImportError: If module cannot be imported
        AttributeError: If name not found in module
    """
    if ":" not in path:
        # Try legacy format module.name
        if "." in path:
            module_path, attr_name = path.rsplit(".", 1)
        else:
            raise ValueError(
                f"Invalid middleware path '{path}': use 'module:ClassName' format"
            )
    else:
        module_path, attr_name = path.split(":", 1)

    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise ImportError(f"Failed to import middleware module '{module_path}': {exc}") from exc

    try:
        target = getattr(module, attr_name)
    except AttributeError as exc:
        raise AttributeError(
            f"Middleware '{attr_name}' not found in module '{module_path}'"
        ) from exc

    # If it's already a middleware instance, return it
    if isinstance(target, FunctionMiddleware):
        return target

    # If it's a class, check if it's a FunctionMiddleware subclass
    if isinstance(target, type):
        if issubclass(target, FunctionMiddleware):
            middleware = target()
            LOGGER.debug("Loaded middleware class | path=%s", path)
            return middleware
        raise ValueError(
            f"'{path}' is a class but not a FunctionMiddleware subclass"
        )

    # If it's callable (factory function), call it
    if callable(target):
        result = target()
        if isinstance(result, FunctionMiddleware):
            LOGGER.debug("Loaded middleware from factory | path=%s", path)
            return result
        raise ValueError(
            f"Factory '{path}' returned {type(result).__name__}, expected FunctionMiddleware"
        )

    raise ValueError(
        f"'{path}' is not a FunctionMiddleware class, instance, or factory function"
    )


def load_middlewares(paths: Sequence[str] | None) -> list[FunctionMiddleware]:
    """Load multiple middlewares from import paths.

    Args:
        paths: List of import paths, or None

    Returns:
        List of instantiated FunctionMiddleware instances
    """
    if not paths:
        return []

    middlewares: list[FunctionMiddleware] = []
    for path in paths:
        middleware = load_middleware(path)
        middlewares.append(middleware)

    LOGGER.debug("Loaded %d middleware(s) | paths=%s", len(middlewares), paths)
    return middlewares


__all__ = ["load_middleware", "load_middlewares"]
