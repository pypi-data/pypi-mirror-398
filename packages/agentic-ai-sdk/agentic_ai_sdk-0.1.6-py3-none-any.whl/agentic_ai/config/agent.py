"""Agent configuration schema for Deep Agent framework."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, model_validator

from ..defaults import get_default_prompt_path


class ResponseHandling(str, Enum):
    """How to handle sub-agent response before auto_load_artifacts.
    
    - none: No processing, return response.text as-is
    - parse_json: Extract and return the last JSON object from response text (default)
    - last_artifact: Get artifact ID from the last tool that called set_last_artifact_id()
    """
    NONE = "none"
    PARSE_JSON = "parse_json"
    LAST_ARTIFACT = "last_artifact"


class SubagentConfig(BaseModel):
    """Configuration for when agent is used as a subagent tool."""

    tool_name: Optional[str] = None  # Tool name override (default: agent_id)
    tool_description: Optional[str] = None  # Tool description (default: agent.description)
    tool_parameters: Optional[dict[str, Any]] = None  # Tool parameter schema
    response_handling: ResponseHandling = ResponseHandling.PARSE_JSON  # How to process response
    auto_load_artifacts: bool = False  # Auto-load artifact data after response_handling
    user_message_template: Optional[str] = None  # Template for rendering task into prompt
    builder: Optional[str] = None  # Import path to custom sub-agent controller builder


class ContextCompactionConfig(BaseModel):
    """Configuration for context compaction (history management)."""

    enabled: bool = True
    max_messages: int = 100  # Maximum number of messages before triggering compaction
    max_tokens: Optional[int] = None  # Optional token limit for triggering compaction

    @model_validator(mode="after")
    def _validate_limits(self) -> "ContextCompactionConfig":
        if self.max_messages <= 0:
            raise ValueError("max_messages must be positive")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive if specified")
        return self


class AgentConfig(BaseModel):
    """Configuration for a Deep Agent instance."""

    id: str  # Unique identifier for the agent
    llm_profile_name: str = "default"  # Name of the LLM profile to use
    name: Optional[str] = None  # Human-readable agent name
    description: Optional[str] = None  # Agent description
    system_prompt_file: Optional[str] = None  # Path to system prompt file, default: manifest/prompts/{agent_id}.md
    workspace_root: Path | str = Path(".ws")  # Workspace root directory
    max_tool_iterations: int = 30  # Maximum tool calls allowed
    planning_enabled: bool = True  # Enable update_plan tool
    inject_workspace_instructions: bool = True  # Inject workspace context
    auto_persist_tools: bool = False  # Auto-persist tool results
    context_compaction: Optional[ContextCompactionConfig] = None  # Context compaction settings
    middlewares: Optional[list[str]] = None  # Middleware function paths (module:ClassName or module:factory_func)
    # Declarative agent extensions (optional)
    tools: Optional[list[str]] = None  # Tool provider references for this agent
    subagents: Optional[list[str]] = None  # Sub-agent references for this agent
    # Subagent configuration (when this agent is used as a subagent)
    as_subagent: Optional[SubagentConfig] = None

    @property
    def can_be_subagent(self) -> bool:
        """Check if this agent can be used as a subagent."""
        return self.as_subagent is not None

    @model_validator(mode="after")
    def _validate(self) -> "AgentConfig":
        if isinstance(self.workspace_root, str):
            self.workspace_root = Path(self.workspace_root)
        if self.max_tool_iterations <= 0:
            raise ValueError("max_tool_iterations must be positive")
        if not self.id:
            raise ValueError("Agent id cannot be empty")
        # Set default system_prompt_file if not provided
        if self.system_prompt_file is None:
            self.system_prompt_file = get_default_prompt_path(self.id)
        return self

    def get_system_prompt_path(self, base_dir: Path | str | None = None) -> Path:
        """Get the full path to the system prompt file.
        
        Args:
            base_dir: Base directory for relative paths. If None, uses current working directory.
            
        Returns:
            Full path to the system prompt file.
        """
        if self.system_prompt_file is None:
            raise ValueError("system_prompt_file is not set")
        
        prompt_path = Path(self.system_prompt_file)
        if prompt_path.is_absolute():
            return prompt_path
        
        if base_dir is None:
            base_dir = Path.cwd()
        else:
            base_dir = Path(base_dir)
        
        return base_dir / prompt_path


__all__ = ["AgentConfig", "ContextCompactionConfig", "ResponseHandling", "SubagentConfig"]
