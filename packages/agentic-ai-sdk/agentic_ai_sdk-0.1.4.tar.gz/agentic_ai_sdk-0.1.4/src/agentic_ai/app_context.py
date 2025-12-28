"""Base application context for Deep Agent framework.

This module provides a reusable application context pattern that holds
configuration, LLM factory, and agent config store. Applications can
extend this base context with their own specific fields.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar, Optional, Callable

from .config.agent import AgentConfig
from .config.store import AgentConfigStore
from .llm.factory import LLMClientFactory

if TYPE_CHECKING:
    from .config import BaseAppConfig
    from .llm.config import LLMConfig

LOGGER = logging.getLogger("agentic_ai.app_context")

# Type variable for config classes
ConfigT = TypeVar("ConfigT", bound="BaseAppConfig")
ContextT = TypeVar("ContextT")


@dataclass(frozen=True)
class BaseAppContext(Generic[ConfigT]):
    """Base application context holding config, LLM factory, and agent configs.
    
    This is an immutable context object that provides a single source of truth
    for application-wide configuration. Applications can extend this by creating
    a subclass with additional fields.
    
    Example:
        @dataclass(frozen=True)
        class MyAppContext(BaseAppContext[MyAppConfig]):
            my_client: MyServiceClient
    """
    
    config: ConfigT
    llm_factory: LLMClientFactory
    agent_store: AgentConfigStore
    
    def get_agent_config(self, agent_id: str) -> AgentConfig:
        """Get agent config by ID.
        
        Args:
            agent_id: The unique identifier of the agent configuration.
            
        Returns:
            The agent configuration.
            
        Raises:
            ValueError: If the agent configuration is not found.
        """
        return self.agent_store.get_config(agent_id)
    
    def get_llm_config(self, llm_name: str = "default") -> "LLMConfig":
        """Get LLM config by name.
        
        Args:
            llm_name: The name of the LLM configuration. Defaults to "default".
            
        Returns:
            The LLM configuration.
            
        Raises:
            ValueError: If the LLM configuration is not found.
        """
        return self.llm_factory.get_config(llm_name)


class AppContextManager(Generic[ContextT]):
    """Lightweight singleton manager for application contexts.

    Centralises the global-context pattern so apps don't reimplement it.
    """

    _instance: ContextT | None = None

    @classmethod
    def init(cls, context: ContextT) -> ContextT:
        cls._instance = context
        return context

    @classmethod
    def get(cls, default_factory: Callable[[], ContextT] | None = None) -> ContextT:
        if cls._instance is None and default_factory:
            cls._instance = default_factory()
        if cls._instance is None:
            raise RuntimeError("Application context not initialized")
        return cls._instance


def build_app_context(
    config: "BaseAppConfig",
    *,
    legacy_agent_builder: Optional[callable] = None,
) -> BaseAppContext:
    """Build a base application context from configuration.
    
    This function creates the standard components (LLM factory, agent store)
    from the configuration. Applications can use this directly or extend it
    with additional components.
    
    Args:
        config: The application configuration containing llms and agents lists.
        legacy_agent_builder: Optional callable that takes config and returns
            an AgentConfigStore. Used for backward compatibility when agents
            are not explicitly defined in config.agents.
    
    Returns:
        A configured BaseAppContext instance.
    
    Example:
        # Basic usage
        config = load_yaml_config("config.yaml", MyAppConfig)
        ctx = build_app_context(config)
        
        # With legacy support
        ctx = build_app_context(config, legacy_agent_builder=_build_legacy_agents)
    """
    # Create LLM factory from config
    llm_configs_dict = {llm.name: llm for llm in config.llm_profiles}
    llm_factory = LLMClientFactory(llm_configs_dict)
    
    # Create agent config store
    if config.agents:
        agent_configs_dict = {agent.id: agent for agent in config.agents}
        agent_store = AgentConfigStore(agent_configs_dict)
    elif legacy_agent_builder is not None:
        agent_store = legacy_agent_builder(config)
    else:
        agent_store = AgentConfigStore({})
    
    LOGGER.debug(
        "Built app context | llms=%d | agents=%d",
        len(llm_configs_dict),
        len(agent_store.available_agents),
    )
    
    return BaseAppContext(
        config=config,
        llm_factory=llm_factory,
        agent_store=agent_store,
    )


__all__ = [
    "BaseAppContext",
    "build_app_context",
    "AppContextManager",
]
