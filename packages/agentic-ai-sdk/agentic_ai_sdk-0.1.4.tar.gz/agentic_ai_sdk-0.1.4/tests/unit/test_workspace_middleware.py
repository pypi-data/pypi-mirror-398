from __future__ import annotations

import asyncio
from types import SimpleNamespace

from agentic_ai.workspace import WorkspaceManager, WorkspaceParameterInjectionMiddleware


def test_workspace_middleware_injects_agent_context(tmp_path):
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("mid-ws")
    middleware = WorkspaceParameterInjectionMiddleware(
        workspace=workspace,
        agent_id="agent-x",
        plan_path="/tmp/plan.json",
    )

    captured_kwargs: dict[str, str] = {}

    async def _next(ctx):
        captured_kwargs.update(ctx.kwargs)

    context = SimpleNamespace(kwargs={}, thread=None)
    asyncio.run(middleware.process(context, _next))

    assert captured_kwargs["workspace_id"] == "mid-ws"
    assert captured_kwargs["workspace_dir"] == str(workspace.path)
    assert captured_kwargs["agent_id"] == "agent-x"
    assert captured_kwargs["plan_path"] == "/tmp/plan.json"
