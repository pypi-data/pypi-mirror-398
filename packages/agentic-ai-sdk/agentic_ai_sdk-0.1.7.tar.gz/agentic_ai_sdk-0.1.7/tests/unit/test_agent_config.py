"""Tests for deep_agent agent configuration."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentic_ai import AgentConfig, ContextCompactionConfig, SubagentConfig
from agentic_ai import AgentConfigStore, create_agent_config_store_from_list
from agentic_ai.config.agent import ResponseHandling


def test_agent_config_creation():
    """Test creating a basic agent configuration."""
    config = AgentConfig(
        id="test_agent",
        llm_profile_name="default",
        name="Test Agent",
        description="A test agent",
        max_tool_iterations=20,
    )
    
    assert config.id == "test_agent"
    assert config.llm_profile_name == "default"
    assert config.name == "Test Agent"
    assert config.max_tool_iterations == 20
    assert config.planning_enabled is True  # default


def test_agent_config_with_context_compaction():
    """Test agent configuration with context compaction settings."""
    compaction = ContextCompactionConfig(
        enabled=True,
        max_messages=50,
        max_tokens=100000,
    )
    
    config = AgentConfig(
        id="test_agent",
        llm_profile_name="default",
        context_compaction=compaction,
    )
    
    assert config.context_compaction is not None
    assert config.context_compaction.enabled is True
    assert config.context_compaction.max_messages == 50
    assert config.context_compaction.max_tokens == 100000


def test_agent_config_workspace_root_conversion():
    """Test that workspace_root string is converted to Path."""
    config = AgentConfig(
        id="test_agent",
        llm_profile_name="default",
        workspace_root=".test_ws",
    )
    
    assert isinstance(config.workspace_root, Path)
    assert str(config.workspace_root) == ".test_ws"


def test_agent_config_requires_id():
    """Test that empty id raises error."""
    with pytest.raises(ValueError, match="Agent id cannot be empty"):
        AgentConfig(
            id="",
            llm_profile_name="default",
        )


def test_agent_config_requires_positive_max_iterations():
    """Test that non-positive max_tool_iterations raises error."""
    with pytest.raises(ValueError, match="max_tool_iterations must be positive"):
        AgentConfig(
            id="test_agent",
            llm_profile_name="default",
            max_tool_iterations=0,
        )


def test_agent_config_store_creation():
    """Test creating agent config store from list."""
    configs = [
        AgentConfig(
            id="agent1",
            llm_profile_name="default",
            name="Agent 1",
        ),
        AgentConfig(
            id="agent2",
            llm_profile_name="smart",
            name="Agent 2",
        ),
    ]
    
    store = create_agent_config_store_from_list(configs)
    
    assert store.available_agents == ["agent1", "agent2"]


def test_agent_config_store_get_config():
    """Test getting config from store."""
    configs = [
        AgentConfig(
            id="test_agent",
            llm_profile_name="default",
            name="Test Agent",
        ),
    ]
    
    store = create_agent_config_store_from_list(configs)
    config = store.get_config("test_agent")
    
    assert config.id == "test_agent"
    assert config.name == "Test Agent"


def test_agent_config_store_get_config_not_found():
    """Test getting non-existent config raises error."""
    store = AgentConfigStore({})
    
    with pytest.raises(ValueError, match="Agent configuration 'nonexistent' not found"):
        store.get_config("nonexistent")


def test_agent_config_store_get_config_optional():
    """Test getting config optionally returns None if not found."""
    store = AgentConfigStore({})
    
    config = store.get_config_optional("nonexistent")
    assert config is None


def test_agent_config_store_has_config():
    """Test checking if config exists."""
    configs = [
        AgentConfig(
            id="test_agent",
            llm_profile_name="default",
        ),
    ]
    
    store = create_agent_config_store_from_list(configs)
    
    assert store.has_config("test_agent") is True
    assert store.has_config("nonexistent") is False


def test_agent_config_store_requires_unique_ids():
    """Test that duplicate IDs are rejected."""
    configs = [
        AgentConfig(
            id="test",
            llm_profile_name="default",
        ),
        AgentConfig(
            id="test",
            llm_profile_name="smart",
        ),
    ]
    
    with pytest.raises(ValueError, match="Duplicate agent configuration id"):
        create_agent_config_store_from_list(configs)


def test_agent_config_store_requires_ids():
    """Test that configs without IDs are rejected."""
    # Can't create config without id due to Pydantic validation
    # This test validates the error message format
    with pytest.raises(ValueError):
        AgentConfig(llm_profile_name="default")  # Missing required 'id'


def test_context_compaction_config_validation():
    """Test context compaction config validation."""
    # Valid config
    config = ContextCompactionConfig(
        enabled=True,
        max_messages=50,
        max_tokens=100000,
    )
    assert config.max_messages == 50
    
    # Invalid max_messages
    with pytest.raises(ValueError, match="max_messages must be positive"):
        ContextCompactionConfig(
            enabled=True,
            max_messages=0,
        )
    
    # Invalid max_tokens
    with pytest.raises(ValueError, match="max_tokens must be positive"):
        ContextCompactionConfig(
            enabled=True,
            max_messages=50,
            max_tokens=-1,
        )


def test_agent_config_all_fields():
    """Test agent config with all fields specified."""
    compaction = ContextCompactionConfig(
        enabled=True,
        max_messages=60,
        max_tokens=120000,
    )
    
    config = AgentConfig(
        id="full_agent",
        llm_profile_name="reasoning",
        name="Full Agent",
        description="Agent with all fields",
        workspace_root="/tmp/ws",
        max_tool_iterations=50,
        planning_enabled=False,
        inject_workspace_instructions=False,
        auto_persist_tools=True,
        context_compaction=compaction,
    )
    
    assert config.id == "full_agent"
    assert config.llm_profile_name == "reasoning"
    assert config.name == "Full Agent"
    assert config.description == "Agent with all fields"
    assert config.workspace_root == Path("/tmp/ws")
    assert config.max_tool_iterations == 50
    assert config.planning_enabled is False
    assert config.inject_workspace_instructions is False
    assert config.auto_persist_tools is True
    assert config.context_compaction.enabled is True


def test_subagent_config():
    """Test SubagentConfig and can_be_subagent property."""
    # Agent without as_subagent
    config = AgentConfig(id="main_agent", name="Main Agent")
    assert not config.can_be_subagent
    assert config.as_subagent is None

    # Agent with as_subagent
    sub_cfg = SubagentConfig(
        tool_name="discovery_tool",
        tool_description="Find relevant data",
        tool_parameters={"query": {"type": "string", "required": True}},
        response_handling=ResponseHandling.PARSE_JSON,
        auto_load_artifacts=True,
        user_message_template="Query: {query}",
    )
    config_with_sub = AgentConfig(
        id="discovery_agent",
        name="Discovery Agent",
        as_subagent=sub_cfg,
    )
    assert config_with_sub.can_be_subagent
    assert config_with_sub.as_subagent.tool_name == "discovery_tool"
    assert config_with_sub.as_subagent.auto_load_artifacts is True
    assert config_with_sub.as_subagent.user_message_template == "Query: {query}"
