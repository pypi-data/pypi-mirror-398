from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..artifacts.core import ArtifactStore


class ToolContextUnavailableError(RuntimeError):
    """Raised when a tool requests Deep Agent context outside of middleware scope."""


@dataclass(slots=True)
class ToolExecutionContext:
    """工具执行上下文（统一入口）。
    
    整合原 ToolContext 和 tool_runtime 中的上下文信息。
    
    Attributes:
        workspace_id: 工作空间标识符
        workspace_dir: 工作空间目录路径
        agent_id: 当前 agent 标识符
        artifact_store: artifact 存储实例
        session_id: 会话标识符
        thread_id: 线程标识符（AG-UI）
        run_id: 运行标识符（AG-UI）
        message_id: 消息标识符
        response_id: 响应标识符
        task: 当前任务（由 SubAgentController 设置）
        tool_config: 工具配置（由 middleware 注入）
    """
    workspace_id: str | None = None
    workspace_dir: Path | None = None
    agent_id: str | None = None
    artifact_store: "ArtifactStore | None" = None
    
    # Legacy fields (for backward compatibility)
    plan_path: Path | None = None
    
    # Session tracking
    session_id: str | None = None
    thread_id: str | None = None
    run_id: str | None = None
    message_id: str | None = None
    response_id: str | None = None
    
    # Task context (set by SubAgentController)
    task: Any | None = None
    
    # Tool configuration (injected by middleware)
    tool_config: dict[str, Any] = field(default_factory=dict)


_CURRENT_CONTEXT: ContextVar[ToolExecutionContext | None] = ContextVar(
    "tool_execution_context", default=None
)


def ctx() -> ToolExecutionContext:
    """获取当前工具执行上下文（必需）。
    
    Returns:
        ToolExecutionContext 实例
        
    Raises:
        ToolContextUnavailableError: 无可用上下文
        
    Example:
        context = ctx()
        store = context.artifact_store
    """
    context = _CURRENT_CONTEXT.get()
    if context is None:
        raise ToolContextUnavailableError(
            "Tool context is unavailable. Ensure tools are invoked via SDK middleware."
        )
    return context


def try_ctx() -> ToolExecutionContext | None:
    """获取当前工具执行上下文（可选）。
    
    Returns:
        上下文对象，或 None（无上下文时）
        
    Example:
        context = try_ctx()
        if context and context.artifact_store:
            # use artifact_store
            pass
    """
    return _CURRENT_CONTEXT.get()


@contextmanager
def tool_context(context: ToolExecutionContext) -> Iterator[None]:
    """上下文管理器：安装 ToolExecutionContext。
    
    Args:
        context: 要安装的上下文
        
    Example:
        with tool_context(my_context):
            # tools can now access context via ctx()
            result = my_tool()
    """
    token: Token[ToolExecutionContext | None] = _CURRENT_CONTEXT.set(context)
    try:
        yield
    finally:
        _CURRENT_CONTEXT.reset(token)

