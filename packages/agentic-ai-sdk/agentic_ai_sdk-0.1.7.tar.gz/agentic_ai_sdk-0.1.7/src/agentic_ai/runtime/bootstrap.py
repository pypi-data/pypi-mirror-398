"""Runtime bootstrap - load configuration and manifests.

This module provides the bootstrap functionality for initializing the
Deep Agent runtime. It handles loading configuration files, manifest files,
and creating the RuntimeContext that is used throughout the application.

Example:
    from agentic_ai.config import BaseAppConfig
    from agentic_ai.runtime import bootstrap_runtime
    
    # Bootstrap runtime (once at startup)
    ctx = bootstrap_runtime(BaseAppConfig)
    
    # Or with explicit paths
    ctx = bootstrap_runtime(
        BaseAppConfig,
        config_path="env.production.yaml",
        manifest_dir="manifest",
    )
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any, Type, TypeVar

import yaml

from ..config.base import BaseAppConfig, load_yaml_config
from ..config.registry import (
    get_tool_config_registry,
    register_tool_config_schemas,
)
from ..config.base import ConfigError
from ..config.manifest import AgentManifest
from ..config.loader import AgentManifestLoader
from ..tools.manifest import ToolsManifest, load_tools_manifest
from ..mcp.loader import MCPManifestLoader
from ..mcp.manifest import MCPManifest
from ..llm.factory import LLMClientFactory
from ..config.store import create_agent_config_store_from_manifest
from ..defaults import ENV_CONFIG_FILE

from .context import RuntimeContext, set_runtime_context

LOGGER = logging.getLogger("agentic_ai.runtime")

ConfigT = TypeVar("ConfigT", bound=BaseAppConfig)


class RuntimeBootstrap:
    """Bootstrap helper for loading configuration and creating RuntimeContext.
    
    This class encapsulates the logic for:
    1. Loading application configuration from YAML
    2. Loading agent manifest (agents.yaml)
    3. Loading tools manifest (tools.yaml)
    4. Loading MCP manifest (mcp.yaml)
    5. Creating LLM factory and agent store
    6. Assembling the RuntimeContext
    
    Example:
        bootstrap = RuntimeBootstrap(
            config_class=BaseAppConfig,
            config_path="env.yaml",
            manifest_dir="manifest",
        )
        ctx = bootstrap.create_context()
    """
    
    def __init__(
        self,
        config_class: Type[ConfigT],
        config_path: Path | str | None = None,
        manifest_dir: Path | str = "manifest",
    ):
        """Initialize the bootstrap helper.
        
        Args:
            config_class: Pydantic config class (subclass of BaseAppConfig).
            config_path: Path to env.yaml configuration file. Defaults to "env.yaml".
            manifest_dir: Directory containing manifest files. Defaults to "manifest".
        """
        self.config_class = config_class
        self.config_path = Path(config_path) if config_path else Path(ENV_CONFIG_FILE)
        self.manifest_dir = Path(manifest_dir)
    
    def load_config(self) -> ConfigT:
        """Load application configuration from YAML.
        
        Returns:
            The validated configuration instance.
            
        Raises:
            ConfigError: If the configuration file cannot be loaded or validated.
        """
        return load_yaml_config(self.config_path, self.config_class)

    def load_raw_config(self) -> dict[str, Any]:
        """Load raw YAML mapping for tool config sections."""
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

    def _resolve_manifest_path(self, filename: str) -> Path:
        """Resolve a manifest filename against the configured manifest_dir.

        If manifest_dir is relative, resolve it relative to the config_path's parent.
        """
        base_dir = self.manifest_dir
        if not base_dir.is_absolute():
            base_dir = self.config_path.parent / base_dir
        return base_dir / filename
    
    def load_agent_manifest(self) -> AgentManifest | None:
        """Load and resolve agent manifest.
        
        Returns:
            The resolved AgentManifest or None if not found.
        """
        agent_path = self._resolve_manifest_path("agents.yaml")
        agent_loader = AgentManifestLoader(
            self.config_path,
            agent_manifest_path=agent_path,
        )
        return agent_loader.load_resolved_manifest()
    
    def load_tools_manifest(self) -> ToolsManifest | None:
        """Load tools manifest.
        
        Returns:
            The ToolsManifest or None if not found.
        """
        tools_path = self._resolve_manifest_path("tools.yaml")
        if not tools_path.exists():
            return None
        return load_tools_manifest(str(tools_path))

    def _import_tool_modules(self, tools_manifest: ToolsManifest | None) -> None:
        """Import tool modules and register their config schemas."""
        if not tools_manifest:
            return
        registry = get_tool_config_registry()
        registered_packages: set[str] = set()
        for tool in tools_manifest.tools.values():
            module_path = tool.function.split(":", 1)[0]
            importlib.import_module(module_path)
            # Derive package path from tool module (e.g., "toolsets.sql.tools" -> "toolsets.sql")
            parts = module_path.rsplit(".", 1)
            if len(parts) > 1:
                package_path = parts[0]
                if package_path not in registered_packages:
                    registered_packages.add(package_path)
                    # Register config schemas from config module
                    registry.register_from_module(f"{package_path}.config")
    
    def load_mcp_manifest(self) -> MCPManifest | None:
        """Load MCP manifest.
        
        Returns:
            The MCPManifest or None if not found.
        """
        mcp_path = self._resolve_manifest_path("mcp.yaml")
        mcp_loader = MCPManifestLoader(
            self.config_path,
            mcp_manifest_path=mcp_path,
        )
        return mcp_loader.load_resolved_manifest()
    
    def create_context(self) -> RuntimeContext:
        """Create a complete RuntimeContext.
        
        This method loads all configuration and manifest files, creates the
        necessary components (LLM factory, agent store), and assembles them
        into an immutable RuntimeContext.
        
        Schema Resolution Strategy:
        1. Explicit config_schemas in tools.yaml (highest priority)
        2. Convention-based auto-inference from toolset modules
        3. Schema-less fallback (raw dict returned as-is)
        
        Returns:
            The configured RuntimeContext.
            
        Raises:
            RuntimeError: If required manifests are missing.
            ConfigError: If configuration cannot be loaded.
        """
        # Load configuration
        config = self.load_config()
        raw_config = self.load_raw_config()
        
        # Load manifests
        agent_manifest = self.load_agent_manifest()
        if agent_manifest is None:
            agent_path = self._resolve_manifest_path("agents.yaml")
            raise RuntimeError(
                f"Agent manifest not found. Expected at {agent_path}"
            )
        
        tools_manifest = self.load_tools_manifest()
        
        # Register explicit config_schemas if provided
        if tools_manifest and tools_manifest.config_schemas:
            register_tool_config_schemas(tools_manifest.config_schemas)
        
        # Import tool modules (also registers them for convention-based inference)
        self._import_tool_modules(tools_manifest)
        
        mcp_manifest = self.load_mcp_manifest()

        # Collect all config_section names from tools for loading
        section_names: set[str] = set()
        if tools_manifest:
            for tool in tools_manifest.tools.values():
                if tool.config_section:
                    section_names.add(tool.config_section)
        
        # Load tool configs with auto-inference and schema-less support
        registry = get_tool_config_registry()
        tool_configs = registry.load_from_raw(raw_config, section_names or None)
        
        # Create LLM factory
        llm_configs = {llm.name: llm for llm in config.llm_profiles}
        llm_factory = LLMClientFactory(llm_configs)
        
        # Create agent store from manifest
        agent_store = create_agent_config_store_from_manifest(agent_manifest)
        
        ctx = RuntimeContext(
            config=config,
            agent_manifest=agent_manifest,
            tools_manifest=tools_manifest,
            llm_factory=llm_factory,
            agent_store=agent_store,
            mcp_manifest=mcp_manifest,
            tool_configs=tool_configs,
        )
        
        LOGGER.info(
            "Runtime context created | agents=%d | tools=%d | llms=%d",
            len(agent_store.available_agents),
            len(tools_manifest.tools) if tools_manifest else 0,
            len(llm_configs),
        )
        
        return ctx


def bootstrap_runtime(
    config_class: Type[ConfigT],
    config_path: Path | str | None = None,
    manifest_dir: Path | str = "manifest",
) -> RuntimeContext:
    """Bootstrap runtime and set global context.
    
    This is the main entry point for initializing the Deep Agent runtime.
    It loads configuration, manifests, and sets up the global RuntimeContext
    that can be accessed via get_runtime_context().
    
    Args:
        config_class: Pydantic config class for the application.
        config_path: Path to env.yaml configuration file.
        manifest_dir: Directory containing manifest files.
        
    Returns:
        The created RuntimeContext.
        
    Example:
        from agentic_ai.config import BaseAppConfig
        from agentic_ai.runtime import bootstrap_runtime
        
        ctx = bootstrap_runtime(BaseAppConfig)
        
        # Now you can use get_runtime_context() anywhere in your app
        from agentic_ai.runtime import get_runtime_context
        ctx = get_runtime_context()
    """
    bootstrap = RuntimeBootstrap(config_class, config_path, manifest_dir)
    ctx = bootstrap.create_context()
    set_runtime_context(ctx)
    return ctx


__all__ = [
    "RuntimeBootstrap",
    "bootstrap_runtime",
]
