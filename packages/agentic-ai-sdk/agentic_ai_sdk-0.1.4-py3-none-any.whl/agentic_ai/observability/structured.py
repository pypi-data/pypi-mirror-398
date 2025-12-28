"""Structured logging helpers shared by Deep Agent and Agentic Analyst."""

from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

STANDARD_LOG_KEYS: set[str] = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
}


def _serialize(value: Any) -> Any:
    """Best-effort serialization for JSON logging."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return {str(k): _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_serialize(v) for v in value]
    return str(value)


def _current_trace_context() -> tuple[str | None, str | None]:
    """Return the current trace/span ids if OpenTelemetry is available."""
    try:
        from opentelemetry import trace
    except Exception:
        return None, None

    try:
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.is_valid:
            trace_id = f"{ctx.trace_id:032x}"
            span_id = f"{ctx.span_id:016x}"
            return trace_id, span_id
    except Exception:
        return None, None
    return None, None


class StructuredLogFormatter(logging.Formatter):
    """Emit logs as single-line JSON with OTEL trace context and exceptions."""

    def __init__(self, *, service: str | None = None) -> None:
        super().__init__()
        self._service = service

    def format(self, record: logging.LogRecord) -> str:
        trace_id, span_id = _current_trace_context()
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if self._service:
            payload["service"] = self._service
        if trace_id:
            payload["trace_id"] = trace_id
        if span_id:
            payload["span_id"] = span_id

        # Attach non-standard attributes as structured fields
        for key, value in record.__dict__.items():
            if key in STANDARD_LOG_KEYS or key.startswith("_"):
                continue
            payload[key] = _serialize(value)

        if record.exc_info:
            exc_type, exc, tb = record.exc_info
            payload["error"] = {
                "type": exc_type.__name__ if exc_type else None,
                "message": str(exc),
                "stack": "".join(traceback.format_exception(exc_type, exc, tb)),
            }
        elif record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)
        elif record.levelno >= logging.ERROR:
            payload["error"] = {
                "stack": "".join(traceback.format_stack(limit=25)),
            }

        return json.dumps(payload, ensure_ascii=False)


class PrettyConsoleFormatter(logging.Formatter):
    """Human-readable console renderer that still preserves key fields."""

    def __init__(self, *, service: str | None = None) -> None:
        super().__init__()
        self._service = service

    def format(self, record: logging.LogRecord) -> str:
        trace_id, span_id = _current_trace_context()
        parts = [
            datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            f"{record.levelname:7s}",
            record.name,
        ]
        if self._service:
            parts.append(f"svc={self._service}")
        if trace_id:
            parts.append(f"trace={trace_id}")
        if span_id:
            parts.append(f"span={span_id}")
        parts.append(f"msg={record.getMessage()}")

        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in STANDARD_LOG_KEYS and not k.startswith("_")
        }
        if extras:
            parts.append(f"fields={_serialize(extras)}")

        if record.exc_info:
            parts.append("exc=" + self.formatException(record.exc_info))
        elif record.stack_info:
            parts.append("stack=" + self.formatStack(record.stack_info))
        elif record.levelno >= logging.ERROR:
            parts.append("stack=" + "".join(traceback.format_stack(limit=25)))
        return " | ".join(parts)


def add_common_handlers(
    *,
    root_logger: logging.Logger,
    level: int,
    console_output: bool,
    log_file: str | None,
    formatter: logging.Formatter,
    console_formatter: logging.Formatter | None = None,
) -> None:
    """Attach console/file handlers with provided formatters."""
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter or formatter)
        root_logger.addHandler(console_handler)

    if log_file:
        from pathlib import Path

        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def build_otlp_log_handler(
    *,
    level: int,
    endpoint: str,
    headers: Mapping[str, str] | None,
    service: str,
) -> logging.Handler | None:
    """
    Create an OpenTelemetry log handler if the SDK/exporter is available.

    Returns None when OTEL logging is not installed to avoid crashing app startup.
    """
    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    except Exception as exc:  # pragma: no cover - import guard
        fallback_logger = logging.getLogger("agentic_ai.logging")
        fallback_logger.warning(
            "OTLP log export requested but OpenTelemetry logging is not available: %s", exc
        )
        return None

    resource = Resource.create({"service.name": service})
    provider = LoggerProvider(resource=resource)
    provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, headers=dict(headers or {})))
    )
    set_logger_provider(provider)
    return LoggingHandler(level=level, logger_provider=provider)
