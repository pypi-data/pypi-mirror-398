from __future__ import annotations

import json
from pathlib import Path

from agentic_ai.artifacts import ArtifactStore, persist_full
from agentic_ai.runtime.contexts import ToolExecutionContext, tool_context


def test_persist_full_uses_current_context(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    ctx = ToolExecutionContext(
        workspace_id="ws1",
        workspace_dir=tmp_path,
        agent_id="agent",
        artifact_store=store,
    )
    payload = {"rows": 3}
    with tool_context(ctx):
        envelope = persist_full(payload, summary={"row_count": 3})

    assert envelope.artifact_id is not None
    # persist_full always sets is_preview=False (full data)
    assert envelope.is_preview is False
    artifact_dir = tmp_path / envelope.artifact_id
    data_path = artifact_dir / "data.json"
    assert data_path.exists()
    assert json.loads(data_path.read_text()) == payload

