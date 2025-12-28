"""Tool runtime registry for per-session resource management.

This module provides:
1. ToolRuntimeRegistry: Per-session resource caching with lazy initialization
2. ContextVar-based task context for automatic task binding in tools
3. Cleanup hooks for resource lifecycle management
4. Dependency injection API for tools to access configuration and clients
5. ToolOutputPolicy and @tool_handler for unified output handling

Key concepts:
- Resources are cached per session_id to avoid multi-session conflicts
- Task context is automatically set before tool calls via ContextVar
- Cleanup is triggered when sessions are closed
- Tools use get_effective_tool_config() and get_client() for dependency injection
- @tool_handler provides automatic error handling and output normalization

Injection API for tools:
    from agentic_ai.tool_runtime import get_effective_tool_config, get_client
    
    @ai_function(name="search_metadata")
    @tool_handler()
    async def search_metadata(query: str):
        om_config = get_effective_tool_config("openmetadata")["section"]
        om_client = get_client("openmetadata")
        ...
"""
from __future__ import annotations

import contextvars
import logging
from enum import Enum
from functools import wraps
from typing import Any, Callable, Generic, TypeVar

LOGGER = logging.getLogger("agentic_ai.tool_runtime")

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


# =============================================================================
# Tool Output Policy
# =============================================================================

class ToolOutputPolicy(str, Enum):
    """工具输出处理策略。
    
    - RAW: 原生返回，不做任何包装
    - MANAGED: 自动封装 + 异常转 error ToolResult（默认）
    - MANUAL: 手动控制 ToolResult / ArtifactStore
    """
    RAW = "raw"
    MANAGED = "managed"
    MANUAL = "manual"


# 默认配置
DEFAULT_OUTPUT_POLICY = ToolOutputPolicy.MANAGED
DEFAULT_PREVIEW_ROWS = 200
DEFAULT_AUTO_LOAD_ON_ERROR = "return_error"

# Tool output config defaults
DEFAULT_TOOL_OUTPUT_CONFIG = {
    "output_policy": "managed",
    "preview_rows": 200,
    "auto_load_on_error": "return_error",
}


def get_output_config() -> dict[str, Any]:
    """获取工具输出配置（合并全局默认 + 工具级覆盖）。
    
    配置合并优先级（从低到高）：
    1. 硬编码默认值 (DEFAULT_TOOL_OUTPUT_CONFIG)
    2. tools.yaml defaults 块
    3. 工具级 config 块
    
    Returns:
        合并后的配置字典，包含 output_policy, preview_rows, auto_load_on_error
    """
    tool_config = get_tool_config().get("config", {})
    
    # 从 RuntimeContext.tools_manifest.defaults 获取全局配置
    global_defaults: dict[str, Any] = {}
    try:
        from .context import try_get_runtime_context
        runtime_ctx = try_get_runtime_context()
        if runtime_ctx and runtime_ctx.tools_manifest:
            defaults = runtime_ctx.tools_manifest.defaults
            global_defaults = {
                "output_policy": defaults.output_policy,
                "preview_rows": defaults.preview_rows,
                "auto_load_on_error": defaults.auto_load_on_error,
            }
    except (ImportError, AttributeError):
        pass
    
    # 合并优先级：工具级 > 全局 > 硬编码默认
    return {
        **DEFAULT_TOOL_OUTPUT_CONFIG,
        **{k: v for k, v in global_defaults.items() if k in DEFAULT_TOOL_OUTPUT_CONFIG},
        **{k: v for k, v in tool_config.items() if k in DEFAULT_TOOL_OUTPUT_CONFIG},
    }


