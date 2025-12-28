from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from textwrap import dedent
from typing import Iterable, Sequence

from agent_framework import AgentRunResponse, BaseChatClient, ChatAgent, ChatMessage

DEFAULT_SUMMARY_PROMPT = dedent(
    """
    You are acting as a senior AI engineer compressing the conversation history for a follow-on agent.
    Summarize the important user goals, decisions, tool results, and remaining TODOs.
    Use compact bullet points. If there are outstanding tasks, spell them out clearly.
    """
).strip()

DEFAULT_BRIDGE_TEMPLATE = dedent(
    """
    You were originally given instructions from a user over one or more turns.
    Here are the user messages so far:

    {user_messages_text}

    A previous assistant already worked on this request and produced the following summary.
    Use it to pick up the work from where it stopped and avoid duplicating effort:

    {summary_text}
    """
).strip()

LOGGER = logging.getLogger("agentic_ai.context_compaction")


@dataclass(slots=True)
class CompactionConfig:
    enabled: bool = True
    max_messages: int = 60
    token_limit: int | None = None
    cooldown_turns: int = 2
    summary_prompt: str = DEFAULT_SUMMARY_PROMPT
    bridge_template: str = DEFAULT_BRIDGE_TEMPLATE
    preserve_system_messages: int = 1
    summary_tail_messages: int = 20
    summary_max_chars: int = 2000


class CompactionSummarizer:
    async def summarize(self, messages: Sequence[ChatMessage], config: CompactionConfig) -> str:
        raise NotImplementedError


class HeuristicSummarizer(CompactionSummarizer):
    async def summarize(self, messages: Sequence[ChatMessage], config: CompactionConfig) -> str:
        tail = list(messages[-config.summary_tail_messages :])
        user_lines: list[str] = []
        assistant_lines: list[str] = []
        for msg in tail:
            text = _message_to_text(msg)
            if not text:
                continue
            if msg.role == "user":
                user_lines.append(text.strip())
            elif msg.role == "assistant":
                assistant_lines.append(text.strip())
        summary_parts: list[str] = []
        if user_lines:
            summary_parts.append("User focus:")
            summary_parts.extend(f"- {line}" for line in user_lines[-3:])
        if assistant_lines:
            summary_parts.append("Assistant actions:")
            summary_parts.extend(f"- {line}" for line in assistant_lines[-3:])
        if not summary_parts:
            summary_parts.append("No significant dialogue yet.")
        summary = "\n".join(summary_parts)
        if len(summary) > config.summary_max_chars:
            summary = summary[: config.summary_max_chars - 3] + "..."
        return summary


class LLMSummarizer(CompactionSummarizer):
    def __init__(self, chat_client: BaseChatClient, system_prompt: str | None = None) -> None:
        self._agent = ChatAgent(
            chat_client=chat_client,
            instructions=system_prompt or DEFAULT_SUMMARY_PROMPT,
        )

    async def summarize(self, messages: Sequence[ChatMessage], config: CompactionConfig) -> str:
        history_text = _format_history(messages[-config.summary_tail_messages :])
        prompt = f"{config.summary_prompt}\n\nConversation History:\n{history_text}"
        thread = self._agent.get_new_thread()
        response = await self._agent.run(prompt, thread=thread)
        text = response.text or ""
        if len(text) > config.summary_max_chars:
            text = text[: config.summary_max_chars - 3] + "..."
        return text.strip()


