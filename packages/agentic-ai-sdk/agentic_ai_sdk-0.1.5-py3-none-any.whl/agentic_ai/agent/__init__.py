"""Agent core components for Agentic AI SDK.

This subpackage provides:
- DeepAgentSession: Main agent session class
- SubAgentController: Controller for sub-agent orchestration
- DeclarativeAgentBuilder: Build agents from declarative manifests
- Various agent builder functions
"""
from __future__ import annotations

from .core import (
    ChatInput,
    DeepAgentSession,
    build_agent,
    build_agent_from_config,
    build_agent_from_store,
    build_agent_session,
    build_agent_with_llm,
)
from .sub_agent import AutoLoadOnError, SubAgentController
from .declarative_builder import DeclarativeAgentBuilder, DeclarativeBuildResult

__all__ = [
    # Core
    "ChatInput",
    "DeepAgentSession",
    "build_agent",
    "build_agent_from_config",
    "build_agent_from_store",
    "build_agent_session",
    "build_agent_with_llm",
    # Sub-agent
    "AutoLoadOnError",
    "SubAgentController",
    # Declarative builder
    "DeclarativeAgentBuilder",
    "DeclarativeBuildResult",
]
