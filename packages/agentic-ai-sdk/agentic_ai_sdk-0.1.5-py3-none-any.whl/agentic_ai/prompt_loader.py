"""Prompt loading utilities for Deep Agent framework."""

from __future__ import annotations

from pathlib import Path


def load_prompt_from_file(
    file_path: Path | str,
    *,
    strip_markdown_headers: bool = True,
) -> str:
    """
    Load a prompt from a file.
    
    Args:
        file_path: Path to the prompt file
        strip_markdown_headers: Whether to strip markdown headers and convert to plain text
        
    Returns:
        The prompt content as a string
        
    Raises:
        FileNotFoundError: If the prompt file does not exist
        
    Example:
        >>> prompt = load_prompt_from_file("prompts/my_agent.md")
        >>> prompt = load_prompt_from_file(Path("prompts/my_agent.md"), strip_markdown_headers=False)
    """
    prompt_file = Path(file_path)
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    content = prompt_file.read_text(encoding="utf-8")
    
    if not strip_markdown_headers:
        return content
    
    # Strip markdown headers and convert to plain text for system prompts
    lines = content.split("\n")
    result_lines = []
    for line in lines:
        # Skip markdown headers (# Title)
        if line.startswith("# ") and not line.startswith("# Your Task"):
            continue
        # Skip horizontal rules
        if line.strip() == "---":
            continue
        # Convert markdown headers (## Section) to plain text
        if line.startswith("## "):
            result_lines.append(line[3:].strip())
            continue
        # Keep everything else
        result_lines.append(line)
    
    return "\n".join(result_lines).strip()


def load_prompt_from_agent_config(
    agent_config,  # AgentConfig type
    base_dir: Path | str | None = None,
    *,
    strip_markdown_headers: bool = True,
) -> str:
    """
    Load a prompt from an agent configuration.
    
    Args:
        agent_config: AgentConfig instance with system_prompt_file set
        base_dir: Base directory for resolving relative paths
        strip_markdown_headers: Whether to strip markdown headers
        
    Returns:
        The prompt content as a string
        
    Raises:
        FileNotFoundError: If the prompt file does not exist
        
    Example:
        >>> from agentic_ai import AgentConfig
        >>> config = AgentConfig(id="my_agent")
        >>> prompt = load_prompt_from_agent_config(config)
    """
    prompt_path = agent_config.get_system_prompt_path(base_dir)
    return load_prompt_from_file(prompt_path, strip_markdown_headers=strip_markdown_headers)


__all__ = [
    "load_prompt_from_file",
    "load_prompt_from_agent_config",
]
