from __future__ import annotations

from fastapi.testclient import TestClient

from agentic_ai.ag_ui.server.app import AgUIAppOptions, create_ag_ui_app


def test_ag_ui_app_health_ready_ui_config_defaults() -> None:
    ui_config = {"passcode": "secret", "theme": "midnight"}
    app = create_ag_ui_app(ui_config=ui_config, options=AgUIAppOptions())
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "healthy", "service": "deep-agent"}

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready", "mode": "single-tenant"}

    config = client.get("/api/ui-config")
    assert config.status_code == 200
    config_payload = config.json()
    assert config_payload["theme"] == "midnight"
    assert config_payload["auth_required"] is True
    assert "passcode" not in config_payload

    verify = client.post("/api/verify-passcode", json={"passcode": "secret"})
    assert verify.status_code == 200
    assert verify.json()["valid"] is True


def test_ag_ui_app_session_stats_and_ready_multi_tenant() -> None:
    stats_payload = {
        "active_sessions": 2,
        "max_concurrent": 9,
        "sessions": [
            {"thread_id": "alpha", "age_seconds": 12.5, "idle_seconds": 1.2},
            {"thread_id": "beta", "age_seconds": 30.0, "idle_seconds": 4.8},
        ],
    }

    def stats_provider() -> dict[str, float | int | list[dict[str, float | str]]]:
        return stats_payload

    app = create_ag_ui_app(
        options=AgUIAppOptions(),
        session_stats_provider=stats_provider,
    )
    client = TestClient(app)

    stats = client.get("/api/session-stats")
    assert stats.status_code == 200
    payload = stats.json()
    assert payload["active_sessions"] == stats_payload["active_sessions"]
    assert payload["max_concurrent"] == stats_payload["max_concurrent"]
    assert len(payload["sessions"]) == 2

    sample = payload["sessions"][0]
    assert sample["thread_id"] == "alpha"
    assert sample["age_seconds"] == 12.5

    idle_total = sum(entry["idle_seconds"] for entry in payload["sessions"])
    assert idle_total == 6.0

    ready = client.get("/ready")
    assert ready.status_code == 200
    ready_payload = ready.json()
    assert ready_payload["mode"] == "multi-tenant"
    assert ready_payload["active_sessions"] == stats_payload["active_sessions"]
    assert ready_payload["max_concurrent"] == stats_payload["max_concurrent"]


def test_ag_ui_app_disable_endpoints() -> None:
    options = AgUIAppOptions(
        enable_health=False,
        enable_ready=False,
        enable_ui_config=False,
    )
    app = create_ag_ui_app(options=options)
    client = TestClient(app)

    assert client.get("/health").status_code == 404
    assert client.get("/ready").status_code == 404
    assert client.get("/api/ui-config").status_code == 404
    assert client.post("/api/verify-passcode", json={"passcode": "x"}).status_code == 404
