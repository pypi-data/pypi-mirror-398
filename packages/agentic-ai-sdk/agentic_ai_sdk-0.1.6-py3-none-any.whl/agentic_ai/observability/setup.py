from __future__ import annotations

import logging
from dataclasses import dataclass
from threading import Lock
from typing import Any, Sequence

from agent_framework.observability import configure_otel_providers, enable_instrumentation

LOGGER = logging.getLogger("agentic_ai.observability")
_INIT_LOCK = Lock()
_INITIALIZED = False


@dataclass(slots=True)
class ObservabilityOptions:
    """Runtime configuration for Agent Framework observability."""

    enabled: bool = False
    enable_sensitive_data: bool = False
    otlp_endpoint: str | Sequence[str] | None = None
    log_export: bool = True  # Export structured logs via OTLP using the same endpoint/headers when available
    log_headers: dict[str, str] | None = None
    application_insights_connection_string: str | None = None
    vs_code_extension_port: int | None = None
    disable_console_exporter: bool = False  # When False (default), traces output to both console and OTLP endpoint


def _normalize_endpoint(value: str | Sequence[str] | None) -> str | Sequence[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    seq = [item.strip() for item in value if item and item.strip()]
    if not seq:
        return None
    return seq if len(seq) > 1 else seq[0]


def enable_observability(options: ObservabilityOptions | None) -> bool:
    """
    Enable Agent Framework observability once per process.

    Returns:
        bool: True if observability was initialized during this call.
    """
    global _INITIALIZED
    if not options or not options.enabled:
        LOGGER.info("🔍 Observability: DISABLED (set enabled=true to enable)")
        return False

    with _INIT_LOCK:
        if _INITIALIZED:
            LOGGER.debug("Observability already initialized; skipping setup.")
            return False

        kwargs: dict[str, Any] = {
            "enable_sensitive_data": options.enable_sensitive_data,
        }
        otlp_endpoint = _normalize_endpoint(options.otlp_endpoint)
        log_export = options.log_export
        
        # Log initialization start
        LOGGER.info("🔍 Observability: Initializing OpenTelemetry tracing...")
        
        # Control console exporter based on configuration
        # When disable_console_exporter is True and OTLP endpoint exists, use custom exporters
        if options.disable_console_exporter and otlp_endpoint:
            # New API uses exporters list
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporters = []
                if isinstance(otlp_endpoint, str):
                    LOGGER.debug("   → OTLP endpoint: %s", otlp_endpoint)
                    exporters.append(OTLPSpanExporter(endpoint=otlp_endpoint))
                else:  # Sequence of endpoints
                    for ep in otlp_endpoint:
                        LOGGER.debug("   → OTLP endpoint: %s", ep)
                    exporters.extend([OTLPSpanExporter(endpoint=ep) for ep in otlp_endpoint])
                kwargs["exporters"] = exporters
                LOGGER.debug("   → Console exporter: DISABLED")
            except ImportError:
                LOGGER.warning("   ⚠️  OTLP exporter not available, falling back to default")
        elif otlp_endpoint:
            # Use framework's default behavior (both console and OTLP)
            if isinstance(otlp_endpoint, str):
                LOGGER.debug("   → OTLP endpoint: %s", otlp_endpoint)
            else:
                for ep in otlp_endpoint:
                    LOGGER.debug("   → OTLP endpoint: %s", ep)
            # Note: New API may not support otlp_endpoint directly - use environment variables instead
            import os
            if isinstance(otlp_endpoint, str):
                os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", otlp_endpoint)
            else:
                os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", otlp_endpoint[0])
            LOGGER.debug("   → Console exporter: ENABLED")
        else:
            LOGGER.debug("   → Console exporter: ENABLED (default)")
            
        if options.application_insights_connection_string:
            masked_conn = options.application_insights_connection_string[:50] + "..." if len(options.application_insights_connection_string) > 50 else options.application_insights_connection_string
            LOGGER.debug("   → Application Insights: %s", masked_conn)
            import os
            os.environ.setdefault("APPLICATIONINSIGHTS_CONNECTION_STRING", options.application_insights_connection_string)
            
        if options.vs_code_extension_port:
            LOGGER.debug("   → VS Code extension port: %s", options.vs_code_extension_port)
            kwargs["vs_code_extension_port"] = options.vs_code_extension_port
            
        LOGGER.debug("   → Sensitive data capture: %s", "ENABLED" if options.enable_sensitive_data else "DISABLED")

        # Call new agent-framework observability API
        try:
            # configure_otel_providers sets up the OTLP exporters
            configure_otel_providers(
                enable_sensitive_data=options.enable_sensitive_data,
                vs_code_extension_port=options.vs_code_extension_port,
                exporters=kwargs.get("exporters"),
            )
            # enable_instrumentation activates the agent/chat client decorators
            enable_instrumentation(enable_sensitive_data=options.enable_sensitive_data)
            _INITIALIZED = True
            
            # Log success with connection verification hint
            LOGGER.info("✅ Observability: OpenTelemetry initialized successfully")
            if otlp_endpoint:
                LOGGER.debug("   💡 Verify traces at your OTLP dashboard (e.g., Aspire Dashboard: http://localhost:18888)")
            if log_export and otlp_endpoint:
                LOGGER.debug("   → Log export: ENABLED (OTLP)")
            
            return True
        except Exception as exc:
            LOGGER.error("❌ Observability: Failed to initialize OpenTelemetry: %s", exc, exc_info=True)
            LOGGER.warning("   ⚠️  Application will continue without observability tracing")
            return False


def configure_observability_from_config(config: Any) -> bool:
    """Configure observability from an application config object.
    
    This is a convenience function that extracts observability settings from
    a config object and calls enable_observability(). Works with any config
    object that has an 'observability' attribute with the standard fields.
    
    Args:
        config: Application config object with an 'observability' attribute.
            The observability attribute should have fields like:
            - enabled: bool
            - enable_sensitive_data: bool
            - otlp_endpoint: str | list[str] | None
            - log_export: bool
            - log_headers: dict | None
            - application_insights_connection_string: str | None
            - vs_code_extension_port: int | None
            - disable_console_exporter: bool
    
    Returns:
        bool: True if observability was successfully initialized.
    
    Example:
        from agentic_ai import configure_observability_from_config
        
        config = load_config("env.yaml")
        configure_observability_from_config(config)
    """
    observability_config = getattr(config, "observability", None)
    if not observability_config or not getattr(observability_config, "enabled", False):
        return False

    options = ObservabilityOptions(
        enabled=True,
        enable_sensitive_data=getattr(observability_config, "enable_sensitive_data", False),
        otlp_endpoint=getattr(observability_config, "otlp_endpoint", None),
        log_export=getattr(observability_config, "log_export", True),
        log_headers=getattr(observability_config, "log_headers", None),
        application_insights_connection_string=getattr(
            observability_config, "application_insights_connection_string", None
        ),
        vs_code_extension_port=getattr(observability_config, "vs_code_extension_port", None),
        disable_console_exporter=getattr(observability_config, "disable_console_exporter", False),
    )
    return enable_observability(options)


__all__ = [
    "ObservabilityOptions",
    "configure_observability_from_config",
    "enable_observability",
]
