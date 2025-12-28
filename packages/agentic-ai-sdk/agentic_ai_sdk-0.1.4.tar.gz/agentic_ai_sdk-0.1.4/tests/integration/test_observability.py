"""Integration tests for Agentic AI observability helpers."""

from __future__ import annotations

import importlib

import pytest

import agentic_ai.observability as observability_module
import agentic_ai.observability.setup as observability_setup_module


@pytest.fixture(autouse=True)
def reset_observability_state():
    """Ensure each test starts with a clean observability module state."""
    importlib.reload(observability_setup_module)
    importlib.reload(observability_module)
    yield
    importlib.reload(observability_setup_module)
    importlib.reload(observability_module)


def test_enable_observability_only_initializes_once(monkeypatch):
    """enable_observability should configure tracing once and skip duplicate calls."""
    captured_calls: list[dict] = []

    def fake_configure_otel_providers(**kwargs):
        captured_calls.append(kwargs)
    
    def fake_enable_instrumentation(**kwargs):
        pass  # No-op for testing

    monkeypatch.setattr(observability_setup_module, "configure_otel_providers", fake_configure_otel_providers)
    monkeypatch.setattr(observability_setup_module, "enable_instrumentation", fake_enable_instrumentation)

    options = observability_module.ObservabilityOptions(
        enabled=True,
        enable_sensitive_data=True,
        otlp_endpoint="http://localhost:4317",
        application_insights_connection_string="InstrumentationKey=test",
        vs_code_extension_port=6319,
    )

    first = observability_module.enable_observability(options)
    second = observability_module.enable_observability(options)

    assert first is True
    assert second is False  # No re-initialization
    assert len(captured_calls) == 1
    assert captured_calls[0]["enable_sensitive_data"] is True
    assert captured_calls[0]["vs_code_extension_port"] == 6319
    assert captured_calls[0]["vs_code_extension_port"] == 6319