def normalize_tool_output(result: Any) -> dict[str, Any]:
    """将任意返回值归一化为 ToolResult dict。
    
    Args:
        result: 工具返回的任意值
        
    Returns:
        ToolResult 格式的 dict
    """
    from ..artifacts import ToolResult
    
    if isinstance(result, ToolResult):
        return result.model_dump()
    if isinstance(result, dict):
        # 尝试解析为 ToolResult
        if "result" in result or "artifact_id" in result:
            try:
                return ToolResult.model_validate(result).model_dump()
            except Exception:
                pass
        # 非 ToolResult dict，包装为 result
        return ToolResult(result=result).model_dump()
    # 其他类型，包装为 result
    return ToolResult(result=result).model_dump()


def tool_handler(
    policy: ToolOutputPolicy | str | None = None,
    *,
    auto_normalize: bool = True,
) -> Callable[[F], F]:
    """工具输出处理装饰器。
    
    Args:
        policy: 输出策略，默认从 tools.yaml 配置或 MANAGED
        auto_normalize: 是否自动将非 ToolResult 返回值包装
        
    功能：
    1. 异常捕获 → error ToolResult（仅 managed 模式）
    2. 自动 normalize（auto_normalize=True 时，raw 除外）
    
    Example:
        @ai_function(name="my_tool")
        @tool_handler()
        async def my_tool(query: str) -> dict:
            result = do_something(query)
            return persist_full(result).model_dump()
    """
    def decorator(fn: F) -> F:
        @wraps(fn)
        async def async_wrapper(*args, **kwargs):
            # 解析 policy：优先装饰器参数 > tools.yaml 配置 > 默认值
            effective_policy = policy
            if effective_policy is None:
                output_cfg = get_output_config()
                policy_str = output_cfg.get("output_policy", "managed")
                effective_policy = ToolOutputPolicy(policy_str) if policy_str else DEFAULT_OUTPUT_POLICY
            elif isinstance(effective_policy, str):
                effective_policy = ToolOutputPolicy(effective_policy)
            
            if effective_policy == ToolOutputPolicy.MANAGED:
                from ..artifacts import error as error_result
                try:
                    result = await fn(*args, **kwargs)
                    return normalize_tool_output(result) if auto_normalize else result
                except Exception as exc:
                    LOGGER.error("Tool error: %s: %s", type(exc).__name__, exc, exc_info=True)
                    return error_result(f"{type(exc).__name__}: {exc}").model_dump()

            # RAW/MANUAL: do not intercept exceptions
            result = await fn(*args, **kwargs)
            if effective_policy == ToolOutputPolicy.RAW:
                return result
            return normalize_tool_output(result) if auto_normalize else result
        
        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            # 解析 policy
            effective_policy = policy
            if effective_policy is None:
                output_cfg = get_output_config()
                policy_str = output_cfg.get("output_policy", "managed")
                effective_policy = ToolOutputPolicy(policy_str) if policy_str else DEFAULT_OUTPUT_POLICY
            elif isinstance(effective_policy, str):
                effective_policy = ToolOutputPolicy(effective_policy)
            
            if effective_policy == ToolOutputPolicy.MANAGED:
                from ..artifacts import error as error_result
                try:
                    result = fn(*args, **kwargs)
                    return normalize_tool_output(result) if auto_normalize else result
                except Exception as exc:
                    LOGGER.error("Tool error: %s: %s", type(exc).__name__, exc, exc_info=True)
                    return error_result(f"{type(exc).__name__}: {exc}").model_dump()

            # RAW/MANUAL: do not intercept exceptions
            result = fn(*args, **kwargs)
            if effective_policy == ToolOutputPolicy.RAW:
                return result
            return normalize_tool_output(result) if auto_normalize else result
        
        # 选择同步或异步 wrapper
        import inspect
        if inspect.iscoroutinefunction(fn):
            # Preserve original signature to avoid forwarding runtime kwargs.
            async_wrapper.__signature__ = inspect.signature(fn)  # type: ignore[attr-defined]
            return async_wrapper  # type: ignore
        # Preserve original signature to avoid forwarding runtime kwargs.
        sync_wrapper.__signature__ = inspect.signature(fn)  # type: ignore[attr-defined]
        return sync_wrapper  # type: ignore
    
    return decorator

