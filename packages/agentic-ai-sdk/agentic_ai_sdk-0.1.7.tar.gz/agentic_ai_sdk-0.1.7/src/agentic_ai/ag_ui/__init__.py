"""AG-UI protocol support for Agentic AI SDK.

This subpackage provides:
- DeepAgentProtocolAdapter: Adapter for AG-UI protocol
- AG-UI server components
"""
from __future__ import annotations

from .adapter import (
    DeepAgentProtocolAdapter,
    SessionProvider,
    build_ag_ui_agent,
    build_multi_tenant_ag_ui_agent,
)
from .server import (
    AgUIAppOptions,
    ConcurrencyLimitMiddleware,
    HealthCheckFilter,
    build_ag_ui_arg_parser,
    create_ag_ui_app,
    run_ag_ui_server,
)

__all__ = [
    # Adapter
    "DeepAgentProtocolAdapter",
    "SessionProvider",
    "build_ag_ui_agent",
    "build_multi_tenant_ag_ui_agent",
    # Server
    "AgUIAppOptions",
    "ConcurrencyLimitMiddleware",
    "HealthCheckFilter",
    "build_ag_ui_arg_parser",
    "create_ag_ui_app",
    "run_ag_ui_server",
]
