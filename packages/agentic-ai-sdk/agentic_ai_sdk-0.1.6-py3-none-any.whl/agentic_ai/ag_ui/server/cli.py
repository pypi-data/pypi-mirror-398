"""CLI helpers for AG-UI servers."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

import uvicorn

from ...runtime.session_factory import DEFAULT_SESSION_TTL_SECONDS
from ...config import BaseAppConfig
from ...observability import configure_observability_from_config
from ...runtime import bootstrap_runtime, build_session, create_session_factory
from ...workspace import create_workspace
from ...observability.logging import setup_logging_from_config
from .app import AgUIAppOptions, DEFAULT_CORS_ORIGINS, create_ag_ui_app, load_ui_config
from .middleware import HealthCheckFilter

LOGGER = logging.getLogger("agentic_ai.ag_ui_server")

def build_ag_ui_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Expose a Deep Agent over the AG-UI protocol."
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        default=None,
        help="Path to env.yaml (defaults to ./env.yaml if omitted)",
    )
    parser.add_argument(
        "--manifest-dir",
        dest="manifest_dir",
        default="manifest",
        help="Manifest directory (default: manifest)",
    )
    parser.add_argument(
        "--ui-config",
        dest="ui_config_path",
        default=None,
        help="Path to manifest/ui.yaml (defaults to ./manifest/ui.yaml if omitted)",
    )
    parser.add_argument(
        "--workspace-root",
        dest="workspace_root",
        default=None,
        help="Optional workspace root directory (defaults to ./.ws)",
    )
    parser.add_argument(
        "--agent",
        dest="agent_id",
        default="agentic_analyst",
        help="Agent ID to serve (default: agentic_analyst)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface for the AG-UI server (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the AG-UI server (default: 8000)",
    )
    parser.add_argument(
        "--allow-origin",
        action="append",
        dest="allow_origins",
        default=None,
        help="Allowed CORS origins (may be provided multiple times).",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Path prefix for the AG-UI endpoint (default: /)",
    )
    parser.add_argument(
        "--single-tenant",
        action="store_true",
        dest="single_tenant",
        help="Use single-tenant mode (shared session). Default is multi-tenant.",
    )
    parser.add_argument(
        "--session-ttl",
        type=int,
        dest="session_ttl",
        default=DEFAULT_SESSION_TTL_SECONDS,
        help=f"Session TTL in seconds (default: {DEFAULT_SESSION_TTL_SECONDS})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1, use 0 for auto based on CPU cores)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        dest="max_concurrent",
        default=None,
        help="Maximum concurrent requests per worker (default: 100)",
    )
    health_group = parser.add_mutually_exclusive_group()
    health_group.add_argument(
        "--enable-health",
        dest="enable_health",
        action="store_true",
        default=None,
        help="Enable /health endpoint (default: enabled)",
    )
    health_group.add_argument(
        "--disable-health",
        dest="enable_health",
        action="store_false",
        help="Disable /health endpoint",
    )
    ready_group = parser.add_mutually_exclusive_group()
    ready_group.add_argument(
        "--enable-ready",
        dest="enable_ready",
        action="store_true",
        default=None,
        help="Enable /ready endpoint (default: enabled)",
    )
    ready_group.add_argument(
        "--disable-ready",
        dest="enable_ready",
        action="store_false",
        help="Disable /ready endpoint",
    )
    ui_config_group = parser.add_mutually_exclusive_group()
    ui_config_group.add_argument(
        "--enable-ui-config",
        dest="enable_ui_config",
        action="store_true",
        default=None,
        help="Enable /api/ui-config endpoints (default: enabled)",
    )
    ui_config_group.add_argument(
        "--disable-ui-config",
        dest="enable_ui_config",
        action="store_false",
        help="Disable /api/ui-config endpoints",
    )
    return parser


def run_ag_ui_server(
    *,
    agent_id: str = "agentic_analyst",
    config_path: str | Path | None = None,
    manifest_dir: str | Path = "manifest",
    ui_config_path: str | Path | None = None,
    workspace_root: str | Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str | None = None,
    allow_origins: Sequence[str] | None = None,
    single_tenant: bool = False,
    session_ttl: int = DEFAULT_SESSION_TTL_SECONDS,
    workers: int = 1,
    max_concurrent: int | None = None,
    enable_ready: bool | None = None,
    enable_health: bool | None = None,
    enable_ui_config: bool | None = None,
    require_confirmation: bool | None = None,
    config_class: type[BaseAppConfig] = BaseAppConfig,
    app_options: AgUIAppOptions | None = None,
) -> None:
    multi_tenant = not single_tenant

    ctx = bootstrap_runtime(
        config_class,
        config_path=config_path,
        manifest_dir=manifest_dir,
    )
    configure_observability_from_config(ctx.config)
    setup_logging_from_config(ctx.config.model_dump())

    agent_config = ctx.agent_store.get_config_optional(agent_id)
    if agent_config is None:
        raise ValueError(
            f"Agent '{agent_id}' not found in manifest. "
            f"Available agents: {', '.join(ctx.agent_store.available_agents)}"
        )

    config_ag_ui = getattr(ctx.config, "ag_ui", None)
    allow_origins = (
        allow_origins
        if allow_origins is not None
        else (
            config_ag_ui.allowed_origins
            if config_ag_ui and config_ag_ui.allowed_origins is not None
            else DEFAULT_CORS_ORIGINS
        )
    )
    max_concurrent = (
        max_concurrent
        if max_concurrent is not None
        else (config_ag_ui.max_concurrent if config_ag_ui else 100)
    )
    enable_ready = (
        enable_ready
        if enable_ready is not None
        else (config_ag_ui.enable_ready if config_ag_ui else True)
    )
    enable_health = (
        enable_health
        if enable_health is not None
        else (config_ag_ui.enable_health if config_ag_ui else True)
    )
    enable_ui_config = (
        enable_ui_config
        if enable_ui_config is not None
        else (config_ag_ui.enable_ui_config if config_ag_ui else True)
    )
    require_confirmation = (
        require_confirmation
        if require_confirmation is not None
        else (config_ag_ui.require_confirmation if config_ag_ui else False)
    )
    path = path if path is not None else (config_ag_ui.path if config_ag_ui else "/")

    options = app_options or AgUIAppOptions(
        allowed_origins=allow_origins,
        max_concurrent=max_concurrent,
        enable_ready=enable_ready,
        enable_health=enable_health,
        enable_ui_config=enable_ui_config,
    )
    ui_config = load_ui_config(ui_config_path)

    if multi_tenant:
        session_factory = create_session_factory(
            runtime_ctx=ctx,
            agent_id=agent_id,
            workspace_root=workspace_root or ".ws",
            session_ttl_seconds=session_ttl,
        )
        session_provider = session_factory.get_session
        session_stats_provider = lambda: {
            **session_factory.get_stats(),
            "max_concurrent": max_concurrent,
        }
    else:
        workspace = create_workspace(
            explicit_root=workspace_root,
            default_root=".ws",
        )
        build_result = build_session(
            runtime_ctx=ctx,
            agent_id=agent_id,
            workspace=workspace,
        )
        session_provider = None
        session_stats_provider = None

    agent_name = agent_config.name or agent_id
    if not multi_tenant and build_result.session.agent.name:
        agent_name = build_result.session.agent.name

    app = create_ag_ui_app(
        ui_config=ui_config,
        options=options,
        session=build_result.session if not multi_tenant else None,
        session_provider=session_provider if multi_tenant else None,
        session_stats_provider=session_stats_provider,
        ag_ui_path=path,
        agent_name=agent_name,
        agent_description=(
            "Deep Agent (Multi-Tenant)" if multi_tenant else "Deep Agent (Single-Tenant)"
        ),
        require_confirmation=require_confirmation,
    )

    if multi_tenant:
        app.state.session_factory = session_factory
    else:
        app.state.session_build = build_result
        app.state.workspace = workspace

    logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

    effective_workers = workers
    if effective_workers == 0:
        effective_workers = 1
    elif effective_workers > 1:
        LOGGER.warning(
            "Requested %d workers, but AG-UI server runs in single-worker mode.",
            effective_workers,
        )
        effective_workers = 1

    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=effective_workers,
        timeout_keep_alive=75,
        timeout_graceful_shutdown=30,
        log_level="info",
    )


__all__ = ["build_ag_ui_arg_parser", "run_ag_ui_server"]
