"""Tool provider loading utilities for declarative manifests."""
from __future__ import annotations

from typing import Callable

from ..config.manifest import AgentManifest
from ..mcp.tools import load_mcp_tools
from ..mcp.manifest import MCPManifest
from .manifest import ToolsManifest
from .loader import resolve_tool_ref as _resolve_from_tools_manifest


def resolve_tool_refs(
    tool_refs: list[str] | None,
    *,
    manifest: AgentManifest,
    mcp_manifest: MCPManifest | None = None,
    tools_manifest: ToolsManifest | None = None,
) -> list[Callable]:
    """Resolve tool references against manifest definitions.
    
    Tool references are resolved in the following order:
    1. MCP tools (prefix "mcp:")
    2. tools.yaml (individual tools) if tools_manifest is provided
    """
    if not tool_refs:
        return []
    tools: list[Callable] = []
    for ref in tool_refs:
        # 1. MCP tools
        if ref.startswith("mcp:"):
            if mcp_manifest is None:
                raise ValueError("mcp.yaml is required to resolve MCP tool references")
            server_name = ref.split(":", 1)[1]
            tools.extend(load_mcp_tools(mcp_manifest, server_name))
            continue

        # 2. Try tools.yaml (plugin-style)
        if tools_manifest is not None and ref in tools_manifest.tools:
            tools.extend(
                _resolve_from_tools_manifest(
                    ref,
                    manifest=tools_manifest,
                )
            )
            continue

        raise ValueError(
            f"Tool reference '{ref}' not found in tools.yaml or mcp.yaml. "
            "Define it in manifest/tools.yaml or manifest/mcp.yaml."
        )
    return tools


__all__ = ["resolve_tool_refs"]
