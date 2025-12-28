"""Test to reproduce the update_plan failure when only explanation is provided."""

from pathlib import Path
import pytest
from agentic_ai.planning import build_update_plan_tool, PlanStore


def test_update_plan_missing_required_plan_parameter(tmp_path: Path):
    """
    Reproduce the issue where LLM calls update_plan with only 'explanation' 
    but without the required 'plan' parameter.
    
    Expected behavior: Should fail with missing parameter error.
    """
    plan_store = PlanStore(workspace_dir=tmp_path, agent_id="test-agent")
    update_plan_tool = build_update_plan_tool(plan_store, "test-agent")
    
    # Simulate what the LLM is doing: calling with only explanation
    try:
        # This should fail because 'plan' is a required parameter
        result = update_plan_tool.func(
            explanation="Plan: 1) Aggregate recent 90-day consumption by subscription. 2) Detect spikes/drops via day-over-day percent change."
        )  # type: ignore[call-arg]
        print(f"Result: {result}")
        assert False, "Expected TypeError for missing 'plan' parameter"
    except TypeError as e:
        print(f"✅ Got expected TypeError: {e}")
        assert "plan" in str(e).lower() or "required" in str(e).lower()


def test_update_plan_with_correct_parameters(tmp_path: Path):
    """
    Test that update_plan works when plan parameter is provided correctly.
    """
    plan_store = PlanStore(workspace_dir=tmp_path, agent_id="test-agent")
    update_plan_tool = build_update_plan_tool(plan_store, "test-agent")
    
    plan_steps = [
        {"step": "Aggregate consumption data", "status": "in_progress"},
        {"step": "Detect anomalies", "status": "pending"},
    ]
    
    result = update_plan_tool.func(plan=plan_steps)  # type: ignore[arg-type]
    
    print(f"✅ Result: {result}")
    assert result == "Plan updated"


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_update_plan_missing_required_plan_parameter(Path(tmp))
        print()
        test_update_plan_with_correct_parameters(Path(tmp))
