"""Unit tests for sub_agent module."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from agentic_ai.artifacts import ToolResult
from agentic_ai.agent.sub_agent import _handle_response, _auto_load_artifact, _extract_last_json
from agentic_ai.runtime.tool_runtime import set_last_artifact_id, reset_last_artifact_id


class MockAgentRunResponse:
    """Mock AgentRunResponse for testing."""
    def __init__(self, text: str = ""):
        self.text = text
        self.messages = []


@dataclass
class MockController:
    """Mock SubAgentController for testing."""
    toolset: Any | None = None


class TestExtractLastJson:
    """Tests for _extract_last_json function."""

    def test_extract_simple_object(self):
        """Extract a simple JSON object."""
        text = 'Here is the result: {"key": "value"}'
        result = _extract_last_json(text)
        assert result == {"key": "value"}

    def test_extract_nested_object(self):
        """Extract a nested JSON object."""
        text = 'Output: {"outer": {"inner": 123}}'
        result = _extract_last_json(text)
        assert result == {"outer": {"inner": 123}}

    def test_extract_array(self):
        """Extract a JSON array."""
        text = 'List: [1, 2, 3]'
        result = _extract_last_json(text)
        assert result == [1, 2, 3]

    def test_extract_last_json_multiple(self):
        """When multiple JSON objects, extract the last one."""
        text = 'First: {"a": 1}. Second: {"b": 2}'
        result = _extract_last_json(text)
        assert result == {"b": 2}

    def test_no_json_returns_none(self):
        """When no JSON found, return None."""
        text = 'Just plain text here'
        result = _extract_last_json(text)
        assert result is None

    def test_empty_text_returns_none(self):
        """Empty text returns None."""
        assert _extract_last_json("") is None
        assert _extract_last_json(None) is None

    def test_json_with_artifact_id(self):
        """Extract JSON containing artifact_id."""
        text = 'Discovery complete. {"artifact_id": "abc123", "status": "ok"}'
        result = _extract_last_json(text)
        assert result == {"artifact_id": "abc123", "status": "ok"}


class TestHandleResponse:
    """Tests for _handle_response function."""

    def setup_method(self):
        """Reset context var before each test."""
        reset_last_artifact_id()

    def teardown_method(self):
        """Reset context var after each test."""
        reset_last_artifact_id()

    def test_none_mode_returns_raw_text(self):
        """response_handling=None returns raw text."""
        controller = MockController()
        response = MockAgentRunResponse(text="Raw response text")
        
        result = _handle_response(controller, response, {}, None)
        assert result == "Raw response text"

    def test_none_string_mode_returns_raw_text(self):
        """response_handling='none' returns raw text."""
        controller = MockController()
        response = MockAgentRunResponse(text="Raw response text")
        
        result = _handle_response(controller, response, {}, "none")
        assert result == "Raw response text"

    def test_parse_json_extracts_json(self):
        """response_handling='parse_json' extracts JSON."""
        controller = MockController()
        response = MockAgentRunResponse(text='Result: {"data": "value"}')
        
        result = _handle_response(controller, response, {}, "parse_json")
        assert result == {"data": "value"}

    def test_parse_json_fallback_to_text(self):
        """parse_json falls back to raw text if no JSON found."""
        controller = MockController()
        response = MockAgentRunResponse(text="No JSON here")
        
        result = _handle_response(controller, response, {}, "parse_json")
        assert result == "No JSON here"

    def test_last_artifact_gets_from_context(self):
        """response_handling='last_artifact' gets ID from context."""
        set_last_artifact_id("context-art-123")
        
        controller = MockController()
        response = MockAgentRunResponse()
        
        result = _handle_response(controller, response, {}, "last_artifact")
        assert result == {"artifact_id": "context-art-123"}

    def test_last_artifact_no_id_returns_error(self):
        """last_artifact with no ID returns error dict."""
        controller = MockController()
        response = MockAgentRunResponse()
        
        result = _handle_response(controller, response, {}, "last_artifact")
        assert result["artifact_id"] is None
        assert "error" in result


class TestAutoLoadArtifact:
    """Tests for _auto_load_artifact function."""

    @patch("agentic_ai.agent.sub_agent.load_artifact")
    def test_loads_artifact_by_id(self, mock_load):
        """Loads artifact data when result has artifact_id."""
        mock_load.return_value = {"tables": ["t1"], "metrics": []}
        
        result = {"artifact_id": "art-123"}
        response = MockAgentRunResponse()
        
        output = _auto_load_artifact(result, response, {})
        
        mock_load.assert_called_once_with("art-123", format="json")
        assert output["result"] == {"tables": ["t1"], "metrics": []}
        assert output["artifact_id"] == "art-123"

    def test_no_artifact_id_wraps_result(self):
        """When no artifact_id, wrap result in ToolResult."""
        result = {"data": "value"}
        response = MockAgentRunResponse()
        
        output = _auto_load_artifact(result, response, {})
        
        assert output["result"] == {"data": "value"}
        assert "artifact_id" not in output or output.get("artifact_id") is None

    def test_string_result_wrapped(self):
        """String result is wrapped in dict."""
        result = "just text"
        response = MockAgentRunResponse()
        
        output = _auto_load_artifact(result, response, {})
        
        assert output["result"] == {"text": "just text"}

    @patch("agentic_ai.agent.sub_agent.load_artifact")
    def test_handles_load_error_returns_error_result(self, mock_load):
        """Returns error ToolResult when artifact load fails."""
        mock_load.side_effect = FileNotFoundError("File not found")
        
        result = {"artifact_id": "bad-art"}
        response = MockAgentRunResponse()
        
        output = _auto_load_artifact(result, response, {})
        
        # Should return error status, not swallow the error
        assert output["status"] == "error"
        assert "bad-art" in output["error_message"]
        assert output["result"] == {"artifact_id": "bad-art"}

    @patch("agentic_ai.agent.sub_agent.load_artifact")
    def test_handles_load_error_raises_when_configured(self, mock_load):
        """Raises exception when on_error is RAISE."""
        from agentic_ai.agent.sub_agent import AutoLoadOnError
        mock_load.side_effect = FileNotFoundError("File not found")
        
        result = {"artifact_id": "bad-art"}
        response = MockAgentRunResponse()
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            _auto_load_artifact(result, response, {}, on_error=AutoLoadOnError.RAISE)

    @patch("agentic_ai.agent.sub_agent.load_artifact")
    def test_output_is_valid_tool_result(self, mock_load):
        """Output can be parsed as ToolResult."""
        mock_load.return_value = {"data": "test"}
        
        result = {"artifact_id": "art-789"}
        response = MockAgentRunResponse()
        
        output = _auto_load_artifact(result, response, {})
        
        envelope = ToolResult.model_validate(output)
        assert envelope.result == {"data": "test"}
        assert envelope.artifact_id == "art-789"

