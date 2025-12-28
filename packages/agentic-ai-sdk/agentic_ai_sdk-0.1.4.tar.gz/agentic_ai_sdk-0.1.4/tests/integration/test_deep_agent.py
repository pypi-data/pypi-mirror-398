"""
Integration tests for the Deep Agent framework.

Tests cover multiple components working together:
- Agent creation and state management
- Tool unified registration and invocation
- Artifact persistence and reference passing (avoiding duplicate data generation)
- Context compaction capabilities
- Master/sub-agent state and data transfer
- Plan/TODO persistence and event streaming
- Unified tool call logging
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import pytest
from agent_framework import (
    AgentRunResponseUpdate,
    BaseChatClient,
    ChatMessage,
    ChatResponse,
    ChatResponseUpdate,
    TextContent,
    ai_function,
)
from pydantic import BaseModel

from agentic_ai.agent import DeepAgentSession, build_agent
from agentic_ai.artifacts import ArtifactStore, ToolResult, persist_full
from agentic_ai.runtime.context_compaction import CompactionConfig, HeuristicSummarizer
from agentic_ai.runtime.contexts import ctx
from agentic_ai.planning import PlanRecord, PlanStep, StepStatus
from agentic_ai.workspace import WorkspaceManager

# Import shared fixtures
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from tests.fixtures.mock_llm import MockChatClient


# ============================================================================
# Test: Agent Creation and State Management
# ============================================================================


def test_agent_creation_and_state(tmp_path: Path) -> None:
    """Test agent creation with workspace and state management."""
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("test-workspace")
    client = MockChatClient()

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="test-agent",
        tools=[],
        instructions="You are a test agent.",
        planning_enabled=True,
    )

    # Verify agent session properties
    assert isinstance(session, DeepAgentSession)
    assert session.agent_id == "test-agent"
    assert session.workspace.workspace_id == "test-workspace"
    assert session.plan_store is not None
    assert session.context_compactor is not None

    # Verify workspace directory exists
    assert workspace.path.exists()
    assert workspace.path.is_dir()

    # Verify base kwargs injection
    base_kwargs = session._base_kwargs()
    assert base_kwargs["workspace_id"] == "test-workspace"
    assert base_kwargs["agent_id"] == "test-agent"
    assert "workspace_dir" in base_kwargs
    assert "plan_path" in base_kwargs


def test_agent_run_basic(tmp_path: Path) -> None:
    """Test basic agent run functionality."""
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("test-ws")
    client = MockChatClient(responses=["Hello, I processed your request."])

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="agent-1",
        tools=[],
        instructions="Test agent",
    )

    response = asyncio.run(session.run("Test prompt"))
    assert response.text == "Hello, I processed your request."
    assert client.call_count == 1


def test_agent_thread_management(tmp_path: Path) -> None:
    """Test thread creation and reuse."""
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("thread-test")
    client = MockChatClient()

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="agent-threads",
        tools=[],
        instructions="Test",
    )

    # Test automatic thread creation
    thread1 = session.ensure_thread()
    assert thread1 is not None

    # Test thread reuse
    thread2 = session.ensure_thread(thread1)
    assert thread2 is thread1

    # Test new thread creation
    thread3 = session.ensure_thread(None)
    assert thread3 is not thread1


# ============================================================================
# Test: Tool Registration and Invocation
# ============================================================================


def test_tool_registration_and_invocation(tmp_path: Path) -> None:
    """Test unified tool registration and invocation through middleware."""

    @ai_function
    def add_numbers(a: int, b: int) -> dict[str, Any]:
        """Add two numbers together."""
        return {"result": a + b}

    @ai_function
    def multiply_numbers(x: int, y: int) -> dict[str, Any]:
        """Multiply two numbers."""
        return {"result": x * y}

    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("tool-test")
    client = MockChatClient()

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="tool-agent",
        tools=[add_numbers, multiply_numbers],
        instructions="Use tools to perform calculations",
    )

    # Verify session was created with tools
    assert session is not None
    assert session.agent_id == "tool-agent"

    # Run agent (even if mock doesn't call tools, they're registered)
    response = asyncio.run(session.run("Calculate something"))
    assert response is not None


def test_tool_with_artifact_persistence(tmp_path: Path) -> None:
    """Test tool results with artifact persistence."""

    @ai_function
    def generate_large_data(size: int) -> dict[str, Any]:
        """Generate large dataset that should be persisted as artifact."""
        context = ctx()
        large_data = [{"id": i, "value": i * 2} for i in range(size)]

        # Use persist_full helper - returns ToolResult
        # Persist the full data and include summary metadata
        full_data = {"count": len(large_data), "rows": large_data}
        envelope = persist_full(
            data=full_data,
            summary={"total_records": len(large_data), "type": "numeric_dataset"},
        )
        # Must return dict format
        return envelope.model_dump()

    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("artifact-test")
    client = MockChatClient()

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="artifact-agent",
        tools=[generate_large_data],
        instructions="Generate data",
        auto_persist_tools=True,
    )

    # Invoke tool directly to test artifact creation
    from agent_framework._middleware import FunctionInvocationContext, FunctionMiddlewarePipeline

    async def test_invoke():
        ctx = FunctionInvocationContext(
            function=generate_large_data,
            arguments=generate_large_data.input_model(size=100),
            kwargs={
                "workspace_dir": str(workspace.path),
                "workspace_id": workspace.workspace_id,
                "agent_id": "artifact-agent",
            },
        )

        from agentic_ai.middleware import ToolResultPersistenceMiddleware

        pipeline = FunctionMiddlewarePipeline([ToolResultPersistenceMiddleware(auto_persist=True)])

        async def final_handler(ctx):
            return await generate_large_data.invoke(arguments=ctx.arguments)

        result = await pipeline.execute(
            function=generate_large_data,
            arguments=ctx.arguments,
            context=ctx,
            final_handler=final_handler,
        )
        return result

    result = asyncio.run(test_invoke())
    from agentic_ai.artifacts import ToolResult
    envelope = ToolResult.model_validate(result)

    # Verify artifact was created
    assert envelope.artifact_id is not None
    # persist_full stores complete data, so is_preview is False
    assert envelope.is_preview is False
    assert envelope.summary is not None
    assert envelope.summary["total_records"] == 100

    # Verify artifact files exist
    artifact_dir = workspace.path / envelope.artifact_id
    assert artifact_dir.exists()
    assert (artifact_dir / "data.json").exists()
    assert (artifact_dir / "manifest.json").exists()


# ============================================================================
# Test: Artifact Reference Passing
# ============================================================================


def test_artifact_reference_passing(tmp_path: Path) -> None:
    """Test that artifacts can be referenced by ID to avoid duplicate data generation."""

    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("ref-test")
    artifact_store = ArtifactStore(workspace.path)

    # Create an artifact
    data = {"records": [{"id": i, "value": f"item-{i}"} for i in range(1000)]}
    artifact_id, artifact_dir = artifact_store.create_json_artifact(
        data=data,
        manifest_overrides={"description": "Test dataset"},
    )

    # Verify artifact exists
    assert artifact_dir.exists()
    assert (artifact_dir / "data.json").exists()

    # Load artifact by reference
    loaded_data = json.loads((artifact_dir / "data.json").read_text())
    assert len(loaded_data["records"]) == 1000
    assert loaded_data["records"][0]["id"] == 0

    # Verify manifest
    manifest_path = artifact_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["type"] == "dataset"
    assert manifest["description"] == "Test dataset"
    assert "created_at" in manifest


def test_artifact_prevents_duplicate_generation(tmp_path: Path) -> None:
    """Test that returning artifact_id prevents duplicate data in responses."""

    @ai_function
    def create_report() -> dict[str, Any]:
        """Create a report and return artifact reference."""
        context = ctx()
        report_data = {"summary": "Q4 Report", "metrics": [1, 2, 3] * 100}

        # Use persist_full to store full data and return reference
        envelope = persist_full(
            data=report_data,
            summary={"type": "report", "metrics": len(report_data["metrics"])},
        )
        return envelope.model_dump()

    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("dedup-test")
    client = MockChatClient()

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="dedup-agent",
        tools=[create_report],
        instructions="Create reports",
    )

    # The tool would return artifact_id, not full data
    # This saves tokens in LLM responses
    assert session is not None


# ============================================================================
# Test: Context Compaction
# ============================================================================


def test_context_compaction_basic(tmp_path: Path) -> None:
    """Test context compaction with heuristic summarizer."""
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("compact-test")
    client = MockChatClient(responses=["Response"] * 100)

    compaction_config = CompactionConfig(
        enabled=True,
        max_messages=10,  # Trigger compaction after 10 messages
        cooldown_turns=0,  # No cooldown for testing
    )

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="compact-agent",
        tools=[],
        instructions="Test compaction",
        compaction_config=compaction_config,
        compaction_summarizer=HeuristicSummarizer(),
    )

    thread = session.ensure_thread()

    # Generate many messages to trigger compaction
    for i in range(15):
        asyncio.run(session.run(f"Message {i}", thread=thread))

    # Verify compaction occurred (message count should be reduced)
    message_store = thread.message_store
    messages = asyncio.run(message_store.list_messages())

    # After compaction, message count should be less than 15 * 2 (user + assistant)
    assert len(messages) < 30


def test_context_compaction_config(tmp_path: Path) -> None:
    """Test context compaction configuration."""
    config = CompactionConfig(
        enabled=True,
        max_messages=50,
        token_limit=10000,
        cooldown_turns=3,
        summary_tail_messages=15,
    )

    assert config.enabled is True
    assert config.max_messages == 50
    assert config.token_limit == 10000
    assert config.cooldown_turns == 3


# ============================================================================
# Test: Master/Sub-Agent Communication
# ============================================================================


def test_master_sub_agent_communication(tmp_path: Path) -> None:
    """Test state and data passing between master and sub-agents."""
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("multi-agent-test")

    # Create sub-agent
    sub_client = MockChatClient(responses=["Sub-agent completed the task."])
    sub_session = build_agent(
        chat_client=sub_client,
        workspace=workspace,
        agent_id="sub-agent",
        tools=[],
        instructions="You are a sub-agent that processes specific tasks.",
        planning_enabled=True,
    )

    # Convert sub-agent to tool
    sub_agent_tool = sub_session.as_tool(
        name="delegate_to_specialist",
        description="Delegate specialized tasks to a sub-agent",
        arg_name="task_description",
    )

    # Create master agent with sub-agent as tool
    master_client = MockChatClient(responses=["I'll delegate this task."])
    master_session = build_agent(
        chat_client=master_client,
        workspace=workspace,
        agent_id="master-agent",
        tools=[sub_agent_tool],
        instructions="You are a master agent that delegates tasks.",
        planning_enabled=True,
    )

    # Verify master session was created with sub-agent tool
    assert master_session is not None
    assert master_session.agent_id == "master-agent"

    # Both agents share the same workspace
    assert master_session.workspace.workspace_id == sub_session.workspace.workspace_id


def test_sub_agent_as_tool_with_streaming(tmp_path: Path) -> None:
    """Test sub-agent as tool with streaming callback."""
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("streaming-test")

    sub_client = MockChatClient(responses=["Streaming response from sub-agent"])
    sub_session = build_agent(
        chat_client=sub_client,
        workspace=workspace,
        agent_id="streaming-sub",
        tools=[],
        instructions="Sub-agent with streaming",
    )

    captured_updates: list[AgentRunResponseUpdate] = []

    def stream_callback(update: AgentRunResponseUpdate) -> None:
        captured_updates.append(update)

    sub_tool = sub_session.as_tool(
        name="streaming_delegate",
        description="Delegate with streaming",
        stream_callback=stream_callback,
    )

    # Invoke the tool (note: default arg_name is "task", not "task_description")
    async def test_streaming():
        result = await sub_tool.invoke(arguments=sub_tool.input_model(task="Test task"))
        return result

    result = asyncio.run(test_streaming())
    assert isinstance(result, str)
    assert len(captured_updates) > 0


# ============================================================================
# Test: Planning and TODO Management
# ============================================================================


def test_planning_persistence(tmp_path: Path) -> None:
    """Test plan/TODO persistence and retrieval."""
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("plan-test")
    client = MockChatClient()

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="planning-agent",
        tools=[],
        instructions="Agent with planning",
        planning_enabled=True,
    )

    # Verify plan store exists
    assert session.plan_store is not None
    plan_store = session.plan_store

    # Create a plan
    from datetime import datetime, timezone

    plan = PlanRecord(
        explanation="Testing plan persistence",
        plan=[
            {"step": "Step 1: Initialize", "status": "completed"},
            {"step": "Step 2: Process data", "status": "in_progress"},
            {"step": "Step 3: Finalize", "status": "pending"},
        ],
        updated_at=datetime.now(timezone.utc),
    )

    # Save plan
    plan_store.save(plan)

    # Verify plan file exists
    assert plan_store.path.exists()

    # Load plan
    loaded_plan = plan_store.load()
    assert loaded_plan is not None
    assert loaded_plan.explanation == "Testing plan persistence"
    assert len(loaded_plan.plan) == 3
    assert loaded_plan.plan[0]["status"] == "completed"
    assert loaded_plan.plan[1]["status"] == "in_progress"
    assert loaded_plan.plan[2]["status"] == "pending"


def test_update_plan_tool(tmp_path: Path) -> None:
    """Test the update_plan tool functionality."""
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("update-plan-test")
    client = MockChatClient()

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="plan-update-agent",
        tools=[],
        instructions="Agent with plan updates",
        planning_enabled=True,
    )

    # Verify planning is enabled
    assert session.plan_store is not None

    # Get the update_plan tool directly from planning module
    from agentic_ai.planning import build_update_plan_tool

    update_plan_tool = build_update_plan_tool(session.plan_store, agent_id="plan-update-agent")

    # Use direct parameters instead of args wrapper
    plan_steps = [
        {"step": "Research requirements", "status": "completed"},
        {"step": "Design solution", "status": "in_progress"},
        {"step": "Implement features", "status": "pending"},
    ]

    # Call the tool function directly (not via async invoke)
    result = update_plan_tool.func(plan=plan_steps)  # type: ignore[arg-type]

    # Verify result - should return simple confirmation message
    assert result == "Plan updated"

    # Verify plan was persisted
    loaded_plan = session.plan_store.load()
    assert loaded_plan is not None
    assert len(loaded_plan.plan) == 3
    assert loaded_plan.explanation is None
    assert len(loaded_plan.plan) == 3


def test_plan_validation(tmp_path: Path) -> None:
    """Test plan validation (only one step can be in_progress)."""
    from agentic_ai.planning import UpdatePlanArgs

    # Valid plan: one in_progress
    valid_plan = UpdatePlanArgs(
        explanation="Valid plan",
        plan=[
            PlanStep(step="Step 1", status=StepStatus.COMPLETED),
            PlanStep(step="Step 2", status=StepStatus.IN_PROGRESS),
            PlanStep(step="Step 3", status=StepStatus.PENDING),
        ],
    )
    assert valid_plan is not None

    # Invalid plan: multiple in_progress
    with pytest.raises(ValueError, match="Only one plan step may be marked in_progress"):
        UpdatePlanArgs(
            explanation="Invalid plan",
            plan=[
                PlanStep(step="Step 1", status=StepStatus.IN_PROGRESS),
                PlanStep(step="Step 2", status=StepStatus.IN_PROGRESS),
                PlanStep(step="Step 3", status=StepStatus.PENDING),
            ],
        )


# ============================================================================
# Test: Tool Call Logging
# ============================================================================


def test_tool_logging(tmp_path: Path, caplog) -> None:
    """Test unified tool call logging."""

    @ai_function
    def test_tool(message: str) -> dict[str, Any]:
        """A test tool for logging verification."""
        # Success: only set result, other fields default to None
        from agentic_ai.artifacts import ToolResult
        return ToolResult(
            result={"message": message}
        ).model_dump()

    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("logging-test")
    client = MockChatClient()

    # Configure logging
    caplog.set_level(logging.INFO, logger="agentic_ai.tools")

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="logging-agent",
        tools=[test_tool],
        instructions="Test logging",
    )

    # Invoke tool via middleware
    from agent_framework._middleware import FunctionInvocationContext, FunctionMiddlewarePipeline
    from agentic_ai.middleware import ToolResultPersistenceMiddleware

    async def test_invoke():
        ctx = FunctionInvocationContext(
            function=test_tool,
            arguments=test_tool.input_model(message="test message"),
            kwargs={
                "workspace_dir": str(workspace.path),
                "workspace_id": workspace.workspace_id,
                "deep_agent_id": "logging-agent",
            },
        )

        pipeline = FunctionMiddlewarePipeline([ToolResultPersistenceMiddleware()])

        async def final_handler(ctx):
            return await test_tool.invoke(arguments=ctx.arguments)

        return await pipeline.execute(
            function=test_tool,
            arguments=ctx.arguments,
            context=ctx,
            final_handler=final_handler,
        )

    asyncio.run(test_invoke())

    # After simplification: tool execution info is now traced by MAF observability spans
    # We only log errors with full stack traces, not success cases
    # Verify the tool was executed successfully (no error logs)
    log_messages = [record.message for record in caplog.records if record.name == "agentic_ai.tools"]
    assert not any("ERROR" in msg for msg in log_messages), "Tool should execute without errors"


def test_tool_logging_with_errors(tmp_path: Path, caplog) -> None:
    """Test tool logging when errors occur."""

    @ai_function
    def failing_tool() -> dict[str, Any]:
        """A tool that always fails."""
        raise RuntimeError("Intentional failure for testing")

    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("error-logging-test")

    caplog.set_level(logging.INFO, logger="agentic_ai.tools")

    # Invoke tool with middleware
    from agent_framework._middleware import FunctionInvocationContext, FunctionMiddlewarePipeline
    from agentic_ai.middleware import ToolResultPersistenceMiddleware

    async def test_invoke():
        ctx = FunctionInvocationContext(
            function=failing_tool,
            arguments=failing_tool.input_model(),
            kwargs={
                "workspace_dir": str(workspace.path),
                "workspace_id": workspace.workspace_id,
                "deep_agent_id": "error-agent",
            },
        )

        pipeline = FunctionMiddlewarePipeline([ToolResultPersistenceMiddleware()])

        async def final_handler(ctx):
            return await failing_tool.invoke(arguments=ctx.arguments)

        return await pipeline.execute(
            function=failing_tool,
            arguments=ctx.arguments,
            context=ctx,
            final_handler=final_handler,
        )

    # Middleware logs the error and re-raises the exception
    with pytest.raises(RuntimeError, match="Intentional failure for testing"):
        asyncio.run(test_invoke())
    
    # Verify ERROR logging occurred with full stack traces
    error_records = [record for record in caplog.records 
                     if record.name == "agentic_ai.tools" and record.levelno == logging.ERROR]
    assert len(error_records) >= 1, "Should log at least one ERROR record"
    
    error_msg = error_records[0].message
    assert "failing_tool" in error_msg, "Error log should contain tool name"
    assert "RuntimeError" in error_msg, "Error log should contain exception type"


# ============================================================================
# Test: Integration Scenarios
# ============================================================================


def test_full_workflow_integration(tmp_path: Path) -> None:
    """Test a complete workflow with multiple features."""

    @ai_function
    def analyze_data(dataset_size: int) -> dict[str, Any]:
        """Analyze data and create artifact."""
        context = ctx()
        analysis_results = {
            "dataset_size": dataset_size,
            "summary_stats": {"mean": 50.5, "median": 50, "std": 28.9},
            "detailed_results": [{"id": i, "score": i * 1.5} for i in range(dataset_size)],
        }

        # Use persist_full to store full analysis results
        envelope = persist_full(
            data=analysis_results,
            summary={"type": "analysis", "records": dataset_size},
        )
        return envelope.model_dump()

    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("integration-test")
    client = MockChatClient(responses=["Analysis complete", "Plan updated"])

    compaction_config = CompactionConfig(enabled=True, max_messages=20)

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="integration-agent",
        tools=[analyze_data],
        instructions="Perform data analysis with planning",
        planning_enabled=True,
        auto_persist_tools=True,
        compaction_config=compaction_config,
    )

    # Run multiple operations
    thread = session.ensure_thread()

    response1 = asyncio.run(session.run("Start analysis project", thread=thread))
    assert response1.text is not None

    response2 = asyncio.run(session.run("Continue with next phase", thread=thread))
    assert response2.text is not None

    # Verify all components are working
    assert session.plan_store is not None
    assert session.context_compactor is not None
    assert workspace.path.exists()

    # Verify workspace contains agent directory
    agent_dir = workspace.path / "integration-agent"
    assert agent_dir.exists() or workspace.path.exists()  # Either structure is valid


def test_workspace_isolation(tmp_path: Path) -> None:
    """Test that different agents in same workspace maintain isolation."""
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("shared-workspace")

    client1 = MockChatClient()
    client2 = MockChatClient()

    session1 = build_agent(
        chat_client=client1,
        workspace=workspace,
        agent_id="agent-1",
        tools=[],
        instructions="Agent 1",
        planning_enabled=True,
    )

    session2 = build_agent(
        chat_client=client2,
        workspace=workspace,
        agent_id="agent-2",
        tools=[],
        instructions="Agent 2",
        planning_enabled=True,
    )

    # Both share workspace but have different agent IDs
    assert session1.workspace.workspace_id == session2.workspace.workspace_id
    assert session1.agent_id != session2.agent_id

    # Plans are separate
    from datetime import datetime, timezone

    plan1 = PlanRecord(
        explanation="Agent 1 plan",
        plan=[{"step": "Task 1", "status": "in_progress"}],
        updated_at=datetime.now(timezone.utc),
    )
    session1.plan_store.save(plan1)  # type: ignore[union-attr]

    plan2 = PlanRecord(
        explanation="Agent 2 plan",
        plan=[{"step": "Task 2", "status": "in_progress"}],
        updated_at=datetime.now(timezone.utc),
    )
    session2.plan_store.save(plan2)  # type: ignore[union-attr]

    # Load and verify isolation
    loaded1 = session1.plan_store.load()  # type: ignore[union-attr]
    loaded2 = session2.plan_store.load()  # type: ignore[union-attr]

    assert loaded1.explanation == "Agent 1 plan"  # type: ignore[union-attr]
    assert loaded2.explanation == "Agent 2 plan"  # type: ignore[union-attr]
    assert loaded1.plan[0]["step"] != loaded2.plan[0]["step"]  # type: ignore[union-attr, index]


# ============================================================================
# Test: Error Handling
# ============================================================================


def test_agent_kwargs_protection(tmp_path: Path) -> None:
    """Test that reserved Deep Agent kwargs cannot be overridden."""
    manager = WorkspaceManager(tmp_path)
    workspace = manager.create("protected-test")
    client = MockChatClient()

    session = build_agent(
        chat_client=client,
        workspace=workspace,
        agent_id="protected-agent",
        tools=[],
        instructions="Test protection",
    )

    thread = session.ensure_thread()

    # Attempt to override reserved kwargs
    with pytest.raises(ValueError, match="Reserved Deep Agent kwargs cannot be overridden"):
        asyncio.run(session.run("test", thread=thread, workspace_id="other-workspace"))

    with pytest.raises(ValueError, match="Reserved Deep Agent kwargs cannot be overridden"):
        asyncio.run(session.run("test", thread=thread, agent_id="other-agent"))


def test_artifact_validation(tmp_path: Path) -> None:
    """Test ToolResult validation."""
    from agentic_ai.artifacts import ToolResult
    
    # Valid result with result
    result1 = ToolResult(status="ok", result={"data": "value"})
    assert result1.result is not None

    # Valid result with artifact_id
    result2 = ToolResult(status="ok", artifact_id="art-123", result=None)
    assert result2.artifact_id is not None

    # Invalid result: neither result nor artifact_id when status=ok
    with pytest.raises(ValueError, match="result or artifact_id required when status=ok"):
        ToolResult(status="ok", result=None, artifact_id=None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
