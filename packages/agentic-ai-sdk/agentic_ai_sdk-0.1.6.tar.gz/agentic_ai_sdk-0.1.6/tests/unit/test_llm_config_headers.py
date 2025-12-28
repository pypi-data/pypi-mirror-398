"""Tests for LLM configuration with custom headers support."""
import pytest
from agentic_ai.llm import LLMConfig, create_chat_client


def test_llm_config_with_default_headers():
    """Test that LLMConfig accepts default_headers."""
    config = LLMConfig(
        name="bmw-qwen",
        provider="openai",
        api_key="dummy",
        model="qwen3-235b-a22b",
        base_url="https://cnapi-service-i.ali.bba.cloud.bmw/aiplatform/llmplatformapimanagementaliyun/v1/lm-platform/llm/v1",
        temperature=1.0,
        default_headers={
            "apikey": "test-api-key-12345",
            "Authorization": "ACCESSCODE test-access-code-67890"
        }
    )
    
    assert config.name == "bmw-qwen"
    assert config.default_headers is not None
    assert config.default_headers["apikey"] == "test-api-key-12345"
    assert config.default_headers["Authorization"] == "ACCESSCODE test-access-code-67890"


def test_llm_config_without_default_headers():
    """Test that default_headers is optional."""
    config = LLMConfig(
        name="default",
        provider="openai",
        api_key="sk-test",
        model="gpt-4",
    )
    
    assert config.default_headers is None


def test_create_chat_client_with_headers():
    """Test that create_chat_client passes headers to OpenAIChatClient."""
    config = LLMConfig(
        name="bmw-qwen",
        provider="openai",
        api_key="dummy",
        model="qwen3-235b-a22b",
        base_url="https://cnapi-service-i.ali.bba.cloud.bmw/test",
        default_headers={
            "apikey": "test-key",
            "Authorization": "ACCESSCODE test-code"
        }
    )
    
    # This should not raise an error
    client = create_chat_client(config)
    assert client is not None


def test_create_chat_client_without_headers():
    """Test that create_chat_client works without headers."""
    config = LLMConfig(
        name="default",
        provider="openai",
        api_key="sk-test",
        model="gpt-4",
    )
    
    client = create_chat_client(config)
    assert client is not None


def test_llm_config_with_extra_body():
    """Test that LLMConfig accepts extra_body."""
    config = LLMConfig(
        name="deepseek-reasoning",
        provider="openai",
        api_key="sk-test",
        model="deepseek-reasoner",
        temperature=1.0,
        extra_body={
            "enable_thinking": True,
            "thinking_budget": 2048,
        }
    )
    
    assert config.extra_body is not None
    assert config.extra_body["enable_thinking"] is True
    assert config.extra_body["thinking_budget"] == 2048


def test_llm_config_with_nested_extra_body():
    """Test that LLMConfig accepts nested extra_body structures."""
    config = LLMConfig(
        name="claude-reasoning",
        provider="openai",
        api_key="test-key",
        model="claude-3-7-sonnet",
        extra_body={
            "thinking": {
                "type": "enabled",
                "budget_tokens": 10240
            }
        }
    )
    
    assert config.extra_body is not None
    assert "thinking" in config.extra_body
    assert config.extra_body["thinking"]["type"] == "enabled"
    assert config.extra_body["thinking"]["budget_tokens"] == 10240


def test_llm_config_without_extra_body():
    """Test that extra_body is optional."""
    config = LLMConfig(
        name="default",
        provider="openai",
        api_key="sk-test",
        model="gpt-4",
    )
    
    assert config.extra_body is None
