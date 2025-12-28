"""Unified structured logging configuration for Deep Agent framework."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, Mapping

from .structured import (
    PrettyConsoleFormatter,
    StructuredLogFormatter,
    add_common_handlers,
    build_otlp_log_handler,
)

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logging(
    level: LogLevel = "INFO",
    *,
    log_file: Path | None = None,
    console_output: bool = True,
    format_style: Literal["structured", "pretty", "simple", "detailed"] = "structured",
    otlp_endpoint: str | None = None,
    otlp_headers: Mapping[str, str] | None = None,
    service_name: str = "agentic_ai",
) -> None:
    """
    Configure unified logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If provided, logs will be written to both console and file.
        console_output: Whether to output logs to console (default: True)
        format_style: Log format style:
            - "structured": JSON structured logs (default)
            - "pretty": Human-readable console output (still single line)
            - "simple"/"detailed": preserved for backward compatibility, map to "structured"
        otlp_endpoint: Optional OTLP gRPC endpoint for exporting logs
        otlp_headers: Optional headers dict for OTLP log exporter
        service_name: Logical service name to stamp into logs

    Example:
        >>> setup_logging(level="INFO", log_file=Path("app.log"))
        >>> setup_logging(level="DEBUG", format_style="simple")
    """
    # Remove any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set root logger level
    numeric_level = getattr(logging, level.upper())
    root_logger.setLevel(numeric_level)

    selected_style = "structured" if format_style in {"simple", "detailed"} else format_style
    structured_formatter = StructuredLogFormatter(service=service_name)
    console_formatter = structured_formatter if selected_style == "structured" else PrettyConsoleFormatter(service=service_name)

    add_common_handlers(
        root_logger=root_logger,
        level=numeric_level,
        console_output=console_output,
        log_file=str(log_file) if log_file else None,
        formatter=structured_formatter,
        console_formatter=console_formatter,
    )

    # Optional OTLP log export
    if otlp_endpoint:
        otlp_handler = build_otlp_log_handler(
            level=numeric_level,
            endpoint=otlp_endpoint,
            headers=otlp_headers,
            service=service_name,
        )
        if otlp_handler:
            root_logger.addHandler(otlp_handler)

    # Configure Deep Agent framework logs
    logging.getLogger("agentic-ai").setLevel(numeric_level)

    # Reduce verbosity of third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    # Reduce verbosity of agent framework libraries (streaming logs are very noisy)
    logging.getLogger("agent_framework").setLevel(logging.WARNING)
    logging.getLogger("agent_framework_ag_ui").setLevel(logging.WARNING)

    # Log initialization message
    logger = logging.getLogger("agentic_ai.logging")
    logger.info(
        "logging_configured",
        extra={
            "event": "logging.configured",
            "level": level,
            "console_enabled": console_output,
            "log_file": str(log_file) if log_file else None,
            "otlp_endpoint": otlp_endpoint,
            "service": service_name,
        },
    )


def setup_logging_from_config(
    config: dict,
    *,
    console_output: bool = True,
) -> None:
    """
    Configure logging from a configuration dictionary.

    Args:
        config: Configuration dict with optional 'logging' section
        console_output: Whether to output logs to console

    Example config:
        logging:
          level: INFO
          file: logs/app.log
          format: detailed
    """
    logging_config = config.get("logging", {}) or {}
    observability_config = config.get("observability", {}) or {}

    if not logging_config:
        logging_config = {
            "level": observability_config.get("log_level", "INFO"),
            "file": observability_config.get("log_file"),
            "format": observability_config.get("log_format", "structured"),
            "inherit_from_observability": True,
            "service_name": observability_config.get("log_service_name", "agentic_ai"),
            "otlp_endpoint": observability_config.get("otlp_endpoint"),
            "otlp_headers": observability_config.get("log_headers") or observability_config.get("otlp_headers"),
            "console_output": observability_config.get("log_console_output"),
        }

    level = logging_config.get("level") or "INFO"
    log_file_str = logging_config.get("file")
    log_file = Path(log_file_str) if log_file_str else None
    format_style = logging_config.get("format") or "structured"

    inherit_from_observability = logging_config.get("inherit_from_observability", True)
    otlp_endpoint = logging_config.get("otlp_endpoint")
    otlp_headers = logging_config.get("otlp_headers")
    service_name = logging_config.get("service_name") or "agentic_ai"
    console_pref = logging_config.get("console_output")

    if inherit_from_observability:
        obs_log_export = observability_config.get("log_export", True)
        if obs_log_export:
            if not otlp_endpoint:
                otlp_endpoint = observability_config.get("otlp_endpoint")
            if not otlp_headers:
                otlp_headers = (
                    observability_config.get("log_headers")
                    or observability_config.get("otlp_headers")
                )

    setup_logging(
        level=level,  # type: ignore[arg-type]
        log_file=log_file,
        console_output=console_pref if console_pref is not None else console_output,
        format_style=format_style,  # type: ignore[arg-type]
        otlp_endpoint=otlp_endpoint,
        otlp_headers=otlp_headers,
        service_name=service_name,
    )


__all__ = [
    "setup_logging",
    "setup_logging_from_config",
    "LogLevel",
]
