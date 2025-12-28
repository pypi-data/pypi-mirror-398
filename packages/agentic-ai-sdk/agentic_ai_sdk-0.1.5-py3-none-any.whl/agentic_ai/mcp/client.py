"""Minimal MCP client for stdio/http transports."""
from __future__ import annotations

import json
import subprocess
import threading
import uuid
from dataclasses import dataclass
from typing import Any
from urllib import request as urlrequest
from urllib.error import URLError


@dataclass
class MCPResponse:
    result: Any | None = None
    error: Any | None = None


def mcp_http_request(
    url: str,
    *,
    method: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> MCPResponse:
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": params or {},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)

    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except URLError as exc:
        return MCPResponse(error=str(exc))

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return MCPResponse(error=f"Invalid JSON response: {exc}")

    if "error" in parsed and parsed["error"] is not None:
        return MCPResponse(error=parsed["error"])
    return MCPResponse(result=parsed.get("result"))


def mcp_stdio_request(
    command: str,
    *,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    cwd: str | None = None,
    method: str,
    params: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> MCPResponse:
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": params or {},
    }

    try:
        proc = subprocess.Popen(
            [command, *(args or [])],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=cwd,
        )
    except FileNotFoundError as exc:
        return MCPResponse(error=str(exc))

    stdout_line: list[str] = []
    stderr_lines: list[str] = []

    def _read_stdout():
        line = proc.stdout.readline() if proc.stdout else ""
        if line:
            stdout_line.append(line)

    def _read_stderr():
        if proc.stderr:
            stderr_lines.extend(proc.stderr.readlines())

    try:
        if proc.stdin:
            proc.stdin.write(json.dumps(payload) + "\n")
            proc.stdin.flush()

        t = threading.Thread(target=_read_stdout)
        t.daemon = True
        t.start()
        t.join(timeout=timeout)

        if proc.poll() is None:
            proc.terminate()
    finally:
        if proc.stdin:
            proc.stdin.close()
        if proc.stdout:
            proc.stdout.close()
        if proc.stderr:
            proc.stderr.close()

    if stderr_lines and not stdout_line:
        return MCPResponse(error="".join(stderr_lines).strip())

    if not stdout_line:
        return MCPResponse(error="No response from MCP stdio server")

    try:
        parsed = json.loads(stdout_line[0])
    except json.JSONDecodeError as exc:
        return MCPResponse(error=f"Invalid JSON response: {exc}")

    if "error" in parsed and parsed["error"] is not None:
        return MCPResponse(error=parsed["error"])
    return MCPResponse(result=parsed.get("result"))


__all__ = ["mcp_http_request", "mcp_stdio_request", "MCPResponse"]
