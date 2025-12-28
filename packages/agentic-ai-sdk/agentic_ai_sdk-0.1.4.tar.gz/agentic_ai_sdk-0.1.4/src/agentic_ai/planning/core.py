from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Annotated

from agent_framework import AIFunction, ai_function
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StepStatus(str, Enum):
    """Status of a plan step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PlanStep(BaseModel):
    """A single step in the task plan."""
    step: Annotated[
        str,
        Field(
            description="Clear, actionable description of what needs to be done in this step"
        )
    ]
    status: Annotated[
        StepStatus,
        Field(
            description=(
                "Current status of this step. Use 'pending' for not started, "
                "'in_progress' for currently executing (only ONE step can be in_progress), "
                "'completed' for finished steps"
            )
        )
    ]

    model_config = ConfigDict(extra="forbid")


class UpdatePlanArgs(BaseModel):
    """Arguments for updating the task plan."""
    explanation: Annotated[
        str | None,
        Field(
            description=(
                "Optional explanation of the plan or recent changes. "
                "Describe the overall approach or why the plan was updated"
            ),
            default=None
        )
    ] = None
    plan: Annotated[
        list[PlanStep],
        Field(
            description=(
                "List of plan steps. Each step must have 'step' (description) and 'status'. "
                "IMPORTANT: At most ONE step can have status='in_progress'"
            )
        )
    ]

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _validate_plan(self) -> "UpdatePlanArgs":
        active = [item for item in self.plan if item.status == StepStatus.IN_PROGRESS]
        if len(active) > 1:
            raise ValueError("Only one plan step may be marked in_progress.")
        return self


class PlanRecord(BaseModel):
    explanation: str | None = None
    plan: list[dict[str, Any]]
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class PlanStore:
    """Persist agent plans as structured artifacts within the workspace."""

    def __init__(self, workspace_dir: Path, agent_id: str):
        self._plan_path = Path(workspace_dir) / agent_id / "plan.json"

    @property
    def path(self) -> Path:
        return self._plan_path

    def save(self, record: PlanRecord) -> None:
        self._plan_path.parent.mkdir(parents=True, exist_ok=True)
        self._plan_path.write_text(record.model_dump_json(ensure_ascii=False))

    def load(self) -> PlanRecord | None:
        if not self._plan_path.exists():
            return None
        return PlanRecord.model_validate_json(self._plan_path.read_text())


def build_update_plan_tool(store: PlanStore, agent_id: str) -> AIFunction[Any, str | dict[str, Any]]:
    """Return an ai_function that persists the latest plan for the given agent."""

    @ai_function(
        name="update_plan",
        description="Update the task execution plan with steps to track progress.",
    )
    def update_plan(
        plan: Annotated[
            list[dict[str, Any]] | None,
            Field(
                default=None,
                description=(
                    "List of plan steps. Each step requires 'step' (description) and "
                    "'status' ('pending' | 'in_progress' | 'completed'). "
                    "At most ONE step can be 'in_progress'."
                )
            )
        ] = None,
    ) -> str | dict[str, Any]:
        try:
            # Validate plan is provided and not empty
            if not plan:
                return {
                    "error": True,
                    "error_type": "ValidationError",
                    "error_message": "plan parameter is required and cannot be empty",
                    "suggestion": "Provide plan as a list of steps, e.g., plan=[{'step': 'Find data', 'status': 'in_progress'}]",
                }
            
            # Validate each step has required fields
            for i, step in enumerate(plan):
                if "step" not in step or "status" not in step:
                    return {
                        "error": True,
                        "error_type": "ValidationError", 
                        "error_message": f"Step {i+1} missing required fields",
                        "suggestion": "Each step must have 'step' (description) and 'status' ('pending'|'in_progress'|'completed')",
                    }
            
            # Store plan
            record = PlanRecord(
                explanation=None,
                plan=plan,
                updated_at=datetime.now(timezone.utc),
            )
            store.save(record)
            
            return "Plan updated"
        except Exception as exc:
            # Return error information
            return {
                "error": True,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "suggestion": "Please review the plan structure and try again.",
            }

    return update_plan


__all__ = [
    "PlanRecord",
    "PlanStep",
    "PlanStore",
    "StepStatus",
    "UpdatePlanArgs",
    "build_update_plan_tool",
]


# Ensure all Pydantic models resolve forward references before runtime usage.
PlanStep.model_rebuild()
UpdatePlanArgs.model_rebuild()
PlanRecord.model_rebuild()
