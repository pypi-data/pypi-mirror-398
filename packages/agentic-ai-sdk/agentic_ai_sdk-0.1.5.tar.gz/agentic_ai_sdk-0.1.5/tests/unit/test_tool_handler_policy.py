from __future__ import annotations

import pytest

from agentic_ai.artifacts import ToolResult
from agentic_ai.runtime.tool_runtime import ToolOutputPolicy, tool_handler


def test_tool_handler_managed_catches_exceptions() -> None:
    @tool_handler(policy=ToolOutputPolicy.MANAGED)
    def boom() -> dict:
        raise ValueError("boom")

    result = boom()
    envelope = ToolResult.model_validate(result)
    assert envelope.status == "error"
    assert "ValueError: boom" in (envelope.error_message or "")


def test_tool_handler_raw_propagates_exceptions() -> None:
    @tool_handler(policy=ToolOutputPolicy.RAW)
    def boom() -> dict:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        boom()


def test_tool_handler_manual_propagates_exceptions() -> None:
    @tool_handler(policy=ToolOutputPolicy.MANUAL)
    def boom() -> dict:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        boom()
