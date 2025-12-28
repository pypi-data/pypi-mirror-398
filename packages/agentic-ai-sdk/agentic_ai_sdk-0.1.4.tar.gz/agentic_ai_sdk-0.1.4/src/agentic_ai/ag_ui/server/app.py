"""AG-UI FastAPI server helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import yaml
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from agent_framework_ag_ui import add_agent_framework_fastapi_endpoint

from ..adapter import build_ag_ui_agent, build_multi_tenant_ag_ui_agent, SessionProvider
from ...agent import DeepAgentSession
from ...defaults import UI_CONFIG_FILE
from .middleware import ConcurrencyLimitMiddleware


DEFAULT_CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
SessionStatsProvider = Callable[[], dict[str, Any]]


@dataclass(frozen=True)
class AgUIAppOptions:
    allowed_origins: Sequence[str] = ()
    max_concurrent: int = 100
    enable_ready: bool = True
    enable_health: bool = True
    enable_ui_config: bool = True
    custom_routes: Callable[[FastAPI], None] | None = None
    custom_middleware: Callable[[FastAPI], None] | None = None
    auth_hook: Callable[[Request, dict[str, Any]], bool] | None = None
    title: str = "Deep Agent AG-UI Server"
    version: str = "0.1.0"


def load_ui_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load UI configuration from YAML file."""
    config_path = Path(path) if path else Path(UI_CONFIG_FILE)
    if not config_path.exists():
        return {}
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return data.get("ui", {}) if data else {}


def _default_verify_passcode(request: Request, ui_config: dict[str, Any]) -> bool:
    expected_passcode = ui_config.get("passcode")
    if not expected_passcode:
        return True
    body = {}
    try:
        body = request.state._cached_body
    except AttributeError:
        pass
    passcode = body.get("passcode") if isinstance(body, dict) else None
    return str(passcode) == str(expected_passcode)


def create_ag_ui_app(
    *,
    ui_config: dict[str, Any] | None = None,
    options: AgUIAppOptions | None = None,
    session: DeepAgentSession | None = None,
    session_provider: SessionProvider | None = None,
    ag_ui_path: str = "/",
    session_stats_provider: SessionStatsProvider | None = None,
    agent_name: str | None = None,
    agent_description: str | None = None,
    require_confirmation: bool = False,
    fallback_session: DeepAgentSession | None = None,
) -> FastAPI:
    """Create a FastAPI app for AG-UI servers."""
    ui_config = ui_config or {}
    opts = options or AgUIAppOptions()
    app = FastAPI(title=opts.title, version=opts.version)

    app.add_middleware(ConcurrencyLimitMiddleware, max_concurrent=opts.max_concurrent)

    if opts.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(opts.allowed_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.state.ui_config = ui_config

    if opts.enable_ui_config:

        @app.get("/api/ui-config")
        async def get_ui_config():
            config = app.state.ui_config.copy()
            if "passcode" in config:
                config["auth_required"] = True
                del config["passcode"]
            else:
                config["auth_required"] = False
            return config

        @app.post("/api/verify-passcode")
        async def verify_passcode(request: Request):
            body = await request.json()
            request.state._cached_body = body
            verify = opts.auth_hook or _default_verify_passcode
            return {"valid": verify(request, app.state.ui_config)}

    if session_stats_provider:
        app.state.session_stats_provider = session_stats_provider

        @app.get("/api/session-stats")
        async def get_session_stats():
            return session_stats_provider()

    if opts.enable_health:

        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "deep-agent"}

    if opts.enable_ready:

        @app.get("/ready")
        async def readiness_check():
            stats_provider = getattr(app.state, "session_stats_provider", None)
            if stats_provider:
                stats = stats_provider()
                return {
                    "status": "ready",
                    "mode": "multi-tenant",
                    "active_sessions": stats.get("active_sessions", 0),
                    "max_concurrent": stats.get("max_concurrent", 0),
                }
            session_factory = getattr(app.state, "session_factory", None)
            if session_factory and hasattr(session_factory, "get_stats"):
                stats = session_factory.get_stats()
                return {
                    "status": "ready",
                    "mode": "multi-tenant",
                    "active_sessions": stats.get("active_sessions", 0),
                    "max_concurrent": stats.get("max_concurrent", 0),
                }
            return {"status": "ready", "mode": "single-tenant"}

    if opts.custom_middleware:
        opts.custom_middleware(app)

    if opts.custom_routes:
        opts.custom_routes(app)

    if session and session_provider:
        raise ValueError("Provide only one of session or session_provider")

    agui_agent = None
    if session_provider:
        agui_agent = build_multi_tenant_ag_ui_agent(
            session_provider=session_provider,
            name=agent_name or "agentic_analyst",
            description=agent_description or "Deep Agent (Multi-Tenant)",
            require_confirmation=require_confirmation,
            fallback_session=fallback_session,
        )
        app.state.session_provider = session_provider
    elif session:
        agui_agent = build_ag_ui_agent(
            session,
            name=agent_name,
            description=agent_description,
            require_confirmation=require_confirmation,
        )
        app.state.session = session

    if agui_agent:
        app.state.agui_agent = agui_agent
        add_agent_framework_fastapi_endpoint(app=app, agent=agui_agent, path=ag_ui_path)

    return app


__all__ = [
    "AgUIAppOptions",
    "DEFAULT_CORS_ORIGINS",
    "create_ag_ui_app",
    "load_ui_config",
]
