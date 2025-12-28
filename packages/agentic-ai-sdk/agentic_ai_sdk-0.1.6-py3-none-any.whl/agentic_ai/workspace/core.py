from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from agent_framework import Context, ContextProvider

from ..ids import generate_short_id

AGENT_ID_KWARG = "agent_id"


def inject_workspace_kwargs(
    kwargs: dict,
    *,
    workspace: "WorkspaceHandle",
    agent_id: str,
    plan_path: str | None = None,
    thread: object | None = None,
) -> None:
    """
    Ensure workspace-related kwargs are populated once.

    Shared by DeepAgentSession, WorkspaceContextProvider and
    WorkspaceParameterInjectionMiddleware to keep behaviour consistent.
    """
    if "workspace_id" not in kwargs:
        kwargs["workspace_id"] = workspace.workspace_id
    if "workspace_dir" not in kwargs:
        kwargs["workspace_dir"] = str(workspace.path)
    # NOTE: We intentionally do NOT inject agent_id here because agent-framework's
    # observability layer extracts agent_id from the agent instance directly.
    # Injecting it into kwargs causes "got multiple values for keyword argument 'agent_id'" error.
    if plan_path and "plan_path" not in kwargs:
        kwargs["plan_path"] = plan_path

    # Extract run_id from AG-UI thread metadata if available
    # NOTE: We intentionally do NOT inject thread_id here because agent-framework's
    # observability layer extracts thread_id from the thread parameter directly.
    # Injecting it into kwargs causes "got multiple values for keyword argument 'thread_id'" error.
    if thread:
        metadata = getattr(thread, "metadata", None) or {}
        
        # Extract run_id for request-level tracing
        if "run_id" not in kwargs:
            run_id = metadata.get("ag_ui_run_id")
            if run_id:
                kwargs["run_id"] = str(run_id)


@dataclass(slots=True)
class WorkspaceHandle:
    workspace_id: str
    root: Path

    @property
    def path(self) -> Path:
        return self.root / self.workspace_id


class WorkspaceManager:
    """Manage Deep Agent workspaces on the local filesystem."""

    def __init__(self, root: Path):
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def create(self, workspace_id: str | None = None) -> WorkspaceHandle:
        identifier = workspace_id or self._generate_unique_id()
        handle = WorkspaceHandle(workspace_id=identifier, root=self._root)
        handle.path.mkdir(parents=True, exist_ok=True)
        return handle

    def ensure(self, workspace_id: str) -> WorkspaceHandle:
        handle = WorkspaceHandle(workspace_id=workspace_id, root=self._root)
        handle.path.mkdir(parents=True, exist_ok=True)
        return handle

    def _generate_unique_id(self) -> str:
        for _ in range(5):
            candidate = generate_short_id()
            if not (self._root / candidate).exists():
                return candidate
        raise RuntimeError("Failed to generate a unique workspace identifier.")


class WorkspaceContextProvider(ContextProvider):
    """Context provider that injects workspace metadata into both instructions and kwargs."""

    def __init__(
        self,
        handle: WorkspaceHandle,
        *,
        inject_instructions: bool = True,
        plan_path: Optional[Path] = None,
        agent_id: str = "agent",
    ):
        self._handle = handle
        self._inject_instructions = inject_instructions
        self._plan_path = plan_path
        self._agent_id = agent_id

    @property
    def workspace_id(self) -> str:
        return self._handle.workspace_id

    @property
    def workspace_dir(self) -> Path:
        return self._handle.path

    @property
    def plan_path(self) -> Optional[Path]:
        return self._plan_path

    @property
    def agent_id(self) -> str:
        return self._agent_id

    def with_plan_path(self, plan_path: Optional[Path]) -> "WorkspaceContextProvider":
        self._plan_path = plan_path
        return self

    async def invoking(self, messages, **kwargs) -> Context:  # type: ignore[override]
        # Inject workspace parameters into kwargs for middleware to access
        # This is critical for tool calls through DevUI which don't go through DeepAgentSession
        inject_workspace_kwargs(
            kwargs,
            workspace=self._handle,
            agent_id=self._agent_id,
            plan_path=str(self._plan_path) if self._plan_path else None,
        )
        return Context()


def create_workspace(
    explicit_root: Path | str | None = None,
    config_root: Path | str | None = None,
    default_root: str = ".ws",
) -> WorkspaceHandle:
    """Create a workspace with priority: explicit > config > default.
    
    This is a convenience function for creating workspaces with a standard
    priority chain. Useful when workspace root can come from multiple sources.
    
    Args:
        explicit_root: Explicitly specified workspace root (highest priority).
        config_root: Workspace root from configuration (medium priority).
        default_root: Default workspace root (lowest priority). Defaults to ".ws".
    
    Returns:
        A WorkspaceHandle for the created workspace.
    
    Example:
        # From agent builder
        workspace = create_workspace(
            explicit_root=args.workspace,
            config_root=config.workspace_root,  # From your config model
        )
    """
    if explicit_root:
        resolved = Path(explicit_root).resolve()
    elif config_root:
        resolved = Path(config_root).resolve()
    else:
        resolved = Path(default_root).resolve()
    
    manager = WorkspaceManager(resolved)
    return manager.create()
