"""Artifact persistence and loading for Deep Agent.

This subpackage provides:
- ToolResult: Unified tool output structure
- ArtifactStore: Storage for tool execution artifacts
- persist_full/persist_preview: Persist data as artifacts
- ok/error: Quick response helpers
- load_artifact: Load artifacts with explicit failure

Example:
    from agentic_ai.artifacts import (
        ToolResult,
        ArtifactStore,
        persist_full,
        persist_preview,
        ok,
        error,
        load_artifact,
    )
    
    # Simple success response
    return ok({"data": "value"}).model_dump()
    
    # Persist with preview
    return persist_preview(
        full_data={"rows": large_data},
        preview_rows=100,
    ).model_dump()
    
    # Error response
    return error("Something went wrong").model_dump()
"""
from __future__ import annotations

# Re-export from files in this directory
from .core import (
    # Core types
    ArtifactStore,
    ToolResult,
    # Helpers
    persist_full,
    persist_preview,
    ok,
    error,
    load_artifact,
    try_load_artifact,
)

__all__ = [
    # Core types
    "ArtifactStore",
    "ToolResult",
    # Helpers
    "persist_full",
    "persist_preview",
    "ok",
    "error",
    "load_artifact",
    "try_load_artifact",
]
