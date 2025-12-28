from __future__ import annotations

from agentic_ai.ag_ui.server.cli import build_ag_ui_arg_parser


def test_ag_ui_cli_parses_feature_flags() -> None:
    parser = build_ag_ui_arg_parser()
    args = parser.parse_args(
        [
            "--disable-health",
            "--enable-ready",
            "--disable-ui-config",
            "--max-concurrent",
            "55",
            "--path",
            "/ag",
            "--allow-origin",
            "http://localhost:3000",
            "--allow-origin",
            "http://example.com",
        ]
    )

    assert args.enable_health is False
    assert args.enable_ready is True
    assert args.enable_ui_config is False
    assert args.max_concurrent == 55
    assert args.path == "/ag"
    assert args.allow_origins == ["http://localhost:3000", "http://example.com"]
