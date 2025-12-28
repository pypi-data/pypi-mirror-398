from __future__ import annotations

import json
import logging
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from agent_framework import FunctionMiddleware
from agent_framework.observability import (
    OBSERVABILITY_SETTINGS,
    capture_exception as otel_capture_exception,
    get_function_span,
    get_function_span_attributes,
)

from ..artifacts.core import ArtifactStore, ToolResult
from ..runtime.contexts import ToolExecutionContext, tool_context
from ..workspace.core import AGENT_ID_KWARG

_LOGGER = logging.getLogger("agentic_ai.tools")


def _preview(value: Any, limit: int = 300) -> str:
    if value is None:
        return "None"
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        text = str(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _start_tool_span(context):
    if not OBSERVABILITY_SETTINGS.ENABLED:
        return nullcontext(None)
    tool_call_id = (
        context.kwargs.get("tool_call_id")
        or context.kwargs.get("message_id")
        or context.kwargs.get("response_id")
    )
    attributes = get_function_span_attributes(context.function, tool_call_id=tool_call_id)
    return get_function_span(attributes)


def _maybe_parse_tool_result(result: Any) -> ToolResult | None:
    if isinstance(result, ToolResult):
        return result
    if not isinstance(result, dict):
        return None
    try:
        return ToolResult.model_validate(result)
    except Exception:
        return None


def _auto_persist_result(
    result: Any,
    parsed: ToolResult | None,
    store: ArtifactStore,
) -> dict[str, Any]:
    if parsed is not None:
        if parsed.status != "ok":
            return result
        if parsed.artifact_id is not None:
            return result
        if parsed.result is None:
            return result
        data_to_persist = parsed.result
        summary = parsed.summary
    else:
        if result is None:
            return result
        data_to_persist = result
        summary = None

    artifact_id, _ = store.create_json_artifact(data=data_to_persist)
    return ToolResult(
        result=data_to_persist,
        artifact_id=artifact_id,
        summary=summary,
        is_preview=False,
    ).model_dump()


class ToolResultPersistenceMiddleware(FunctionMiddleware):
    """Function middleware that normalizes tool outputs and manages artifact persistence."""

    def __init__(self, *, auto_persist: bool = False, agent_id: str | None = None) -> None:
        self._auto_persist = auto_persist
        self._agent_id = agent_id

    async def process(self, context, next) -> None:  # type: ignore[override]
        workspace_dir = context.kwargs.get("workspace_dir")
        workspace_id = context.kwargs.get("workspace_id")
        # Use injected agent_id first, then fall back to kwargs
        agent_id = self._agent_id or context.kwargs.get(AGENT_ID_KWARG) or context.kwargs.get("agent_id")
        plan_path = context.kwargs.get("plan_path")
        thread_id = context.kwargs.get("thread_id")
        run_id = context.kwargs.get("run_id")
        message_id = context.kwargs.get("message_id")
        response_id = context.kwargs.get("response_id")
        session_id = context.kwargs.get("session_id")
        
        function_name = getattr(context.function, "name", getattr(context.function, "__name__", "unknown"))
        args_value = (
            context.arguments.model_dump(mode="json")
            if hasattr(context.arguments, "model_dump")
            else context.arguments
        )
        
        # Start timing
        start_time = time.time()
        
        # Build log context
        log_parts = [
            f"tool={function_name}",
            f"agent={agent_id or 'none'}",
            f"workspace={workspace_id or 'none'}",
        ]
        if thread_id:
            log_parts.append(f"thread={thread_id}")
        if run_id:
            log_parts.append(f"run={run_id}")
        # MAF observability automatically traces execute_tool span with function_name, args, results, duration
        # We only need to log errors with full stack traces since MAF doesn't capture those details
        
        artifact_store: ArtifactStore | None = None
        final_result: ToolResult | None = None
        handled = False
        span = None
        span_cm = _start_tool_span(context)
        try:
            with span_cm as active_span:
                span = active_span
                if span and OBSERVABILITY_SETTINGS.SENSITIVE_DATA_ENABLED:
                    span.add_event(
                        "tool.input",
                        {"preview": _preview(args_value, limit=500)},
                    )

                if workspace_dir and workspace_id and agent_id:
                    artifact_store = ArtifactStore(Path(workspace_dir))
                    tool_ctx = ToolExecutionContext(
                        workspace_id=workspace_id,
                        workspace_dir=artifact_store.workspace_dir,
                        agent_id=agent_id,
                        artifact_store=artifact_store,
                        plan_path=Path(plan_path) if plan_path else None,
                        session_id=session_id,
                        thread_id=thread_id,
                        run_id=run_id,
                        message_id=message_id,
                        response_id=response_id,
                    )
                    with tool_context(tool_ctx):
                        await next(context)
                        final_result = _maybe_parse_tool_result(context.result)
                        handled = True

                if not handled:
                    await next(context)
                    final_result = _maybe_parse_tool_result(context.result)

                if self._auto_persist and artifact_store:
                    context.result = _auto_persist_result(
                        context.result,
                        final_result,
                        artifact_store,
                    )
                    final_result = _maybe_parse_tool_result(context.result)

                if span and OBSERVABILITY_SETTINGS.SENSITIVE_DATA_ENABLED:
                    span.add_event(
                        "tool.output",
                        {"preview": _preview(context.result, limit=500)},
                    )
        except Exception as exc:
            if span:
                otel_capture_exception(span=span, exception=exc, timestamp=time.time_ns())
            
            # ERROR level: Tool call ERROR with full traceback
            # This supplements MAF observability which only records error events
            duration = time.time() - start_time
            error_type = type(exc).__name__
            error_msg = str(exc)
            
            _LOGGER.error(
                "❌ Tool call ERROR | tool=%s | agent=%s | duration=%.3fs | error=%s: %s",
                function_name,
                agent_id or 'none',
                duration,
                error_type,
                error_msg,
                exc_info=True,  # Include full exception traceback
            )
            raise


__all__ = ["ToolResultPersistenceMiddleware"]
