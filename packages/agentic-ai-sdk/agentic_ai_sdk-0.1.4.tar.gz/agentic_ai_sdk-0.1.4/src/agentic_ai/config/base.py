"""Configuration models for Deep Agent framework.

This module provides base configuration classes that can be reused across different
agent applications. Application-specific configurations should inherit from these
base classes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Optional

import yaml
from pydantic import BaseModel, ValidationError, model_validator

from ..llm.config import LLMConfig
from .agent import AgentConfig, ContextCompactionConfig


class LoggingConfig(BaseModel):
    """Application logging configuration.
    
    This is a reusable configuration model for logging settings that can be
    used across different agent applications.
    """

    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    file: str | None = None  # Optional path to log file
    format: str = "structured"  # structured (JSON) or pretty
    otlp_endpoint: str | None = None  # Optional OTLP endpoint for log export
    otlp_headers: dict[str, str] | None = None  # Optional headers for OTLP log export
    service_name: str | None = "agentic_ai"
    inherit_from_observability: bool = True  # When true, reuse observability.otlp_endpoint/headers if logging ones missing


class ObservabilityConfig(BaseModel):
    """Agent Framework observability instrumentation settings.
    
    This is a reusable configuration model for observability/tracing settings
    that can be used across different agent applications.
    """

    enabled: bool = False
    enable_sensitive_data: bool = False
    otlp_endpoint: str | list[str] | None = None
    application_insights_connection_string: str | None = None
    vs_code_extension_port: int | None = None
    disable_console_exporter: bool = False  # When False (default), traces output to both console and OTLP endpoint
    log_export: bool = True  # When true, also export structured logs via OTLP (shares endpoint/headers)
    log_headers: dict[str, str] | None = None  # Optional headers for log OTLP exporter
    # Optional logging overrides (lets you omit the separate `logging` section)
    log_level: str | None = None  # Falls back to INFO
    log_file: str | None = None
    log_format: str = "structured"
    log_service_name: str | None = None
    log_console_output: bool | None = None

    @model_validator(mode="after")
    def _validate(self) -> "ObservabilityConfig":
        if self.vs_code_extension_port is not None and self.vs_code_extension_port <= 0:
            raise ValueError("vs_code_extension_port must be positive")
        return self


class AgUiConfig(BaseModel):
    """Configuration for AG-UI server behavior."""

    allowed_origins: list[str] | None = None
    max_concurrent: int = 100
    enable_ready: bool = True
    enable_health: bool = True
    enable_ui_config: bool = True
    require_confirmation: bool = False
    path: str = "/"


class ArtifactWorkspaceConfig(BaseModel):
    """Configuration for artifact workspace paths.
    
    This centralizes workspace root configuration that was previously
    scattered across individual agent configs in env*.yaml.
    """

    root: str = ".ws"  # Root directory for artifact workspaces


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation.
    
    Supports OpenAI, Azure OpenAI, and other OpenAI-compatible embedding APIs.
    This is a reusable configuration model that can be used across different
    agent applications.
    """

    CONFIG_SECTION: ClassVar[str] = "embedding"

    provider: str = "openai"  # openai, azure, or other compatible providers
    model: str
    endpoint: str
    api_key: str
    dimension: int
    api_version: str = "2024-02-01"
    default_headers: Optional[dict[str, str]] = None  # Custom headers for API requests
    verify_ssl: bool = True  # Whether to verify SSL certificates for HTTPS requests

    @model_validator(mode="after")
    def _validate(self) -> "EmbeddingConfig":
        if not self.model:
            raise ValueError("embedding.model is required")
        if not self.endpoint:
            raise ValueError("embedding.endpoint is required")
        if not self.api_key:
            raise ValueError("embedding.api_key is required")
        if self.dimension <= 0:
            raise ValueError("embedding.dimension must be positive")
        if not self.api_version:
            raise ValueError("embedding.api_version is required")
        return self


class BaseAppConfig(BaseModel):
    """Base application configuration with common fields.
    
    This provides the foundation for application-specific configurations.
    Subclass this to add application-specific configuration fields.
    
    Example:
        class MyAppConfig(BaseAppConfig):
            my_service: Optional[MyServiceConfig] = None
    """
    
    llm_profiles: list[LLMConfig]  # List of LLM profile configurations
    agents: Optional[list[AgentConfig]] = None  # List of agent configurations (legacy, use manifest/agents.yaml)
    artifact_workspace: Optional[ArtifactWorkspaceConfig] = None  # Workspace path configuration
    logging: Optional[LoggingConfig] = None  # Logging configuration
    observability: Optional[ObservabilityConfig] = None  # Observability configuration
    ag_ui: Optional[AgUiConfig] = None  # AG-UI server configuration

    def get_workspace_root(self) -> str:
        """Get the configured workspace root path.
        
        Returns:
            Workspace root path, defaults to ".ws".
        """
        if self.artifact_workspace:
            return self.artifact_workspace.root
        return ".ws"

    def get_llm_config(self, name: str = "default") -> LLMConfig:
        """Get LLM profile configuration by name.
        
        Args:
            name: The name of the LLM profile. Defaults to "default".
        
        Returns:
            The requested LLM configuration.
        
        Raises:
            ValueError: If the named LLM profile is not found.
        """
        for llm_config in self.llm_profiles:
            if llm_config.name == name:
                return llm_config
        
        available = ", ".join(llm.name or "(unnamed)" for llm in self.llm_profiles)
        raise ValueError(f"LLM profile '{name}' not found. Available: {available}")

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID.
        
        Args:
            agent_id: The ID of the agent configuration.
        
        Returns:
            The agent configuration or None if not found.
        """
        if not self.agents:
            return None
        
        for agent_config in self.agents:
            if agent_config.id == agent_id:
                return agent_config
        
        return None


class ConfigError(RuntimeError):
    """Raised when configuration cannot be loaded or validated."""


def load_yaml_config(path: str | Path, config_class: type[BaseModel]) -> BaseModel:
    """Load and validate configuration from a YAML file.
    
    This is a generic YAML configuration loader that can be used with any
    Pydantic model class.
    
    Args:
        path: Path to the YAML configuration file.
        config_class: The Pydantic model class to validate against.
    
    Returns:
        The validated configuration instance.
    
    Raises:
        ConfigError: If the file is not found, cannot be parsed, or validation fails.
    
    Example:
        config = load_yaml_config("env.yaml", MyAppConfig)
    """
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        raw: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse YAML configuration: {exc}") from exc

    if raw is None:
        raise ConfigError(f"Configuration file {config_path} is empty.")

    try:
        return config_class.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"Invalid configuration in {config_path}: {exc}") from exc


__all__ = [
    "AgentConfig",
    "AgUiConfig",
    "BaseAppConfig",
    "ConfigError",
    "ContextCompactionConfig",
    "EmbeddingConfig",
    "LLMConfig",
    "LoggingConfig",
    "ObservabilityConfig",
    "load_yaml_config",
]
