"""MCP manifest models."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""

    name: str
    transport: Literal["stdio", "http"]
    # stdio
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None
    cwd: str | None = None
    # http
    url: str | None = None
    headers: dict[str, str] | None = None
    # filters
    allow_tools: list[str] | None = None
    deny_tools: list[str] | None = None
    # timeouts (seconds)
    request_timeout: float = 30.0

    @model_validator(mode="after")
    def _validate(self) -> "MCPServerConfig":
        if not self.name:
            raise ValueError("mcp.servers.name is required")
        if self.transport == "stdio":
            if not self.command:
                raise ValueError("mcp.servers.command is required for stdio")
        if self.transport == "http":
            if not self.url:
                raise ValueError("mcp.servers.url is required for http")
        return self


class MCPManifest(BaseModel):
    """Top-level MCP manifest loaded from mcp.yaml."""

    version: str = "1.0"
    servers: list[MCPServerConfig] = Field(default_factory=list)

    def get_server(self, name: str) -> MCPServerConfig:
        for server in self.servers:
            if server.name == name:
                return server
        raise ValueError(f"MCP server '{name}' not found in manifest")


__all__ = ["MCPManifest", "MCPServerConfig"]
