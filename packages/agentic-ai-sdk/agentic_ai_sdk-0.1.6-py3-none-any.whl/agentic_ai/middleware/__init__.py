"""Middleware components for Agentic AI SDK.

This subpackage provides:
- ToolResultPersistenceMiddleware: Persist tool results and manage artifacts
- Middleware loader utilities
"""
from __future__ import annotations

from agent_framework.observability import (
    OBSERVABILITY_SETTINGS,
    get_function_span,
    get_function_span_attributes,
)

from .persistence import ToolResultPersistenceMiddleware
from .loader import load_middleware, load_middlewares

__all__ = [
    "ToolResultPersistenceMiddleware",
    "load_middleware",
    "load_middlewares",
    "OBSERVABILITY_SETTINGS",
    "get_function_span",
    "get_function_span_attributes",
]
