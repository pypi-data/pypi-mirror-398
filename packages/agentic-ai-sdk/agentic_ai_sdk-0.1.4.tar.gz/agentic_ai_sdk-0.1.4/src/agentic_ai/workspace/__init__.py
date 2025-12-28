"""Workspace management for Deep Agent.

This subpackage provides:
- WorkspaceHandle: Handle for workspace operations
- WorkspaceManager: Creates and manages workspaces
- WorkspaceContextProvider: Context provider for workspace instructions
- create_workspace: Utility for creating workspaces with priority chain

Example:
    from agentic_ai.workspace import (
        WorkspaceHandle,
        WorkspaceManager,
        create_workspace,
    )
"""
from __future__ import annotations

# Re-export from files in this directory
from .core import (
    AGENT_ID_KWARG,
    WorkspaceContextProvider,
    WorkspaceHandle,
    WorkspaceManager,
    create_workspace,
)
from .middleware import WorkspaceParameterInjectionMiddleware

__all__ = [
    "AGENT_ID_KWARG",
    "WorkspaceContextProvider",
    "WorkspaceHandle",
    "WorkspaceManager",
    "WorkspaceParameterInjectionMiddleware",
    "create_workspace",
]
