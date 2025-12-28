"""Agentic AI CLI entry point."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from .ag_ui.server.cli import build_ag_ui_arg_parser, run_ag_ui_server
from .config import BaseAppConfig
from .observability import configure_observability_from_config
from .observability.logging import setup_logging_from_config
from .runtime import bootstrap_runtime, build_session
from .workspace import create_workspace


def _build_run_parser(subparsers) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("run", help="Run an agent in the terminal.")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (default: env.yaml)",
    )
    parser.add_argument(
        "--manifest-dir",
        dest="manifest_dir",
        default="manifest",
        help="Manifest directory (default: manifest)",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=".ws",
        help="Workspace root directory (default: .ws)",
    )
    parser.add_argument(
        "--agent",
        type=str,
        default="agentic_analyst",
        help="Agent ID to run (default: agentic_analyst)",
    )
    return parser


def _run_cli(args: argparse.Namespace) -> int:
    try:
        ctx = bootstrap_runtime(
            BaseAppConfig,
            config_path=args.config,
            manifest_dir=args.manifest_dir,
        )
    except Exception as exc:
        print(f"Failed to bootstrap runtime: {exc}", file=sys.stderr)
        return 1

    configure_observability_from_config(ctx.config)
    setup_logging_from_config(ctx.config.model_dump())

    workspace = create_workspace(default_root=args.workspace)
    try:
        result = build_session(
            runtime_ctx=ctx,
            agent_id=args.agent,
            workspace=workspace,
        )
    except Exception as exc:
        print(f"Failed to build session: {exc}", file=sys.stderr)
        return 1

    session = result.session
    print(f"✅ Agent ready | agent={args.agent} | workspace={workspace.workspace_id}")
    print("Type 'exit' or 'quit' to exit. Press Ctrl+C to interrupt.")
    print()

    try:
        while True:
            try:
                user_input = input("> ").strip()
                if user_input.lower() in ("exit", "quit"):
                    break
                if not user_input:
                    continue
                response = asyncio.run(session.run(user_input))
                print(f"\n{response.text}\n")
            except KeyboardInterrupt:
                print("\n(Interrupted)")
                break
    finally:
        session.close()
        for cleanup in result.cleanup_functions:
            try:
                cleanup()
            except Exception:
                pass
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentic-ai", description="Agentic AI CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parent = build_ag_ui_arg_parser()
    subparsers.add_parser(
        "serve",
        help="Run AG-UI server.",
        parents=[serve_parent],
        add_help=False,
    )

    _build_run_parser(subparsers)

    args = parser.parse_args(argv)
    if args.command == "serve":
        run_ag_ui_server(
            agent_id=args.agent_id,
            config_path=args.config_path,
            manifest_dir=args.manifest_dir,
            ui_config_path=args.ui_config_path,
            workspace_root=args.workspace_root,
            host=args.host,
            port=args.port,
            path=args.path,
            allow_origins=args.allow_origins,
            single_tenant=args.single_tenant,
            session_ttl=args.session_ttl,
            workers=args.workers,
            max_concurrent=args.max_concurrent,
            enable_ready=args.enable_ready,
            enable_health=args.enable_health,
            enable_ui_config=args.enable_ui_config,
            config_class=BaseAppConfig,
        )
        return 0
    if args.command == "run":
        return _run_cli(args)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
