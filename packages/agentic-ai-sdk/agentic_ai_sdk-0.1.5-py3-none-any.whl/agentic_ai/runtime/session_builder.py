"""Session builder utilities for declarative session construction.

This module provides utilities for building agent sessions from RuntimeContext
using the declarative manifest configuration.

Example:
    from agentic_ai.runtime import bootstrap_runtime, build_session
    from agentic_ai.workspace import create_workspace
    
    ctx = bootstrap_runtime(BaseAppConfig)
    workspace = create_workspace(default_root=".ws")
    result = build_session(ctx, "agentic_analyst", workspace)
    
    # Use the session
    response = await result.session.master.run("Hello!")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from ..agent.declarative_builder import DeclarativeAgentBuilder, DeclarativeBuildResult
from .session_factory import SessionFactory, ThreadSession, DEFAULT_SESSION_TTL_SECONDS
from ..workspace import WorkspaceHandle, WorkspaceManager

if TYPE_CHECKING:
    from .context import RuntimeContext

LOGGER = logging.getLogger("agentic_ai.runtime.session_builder")


def build_session(
    runtime_ctx: "RuntimeContext",
    agent_id: str,
    workspace: WorkspaceHandle,
) -> DeclarativeBuildResult:
    """Build a session using the declarative manifest.
    
    This function creates a complete agent session with all sub-agents
    configured according to the agent manifest.
    
    Args:
        runtime_ctx: The runtime context containing configuration and manifests.
        agent_id: The ID of the master agent to build.
        workspace: The workspace handle for file operations.
        
    Returns:
        DeclarativeBuildResult containing the session and sub-agent controllers.
        
    Raises:
        ValueError: If the agent is not found in the manifest.
        
    Example:
        from agentic_ai.runtime import bootstrap_runtime, build_session
        from agentic_ai.workspace import create_workspace
        
        ctx = bootstrap_runtime(BaseAppConfig)
        workspace = create_workspace(default_root=".ws")
        result = build_session(ctx, "agentic_analyst", workspace)
        
        master = result.session
        discovery = result.subagent_controllers["data_discovery"]
    """
    # Validate agent exists
    if agent_id not in runtime_ctx.agent_store.available_agents:
        available = ", ".join(runtime_ctx.agent_store.available_agents)
        raise ValueError(
            f"Agent '{agent_id}' not found in manifest. Available agents: {available}"
        )
    
    # Build using declarative builder
    builder = DeclarativeAgentBuilder(
        ctx=runtime_ctx,
        workspace=workspace,
        manifest=runtime_ctx.agent_manifest,
        tools_manifest=runtime_ctx.tools_manifest,
    )
    
    result = builder.build_master_agent(agent_id)
    
    LOGGER.info(
        "Built session | agent_id=%s | subagents=%d",
        agent_id,
        len(result.subagent_controllers),
    )
    
    return result


def create_session_factory(
    runtime_ctx: "RuntimeContext",
    agent_id: str,
    workspace_root: Path | str,
    session_ttl_seconds: float = DEFAULT_SESSION_TTL_SECONDS,
) -> SessionFactory[ThreadSession]:
    """Create a SessionFactory for multi-tenant AG-UI servers.
    
    This function creates a SessionFactory that can manage multiple concurrent
    sessions, each with its own workspace directory and session state.
    
    Args:
        runtime_ctx: The runtime context containing configuration and manifests.
        agent_id: The ID of the master agent to build for each session.
        workspace_root: Root directory for thread workspaces.
        session_ttl_seconds: Session TTL in seconds (default: 1 hour).
        
    Returns:
        Configured SessionFactory instance.
        
    Example:
        from agentic_ai.runtime import bootstrap_runtime, create_session_factory
        
        ctx = bootstrap_runtime(BaseAppConfig)
        factory = create_session_factory(ctx, "agentic_analyst", ".ws")
        
        # Get or create session for a thread
        session = await factory.get_session("thread-123")
        master = session.master
    """
    workspace_root_path = Path(workspace_root).resolve()
    workspace_root_path.mkdir(parents=True, exist_ok=True)
    
    def session_builder(workspace: WorkspaceHandle) -> DeclarativeBuildResult:
        return build_session(runtime_ctx, agent_id, workspace)
    
    factory = SessionFactory(
        session_builder=session_builder,
        workspace_root=workspace_root_path,
        session_ttl_seconds=session_ttl_seconds,
    )
    
    LOGGER.info(
        "Created session factory | agent_id=%s | workspace_root=%s",
        agent_id,
        workspace_root_path,
    )
    
    return factory


__all__ = [
    "build_session",
    "create_session_factory",
]