# =============================================================================
# Context Variables for Session and Task
# =============================================================================

# Current session ID (set by agent session before running)
_current_session_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_session_id", default=None
)

# Current task context (set by SubAgentController before tool calls)
_current_task: contextvars.ContextVar[Any] = contextvars.ContextVar(
    "current_task", default=None
)

# Last artifact ID produced by tools in the current session
_last_artifact_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "last_artifact_id", default=None
)


def get_current_session_id() -> str | None:
    """Get current session ID from context."""
    return _current_session_id.get()


def set_session_context(session_id: str) -> contextvars.Token[str | None]:
    """Set current session ID context. Returns token for reset."""
    return _current_session_id.set(session_id)


def reset_session_context(token: contextvars.Token[str | None]) -> None:
    """Reset session context to previous value."""
    _current_session_id.reset(token)


def get_current_task() -> Any:
    """Get current task from context.
    
    This is set by SubAgentController before tool calls, allowing tools
    to access task information without explicit parameter passing.
    """
    return _current_task.get()


def set_task_context(task: Any) -> contextvars.Token[Any]:
    """Set current task context. Returns token for reset."""
    return _current_task.set(task)


def reset_task_context(token: contextvars.Token[Any]) -> None:
    """Reset task context to previous value."""
    _current_task.reset(token)


def get_last_artifact_id() -> str | None:
    """Get the last artifact ID produced by tools in the current session.
    
    This is used by auto_load_artifacts to find the final artifact
    without needing direct access to the toolset.
    """
    return _last_artifact_id.get()


def set_last_artifact_id(artifact_id: str | None) -> None:
    """Set the last artifact ID.
    
    Tools should call this when they produce an artifact that should be
    auto-loaded by the sub-agent response handler.
    
    Args:
        artifact_id: The artifact ID to record
    """
    _last_artifact_id.set(artifact_id)


def reset_last_artifact_id() -> None:
    """Reset the last artifact ID to None."""
    _last_artifact_id.set(None)


# =============================================================================
# Enhanced Injection API (for tools to use)
# =============================================================================

# Tool-specific config injected before each tool call
_tool_config: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "tool_config", default={}
)

# Client registries for dependency injection
_client_registries: dict[str, "ToolRuntimeRegistry[Any]"] = {}


def get_tool_config() -> dict[str, Any]:
    """Get the configuration injected for the current tool.
    
    This is set by SDK middleware based on tools.yaml `config_section`.
    
    Returns:
        Configuration dict for the current tool.
    """
    return _tool_config.get()


def set_tool_config(config: dict[str, Any]) -> contextvars.Token[dict[str, Any]]:
    """Set the tool-specific configuration. Returns token for reset."""
    return _tool_config.set(config)


def reset_tool_config(token: contextvars.Token[dict[str, Any]]) -> None:
    """Reset tool config to previous value."""
    _tool_config.reset(token)


def get_config_section(name: str) -> Any:
    """Get a configuration section from the runtime context.
    
    This is a convenience wrapper that accesses the global RuntimeContext.
    Tools should use this to access application configuration without
    importing application-specific modules.
    
    Args:
        name: Configuration section name (e.g., "openmetadata", "sql_execution")
        
    Returns:
        The configuration section or None if not found.
        
    Example:
        om_config = get_config_section("openmetadata")
        if om_config:
            base_url = om_config.base_url
    """
    from .context import try_get_runtime_context
    ctx = try_get_runtime_context()
    if ctx is None:
        return None
    return ctx.get_config_section(name)


def get_effective_config_section(name: str) -> Any:
    """Get configuration section, preferring tool-injected config when available.

    If the current tool invocation has a matching config_section injected,
    return that section; otherwise fall back to RuntimeContext lookup.
    """
    tool_payload = get_tool_config()
    if tool_payload.get("config_section") == name:
        injected = tool_payload.get("section")
        if injected is not None:
            return injected
    return get_config_section(name)


