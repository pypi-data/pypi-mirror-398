"""Agentic AI SDK - A toolkit for building AI agents.

This package provides a comprehensive framework for building AI agents with:
- Agent session management (DeepAgentSession)
- Configuration management (config/)
- LLM client utilities (llm/)
- Workspace management (workspace/)
- Artifact persistence (artifacts/)
- Observability and tracing (observability/)
- Planning tools (planning/)
- Runtime management (runtime/)
- Tool management (tools/)
- Middleware (middleware/)
- AG-UI protocol support (ag_ui/)
- MCP protocol support (mcp/)

Quick Start:
    from agentic_ai import (
        DeepAgentSession,
        build_agent_session,
        BaseAppContext,
        build_app_context,
    )

Subpackages:
    agentic_ai.agent        - Agent core components
    agentic_ai.config       - Configuration models and utilities
    agentic_ai.llm          - LLM client creation and management
    agentic_ai.runtime      - Runtime and session management
    agentic_ai.workspace    - Workspace and artifact storage
    agentic_ai.artifacts    - Tool result persistence
    agentic_ai.observability - Logging and tracing
    agentic_ai.planning     - Agent planning tools
    agentic_ai.middleware   - Middleware components
    agentic_ai.tools        - Tool loading and management
    agentic_ai.ag_ui        - AG-UI protocol support
    agentic_ai.mcp          - MCP protocol support
"""
from __future__ import annotations

# =============================================================================
# Subpackages (import for namespace access)
# =============================================================================
from . import (
    agent,
    config,
    llm,
    runtime,
    workspace,
    artifacts,
    observability,
    planning,
    middleware,
    tools,
    ag_ui,
    mcp,
)

# =============================================================================
# Core Agent Components
# =============================================================================
from .agent import (
    DeepAgentSession,
    build_agent,
    build_agent_with_llm,
    build_agent_from_config,
    build_agent_from_store,
    build_agent_session,
    SubAgentController,
    DeclarativeAgentBuilder,
    DeclarativeBuildResult,
)
from .app_context import BaseAppContext, build_app_context
from .ag_ui import (
    DeepAgentProtocolAdapter,
    build_ag_ui_agent,
    AgUIAppOptions,
    ConcurrencyLimitMiddleware,
    HealthCheckFilter,
    build_ag_ui_arg_parser,
    create_ag_ui_app,
    run_ag_ui_server,
)

# =============================================================================
# Configuration
# =============================================================================
from .config import (
    AgUiConfig,
    BaseAppConfig,
    ConfigError,
    EmbeddingConfig,
    LoggingConfig,
    ObservabilityConfig,
    load_yaml_config,
    ToolConfigRegistry,
    get_tool_config_registry,
    register_tool_config,
    register_tool_config_schema,
    register_tool_config_schemas,
    AgentConfig,
    ContextCompactionConfig,
    AgentConfigStore,
    create_agent_config_store_from_list,
    create_agent_config_store_from_manifest,
    AgentManifestLoader,
    LLMConfig,
)
from .config.agent import ResponseHandling, SubagentConfig
from .config.manifest import AgentManifest, ToolProviderConfig

# =============================================================================
# LLM Client
# =============================================================================
from .llm import (
    build_agent_chat_options,
    build_chat_options,
    create_chat_client,
    resolve_temperature,
    LLMClientFactory,
    create_llm_factory_from_list,
)
from .llm.embedding import EmbeddingProvider, EmbeddingError

# =============================================================================
# Workspace & Artifacts
# =============================================================================
from .workspace import (
    WorkspaceContextProvider,
    WorkspaceHandle,
    WorkspaceManager,
    create_workspace,
)
from .artifacts import (
    ArtifactStore,
    ToolResult,
    persist_full,
    persist_preview,
    ok,
    error,
    load_artifact,
    try_load_artifact,
)

# =============================================================================
# Observability
# =============================================================================
from .observability import (
    LogLevel,
    setup_logging,
    setup_logging_from_config,
    ObservabilityOptions,
    enable_observability,
    configure_observability_from_config,
    trace_http_request,
    trace_database_query,
    get_tracer,
)

# =============================================================================
# Planning
# =============================================================================
from .planning import (
    PlanRecord,
    PlanStep,
    PlanStore,
    StepStatus,
    UpdatePlanArgs,
    build_update_plan_tool,
)

