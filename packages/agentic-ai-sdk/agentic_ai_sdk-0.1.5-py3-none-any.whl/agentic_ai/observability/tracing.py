"""OpenTelemetry tracing utilities for remote service calls.

This module provides helpers for creating spans that follow OpenTelemetry semantic conventions
for HTTP clients, database clients, and other remote services.

Semantic conventions references:
- HTTP: https://opentelemetry.io/docs/specs/semconv/http/http-spans/
- Database: https://opentelemetry.io/docs/specs/semconv/database/database-spans/
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Generator

LOGGER = logging.getLogger("agentic_ai.tracing")

# Try to import OpenTelemetry, gracefully degrade if not available
try:
    from opentelemetry import trace
    from opentelemetry.trace import SpanKind, Status, StatusCode, Span
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False
    trace = None  # type: ignore
    SpanKind = None  # type: ignore
    Status = None  # type: ignore
    StatusCode = None  # type: ignore
    Span = None  # type: ignore

# Tracer for remote service calls
_TRACER_NAME = "agentic_ai.remote_calls"


def get_tracer() -> Any:
    """Get the OpenTelemetry tracer for remote calls.
    
    Returns a no-op tracer if OpenTelemetry is not available.
    """
    if not _OTEL_AVAILABLE:
        return None
    return trace.get_tracer(_TRACER_NAME)


# Maximum size for request/response body in trace events (to avoid huge spans)
_MAX_BODY_SIZE = 8192


def _truncate_body(body: str | dict | None, max_size: int = _MAX_BODY_SIZE) -> str | None:
    """Truncate body content for tracing to avoid huge spans."""
    if body is None:
        return None
    
    import json
    if isinstance(body, dict):
        try:
            body_str = json.dumps(body, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            body_str = str(body)
    else:
        body_str = str(body)
    
    if len(body_str) > max_size:
        return body_str[:max_size] + f"... (truncated, total {len(body_str)} chars)"
    return body_str


@contextmanager
def trace_http_request(
    *,
    service_name: str,
    operation: str,
    method: str,
    url: str,
    request_body: dict | str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Context manager for tracing HTTP client requests following OTel semantic conventions.
    
    Creates a span with HTTP client semantic conventions and yields a context dict
    for recording response attributes.
    
    Args:
        service_name: Name of the remote service (e.g., "azure_search", "openmetadata")
        operation: Operation name (e.g., "search_tables", "get_table")
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        request_body: Request body (dict or string), will be recorded as span event
        attributes: Additional span attributes
        
    Yields:
        A dict that can be updated with response data. Keys like "status_code", 
        "error", "result_count", and "response_body" will be added to the span.
        
    Example:
        with trace_http_request(
            service_name="azure_search",
            operation="search_tables",
            method="POST",
            url=url,
            request_body=payload,
        ) as ctx:
            response = client.post(url, json=payload)
            ctx["status_code"] = response.status_code
            ctx["result_count"] = len(results)
            ctx["response_body"] = response.json()  # Optional: record response body
    """
    tracer = get_tracer()
    context: dict[str, Any] = {}
    
    if tracer is None:
        # OpenTelemetry not available, just yield empty context
        yield context
        return
    
    span_name = f"{service_name}.{operation}"
    span_attributes = {
        # HTTP semantic conventions
        "http.request.method": method.upper(),
        "url.full": url,
        "server.address": _extract_host(url),
        # Custom attributes
        "service.target": service_name,
        "operation.name": operation,
    }
    
    if attributes:
        for key, value in attributes.items():
            if value is not None:
                span_attributes[f"{service_name}.{key}"] = _safe_attribute_value(value)
    
    with tracer.start_as_current_span(
        span_name,
        kind=SpanKind.CLIENT,
        attributes=span_attributes,
    ) as span:
        try:
            # Record request body as span event
            if request_body is not None:
                truncated_request = _truncate_body(request_body)
                if truncated_request:
                    span.add_event(
                        "http.request.body",
                        attributes={"http.request.body.content": truncated_request},
                    )
            
            yield context
            
            # Add response attributes from context
            if "status_code" in context:
                span.set_attribute("http.response.status_code", context["status_code"])
            if "result_count" in context:
                span.set_attribute(f"{service_name}.result_count", context["result_count"])
            
            # Record response body as span event if provided
            if "response_body" in context and context["response_body"] is not None:
                truncated_response = _truncate_body(context["response_body"])
                if truncated_response:
                    span.add_event(
                        "http.response.body",
                        attributes={"http.response.body.content": truncated_response},
                    )
            
            if "error" in context:
                span.set_status(Status(StatusCode.ERROR, str(context["error"])))
                span.record_exception(context["error"]) if isinstance(context["error"], Exception) else None
            else:
                span.set_status(Status(StatusCode.OK))
                
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise


