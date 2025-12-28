from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from agent_framework import ChatMessage

from agentic_ai.ag_ui import DeepAgentProtocolAdapter
from agentic_ai.agent import DeepAgentSession


@pytest.mark.asyncio
async def test_adapter_proxies_session_calls() -> None:
    session = MagicMock(spec=DeepAgentSession)
    session.agent_id = "agentic"
    session.agent = MagicMock()
    session.agent.id = "agentic-af"
    session.agent.name = "Agentic Analyst"
    session.agent.description = "Deep analyst"
    session.agent.display_name = "Agentic Analyst"
    session.run = AsyncMock()
    session.run_stream.return_value = "stream-object"
    session.agent.get_new_thread.return_value = "thread-123"

    adapter = DeepAgentProtocolAdapter(session)
    user_message = ChatMessage(role="user", text="hello")

    await adapter.run([user_message])
    session.run.assert_awaited_once_with([user_message], thread=None)

    assert adapter.run_stream([user_message]) == "stream-object"
    session.run_stream.assert_called_once_with([user_message], thread=None)

    assert adapter.get_new_thread(extra="value") == "thread-123"
    session.agent.get_new_thread.assert_called_once_with(extra="value")

    assert adapter.id == "agentic-af"
    assert adapter.name == "Agentic Analyst"
    assert adapter.display_name == "Agentic Analyst"
    assert adapter.description == "Deep analyst"


@pytest.mark.asyncio
async def test_adapter_requires_messages() -> None:
    session = MagicMock(spec=DeepAgentSession)
    session.agent = MagicMock()
    session.run = AsyncMock()

    adapter = DeepAgentProtocolAdapter(session)

    with pytest.raises(ValueError):
        await adapter.run()

    with pytest.raises(ValueError):
        adapter.run_stream()
