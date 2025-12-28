"""Observability utilities for Deep Agent.

This subpackage provides:
- Tracing: OpenTelemetry span creation for HTTP/DB calls
- Logging: Structured logging setup
- Observability setup: enable_observability, configure_observability_from_config

Example:
    from agentic_ai.observability import (
        enable_observability,
        configure_observability_from_config,
        trace_http_request,
        setup_logging,
    )
"""
from __future__ import annotations

# Re-export from files in this directory
from .setup import (
    ObservabilityOptions,
    enable_observability,
    configure_observability_from_config,
)
from .tracing import (
    get_tracer,
    trace_database_query,
    trace_http_request,
)
from .logging import (
    LogLevel,
    setup_logging,
    setup_logging_from_config,
)
from .structured import (
    StructuredLogFormatter,
    PrettyConsoleFormatter,
    add_common_handlers,
)

__all__ = [
    # Observability setup
    "ObservabilityOptions",
    "enable_observability",
    "configure_observability_from_config",
    # Tracing
    "get_tracer",
    "trace_database_query",
    "trace_http_request",
    # Logging
    "LogLevel",
    "setup_logging",
    "setup_logging_from_config",
    "StructuredLogFormatter",
    "PrettyConsoleFormatter",
    "add_common_handlers",
]