@contextmanager
def trace_database_query(
    *,
    db_system: str,
    operation: str,
    statement: str | None = None,
    server_address: str | None = None,
    database: str | None = None,
    schema: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Context manager for tracing database queries following OTel semantic conventions.
    
    Creates a span with database client semantic conventions and yields a context dict
    for recording response attributes.
    
    Args:
        db_system: Database system identifier (e.g., "databricks", "postgresql")
        operation: Database operation (e.g., "SELECT", "execute")
        statement: SQL statement (will be truncated for safety)
        server_address: Database server hostname
        database: Database/catalog name
        schema: Schema name
        attributes: Additional span attributes
        
    Yields:
        A dict that can be updated with response data.
        
    Example:
        with trace_database_query(
            db_system="databricks",
            operation="SELECT",
            statement=sql_query,
            server_address=hostname,
            database=catalog,
        ) as ctx:
            result = cursor.execute(sql_query)
            ctx["row_count"] = len(rows)
    """
    tracer = get_tracer()
    context: dict[str, Any] = {}
    
    if tracer is None:
        yield context
        return
    
    span_name = f"{db_system}.query"
    span_attributes = {
        # Database semantic conventions
        "db.system": db_system,
        "db.operation": operation,
    }
    
    if statement:
        # Truncate statement for safety (avoid huge spans)
        truncated = statement[:500] + "..." if len(statement) > 500 else statement
        span_attributes["db.statement"] = truncated
    if server_address:
        span_attributes["server.address"] = server_address
    if database:
        span_attributes["db.name"] = database
    if schema:
        span_attributes["db.sql.schema"] = schema
        
    if attributes:
        for key, value in attributes.items():
            if value is not None:
                span_attributes[f"db.{key}"] = _safe_attribute_value(value)
    
    with tracer.start_as_current_span(
        span_name,
        kind=SpanKind.CLIENT,
        attributes=span_attributes,
    ) as span:
        try:
            yield context
            
            # Add response attributes from context
            if "row_count" in context:
                span.set_attribute("db.response.row_count", context["row_count"])
            if "column_count" in context:
                span.set_attribute("db.response.column_count", context["column_count"])
            if "sampled" in context:
                span.set_attribute("db.response.sampled", context["sampled"])
            if "error" in context:
                span.set_status(Status(StatusCode.ERROR, str(context["error"])))
                if isinstance(context["error"], Exception):
                    span.record_exception(context["error"])
            else:
                span.set_status(Status(StatusCode.OK))
                
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise


def _extract_host(url: str) -> str:
    """Extract hostname from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc or parsed.hostname or url
    except Exception:
        return url


def _safe_attribute_value(value: Any) -> str | int | float | bool | list:
    """Convert value to a safe OpenTelemetry attribute value."""
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        # OTel supports homogeneous lists of primitives
        return [str(v) for v in value]
    return str(value)


__all__ = [
    "trace_http_request",
    "trace_database_query",
    "get_tracer",
]
