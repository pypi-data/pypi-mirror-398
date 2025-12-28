"""MCP tools loader that exposes MCP tools as AIFunctions."""
from __future__ import annotations

import asyncio
from typing import Any, Callable

from agent_framework import AIFunction
from pydantic import Field, create_model

from .client import mcp_http_request, mcp_stdio_request
from .manifest import MCPManifest, MCPServerConfig


def load_mcp_tools(manifest: MCPManifest, server_name: str) -> list[AIFunction[Any, Any]]:
    server = manifest.get_server(server_name)
    tools = _list_tools(server)
    allowed = _filter_tools(tools, server.allow_tools, server.deny_tools)
    return [_build_tool(server, tool) for tool in allowed]


def _list_tools(server: MCPServerConfig) -> list[dict[str, Any]]:
    response = _request(server, method="tools/list", params={})
    if response.error:
        raise RuntimeError(f"MCP tools/list failed: {response.error}")
    result = response.result or {}
    tools = result.get("tools") if isinstance(result, dict) else None
    if not tools:
        return []
    return list(tools)


def _build_tool(server: MCPServerConfig, tool: dict[str, Any]) -> AIFunction[Any, Any]:
    name = tool.get("name") or "mcp_tool"
    description = tool.get("description") or ""
    input_schema = tool.get("inputSchema") or {}
    input_model = _input_model_from_schema(name, input_schema)

    async def tool_wrapper(**kwargs: Any) -> Any:
        response = await asyncio.to_thread(
            _request,
            server,
            method="tools/call",
            params={"name": name, "arguments": kwargs},
        )
        if response.error:
            raise RuntimeError(f"MCP tools/call failed: {response.error}")
        return response.result

    return AIFunction(
        name=name,
        description=description,
        func=tool_wrapper,
        input_model=input_model,  # type: ignore[arg-type]
    )


def _input_model_from_schema(tool_name: str, schema: dict[str, Any]) -> type:
    properties = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    fields: dict[str, tuple[type, Any]] = {}
    for prop_name, prop in properties.items():
        prop_type = _map_json_schema_type(prop.get("type"))
        description = prop.get("description") or ""
        if prop_name in required:
            fields[prop_name] = (prop_type, Field(..., description=description))
        else:
            fields[prop_name] = (prop_type, Field(None, description=description))
    if not fields:
        fields = {"input": (dict, Field(None, description="Tool input"))}
    return create_model(f"{tool_name}_input", **fields)


def _map_json_schema_type(kind: str | None) -> type:
    if not kind:
        return str
    if kind == "string":
        return str
    if kind == "integer":
        return int
    if kind == "number":
        return float
    if kind == "boolean":
        return bool
    if kind == "array":
        return list
    if kind == "object":
        return dict
    return str


def _filter_tools(
    tools: list[dict[str, Any]],
    allow: list[str] | None,
    deny: list[str] | None,
) -> list[dict[str, Any]]:
    filtered = tools
    if allow:
        allow_set = set(allow)
        filtered = [tool for tool in filtered if tool.get("name") in allow_set]
    if deny:
        deny_set = set(deny)
        filtered = [tool for tool in filtered if tool.get("name") not in deny_set]
    return filtered


def _request(
    server: MCPServerConfig,
    *,
    method: str,
    params: dict[str, Any],
):
    if server.transport == "http":
        return mcp_http_request(
            server.url or "",
            method=method,
            params=params,
            headers=server.headers,
            timeout=server.request_timeout,
        )
    return mcp_stdio_request(
        server.command or "",
        args=server.args,
        env=server.env,
        cwd=server.cwd,
        method=method,
        params=params,
        timeout=server.request_timeout,
    )


__all__ = ["load_mcp_tools"]