def get_effective_tool_config(section_name: str | None = None) -> dict[str, Any]:
    """Get tool overrides and resolved config section in a single call.

    This merges tools.yaml overrides with the resolved config section
    (tool-injected or RuntimeContext lookup).
    """
    tool_payload = get_tool_config()
    tool_config = tool_payload.get("config", {}) if isinstance(tool_payload, dict) else {}
    if section_name:
        section = get_effective_config_section(section_name)
    else:
        section = tool_payload.get("section") if isinstance(tool_payload, dict) else None
    return {
        "config": tool_config,
        "section": section,
    }


def get_client(name: str, required: bool = True) -> Any:
    """Get a client from the ToolRuntimeRegistry.
    
    Clients are lazily created and cached per session. This provides
    dependency injection for tools without tight coupling to application code.
    
    Args:
        name: Client name (e.g., "openmetadata", "databricks")
        required: If True, raises error when client unavailable.
        
    Returns:
        The client instance.
        
    Raises:
        RuntimeError: If required=True and client is not registered.
        
    Example:
        om_client = get_client("openmetadata")
        db_client = get_client("databricks", required=False)
    """
    registry = _client_registries.get(name)
    if registry is None:
        if required:
            available = ", ".join(_client_registries.keys()) or "none"
            raise RuntimeError(
                f"Client '{name}' not registered. Available clients: {available}"
            )
        return None
    return registry.get()


def register_client(name: str, registry: "ToolRuntimeRegistry[Any]") -> None:
    """Register a client registry for dependency injection.
    
    Tool modules should call this during import to register their
    client factories. This enables tools to use get_client() for
    dependency injection.
    
    Args:
        name: Client name (e.g., "openmetadata", "databricks")
        registry: ToolRuntimeRegistry instance for creating/caching clients
        
    Example:
        _om_registry = ToolRuntimeRegistry(
            factory=_create_om_client,
            teardown=lambda c: c.close(),
            name="OpenMetadataClient",
        )
        register_client("openmetadata", _om_registry)
    """
    _client_registries[name] = registry
    LOGGER.debug("Registered client: %s", name)


def unregister_client(name: str) -> None:
    """Unregister a client registry."""
    _client_registries.pop(name, None)


def get_registered_clients() -> list[str]:
    """Get list of registered client names."""
    return list(_client_registries.keys())


# =============================================================================
# Tool Runtime Registry
# =============================================================================

