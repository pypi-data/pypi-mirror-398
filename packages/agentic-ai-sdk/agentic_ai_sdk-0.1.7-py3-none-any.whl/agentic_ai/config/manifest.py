"""Declarative agent manifest models."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolProviderConfig(BaseModel):
    """Tool provider configuration for declarative tools."""

    provider: str
    config: dict[str, Any] = Field(default_factory=dict)


class AgentManifest(BaseModel):
    """Declarative agent manifest loaded from agents.yaml."""

    version: str = "1.0"
    tools: dict[str, ToolProviderConfig] = Field(default_factory=dict)
    agents: dict[str, dict[str, Any]] = Field(default_factory=dict)


__all__ = ["AgentManifest", "ToolProviderConfig"]
