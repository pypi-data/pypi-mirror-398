"""Configuration models and utilities for Deep Agent.

This subpackage provides:
- Base configuration classes (BaseAppConfig, ConfigError)
- Agent configuration (AgentConfig, ContextCompactionConfig)
- LLM configuration (LLMConfig)
- Logging/Observability configuration (LoggingConfig, ObservabilityConfig)
- Configuration store (AgentConfigStore)
- YAML loading utilities (load_yaml_config)

Example:
    from agentic_ai.config import (
        BaseAppConfig,
        AgentConfig,
        LLMConfig,
        load_yaml_config,
    )
"""
from __future__ import annotations

# Re-export from config_base (now in this directory)
from .base import (
    AgUiConfig,
    ArtifactWorkspaceConfig,
    BaseAppConfig,
    ConfigError,
    EmbeddingConfig,
    LoggingConfig,
    ObservabilityConfig,
    load_yaml_config,
)
from .loader import AgentManifestLoader
from .registry import (
    ToolConfigRegistry,
    get_tool_config_registry,
    register_tool_config,
    register_tool_config_schema,
    register_tool_config_schemas,
    register_config_module,
)
from .agent import AgentConfig, ContextCompactionConfig
from .store import (
    AgentConfigStore,
    create_agent_config_store_from_list,
    create_agent_config_store_from_manifest,
)
from ..llm.config import LLMConfig

__all__ = [
    # Base config
    "BaseAppConfig",
    "AgUiConfig",
    "ArtifactWorkspaceConfig",
    "ConfigError",
    "load_yaml_config",
    # Agent config
    "AgentConfig",
    "AgentConfigStore",
    "ContextCompactionConfig",
    "create_agent_config_store_from_list",
    "create_agent_config_store_from_manifest",
    # LLM config
    "LLMConfig",
    # Logging/Observability config
    "EmbeddingConfig",
    "LoggingConfig",
    "ObservabilityConfig",
    "AgentManifestLoader",
    # Tool config registry
    "ToolConfigRegistry",
    "get_tool_config_registry",
    "register_tool_config",
    "register_tool_config_schema",
    "register_config_module",
    "register_tool_config_schemas",
]
