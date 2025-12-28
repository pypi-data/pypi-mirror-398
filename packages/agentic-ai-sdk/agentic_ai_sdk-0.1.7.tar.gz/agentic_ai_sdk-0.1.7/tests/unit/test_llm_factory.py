"""Tests for deep_agent LLM factory."""
from __future__ import annotations

import pytest

from agentic_ai import LLMConfig, LLMClientFactory, create_llm_factory_from_list


def test_llm_factory_creation_from_list():
    """Test creating LLM factory from a list of configurations."""
    configs = [
        LLMConfig(
            name="default",
            provider="openai",
            api_key="test-key-1",
            model="gpt-5-mini",
        ),
        LLMConfig(
            name="deepseek",
            provider="openai",
            api_key="test-key-2",
            model="deepseek-chat",
        ),
    ]
    
    factory = create_llm_factory_from_list(configs)
    
    assert factory.available_llms == ["default", "deepseek"]


def test_llm_factory_get_config():
    """Test getting config from factory."""
    configs = [
        LLMConfig(
            name="test",
            provider="openai",
            api_key="test-key",
            model="gpt-5-mini",
        ),
    ]
    
    factory = create_llm_factory_from_list(configs)
    config = factory.get_config("test")
    
    assert config.name == "test"
    assert config.model == "gpt-5-mini"


def test_llm_factory_get_config_not_found():
    """Test getting non-existent config raises error."""
    factory = LLMClientFactory({})
    
    with pytest.raises(ValueError, match="LLM configuration 'nonexistent' not found"):
        factory.get_config("nonexistent")


def test_llm_factory_requires_unique_names():
    """Test that duplicate names are rejected."""
    configs = [
        LLMConfig(
            name="test",
            provider="openai",
            api_key="test-key-1",
            model="gpt-5-mini",
        ),
        LLMConfig(
            name="test",
            provider="openai",
            api_key="test-key-2",
            model="gpt-4",
        ),
    ]
    
    with pytest.raises(ValueError, match="Duplicate LLM configuration name"):
        create_llm_factory_from_list(configs)


def test_llm_factory_requires_names():
    """Test that configs without names are rejected."""
    configs = [
        LLMConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-5-mini",
        ),
    ]
    
    with pytest.raises(ValueError, match="All LLM configurations must have a 'name' field"):
        create_llm_factory_from_list(configs)
