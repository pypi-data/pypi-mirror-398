from __future__ import annotations

import asyncio
import pytest
from agent_framework import BaseChatClient, ChatMessage, ChatResponse, ChatResponseUpdate, TextContent

from agentic_ai.agent import build_agent
from agentic_ai.workspace import WorkspaceManager


class StubChatClient(BaseChatClient):
    async def _inner_get_response(self, *, messages, chat_options, **kwargs):
        return ChatResponse(
            messages=[ChatMessage(role="assistant", text="ack")],
            response_id="resp-1",
        )

    async def _inner_get_streaming_response(self, *, messages, chat_options, **kwargs):
        yield ChatResponseUpdate(
            contents=[TextContent(type="text", text="ack")],
            role="assistant",
            response_id="resp-1",
        )


def test_session_injects_workspace_kwargs(tmp_path) -> None:
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("ws-example")
    client = StubChatClient()

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="master",
        tools=[],
        instructions="You are a stub.",
        planning_enabled=True,
    )

    thread = session.ensure_thread()
    response = asyncio.run(session.run("hello", thread=thread))
    assert response.messages[0].text == "ack"

    base_kwargs = session._base_kwargs()  # intentionally using helper for assertions
    assert base_kwargs["workspace_id"] == "ws-example"
    assert "plan_path" in base_kwargs
    assert base_kwargs["agent_id"] == "master"

    with pytest.raises(ValueError):
        asyncio.run(session.run("override test", thread=thread, workspace_id="other"))


def test_session_accepts_full_message_history(tmp_path) -> None:
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("ws-messages")
    client = StubChatClient()

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="master",
        tools=[],
        instructions="You are a stub.",
        planning_enabled=False,
    )

    user_message = ChatMessage(role="user", text="请给我一个示例")
    response = asyncio.run(session.run([user_message]))
    assert response.messages[0].text == "ack"
