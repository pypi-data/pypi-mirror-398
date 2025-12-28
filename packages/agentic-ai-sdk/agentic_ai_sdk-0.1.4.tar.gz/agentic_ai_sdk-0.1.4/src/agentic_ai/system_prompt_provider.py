from __future__ import annotations

"""Context provider that injects a system prompt only when none is present.

Prevents double-injection when the caller already supplies a system message,
while still guaranteeing a system prompt for callers that send only user
messages. Keeps master and sub-agents consistent.
"""

import logging

from agent_framework import ChatMessage, Context, ContextProvider

LOGGER = logging.getLogger(__name__)


class SystemPromptContextProvider(ContextProvider):
    def __init__(self, prompt: str):
        self._prompt = prompt

    async def invoking(self, messages, **kwargs) -> Context:  # type: ignore[override]
        # If any system message already exists, skip injection to avoid duplicates.
        msg_list = messages if isinstance(messages, list) else ([messages] if messages else [])
        LOGGER.debug(
            "SystemPromptContextProvider.invoking called | messages_count=%d",
            len(msg_list),
        )
        for msg in msg_list:
            role = getattr(msg, "role", None)
            # role can be str or Role enum; normalize to string for comparison
            role_val = getattr(role, "value", role) if role else None
            LOGGER.debug("  Message role: %s", role_val)
            if role_val == "system":
                LOGGER.info(
                    "SystemPromptContextProvider: Found existing system message, skipping injection"
                )
                return Context()

        if not self._prompt:
            LOGGER.warning("SystemPromptContextProvider: No prompt configured")
            return Context()

        LOGGER.info(
            "SystemPromptContextProvider: Injecting system prompt | len=%d",
            len(self._prompt),
        )
        return Context(messages=[ChatMessage(role="system", text=self._prompt)])


__all__ = ["SystemPromptContextProvider"]