# =============================================================================
# Runtime
# =============================================================================
from .runtime import (
    RuntimeBootstrap,
    RuntimeContext,
    bootstrap_runtime,
    get_runtime_context,
    set_runtime_context,
    reset_runtime_context,
    build_session,
    create_session_factory,
    SessionFactory,
    SessionBuilder,
    ThreadSession,
    DEFAULT_SESSION_TTL_SECONDS,
    ToolExecutionContext,
    ToolContextUnavailableError,
    ctx,
    try_ctx,
    tool_context,
    CompactionConfig,
    ContextCompactor,
    HeuristicSummarizer,
    CompactionSummarizer,
    LLMSummarizer,
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

# =============================================================================
# Middleware
# =============================================================================
from .middleware import (
    ToolResultPersistenceMiddleware,
    load_middleware,
    load_middlewares,
)

# =============================================================================
# Tools
# =============================================================================
from .tools import (
    ToolsManifest,
    ToolConfig,
    load_tools_manifest,
    load_tool_from_function,
    resolve_tool_ref,
    resolve_tool_refs,
)

# =============================================================================
# MCP
# =============================================================================
from .mcp import (
    MCPManifest,
    MCPServerConfig,
    MCPManifestLoader,
    load_mcp_tools,
)

# =============================================================================
# Utilities
# =============================================================================
from .ids import generate_short_id
from .prompt_loader import load_prompt_from_agent_config, load_prompt_from_file
from . import defaults

# =============================================================================
# Public API
# =============================================================================
__all__ = [
    # Subpackages
    "agent",
    "config",
    "llm",
    "runtime",
    "workspace",
    "artifacts",
    "observability",
    "planning",
    "middleware",
    "tools",
    "ag_ui",
    "mcp",
    "defaults",
    # Core
    "DeepAgentSession",
    "build_agent",
    "build_agent_from_config",
    "build_agent_from_store",
    "build_agent_session",
    "build_agent_with_llm",
    "SubAgentController",
    "DeclarativeAgentBuilder",
    "DeclarativeBuildResult",
    "BaseAppContext",
    "build_app_context",
    # AG-UI
    "DeepAgentProtocolAdapter",
    "build_ag_ui_agent",
    "AgUIAppOptions",
    "ConcurrencyLimitMiddleware",
    "HealthCheckFilter",
    "build_ag_ui_arg_parser",
    "create_ag_ui_app",
    "run_ag_ui_server",
    # Configuration
    "AgentConfig",
    "AgentConfigStore",
    "AgentManifest",
    "AgentManifestLoader",
    "AgUiConfig",
    "BaseAppConfig",
    "ConfigError",
    "ContextCompactionConfig",
    "EmbeddingConfig",
    "LLMConfig",
    "LoggingConfig",
    "ObservabilityConfig",
    "ResponseHandling",
    "SubagentConfig",
    "ToolProviderConfig",
    "create_agent_config_store_from_list",
    "create_agent_config_store_from_manifest",
    "load_yaml_config",
    "ToolConfigRegistry",
    "get_tool_config_registry",
    "register_tool_config",
    "register_tool_config_schema",
    "register_tool_config_schemas",
    # LLM
    "LLMClientFactory",
    "build_agent_chat_options",
    "build_chat_options",
    "create_chat_client",
    "create_llm_factory_from_list",
    "resolve_temperature",
    "EmbeddingProvider",
    "EmbeddingError",
    # Workspace & Artifacts
    "ArtifactStore",
    "ToolResult",
    "WorkspaceContextProvider",
    "WorkspaceHandle",
    "WorkspaceManager",
    "create_workspace",
    "persist_full",
    "persist_preview",
    "ok",
    "error",
    "load_artifact",
    "try_load_artifact",
    # Observability
    "LogLevel",
    "ObservabilityOptions",
    "configure_observability_from_config",
    "enable_observability",
    "get_tracer",
    "setup_logging",
    "setup_logging_from_config",
    "trace_database_query",
    "trace_http_request",
    # Planning
    "PlanRecord",
    "PlanStep",
    "PlanStore",
    "StepStatus",
    "UpdatePlanArgs",
    "build_update_plan_tool",
    # Runtime
    "RuntimeBootstrap",
    "RuntimeContext",
    "bootstrap_runtime",
    "get_runtime_context",
    "set_runtime_context",
    "reset_runtime_context",
    "build_session",
    "create_session_factory",
    "SessionFactory",
    "SessionBuilder",
    "ThreadSession",
    "DEFAULT_SESSION_TTL_SECONDS",
    "ToolExecutionContext",
    "ToolContextUnavailableError",
    "ctx",
    "try_ctx",
    "tool_context",
    "CompactionConfig",
    "ContextCompactor",
    "HeuristicSummarizer",
    "CompactionSummarizer",
    "LLMSummarizer",
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
    # Middleware
    "ToolResultPersistenceMiddleware",
    "load_middleware",
    "load_middlewares",
    # Tools
    "ToolsManifest",
    "ToolConfig",
    "load_tools_manifest",
    "load_tool_from_function",
    "resolve_tool_ref",
    "resolve_tool_refs",
    # MCP
    "MCPManifest",
    "MCPServerConfig",
    "MCPManifestLoader",
    "load_mcp_tools",
    # Utilities
    "generate_short_id",
    "load_prompt_from_agent_config",
    "load_prompt_from_file",
]