class ToolRuntimeRegistry(Generic[T]):
    """Per-session resource registry with lazy initialization.
    
    Solves the global singleton problem by caching resources per session_id.
    Resources are automatically cleaned up when sessions are closed.
    
    Usage:
        _om_client_registry = ToolRuntimeRegistry(
            factory=lambda: OpenMetadataClient.from_config(get_app_context().config),
            teardown=lambda c: c.close(),
            name="OpenMetadataClient",
        )
        
        @ai_function(name="search_metadata")
        def search_metadata(...):
            client = _om_client_registry.get()  # Gets/creates for current session
            ...
    
    Attributes:
        _factory: Callable to create new instances
        _teardown: Optional callable to cleanup instances
        _instances: Dict mapping session_id to instance
        _fallback: Singleton instance for non-session contexts (testing)
    """
    
    def __init__(
        self,
        factory: Callable[[], T],
        *,
        name: str | None = None,
        teardown: Callable[[T], None] | None = None,
    ) -> None:
        """Initialize the registry.
        
        Args:
            factory: Callable that creates a new resource instance
            name: Optional name for logging
            teardown: Optional callable to cleanup instances (e.g., close connections)
        """
        self._factory = factory
        self._name = name or "ToolRuntime"
        self._teardown = teardown
        self._instances: dict[str, T] = {}
        # Fallback singleton for non-session contexts (e.g., testing)
        self._fallback: T | None = None
    
    def get(self, session_id: str | None = None) -> T:
        """Get or create resource for the given/current session.
        
        Args:
            session_id: Explicit session ID, or uses current context if None
            
        Returns:
            Resource instance for the session
        """
        sid = session_id or get_current_session_id()
        
        if sid is None:
            # Fallback to singleton for backward compatibility
            if self._fallback is None:
                self._fallback = self._factory()
                LOGGER.debug("%s: created fallback singleton", self._name)
            return self._fallback
        
        if sid not in self._instances:
            self._instances[sid] = self._factory()
            LOGGER.debug("%s: created instance for session %s", self._name, sid)
        
        return self._instances[sid]
    
    def remove(self, session_id: str) -> None:
        """Remove and cleanup resource for a session.
        
        Args:
            session_id: Session ID to cleanup
        """
        instance = self._instances.pop(session_id, None)
        if instance is not None and self._teardown:
            try:
                self._teardown(instance)
                LOGGER.debug("%s: cleaned up session %s", self._name, session_id)
            except Exception:
                LOGGER.exception("%s: failed to cleanup session %s", self._name, session_id)
    
    def reset_all(self) -> None:
        """Reset all instances. Useful for testing."""
        for sid in list(self._instances.keys()):
            self.remove(sid)
        if self._fallback is not None and self._teardown:
            try:
                self._teardown(self._fallback)
            except Exception:
                LOGGER.debug("%s: failed to cleanup fallback", self._name, exc_info=True)
        self._fallback = None
    
    @property
    def active_sessions(self) -> list[str]:
        """Get list of active session IDs."""
        return list(self._instances.keys())


# =============================================================================
# Global Registry for Cleanup Hooks
# =============================================================================

# All registered tool runtimes (for global cleanup)
_all_registries: list[ToolRuntimeRegistry[Any]] = []


def register_runtime(registry: ToolRuntimeRegistry[T]) -> ToolRuntimeRegistry[T]:
    """Register a runtime for global cleanup.
    
    Args:
        registry: ToolRuntimeRegistry instance to register
        
    Returns:
        The same registry (for chaining)
    """
    _all_registries.append(registry)
    return registry


def cleanup_session(session_id: str) -> None:
    """Cleanup all resources for a session.
    
    Called by DeepAgentSession.close() to ensure all tool resources
    are properly cleaned up when a session ends.
    
    Args:
        session_id: Session ID to cleanup
    """
    cleaned = 0
    for registry in _all_registries:
        if session_id in registry._instances:
            registry.remove(session_id)
            cleaned += 1
    if cleaned > 0:
        LOGGER.debug("Cleaned up %d resources for session %s", cleaned, session_id)


def reset_all_runtimes() -> None:
    """Reset all registered runtimes. Useful for testing."""
    for registry in _all_registries:
        registry.reset_all()


def get_registered_runtimes() -> list[ToolRuntimeRegistry[Any]]:
    """Get all registered runtimes. Useful for debugging."""
    return list(_all_registries)


__all__ = [
    # Output policy and handler
    "ToolOutputPolicy",
    "DEFAULT_OUTPUT_POLICY",
    "DEFAULT_PREVIEW_ROWS",
    "DEFAULT_TOOL_OUTPUT_CONFIG",
    "get_output_config",
    "normalize_tool_output",
    "tool_handler",
    # Context functions
    "get_current_session_id",
    "set_session_context",
    "reset_session_context",
    "get_current_task",
    "set_task_context",
    "reset_task_context",
    "get_last_artifact_id",
    "set_last_artifact_id",
    "reset_last_artifact_id",
    # Enhanced injection API
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
    # Registry
    "ToolRuntimeRegistry",
    "register_runtime",
    "cleanup_session",
    "reset_all_runtimes",
    "get_registered_runtimes",
]
