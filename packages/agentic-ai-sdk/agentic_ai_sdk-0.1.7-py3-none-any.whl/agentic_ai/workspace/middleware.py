"""
Workspace parameter injection middleware for Deep Agent Framework.

This middleware ensures that workspace parameters are available to tool calls
even when the agent is invoked directly (e.g., through DevUI) without going
through DeepAgentSession.run().
"""
from __future__ import annotations

from typing import Any

from agent_framework import AgentMiddleware

from .core import WorkspaceHandle, AGENT_ID_KWARG, inject_workspace_kwargs


class WorkspaceParameterInjectionMiddleware(AgentMiddleware):
    """Agent middleware that injects workspace parameters into all agent calls."""

    def __init__(
        self,
        workspace: WorkspaceHandle,
        agent_id: str,
        plan_path: str | None = None,
    ):
        self._workspace = workspace
        self._agent_id = agent_id
        self._plan_path = plan_path

    async def process(self, context, next) -> None:  # type: ignore[override]
        """Inject workspace parameters before the agent processes the request."""
        inject_workspace_kwargs(
            context.kwargs,
            workspace=self._workspace,
            agent_id=self._agent_id,
            plan_path=self._plan_path,
            thread=getattr(context, "thread", None),
        )

        await next(context)


__all__ = ["WorkspaceParameterInjectionMiddleware"]
