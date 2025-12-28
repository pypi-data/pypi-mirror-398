from __future__ import annotations

import asyncio

from agent_framework import BaseChatClient, ChatMessage, ChatResponse

from agentic_ai.agent import build_agent
from agentic_ai.runtime.context_compaction import CompactionConfig, CompactionSummarizer
from agentic_ai.workspace import WorkspaceManager


class SimpleChatClient(BaseChatClient):
    async def _inner_get_response(self, *, messages, chat_options, **kwargs):
        return ChatResponse(
            messages=[ChatMessage(role="assistant", text="ack")],
            response_id="demo",
        )

    async def _inner_get_streaming_response(self, *, messages, chat_options, **kwargs):
        raise RuntimeError("Streaming not supported in tests.")


class RecordingSummarizer(CompactionSummarizer):
    def __init__(self) -> None:
        self.calls = 0

    async def summarize(self, messages, config):
        self.calls += 1
        return "Summary: compacted history."


def test_context_compaction_rebuilds_history(tmp_path):
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("ws-compact")
    summarizer = RecordingSummarizer()

    session = build_agent(
        chat_client=SimpleChatClient(),
        workspace=workspace,
        agent_id="agent",
        tools=[],
        instructions="test agent",
        planning_enabled=False,
        compaction_config=CompactionConfig(enabled=True, max_messages=4, cooldown_turns=0),
        compaction_summarizer=summarizer,
    )

    thread = session.ensure_thread()

    async def _run_turns():
        for idx in range(6):
            await session.run(f"turn {idx}", thread=thread)

    asyncio.run(_run_turns())

    assert summarizer.calls >= 1
    messages = asyncio.run(thread.message_store.list_messages())
    assert len(messages) <= 5
    assert any("Summary: compacted history." in (msg.text or "") for msg in messages)
