"""LLM client utilities for Deep Agent.

This subpackage provides:
- LLM configuration (LLMConfig)
- Chat client creation (create_chat_client)
- LLM factory for managing multiple LLM configs (LLMClientFactory)
- Chat options building utilities

Example:
    from agentic_ai.llm import (
        LLMConfig,
        LLMClientFactory,
        create_chat_client,
    )
"""
from __future__ import annotations

# Re-export from files in this directory
from .config import LLMConfig
from .client import (
    build_agent_chat_options,
    build_chat_options,
    create_chat_client,
    resolve_temperature,
)
from .factory import LLMClientFactory, create_llm_factory_from_list

__all__ = [
    "LLMConfig",
    "LLMClientFactory",
    "build_agent_chat_options",
    "build_chat_options",
    "create_chat_client",
    "create_llm_factory_from_list",
    "resolve_temperature",
]
