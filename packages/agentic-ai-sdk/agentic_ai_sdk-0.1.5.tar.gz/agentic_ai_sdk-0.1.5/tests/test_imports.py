"""Test that all public API symbols are importable."""
import pytest


def test_import_core_components():
    """Test that core agent components can be imported."""
    from agentic_ai import (
        DeepAgentSession,
        build_agent,
        build_agent_with_llm,
        build_agent_from_config,
        build_agent_from_store,
        build_agent_session,
    )
    
    assert DeepAgentSession is not None
    assert build_agent is not None
    assert build_agent_with_llm is not None
    assert build_agent_from_config is not None
    assert build_agent_from_store is not None
    assert build_agent_session is not None


def test_import_configuration():
    """Test that configuration components can be imported."""
    from agentic_ai import (
        AgentConfig,
        AgentConfigStore,
        BaseAppConfig,
        LLMConfig,
        create_agent_config_store_from_list,
        load_yaml_config,
    )
    
    assert AgentConfig is not None
    assert AgentConfigStore is not None
    assert BaseAppConfig is not None
    assert LLMConfig is not None
    assert create_agent_config_store_from_list is not None
    assert load_yaml_config is not None


def test_import_llm():
    """Test that LLM components can be imported."""
    from agentic_ai import (
        LLMClientFactory,
        create_llm_factory_from_list,
        create_chat_client,
    )
    
    assert LLMClientFactory is not None
    assert create_llm_factory_from_list is not None
    assert create_chat_client is not None


def test_import_workspace():
    """Test that workspace components can be imported."""
    from agentic_ai import (
        WorkspaceHandle,
        WorkspaceManager,
        create_workspace,
        ArtifactStore,
        ToolResult,
        persist_full,
        persist_preview,
        ok,
        error,
        load_artifact,
        try_load_artifact,
    )
    
    assert WorkspaceHandle is not None
    assert WorkspaceManager is not None
    assert create_workspace is not None
    assert ArtifactStore is not None
    assert ToolResult is not None
    assert persist_full is not None
    assert persist_preview is not None
    assert ok is not None
    assert error is not None
    assert load_artifact is not None
    assert try_load_artifact is not None


def test_import_planning():
    """Test that planning components can be imported."""
    from agentic_ai import (
        PlanStore,
        PlanRecord,
        PlanStep,
        StepStatus,
        build_update_plan_tool,
    )
    
    assert PlanStore is not None
    assert PlanRecord is not None
    assert PlanStep is not None
    assert StepStatus is not None
    assert build_update_plan_tool is not None


def test_import_observability():
    """Test that observability components can be imported."""
    from agentic_ai import (
        setup_logging,
        enable_observability,
        get_tracer,
    )
    
    assert setup_logging is not None
    assert enable_observability is not None
    assert get_tracer is not None


def test_import_context():
    """Test that context components can be imported."""
    from agentic_ai import (
        BaseAppContext,
        build_app_context,
        ToolExecutionContext,
        ToolContextUnavailableError,
        ctx,
        try_ctx,
        tool_context,
    )
    
    assert BaseAppContext is not None
    assert build_app_context is not None
    assert ToolExecutionContext is not None
    assert ToolContextUnavailableError is not None
    assert ctx is not None
    assert try_ctx is not None
    assert tool_context is not None
