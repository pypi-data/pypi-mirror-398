"""Store for managing multiple agent configurations."""
from __future__ import annotations

import logging
from typing import Optional

from .agent import AgentConfig

LOGGER = logging.getLogger("agentic_ai.agent_config_store")


class AgentConfigStore:
    """Store for managing multiple agent configurations."""

    def __init__(self, configs: dict[str, AgentConfig]):
        """
        Initialize the store with agent configurations.
        
        Args:
            configs: Dictionary mapping agent IDs to their configurations.
        """
        self._configs = configs
        LOGGER.debug(
            "AgentConfigStore initialized with %d configurations: %s",
            len(configs),
            ", ".join(configs.keys()),
        )

    def get_config(self, agent_id: str) -> AgentConfig:
        """
        Get agent configuration by ID.
        
        Args:
            agent_id: The ID of the agent configuration.
        
        Returns:
            The agent configuration.
        
        Raises:
            ValueError: If the agent configuration is not found.
        """
        if agent_id not in self._configs:
            available = ", ".join(self._configs.keys())
            raise ValueError(
                f"Agent configuration '{agent_id}' not found. Available: {available}"
            )
        return self._configs[agent_id]

    def get_config_optional(self, agent_id: str) -> Optional[AgentConfig]:
        """
        Get agent configuration by ID, returning None if not found.
        
        Args:
            agent_id: The ID of the agent configuration.
        
        Returns:
            The agent configuration or None if not found.
        """
        return self._configs.get(agent_id)

    def has_config(self, agent_id: str) -> bool:
        """
        Check if an agent configuration exists.
        
        Args:
            agent_id: The ID of the agent configuration.
        
        Returns:
            True if the configuration exists, False otherwise.
        """
        return agent_id in self._configs

    @property
    def available_agents(self) -> list[str]:
        """Get list of available agent IDs."""
        return list(self._configs.keys())

    @property
    def configs(self) -> list[AgentConfig]:
        """Get list of agent configurations."""
        return list(self._configs.values())


def create_agent_config_store_from_list(configs: list[AgentConfig]) -> AgentConfigStore:
    """
    Create an agent config store from a list of configurations.
    
    Args:
        configs: List of agent configurations. Each must have a unique 'id' field.
    
    Returns:
        Configured AgentConfigStore instance.
    
    Raises:
        ValueError: If any config lacks an id or IDs are not unique.
    """
    config_dict: dict[str, AgentConfig] = {}
    
    for config in configs:
        if not config.id:
            raise ValueError("All agent configurations must have an 'id' field")
        if config.id in config_dict:
            raise ValueError(f"Duplicate agent configuration id: '{config.id}'")
        config_dict[config.id] = config
    
    return AgentConfigStore(config_dict)


def create_agent_config_store_from_manifest(
    manifest: "AgentManifest",
    fallback_agents: list[AgentConfig] | None = None,
) -> AgentConfigStore:
    """Create an agent config store from a declarative manifest.

    Args:
        manifest: AgentManifest loaded from manifest/agents.yaml.
        fallback_agents: Optional fallback agent configs (e.g., from env.yaml).

    Returns:
        Configured AgentConfigStore instance.
    """
    from .manifest import AgentManifest

    if not isinstance(manifest, AgentManifest):
        raise ValueError("manifest must be an AgentManifest instance")

    configs: list[AgentConfig] = []
    fallback_map = {cfg.id: cfg for cfg in (fallback_agents or []) if cfg.id}

    for agent_id, data in manifest.agents.items():
        payload = {"id": agent_id, **data}
        configs.append(AgentConfig.model_validate(payload))

    # Add fallback configs not overridden by manifest
    for agent_id, cfg in fallback_map.items():
        if not any(entry.id == agent_id for entry in configs):
            configs.append(cfg)

    return create_agent_config_store_from_list(configs)


__all__ = [
    "AgentConfigStore",
    "create_agent_config_store_from_list",
    "create_agent_config_store_from_manifest",
]
