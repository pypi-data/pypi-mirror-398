"""Tool management for Agentic AI SDK.

This subpackage provides:
- ToolsManifest: Manifest for declarative tool configuration
- Tool loading and resolution utilities
"""
from __future__ import annotations

from .manifest import ToolsManifest, ToolConfig, load_tools_manifest
from .loader import load_tool_from_function, resolve_tool_ref
from .provider import resolve_tool_refs

__all__ = [
    # Manifest
    "ToolsManifest",
    "ToolConfig",
    "load_tools_manifest",
    # Loader
    "load_tool_from_function",
    "resolve_tool_ref",
    # Provider
    "resolve_tool_refs",
]
