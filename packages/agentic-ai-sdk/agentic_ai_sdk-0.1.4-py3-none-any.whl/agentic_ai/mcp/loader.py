"""MCP manifest loader with reference resolution."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from ..config.base import ConfigError
from ..defaults import MCP_MANIFEST_FILE
from .manifest import MCPManifest

_REF_PATTERN = re.compile(r"\$\{([^}]+)\}")


class MCPManifestLoader:
    """Load mcp.yaml manifest with ${} reference resolution."""

    def __init__(
        self,
        config_path: str | Path,
        mcp_manifest_path: str | Path | None = None,
    ) -> None:
        self.config_path = Path(config_path)
        self.mcp_manifest_path = (
            Path(mcp_manifest_path)
            if mcp_manifest_path is not None
            else self.config_path.parent / MCP_MANIFEST_FILE
        )

    def load_config_data(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise ConfigError(f"Configuration file not found: {self.config_path}")
        try:
            raw: Any = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigError(f"Failed to parse YAML configuration: {exc}") from exc
        if raw is None:
            raise ConfigError(f"Configuration file {self.config_path} is empty.")
        if not isinstance(raw, dict):
            raise ConfigError(f"Configuration file {self.config_path} must be a mapping.")
        return raw

    def load_manifest(self) -> MCPManifest | None:
        if not self.mcp_manifest_path.exists():
            return None
        try:
            raw: Any = yaml.safe_load(self.mcp_manifest_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigError(f"Failed to parse mcp manifest: {exc}") from exc
        if raw is None:
            raise ConfigError(f"MCP manifest {self.mcp_manifest_path} is empty.")
        if not isinstance(raw, dict):
            raise ConfigError(f"MCP manifest {self.mcp_manifest_path} must be a mapping.")
        return MCPManifest.model_validate(raw)

    def load_resolved_manifest(self) -> MCPManifest | None:
        manifest = self.load_manifest()
        if manifest is None:
            return None
        config = self.load_config_data()
        resolved = self.resolve_references(manifest, config)
        return resolved

    def resolve_references(self, manifest: MCPManifest, config: dict[str, Any]) -> MCPManifest:
        raw = manifest.model_dump()
        resolved = _resolve_value(raw, config)
        return MCPManifest.model_validate(resolved)


def _resolve_value(value: Any, config: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {k: _resolve_value(v, config) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_value(v, config) for v in value]
    if not isinstance(value, str):
        return value

    matches = list(_REF_PATTERN.finditer(value))
    if not matches:
        return value
    if len(matches) == 1 and matches[0].span() == (0, len(value)):
        ref = matches[0].group(1)
        return _resolve_reference(ref, config)

    resolved_text = value
    for match in matches:
        ref = match.group(1)
        resolved = _resolve_reference(ref, config)
        resolved_text = resolved_text.replace(match.group(0), str(resolved))
    return resolved_text


def _resolve_reference(ref: str, config: dict[str, Any]) -> Any:
    key, default = _split_ref_default(ref)
    env_val = os.getenv(key)
    if env_val is not None:
        return env_val
    found, val = _get_config_path(config, key)
    if found:
        return val
    if default is not None:
        return default
    raise ConfigError(f"Unable to resolve reference: {ref}")


def _split_ref_default(ref: str) -> tuple[str, str | None]:
    if ":" not in ref:
        return ref.strip(), None
    key, default = ref.split(":", 1)
    return key.strip(), default


def _get_config_path(config: dict[str, Any], path: str) -> tuple[bool, Any]:
    if not path:
        return False, None
    current: Any = config
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


__all__ = ["MCPManifestLoader"]
