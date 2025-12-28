from __future__ import annotations

import json
from pathlib import Path

from agentic_ai.planning import (
    PlanStore,
    PlanStep,
    StepStatus,
    UpdatePlanArgs,
    build_update_plan_tool,
)


def test_update_plan_tool_persists(tmp_path: Path) -> None:
    store = PlanStore(tmp_path, agent_id="analyst")
    tool = build_update_plan_tool(store, agent_id="analyst")
    
    # Now uses direct parameters instead of args wrapper
    plan_steps = [
        {"step": "Collect baseline metrics", "status": "in_progress"},
        {"step": "Draft summary", "status": "pending"},
    ]

    result = tool.func(plan=plan_steps)  # type: ignore[arg-type]
    # Should return simple confirmation message
    assert result == "Plan updated"
    
    # Verify plan was saved
    plan_path = store.path
    assert plan_path.exists()

    payload = json.loads(plan_path.read_text())
    assert payload["explanation"] is None
    assert len(payload["plan"]) == 2
    assert payload["plan"][0]["status"] == "in_progress"
