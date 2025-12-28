"""Tools manifest models for declarative tool configuration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolParameterOverride(BaseModel):
    """Override for a tool parameter."""

    description: str | None = None
    required: bool | None = None


class ToolConfig(BaseModel):
    """Configuration for a single tool."""

    function: str
    """Python path to the tool function (module:function or module:Class.method)."""

    config_section: str | None = None
    """Optional config section name to inject from RuntimeContext (e.g., "openmetadata")."""

    description: str | None = None
    """Override the default @ai_function description."""

    parameters: dict[str, ToolParameterOverride] = Field(default_factory=dict)
    """Override specific parameter descriptions/requirements."""

    config: dict[str, Any] = Field(default_factory=dict)
    """Runtime configuration passed to the tool."""


class ToolOutputDefaults(BaseModel):
    """Global defaults for tool output handling."""
    
    output_policy: str = "managed"
    """Output policy: raw, managed, or manual."""
    
    preview_rows: int = 200
    """Default number of preview rows for persist_preview()."""
    
    auto_load_on_error: str = "return_error"
    """Error handling for auto_load_artifacts: raise, return_error, or return_empty."""


class ToolsManifest(BaseModel):
    """Declarative tools manifest loaded from tools.yaml."""

    version: str = "1.0"
    defaults: ToolOutputDefaults = Field(default_factory=ToolOutputDefaults)
    """Global defaults for tool output handling."""
    config_schemas: dict[str, str] = Field(default_factory=dict)
    """Mapping of config section name -> schema dotted path (module:Class)."""
    tools: dict[str, ToolConfig] = Field(default_factory=dict)


def load_tools_manifest(path: str) -> ToolsManifest:
    """Load tools manifest from a YAML file."""
    import yaml
    from pathlib import Path

    manifest_path = Path(path)
    if not manifest_path.exists():
        return ToolsManifest()

    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return ToolsManifest.model_validate(data)


__all__ = [
    "ToolConfig",
    "ToolParameterOverride",
    "ToolOutputDefaults",
    "ToolsManifest",
    "load_tools_manifest",
]
