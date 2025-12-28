"""Test AgentConfig and AgentConfigStore."""
import pytest
from pathlib import Path

from agentic_ai import AgentConfig, AgentConfigStore, create_agent_config_store_from_list


class TestAgentConfig:
    """Tests for AgentConfig."""
    
    def test_minimal_config(self):
        """Test creating a minimal agent config."""
        config = AgentConfig(id="test_agent")
        
        assert config.id == "test_agent"
        assert config.llm_profile_name == "default"
        assert config.planning_enabled is True
        assert config.max_tool_iterations == 30
    
    def test_full_config(self):
        """Test creating a fully specified agent config."""
        config = AgentConfig(
            id="analyst",
            name="Data Analyst",
            description="Analyzes data and generates reports",
            llm_profile_name="gpt4",
            system_prompt_file="manifest/prompts/analyst.md",
            workspace_root=Path("/tmp/ws"),
            max_tool_iterations=50,
            planning_enabled=True,
            inject_workspace_instructions=True,
            auto_persist_tools=True,
        )
        
        assert config.id == "analyst"
        assert config.name == "Data Analyst"
        assert config.llm_profile_name == "gpt4"
        assert config.max_tool_iterations == 50
        assert config.workspace_root == Path("/tmp/ws")
    
    def test_default_system_prompt_file(self):
        """Test that system_prompt_file defaults to manifest/prompts/{id}.md."""
        from agentic_ai.defaults import get_default_prompt_path
        
        config = AgentConfig(id="my_agent")
        
        assert config.system_prompt_file == get_default_prompt_path("my_agent")
    
    def test_invalid_max_iterations(self):
        """Test that max_tool_iterations must be positive."""
        with pytest.raises(ValueError, match="max_tool_iterations must be positive"):
            AgentConfig(id="test", max_tool_iterations=0)
    
    def test_empty_id_rejected(self):
        """Test that empty id is rejected."""
        with pytest.raises(ValueError, match="Agent id cannot be empty"):
            AgentConfig(id="")


class TestAgentConfigStore:
    """Tests for AgentConfigStore."""
    
    def test_create_from_list(self):
        """Test creating store from list of configs."""
        configs = [
            AgentConfig(id="agent1"),
            AgentConfig(id="agent2", llm_profile_name="fast"),
        ]
        
        store = create_agent_config_store_from_list(configs)
        
        assert store.get_config("agent1").id == "agent1"
        assert store.get_config("agent2").llm_profile_name == "fast"
    
    def test_get_missing_config(self):
        """Test that getting missing config raises ValueError."""
        store = create_agent_config_store_from_list([AgentConfig(id="only_one")])
        
        with pytest.raises(ValueError, match="not found"):
            store.get_config("missing")
    
    def test_duplicate_id_rejected(self):
        """Test that duplicate IDs are rejected."""
        configs = [
            AgentConfig(id="same"),
            AgentConfig(id="same"),
        ]
        
        with pytest.raises(ValueError, match="Duplicate"):
            create_agent_config_store_from_list(configs)
    
    def test_available_agents(self):
        """Test listing available agents."""
        configs = [
            AgentConfig(id="agent1"),
            AgentConfig(id="agent2"),
            AgentConfig(id="agent3"),
        ]
        
        store = create_agent_config_store_from_list(configs)
        
        assert set(store.available_agents) == {"agent1", "agent2", "agent3"}
