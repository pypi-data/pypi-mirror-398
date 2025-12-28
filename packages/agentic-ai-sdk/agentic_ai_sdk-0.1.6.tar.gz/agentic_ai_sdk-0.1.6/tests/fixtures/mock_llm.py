"""Mock LLM client for testing without real API calls."""

from agent_framework import (
    BaseChatClient,
    ChatMessage,
    ChatResponse,
    ChatResponseUpdate,
    TextContent,
)


class MockChatClient(BaseChatClient):
    """
    Mock chat client for testing without real API calls.
    
    Args:
        responses: List of predefined text responses. Each call cycles through the list,
                  repeating the last response for subsequent calls.
    
    Attributes:
        call_count: Number of times the client has been called
        captured_messages: List of all message lists passed to the client
    
    Example:
        >>> client = MockChatClient(["Response 1", "Response 2"])
        >>> # First call returns "Response 1", second returns "Response 2"
        >>> # All subsequent calls return "Response 2"
    """

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or ["Task completed successfully."]
        self.call_count = 0
        self.captured_messages: list[list[ChatMessage]] = []

    async def _inner_get_response(self, *, messages, chat_options, **kwargs):
        """Return a non-streaming chat response."""
        self.captured_messages.append(list(messages))
        response_text = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        return ChatResponse(
            messages=[ChatMessage(role="assistant", text=response_text)],
            response_id=f"resp-{self.call_count}",
        )

    async def _inner_get_streaming_response(self, *, messages, chat_options, **kwargs):
        """Yield a streaming chat response."""
        self.captured_messages.append(list(messages))
        response_text = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        yield ChatResponseUpdate(
            contents=[TextContent(type="text", text=response_text)],
            role="assistant",
            response_id=f"resp-{self.call_count}",
        )
