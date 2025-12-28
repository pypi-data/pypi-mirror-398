"""Runtime context management using ContextVar.

This module provides the RuntimeContext dataclass and ContextVar-based
context management for dependency injection across the Deep Agent framework.

The RuntimeContext is an immutable container holding:
- Application configuration (BaseAppConfig subclass)
- Agent manifest (from agents.yaml)
- Tools manifest (from tools.yaml)
- LLM factory for creating chat clients
- Agent config store for agent configurations

Example:
    from agentic_ai.runtime import get_runtime_context, get_config_section
    
    # In a tool function
    ctx = get_runtime_context()
    config = ctx.get_config_section("openmetadata")
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import BaseAppConfig
    from ..config.manifest import AgentManifest
    from ..tools.manifest import ToolsManifest
    from ..llm.factory import LLMClientFactory
    from ..config.store import AgentConfigStore
    from ..mcp.manifest import MCPManifest

ConfigT = TypeVar("ConfigT", bound="BaseAppConfig")


@dataclass(frozen=True)
class RuntimeContext:
    """Immutable runtime context containing all configuration and resources.
    
    This is created once at application startup and shared across all
    agents/tools in the same session. The context is immutable to prevent
    accidental modification.
    
    Attributes:
        config: Application configuration (BaseAppConfig subclass)
        agent_manifest: Parsed agents.yaml manifest
        tools_manifest: Parsed tools.yaml manifest (optional)
        llm_factory: Factory for creating LLM chat clients
        agent_store: Store for agent configurations
        mcp_manifest: Parsed mcp.yaml manifest (optional)
        tool_configs: Tool-specific config sections loaded from env.yaml
    """
    
    config: Any  # BaseAppConfig subclass
    agent_manifest: "AgentManifest"
    tools_manifest: "ToolsManifest | None"
    llm_factory: "LLMClientFactory"
    agent_store: "AgentConfigStore"
    mcp_manifest: "MCPManifest | None" = None
    tool_configs: dict[str, Any] | None = None
    
    def get_config_section(self, name: str) -> Any:
        """Get a configuration section by name.
        
        This method provides a consistent way to access application-specific
        configuration sections (e.g., "openmetadata", "databricks", "sql_execution").
        
        Args:
            name: Configuration section name (e.g., "openmetadata", "databricks")
            
        Returns:
            The configuration section object or None if not found.
            
        Example:
            om_config = ctx.get_config_section("openmetadata")
            if om_config:
                base_url = om_config.base_url
        """
        value = getattr(self.config, name, None)
        if value is not None:
            return value
        if self.tool_configs:
            return self.tool_configs.get(name)
        return None
    
    def get_llm_config(self, llm_name: str = "default") -> Any:
        """Get LLM configuration by name.
        
        Args:
            llm_name: Name of the LLM configuration. Defaults to "default".
            
        Returns:
            The LLM configuration.
            
        Raises:
            ValueError: If the LLM configuration is not found.
        """
        return self.llm_factory.get_config(llm_name)
    
    def get_agent_config(self, agent_id: str) -> Any:
        """Get agent configuration by ID.
        
        Args:
            agent_id: The unique identifier of the agent.
            
        Returns:
            The agent configuration.
            
        Raises:
            ValueError: If the agent configuration is not found.
        """
        return self.agent_store.get_config(agent_id)

    def get_tool_config(self, name: str) -> Any:
        """Get tool-specific configuration section by name.

        Tool config schemas are registered from tools.yaml config_schemas.
        """
        if not self.tool_configs:
            return None
        return self.tool_configs.get(name)


# ============================================================================
# ContextVar-based Context Management
# ============================================================================

_runtime_context: ContextVar[RuntimeContext | None] = ContextVar(
    "runtime_context", default=None
)


def get_runtime_context() -> RuntimeContext:
    """Get the current runtime context.
    
    This function retrieves the RuntimeContext from the current execution
    context. It should be called after bootstrap_runtime() has been invoked.
    
    Returns:
        The current RuntimeContext.
        
    Raises:
        RuntimeError: If runtime context is not set (bootstrap_runtime not called).
        
    Example:
        from agentic_ai.runtime import get_runtime_context
        
        ctx = get_runtime_context()
        config = ctx.get_config_section("openmetadata")
    """
    ctx = _runtime_context.get()
    if ctx is None:
        raise RuntimeError(
            "Runtime context not available. "
            "Ensure deep_agent.runtime.bootstrap_runtime() was called."
        )
    return ctx


def set_runtime_context(ctx: RuntimeContext) -> Token[RuntimeContext | None]:
    """Set the runtime context.
    
    This function sets the RuntimeContext in the current execution context.
    It returns a token that can be used to reset the context later.
    
    Args:
        ctx: The RuntimeContext to set.
        
    Returns:
        A token that can be used with reset_runtime_context().
        
    Example:
        token = set_runtime_context(ctx)
        try:
            # Use context
            ...
        finally:
            reset_runtime_context(token)
    """
    return _runtime_context.set(ctx)


def reset_runtime_context(token: Token[RuntimeContext | None]) -> None:
    """Reset runtime context to previous value.
    
    Args:
        token: Token returned by set_runtime_context().
    """
    _runtime_context.reset(token)


def try_get_runtime_context() -> RuntimeContext | None:
    """Try to get the current runtime context without raising.
    
    Returns:
        The current RuntimeContext or None if not set.
    """
    return _runtime_context.get()


__all__ = [
    "RuntimeContext",
    "get_runtime_context",
    "set_runtime_context",
    "reset_runtime_context",
    "try_get_runtime_context",
]
