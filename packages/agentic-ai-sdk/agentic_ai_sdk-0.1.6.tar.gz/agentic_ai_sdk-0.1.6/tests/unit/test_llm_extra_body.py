"""Tests for extra_body support in LLM configuration."""
import pytest
from agentic_ai.llm import LLMConfig, build_agent_chat_options, build_chat_options


def test_build_agent_chat_options_with_extra_body():
    """Test that build_agent_chat_options includes extra_body."""
    config = LLMConfig(
        name="test",
        provider="openai",
        api_key="sk-test",
        model="deepseek-reasoner",
        extra_body={
            "enable_thinking": True,
            "thinking_budget": 2048,
        }
    )
    
    options = build_agent_chat_options(config)
    
    assert "extra_body" in options
    assert options["extra_body"]["enable_thinking"] is True
    assert options["extra_body"]["thinking_budget"] == 2048


def test_build_agent_chat_options_with_reasoning_and_extra_body():
    """Test that both reasoning_effort and extra_body are included."""
    config = LLMConfig(
        name="test",
        provider="openai",
        api_key="sk-test",
        model="gpt-4",
        reasoning_effort="high",
        extra_body={
            "custom_param": "value",
        }
    )
    
    options = build_agent_chat_options(config)
    
    assert "reasoning_effort" in options
    assert options["reasoning_effort"] == "high"
    assert "extra_body" in options
    assert options["extra_body"]["custom_param"] == "value"


def test_build_agent_chat_options_without_extra_body():
    """Test that extra_body is not included when not configured."""
    config = LLMConfig(
        name="test",
        provider="openai",
        api_key="sk-test",
        model="gpt-4",
    )
    
    options = build_agent_chat_options(config)
    
    assert "extra_body" not in options


def test_build_chat_options_with_extra_body():
    """Test that build_chat_options includes extra_body from config."""
    config = LLMConfig(
        name="test",
        provider="openai",
        api_key="sk-test",
        model="deepseek-reasoner",
        temperature=1.0,
        extra_body={
            "enable_thinking": True,
        }
    )
    
    options = build_chat_options(config)
    
    assert "extra_body" in options
    assert options["extra_body"]["enable_thinking"] is True
    assert "temperature" in options
    assert options["temperature"] == 1.0


def test_build_chat_options_with_nested_extra_body():
    """Test nested extra_body structures in build_chat_options."""
    config = LLMConfig(
        name="test",
        provider="openai",
        api_key="sk-test",
        model="claude-sonnet",
        extra_body={
            "thinking": {
                "type": "enabled",
                "budget_tokens": 10240
            }
        }
    )
    
    options = build_chat_options(config)
    
    assert "extra_body" in options
    assert options["extra_body"]["thinking"]["type"] == "enabled"
    assert options["extra_body"]["thinking"]["budget_tokens"] == 10240


def test_build_chat_options_all_parameters():
    """Test build_chat_options with all parameters including extra_body."""
    config = LLMConfig(
        name="test",
        provider="openai",
        api_key="sk-test",
        model="gpt-4",
        temperature=0.7,
        reasoning_effort="medium",
        extra_body={
            "custom_setting": True,
        }
    )
    
    options = build_chat_options(
        config,
        requested_temperature=0.9,
        max_output_tokens=4096,
    )
    
    # Temperature should be overridden
    assert options["temperature"] == 0.9
    # Max tokens should be set
    assert "max_tokens" in options or "max_completion_tokens" in options
    # Reasoning effort should be included
    assert options["reasoning_effort"] == "medium"
    # Extra body should be included
    assert options["extra_body"]["custom_setting"] is True
