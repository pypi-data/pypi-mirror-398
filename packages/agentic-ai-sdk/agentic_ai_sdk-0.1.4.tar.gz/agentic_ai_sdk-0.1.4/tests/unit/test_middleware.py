from __future__ import annotations

import json
import asyncio
from pathlib import Path
from typing import Any

from agent_framework import ai_function
from agent_framework._middleware import FunctionInvocationContext, FunctionMiddlewarePipeline
from types import SimpleNamespace

from agentic_ai.artifacts import ToolResult
from agentic_ai.middleware import ToolResultPersistenceMiddleware


async def _execute_pipeline(pipeline, tool, context):
    async def final_handler(ctx: FunctionInvocationContext):
        return await tool.invoke(arguments=ctx.arguments)

    return await pipeline.execute(
        function=tool,
        arguments=context.arguments,
        context=context,
        final_handler=final_handler,
    )


def test_middleware_wraps_plain_result(tmp_path: Path) -> None:
    @ai_function
    def emit(value: int) -> dict[str, Any]:
        # Tools must now return ToolResult format
        # Success: only set result, other fields default to None
        from agentic_ai.artifacts import ToolResult
        return ToolResult(result={"value": value}).model_dump()

    ctx = FunctionInvocationContext(
        function=emit,
        arguments=emit.input_model(value=7),
        kwargs={"workspace_dir": str(tmp_path), "workspace_id": "ws1", "deep_agent_id": "agent"},
    )
    pipeline = FunctionMiddlewarePipeline([ToolResultPersistenceMiddleware(auto_persist=False)])

    result = asyncio.run(_execute_pipeline(pipeline, emit, ctx))
    envelope = ToolResult.model_validate(result)

    assert envelope.result == {"value": 7}
    # status is 'ok' for success
    assert envelope.status == "ok"
    assert envelope.artifact_id is None
    assert list(tmp_path.iterdir()) == []


def test_auto_persist_creates_artifact(tmp_path: Path) -> None:
    @ai_function
    def emit(value: int) -> dict[str, Any]:
        # Tools should use persist_full to create artifacts
        from agentic_ai.artifacts import persist_full
        envelope = persist_full(
            data={"value": value},
            summary={"count": 1},
        )
        return envelope.model_dump()

    ctx = FunctionInvocationContext(
        function=emit,
        arguments=emit.input_model(value=5),
        kwargs={"workspace_dir": str(tmp_path), "workspace_id": "ws2", "agent_id": "agent"},
    )
    pipeline = FunctionMiddlewarePipeline([ToolResultPersistenceMiddleware(auto_persist=False)])

    result = asyncio.run(_execute_pipeline(pipeline, emit, ctx))
    envelope = ToolResult.model_validate(result)

    assert envelope.artifact_id is not None
    # status is 'ok' for success
    assert envelope.status == "ok"
    # persist_full sets is_preview=False
    assert envelope.is_preview is False
    artifact_dir = tmp_path / envelope.artifact_id
    assert artifact_dir.exists()
    data_path = artifact_dir / "data.json"
    assert json.loads(data_path.read_text()) == {"value": 5}
    manifest_path = artifact_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert any(entry["path"] == "data.json" for entry in manifest["files"])


def test_tool_middleware_traces_tool_calls(monkeypatch, tmp_path: Path) -> None:
    from agentic_ai.middleware import persistence as p

    monkeypatch.setattr(
        p,
        "OBSERVABILITY_SETTINGS",
        SimpleNamespace(ENABLED=True, SENSITIVE_DATA_ENABLED=True),
    )

    recorded_events: list[tuple[str, dict | None]] = []

    class DummySpan:
        def add_event(self, name, attributes=None):
            recorded_events.append((name, attributes))

    def fake_get_function_span_attributes(function, tool_call_id=None):
        return {"tool": getattr(function, "name", "emit")}

    def fake_get_function_span(attrs):
        class _Ctx:
            def __enter__(self):
                recorded_events.append(("enter", attrs))
                return DummySpan()

            def __exit__(self, exc_type, exc, tb):
                recorded_events.append(("exit", attrs))
                return False

        return _Ctx()

    monkeypatch.setattr(p, "get_function_span_attributes", fake_get_function_span_attributes)
    monkeypatch.setattr(p, "get_function_span", fake_get_function_span)

    @ai_function
    def emit(value: int) -> dict[str, Any]:
        return {"value": value}

    ctx = FunctionInvocationContext(
        function=emit,
        arguments=emit.input_model(value=3),
        kwargs={"workspace_dir": str(tmp_path), "workspace_id": "ws-span", "deep_agent_id": "agent"},
    )
    pipeline = FunctionMiddlewarePipeline([ToolResultPersistenceMiddleware(auto_persist=False)])

    result = asyncio.run(_execute_pipeline(pipeline, emit, ctx))
    assert result == {"value": 3}
    assert any(event[0] == "tool.input" for event in recorded_events)
    assert any(event[0] == "tool.output" for event in recorded_events)
