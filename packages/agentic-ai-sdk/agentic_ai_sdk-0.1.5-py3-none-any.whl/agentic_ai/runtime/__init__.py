"""Deep Agent Runtime - Bootstrap and runtime context management.

This module provides the core runtime infrastructure for Deep Agent applications:

- RuntimeContext: Immutable runtime context containing all configuration and resources
- RuntimeBootstrap: Helper for loading configuration and creating RuntimeContext
- bootstrap_runtime: Main entry point for initializing the Deep Agent runtime
- Session builders: Declarative session construction from manifests
- Tool runtime: Per-session resource management
- Context compaction: Automatic history management

Example:
    from agentic_ai.config import BaseAppConfig
    from agentic_ai.runtime import bootstrap_runtime, build_session
    from agentic_ai.workspace import create_workspace
    
    # Bootstrap runtime (once at startup)
    ctx = bootstrap_runtime(BaseAppConfig)
    
    # Create session
    workspace = create_workspace(default_root=".ws")
    session = build_session(ctx, "agentic_analyst", workspace)
"""

from .context import (
    RuntimeContext,
    get_runtime_context,
    set_runtime_context,
    reset_runtime_context,
    try_get_runtime_context,
)
from .session_factory import (
    SessionFactory,
    SessionBuilder,
    ThreadSession,
    DEFAULT_SESSION_TTL_SECONDS,
)
from .contexts import (
    ToolExecutionContext,
    ToolContextUnavailableError,
    ctx,
    try_ctx,
    tool_context,
)
from .context_compaction import (
    CompactionConfig,
    ContextCompactor,
    HeuristicSummarizer,
    CompactionSummarizer,
    LLMSummarizer,
)
from .tool_runtime import (
    ToolRuntimeRegistry,
    ToolOutputPolicy,
    tool_handler,
    get_output_config,
    normalize_tool_output,
    register_runtime,
    cleanup_session,
    reset_all_runtimes,
    get_current_session_id,
    set_session_context,
    reset_session_context,
    get_current_task,
    set_task_context,
    reset_task_context,
    get_last_artifact_id,
    set_last_artifact_id,
    reset_last_artifact_id,
    get_tool_config,
    set_tool_config,
    reset_tool_config,
    get_config_section,
    get_effective_config_section,
    get_effective_tool_config,
    get_client,
    register_client,
    unregister_client,
    get_registered_clients,
)

# Lazy-loaded to avoid circular imports with agent module
_lazy_imports = {
    "RuntimeBootstrap": ".bootstrap",
    "bootstrap_runtime": ".bootstrap",
    "build_session": ".session_builder",
    "create_session_factory": ".session_builder",
}

def __getattr__(name: str):
    if name in _lazy_imports:
        import importlib
        module = importlib.import_module(_lazy_imports[name], __package__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Bootstrap
    "RuntimeBootstrap",
    "bootstrap_runtime",
    # Context
    "RuntimeContext",
    "get_runtime_context",
    "set_runtime_context",
    "reset_runtime_context",
    "try_get_runtime_context",
    # Session builders
    "build_session",
    "create_session_factory",
    # Session factory
    "SessionFactory",
    "SessionBuilder",
    "ThreadSession",
    "DEFAULT_SESSION_TTL_SECONDS",
    # Tool execution context
    "ToolExecutionContext",
    "ToolContextUnavailableError",
    "ctx",
    "try_ctx",
    "tool_context",
    # Context compaction
    "CompactionConfig",
    "ContextCompactor",
    "HeuristicSummarizer",
    "CompactionSummarizer",
    "LLMSummarizer",
    # Tool runtime
    "ToolRuntimeRegistry",
    "ToolOutputPolicy",
    "tool_handler",
    "get_output_config",
    "normalize_tool_output",
    "register_runtime",
    "cleanup_session",
    "reset_all_runtimes",
    "get_current_session_id",
    "set_session_context",
    "reset_session_context",
    "get_current_task",
    "set_task_context",
    "reset_task_context",
    "get_last_artifact_id",
    "set_last_artifact_id",
    "reset_last_artifact_id",
    "get_tool_config",
    "set_tool_config",
    "reset_tool_config",
    "get_config_section",
    "get_effective_config_section",
    "get_effective_tool_config",
    "get_client",
    "register_client",
    "unregister_client",
    "get_registered_clients",
]
