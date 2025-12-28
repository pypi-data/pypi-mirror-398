"""Sub-agent controller base class for Deep Agent framework.

This module provides a reusable pattern for building task-driven sub-agents
that can be orchestrated by a master agent.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generic, TypeVar, AsyncIterator

from agent_framework import AgentRunResponse, AgentRunResponseUpdate, AIFunction
from pydantic import Field, create_model

from .core import DeepAgentSession
from ..artifacts import ToolResult, load_artifact, error as error_result
from ..runtime.tool_runtime import set_task_context, reset_task_context, get_last_artifact_id, reset_last_artifact_id, get_output_config


class AutoLoadOnError(str, Enum):
    """auto_load_artifacts 失败时的行为策略。
    
    - RAISE: 抛出异常
    - RETURN_ERROR: 返回 status="error" 的 ToolResult（默认）
    - RETURN_EMPTY: 返回空结果（不推荐）
    """
    RAISE = "raise"
    RETURN_ERROR = "return_error"
    RETURN_EMPTY = "return_empty"

LOGGER = logging.getLogger("agentic_ai.sub_agent")

# Type variable for task types
TaskT = TypeVar("TaskT")


@dataclass
class SubAgentController(Generic[TaskT]):
    """Base controller for task-driven sub-agents.
    
    This provides a reusable pattern for sub-agents that:
    1. Receive tasks from a master agent
    2. Update their internal state based on the task
    3. Render the task into a prompt
    4. Execute and return results
    
    Subclasses should override:
    - render_prompt(): Convert task to prompt string
    - on_task_start(): Optional hook for task-specific setup (e.g., updating toolset)
    
    Example:
        @dataclass
        class MySubAgentController(SubAgentController[MyTask]):
            toolset: MyToolset
            
            def on_task_start(self, task: MyTask) -> None:
                self.toolset.update_context(task)
            
            def render_prompt(self, task: MyTask) -> str:
                return f"Process this task: {task.description}"
    """
    
    session: DeepAgentSession
    _resources: list[Any] = field(default_factory=list, init=False, repr=False)
    
    def render_prompt(self, task: TaskT) -> str:
        """Render a task into a prompt string for the agent.
        
        Subclasses must override this method to convert their task type
        into an appropriate prompt.
        
        Args:
            task: The task to convert to a prompt.
            
        Returns:
            The prompt string to send to the agent.
        """
        raise NotImplementedError("Subclasses must implement render_prompt()")
    
    def on_task_start(self, task: TaskT) -> None:
        """Hook called before task execution.
        
        Override this method to perform task-specific setup, such as
        updating toolset state with task context.
        
        Args:
            task: The task about to be executed.
        """
        pass
    
    def register_resource(self, resource: Any) -> None:
        """Register a closable resource (must have close())."""
        if resource is not None:
            self._resources.append(resource)
    
    def close(self) -> None:
        """Close all registered resources."""
        for resource in self._resources:
            try:
                closer = getattr(resource, "close", None)
                if callable(closer):
                    closer()
            except Exception:
                LOGGER.debug("Failed to close resource %s", resource, exc_info=True)
        self._resources.clear()
    
    def __enter__(self) -> "SubAgentController[TaskT]":
        return self
    
    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
    
    async def run_task(self, task: TaskT) -> AgentRunResponse:
        """Run a task and return the response.
        
        This method:
        1. Calls on_task_start() for any pre-execution setup
        2. Renders the task to a prompt
        3. Runs the agent and returns the response
        
        Args:
            task: The task to execute.
            
        Returns:
            The agent's response.
        """
        self.on_task_start(task)
        prompt = self.render_prompt(task)
        LOGGER.debug(
            "Running sub-agent task | agent=%s | prompt_len=%d",
            self.session.agent_id,
            len(prompt),
        )
        return await self.session.run(prompt)
    
    async def run_task_stream(self, task: TaskT) -> AsyncIterator[AgentRunResponseUpdate]:
        """Run a task and stream the response updates.
        
        This method:
        1. Calls on_task_start() for any pre-execution setup
        2. Renders the task to a prompt
        3. Streams the agent's response updates
        
        Args:
            task: The task to execute.
            
        Yields:
            Response updates from the agent.
        """
        self.on_task_start(task)
        prompt = self.render_prompt(task)
        LOGGER.debug(
            "Running sub-agent task (streaming) | agent=%s | prompt_len=%d",
            self.session.agent_id,
            len(prompt),
        )
        async for update in self.session.run_stream(prompt):
            yield update

    def as_tool(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
        response_handling: str | None = "parse_json",
        auto_load_artifacts: bool = False,
    ) -> AIFunction[Any, Any]:
        """Expose this sub-agent as an AIFunction tool.
        
        Args:
            name: Tool name override.
            description: Tool description override.
            parameters: Tool parameter schema.
            response_handling: How to process the sub-agent's response:
                - None/"none": No processing, return response.text as-is
                - "parse_json": Extract the last JSON object from response text (default)
                - "last_artifact": Get artifact ID from set_last_artifact_id() context
            auto_load_artifacts: If True and response_handling returns an artifact_id,
                automatically load the full artifact data and return as ToolResult.
        """
        tool_name = name or self.session.agent.name or self.session.agent_id
        tool_description = description or self.session.agent.description or ""

        input_model = _build_input_model(tool_name, parameters)

        async def subagent_wrapper(**kwargs: Any) -> Any:
            task = kwargs
            
            # Reset last_artifact_id before each task execution
            reset_last_artifact_id()
            
            # Set task context so tools can access it via get_current_task()
            token = set_task_context(task)
            try:
                response: AgentRunResponse = await self.run_task(task)
                
                # Apply response_handling
                result = _handle_response(self, response, task, response_handling)
                
                # Auto-load artifact data if enabled and we have an artifact_id
                if auto_load_artifacts:
                    return _auto_load_artifact(result, response, task)
                
                return result
            finally:
                reset_task_context(token)

        return AIFunction(
            name=tool_name,
            description=tool_description,
            func=subagent_wrapper,
            input_model=input_model,  # type: ignore[arg-type]
        )


def _build_input_model(name: str, parameters: dict[str, Any] | None) -> type:
    if not parameters:
        field_info = Field(..., description=f"Task for {name}")
        return create_model(f"{name}_input", **{"task": (str, field_info)})

    fields: dict[str, tuple[type, Any]] = {}
    for param_name, param in parameters.items():
        param_type = _map_param_type(param.get("type"))
        description = param.get("description") or ""
        required = param.get("required", True)
        default = param.get("default", None)
        if required and "default" not in param:
            field_info = Field(..., description=description)
            fields[param_name] = (param_type, field_info)
        else:
            field_info = Field(default if "default" in param else None, description=description)
            fields[param_name] = (param_type, field_info)
    return create_model(f"{name}_input", **fields)


def _map_param_type(param_type: str | None) -> type:
    if not param_type:
        return str
    normalized = param_type.lower()
    if normalized in ("string", "str"):
        return str
    if normalized in ("integer", "int"):
        return int
    if normalized in ("number", "float"):
        return float
    if normalized in ("boolean", "bool"):
        return bool
    if normalized in ("object", "dict"):
        return dict
    if normalized in ("array", "list"):
        return list
    return str


def _extract_last_json(text: str | None) -> dict[str, Any] | list[Any] | None:
    """Extract the last JSON object or array from text.
    
    Scans text from the end to find the last complete JSON structure.
    Handles both objects {} and arrays [].
    
    Args:
        text: The text to parse
        
    Returns:
        Parsed JSON (dict or list) or None if not found
    """
    import json
    
    if not text:
        return None
    
    # Find all potential JSON starting points from the end
    # Look for { or [ characters
    for i in range(len(text) - 1, -1, -1):
        char = text[i]
        if char in '{}[]':
            # Found a potential JSON end, now find its start
            if char in '}]':
                # This is an end bracket, find matching start
                end_pos = i
                open_char = '{' if char == '}' else '['
                close_char = char
                depth = 1
                start_pos = -1
                
                for j in range(i - 1, -1, -1):
                    if text[j] == close_char:
                        depth += 1
                    elif text[j] == open_char:
                        depth -= 1
                        if depth == 0:
                            start_pos = j
                            break
                
                if start_pos >= 0:
                    candidate = text[start_pos:end_pos + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        continue
    
    return None


def _handle_response(
    controller: SubAgentController,
    response: AgentRunResponse,
    task: Any,
    response_handling: str | None,
) -> Any:
    """Process sub-agent response based on response_handling mode.
    
    Args:
        controller: The sub-agent controller
        response: The agent's response
        task: The task that was executed
        response_handling: How to handle the response:
            - None/"none": Return response.text as-is
            - "parse_json": Extract last JSON from response text
            - "last_artifact": Get artifact ID from context
            
    Returns:
        Processed result based on response_handling mode
    """
    mode = (response_handling or "none").lower()
    
    if mode == "none":
        # No processing, return raw text
        return response.text or ""
    
    if mode == "parse_json":
        # Extract last JSON from response text
        json_result = _extract_last_json(response.text)
        if json_result is not None:
            LOGGER.debug("Extracted JSON from response text: %d chars", len(str(json_result)))
            return json_result
        # Fallback to raw text if no JSON found
        LOGGER.debug("No JSON found in response, returning raw text")
        return response.text or ""
    
    if mode == "last_artifact":
        # Get artifact ID from context var
        artifact_id = get_last_artifact_id()
        
        if artifact_id:
            LOGGER.debug("Got artifact ID from context: %s", artifact_id)
            return {"artifact_id": artifact_id}
        
        LOGGER.warning(
            "response_handling='last_artifact' but no artifact ID found. Task: %s",
            task,
        )
        return {"artifact_id": None, "error": "No artifact produced"}
    
    # Unknown mode, log warning and return raw text
    LOGGER.warning("Unknown response_handling mode: %s, returning raw text", mode)
    return response.text or ""


def _auto_load_artifact(
    result: Any,
    response: AgentRunResponse,
    task: Any,
    on_error: AutoLoadOnError | None = None,
) -> dict[str, Any]:
    """Auto-load artifact data if result contains an artifact_id.
    
    This is called after response_handling to load the full artifact content.
    
    Args:
        result: The result from response_handling
        response: The agent's response (for logging)
        task: The task that was executed (for logging)
        on_error: Error handling strategy, defaults to config or RETURN_ERROR
        
    Returns:
        ToolResult dict with artifact data, or error result on failure
        
    Raises:
        Exception: If on_error is RAISE and artifact loading fails
    """
    # Resolve on_error strategy from config if not specified
    if on_error is None:
        output_config = get_output_config()
        on_error_str = output_config.get("auto_load_on_error", "return_error")
        try:
            on_error = AutoLoadOnError(on_error_str)
        except ValueError:
            LOGGER.warning("Invalid auto_load_on_error value: %s, falling back to return_error", on_error_str)
            on_error = AutoLoadOnError.RETURN_ERROR
    
    # Try to extract artifact_id from result
    artifact_id: str | None = None
    
    if isinstance(result, dict):
        artifact_id = result.get("artifact_id")
    
    if not artifact_id:
        # Result doesn't have artifact_id, return as-is wrapped in ToolResult
        LOGGER.debug("No artifact_id in result, returning result as-is")
        return ToolResult(
            status="ok",
            result=result if isinstance(result, dict) else {"text": result},
        ).model_dump()
    
    # Load artifact data
    try:
        complete_data = load_artifact(artifact_id, format="json")
        LOGGER.debug(
            "Loaded artifact %s: %d keys",
            artifact_id,
            len(complete_data) if isinstance(complete_data, dict) else 0,
        )
        return ToolResult(
            status="ok",
            result=complete_data,
            artifact_id=artifact_id,
        ).model_dump()
        
    except Exception as exc:
        error_msg = f"Failed to load artifact {artifact_id}: {type(exc).__name__}: {exc}"
        LOGGER.error(error_msg, exc_info=True)
        
        if on_error == AutoLoadOnError.RAISE:
            raise
        
        # RETURN_ERROR: Return error ToolResult
        if on_error == AutoLoadOnError.RETURN_ERROR:
            return error_result(
                error_msg,
                result={"artifact_id": artifact_id},
            ).model_dump()

        # RETURN_EMPTY: Return empty payload with artifact_id
        return ToolResult(
            status="ok",
            result={},
            artifact_id=artifact_id,
        ).model_dump()


__all__ = [
    "SubAgentController",
    "AutoLoadOnError",
]
