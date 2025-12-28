"""Centralized default paths and runtime conventions.

All default file paths and directory conventions used by the SDK.
Override these by passing explicit paths to functions, or by setting
environment variables where supported.

Usage:
    from agentic_ai.defaults import ENV_CONFIG_FILE, MANIFEST_DIR
    
    # Or import all defaults
    from agentic_ai import defaults
    config_path = defaults.ENV_CONFIG_FILE
"""

# =============================================================================
# Configuration Files (relative to project root)
# =============================================================================

# Environment configuration file (LLM credentials, observability settings, etc.)
ENV_CONFIG_FILE = "env.yaml"

# =============================================================================
# Manifest Directory Structure
# =============================================================================

# Root directory for declarative agent configuration
MANIFEST_DIR = "manifest"

# Agent manifest file (defines agents, tools, sub-agents)
AGENT_MANIFEST_FILE = f"{MANIFEST_DIR}/agents.yaml"

# Tools manifest file (plugin-style tool configuration)
TOOLS_MANIFEST_FILE = f"{MANIFEST_DIR}/tools.yaml"

# MCP (Model Context Protocol) manifest file
MCP_MANIFEST_FILE = f"{MANIFEST_DIR}/mcp.yaml"

# UI configuration file
UI_CONFIG_FILE = f"{MANIFEST_DIR}/ui.yaml"

# Prompts directory
PROMPTS_DIR = f"{MANIFEST_DIR}/prompts"

# =============================================================================
# Workspace Defaults
# =============================================================================

# Default workspace root directory
DEFAULT_WORKSPACE_ROOT = ".ws"

# Default logs directory
DEFAULT_LOGS_DIR = "logs"

# =============================================================================
# Helper Functions
# =============================================================================


def get_default_prompt_path(agent_id: str) -> str:
    """Get default prompt file path for an agent.
    
    Args:
        agent_id: The agent identifier.
        
    Returns:
        Relative path to the prompt file (e.g., "manifest/prompts/my_agent.md").
    """
    return f"{PROMPTS_DIR}/{agent_id}.md"


__all__ = [
    # Configuration files
    "ENV_CONFIG_FILE",
    # Manifest structure
    "MANIFEST_DIR",
    "AGENT_MANIFEST_FILE",
    "TOOLS_MANIFEST_FILE",
    "MCP_MANIFEST_FILE",
    "UI_CONFIG_FILE",
    "PROMPTS_DIR",
    # Workspace
    "DEFAULT_WORKSPACE_ROOT",
    "DEFAULT_LOGS_DIR",
    # Functions
    "get_default_prompt_path",
]
