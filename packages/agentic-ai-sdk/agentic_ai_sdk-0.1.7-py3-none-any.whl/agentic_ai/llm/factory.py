"""Factory for creating LLM clients by name."""
from __future__ import annotations

import logging
from typing import Optional

from agent_framework import BaseChatClient

from .client import create_chat_client
from .config import LLMConfig

LOGGER = logging.getLogger("agentic_ai.llm_factory")


class LLMClientFactory:
    """Factory for creating and caching LLM clients by name."""

    def __init__(self, llm_configs: dict[str, LLMConfig]):
        """
        Initialize the factory with LLM configurations.
        
        Args:
            llm_configs: Dictionary mapping LLM names to their configurations.
        """
        self._configs = llm_configs
        self._clients: dict[str, BaseChatClient] = {}
        LOGGER.debug(
            "LLMClientFactory initialized with %d configurations: %s",
            len(llm_configs),
            ", ".join(llm_configs.keys()),
        )

    def get_client(self, name: str, override_model: Optional[str] = None) -> BaseChatClient:
        """
        Get or create an LLM client by name.
        
        Args:
            name: The name of the LLM configuration to use.
            override_model: Optional model override for this client.
        
        Returns:
            The chat client instance.
        
        Raises:
            ValueError: If the LLM configuration with the given name is not found.
        """
        if name not in self._configs:
            available = ", ".join(self._configs.keys())
            raise ValueError(
                f"LLM configuration '{name}' not found. Available: {available}"
            )

        # Create cache key including override if present
        cache_key = f"{name}:{override_model}" if override_model else name

        if cache_key not in self._clients:
            config = self._configs[name]
            LOGGER.debug("Creating new LLM client for '%s'", cache_key)
            client = create_chat_client(config, override_model=override_model)
            self._clients[cache_key] = client
        else:
            LOGGER.debug("Reusing cached LLM client for '%s'", cache_key)

        return self._clients[cache_key]

    def get_config(self, name: str) -> LLMConfig:
        """
        Get the LLM configuration by name.
        
        Args:
            name: The name of the LLM configuration.
        
        Returns:
            The LLM configuration.
        
        Raises:
            ValueError: If the LLM configuration with the given name is not found.
        """
        if name not in self._configs:
            available = ", ".join(self._configs.keys())
            raise ValueError(
                f"LLM configuration '{name}' not found. Available: {available}"
            )
        return self._configs[name]

    @property
    def available_llms(self) -> list[str]:
        """Get list of available LLM names."""
        return list(self._configs.keys())


def create_llm_factory_from_list(configs: list[LLMConfig]) -> LLMClientFactory:
    """
    Create an LLM factory from a list of configurations.
    
    Args:
        configs: List of LLM configurations. Each must have a unique 'name' field.
    
    Returns:
        Configured LLMClientFactory instance.
    
    Raises:
        ValueError: If any config lacks a name or names are not unique.
    """
    config_dict: dict[str, LLMConfig] = {}
    
    for config in configs:
        if not config.name:
            raise ValueError("All LLM configurations must have a 'name' field")
        if config.name in config_dict:
            raise ValueError(f"Duplicate LLM configuration name: '{config.name}'")
        config_dict[config.name] = config
    
    return LLMClientFactory(config_dict)


__all__ = ["LLMClientFactory", "create_llm_factory_from_list"]