@dataclass(slots=True)
class ContextCompactor:
    config: CompactionConfig
    summarizer: CompactionSummarizer = field(default_factory=HeuristicSummarizer)

    _token_total: int = 0
    _turn_index: int = 0
    _last_compaction_turn: int = -100

    async def maybe_compact(
        self,
        *,
        thread,
        response: AgentRunResponse | None,
    ) -> None:
        if not self.config.enabled:
            return
        message_store = getattr(thread, "message_store", None)
        if message_store is None or not hasattr(message_store, "list_messages"):
            return

        self._turn_index += 1

        if (
            self.config.cooldown_turns > 0
            and self._turn_index - self._last_compaction_turn <= self.config.cooldown_turns
        ):
            return

        if response and getattr(response, "usage_details", None):
            usage = getattr(response.usage_details, "total_tokens", None)
            if usage:
                self._token_total += usage

        messages = await message_store.list_messages()  # type: ignore[call-arg]
        if not messages:
            return

        needs_compaction = len(messages) > self.config.max_messages
        if not needs_compaction and self.config.token_limit is not None:
            needs_compaction = self._token_total >= self.config.token_limit

        if not needs_compaction:
            return

        # Log compaction trigger reason
        trigger_reason = []
        if len(messages) > self.config.max_messages:
            trigger_reason.append(f"messages={len(messages)} > max={self.config.max_messages}")
        if self.config.token_limit and self._token_total >= self.config.token_limit:
            trigger_reason.append(f"tokens={self._token_total} >= max={self.config.token_limit}")
        
        LOGGER.info(
            "🔄 Context compaction triggered: %s",
            ", ".join(trigger_reason),
        )

        summary_text = await self.summarizer.summarize(messages, self.config)
        if not summary_text:
            LOGGER.warning("Compaction skipped because summarizer returned empty summary.")
            return

        new_messages = self._build_compacted_messages(messages, summary_text)
        if hasattr(message_store, "messages"):
            message_store.messages = new_messages  # type: ignore[attr-defined]
        elif hasattr(message_store, "update_from_state"):
            from agent_framework._threads import ChatMessageStoreState

            state = ChatMessageStoreState(messages=new_messages).to_dict()
            await message_store.update_from_state(state)  # type: ignore[attr-defined]
        else:
            LOGGER.warning("Unsupported message store type; compaction skipped.")
            return

        self._token_total = 0
        self._last_compaction_turn = self._turn_index
        LOGGER.info(
            "✅ Context compaction completed: reduced history from %d to %d messages.",
            len(messages),
            len(new_messages),
        )

    def _build_compacted_messages(
        self,
        messages: Sequence[ChatMessage],
        summary_text: str,
    ) -> list[ChatMessage]:
        system_messages = [m for m in messages if m.role == "system"]
        preserved_system = system_messages[: self.config.preserve_system_messages]

        user_lines = [
            f"- {_message_to_text(m).strip()}"
            for m in messages
            if m.role == "user" and _message_to_text(m).strip()
        ]
        user_messages_text = "\n".join(user_lines) if user_lines else "（无历史用户消息）"

        bridge_text = self.config.bridge_template.format(
            user_messages_text=user_messages_text,
            summary_text=summary_text.strip(),
        )

        new_history: list[ChatMessage] = list(preserved_system)
        new_history.append(ChatMessage(role="system", text=bridge_text))
        new_history.append(ChatMessage(role="assistant", text=summary_text.strip()))

        last_user_message = next((m for m in reversed(messages) if m.role == "user"), None)
        if last_user_message:
            new_history.append(last_user_message)

        return new_history


def _format_history(messages: Sequence[ChatMessage]) -> str:
    lines: list[str] = []
    for msg in messages:
        text = _message_to_text(msg)
        if not text:
            continue
        role = msg.role if isinstance(msg.role, str) else getattr(msg.role, "value", str(msg.role))
        lines.append(f"{role}: {text}")
    return "\n".join(lines)


def _message_to_text(message: ChatMessage) -> str:
    if message.text:
        return message.text
    contents = getattr(message, "contents", None) or []
    parts: list[str] = []
    for content in contents:
        text = getattr(content, "text", None)
        if text:
            parts.append(str(text))
            continue
        result = getattr(content, "result", None)
        if result is not None:
            try:
                parts.append(json.dumps(result, ensure_ascii=False)[:200])
            except TypeError:
                parts.append(str(result))
            continue
        arguments = getattr(content, "arguments", None)
        if arguments:
            parts.append(str(arguments))
    return "\n".join(parts)


__all__ = [
    "CompactionConfig",
    "ContextCompactor",
    "CompactionSummarizer",
    "HeuristicSummarizer",
    "LLMSummarizer",
]