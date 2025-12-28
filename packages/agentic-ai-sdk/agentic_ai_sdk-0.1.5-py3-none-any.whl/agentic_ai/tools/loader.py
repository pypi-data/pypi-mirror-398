"""Plugin-style dynamic tool loader from tools.yaml manifest.

This module provides functions to:
1. Load tools dynamically from function paths
2. Apply description and parameter overrides from tools.yaml
"""
from __future__ import annotations

import copy
import functools
import importlib
import inspect
import logging
from typing import Any, Callable, get_type_hints

from agent_framework import AIFunction

from .manifest import (
    ToolConfig,
    ToolParameterOverride,
    ToolsManifest,
)

LOGGER = logging.getLogger("agentic_ai.tool_loader")


def load_tool_from_function(
    function_path: str,
    *,
    description_override: str | None = None,
    parameter_overrides: dict[str, ToolParameterOverride] | None = None,
    config_section: str | None = None,
    tool_config: dict[str, Any] | None = None,
) -> Callable[..., Any]:
    """Load a single tool from a function path and apply overrides.

    Args:
        function_path: Python path to the function (module:function)
        description_override: Override the @ai_function description
        parameter_overrides: Override specific parameter descriptions/requirements

    Returns:
        The loaded tool function, potentially wrapped with overrides applied.
    """
    func = _resolve_function(function_path)

    # Apply overrides by wrapping the function (if needed)
    if description_override or parameter_overrides:
        func = _apply_overrides(func, description_override, parameter_overrides)

    # Inject tool config context if needed
    if config_section or (tool_config and tool_config != {}):
        func = _wrap_tool_with_config(func, config_section=config_section, tool_config=tool_config)

    return func


def resolve_tool_ref(
    ref: str,
    *,
    manifest: ToolsManifest,
) -> list[Callable[..., Any]]:
    """Resolve a tool reference to tool functions.

    Args:
        ref: Tool name as defined in tools.yaml
        manifest: The tools manifest

    Returns:
        List containing the resolved tool function.

    Raises:
        ValueError: If the tool reference is not found in tools.yaml
    """
    # Check if it's an individual tool
    if ref in manifest.tools:
        tool_config = manifest.tools[ref]
        tool = load_tool_from_function(
            tool_config.function,
            description_override=tool_config.description,
            parameter_overrides=tool_config.parameters or None,
            config_section=tool_config.config_section,
            tool_config=tool_config.config or None,
        )
        return [tool]

    raise ValueError(
        f"Tool reference '{ref}' not found in tools.yaml. "
        "Define it in manifest/tools.yaml."
    )


def _wrap_tool_with_config(
    func: Callable[..., Any],
    *,
    config_section: str | None,
    tool_config: dict[str, Any] | None,
) -> Callable[..., Any]:
    """Wrap a tool to inject tool config via ContextVar.

    This ensures tools can access declarative config via deep_agent.tool_runtime.get_tool_config()
    while still supporting runtime config sections from RuntimeContext.
    """
    from agent_framework import AIFunction

    def _build_payload() -> dict[str, Any]:
        payload: dict[str, Any] = {
            "config": tool_config or {},
            "config_section": config_section,
            "section": None,
        }
        if config_section:
            from ..runtime.context import try_get_runtime_context
            ctx = try_get_runtime_context()
            if ctx is not None:
                payload["section"] = ctx.get_config_section(config_section)
        return payload

    def _wrap_callable(callable_obj: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(callable_obj)
        def wrapper(*args, **kwargs):
            from ..runtime.tool_runtime import set_tool_config, reset_tool_config
            from ..runtime.contexts import try_ctx

            payload = _build_payload()
            token = set_tool_config(payload)
            ctx = try_ctx()
            prev_tool_config = None
            if ctx is not None:
                prev_tool_config = ctx.tool_config
                ctx.tool_config = payload
            try:
                result = callable_obj(*args, **kwargs)
            except Exception:
                if ctx is not None:
                    ctx.tool_config = prev_tool_config or {}
                reset_tool_config(token)
                raise

            if inspect.isawaitable(result):
                async def _await_result():
                    try:
                        return await result
                    finally:
                        if ctx is not None:
                            ctx.tool_config = prev_tool_config or {}
                        reset_tool_config(token)

                return _await_result()

            if ctx is not None:
                ctx.tool_config = prev_tool_config or {}
            reset_tool_config(token)
            return result

        return wrapper

    if isinstance(func, AIFunction):
        wrapped_func = _wrap_callable(func.func)
        return AIFunction(
            name=func.name,
            description=func.description,
            approval_mode=getattr(func, "approval_mode", None),
            additional_properties=getattr(func, "additional_properties", None),
            func=wrapped_func,
            input_model=getattr(func, "input_model", None),
        )

    return _wrap_callable(func)


def _resolve_function(path: str) -> Callable[..., Any]:
    """Resolve a Python path to a callable.

    Supports:
    - module:function
    - module:Class.method (for toolset methods)
    """
    if ":" in path:
        module_path, attr_path = path.split(":", 1)
    else:
        module_path, attr_path = path.rsplit(".", 1)

    module = importlib.import_module(module_path)

    # Handle nested attribute paths (e.g., Class.method)
    target = module
    for attr in attr_path.split("."):
        target = getattr(target, attr)

    if not callable(target):
        raise ValueError(f"'{path}' is not callable")

    return target


def _apply_overrides(
    func: Callable[..., Any],
    description_override: str | None,
    parameter_overrides: dict[str, ToolParameterOverride] | None,
) -> Callable[..., Any]:
    """Apply description and parameter overrides to an AI function.

    This creates a new AIFunction with the overridden metadata while
    preserving the original function's behavior.
    """
    from agent_framework import AIFunction
    
    # Check if this is an AIFunction object (from @ai_function decorator)
    if isinstance(func, AIFunction):
        return _create_overridden_ai_function_from_instance(
            func, description_override, parameter_overrides
        )

    # Not an ai_function at all - just a plain function
    func_name = getattr(func, "__name__", repr(func))
    LOGGER.warning(
        "Function %s is not decorated with @ai_function, overrides will be limited",
        func_name,
    )
    # If not an ai_function, we can only modify the docstring
    if description_override:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__doc__ = description_override
        return wrapper
    return func


def _create_overridden_ai_function_from_instance(
    original: "AIFunction",
    description_override: str | None,
    parameter_overrides: dict[str, ToolParameterOverride] | None,
) -> "AIFunction":
    """Create a new AIFunction with overridden description and parameters.
    
    This creates a new AIFunction instance that wraps the original,
    with modified description and/or parameter schema.
    """
    from agent_framework import AIFunction
    from pydantic import create_model, Field
    from typing import get_type_hints, Annotated, Any as TypingAny
    
    original_name = original.name
    original_description = original.description or ""
    
    # Use override or original
    new_description = description_override if description_override else original_description
    
    # Get the original schema to extract parameter info
    original_schema = original.to_json_schema_spec()
    original_params = original_schema.get("function", {}).get("parameters", {})
    original_properties = original_params.get("properties", {})
    original_required = set(original_params.get("required", []))
    
    # Build new input model if we have parameter overrides
    new_input_model = None
    if parameter_overrides:
        new_input_model = _build_overridden_input_model(
            original_name,
            original_properties,
            original_required,
            parameter_overrides,
        )
    
    # Create new AIFunction with overridden values
    # We wrap the original's invoke method
    async def wrapped_invoke(*args, **kwargs):
        return await original.invoke(*args, **kwargs)
    
    # For sync invocation support
    def sync_wrapped(*args, **kwargs):
        result = original.invoke(*args, **kwargs)
        return result
    
    # Determine if original is async
    # AIFunction.invoke is typically async, so we use that
    new_ai_function = AIFunction(
        name=original_name,
        description=new_description,
        func=sync_wrapped,  # AIFunction will handle async wrapping
        input_model=new_input_model,
    )
    
    LOGGER.debug(
        "Created overridden AIFunction '%s' with description='%s', parameter_overrides=%s",
        original_name,
        new_description[:50] + "..." if len(new_description) > 50 else new_description,
        list(parameter_overrides.keys()) if parameter_overrides else None,
    )
    
    return new_ai_function


def _build_overridden_input_model(
    tool_name: str,
    original_properties: dict[str, Any],
    original_required: set[str],
    parameter_overrides: dict[str, ToolParameterOverride],
) -> type:
    """Build a Pydantic model with parameter overrides applied.
    
    Args:
        tool_name: Name of the tool (used for model naming)
        original_properties: Original parameter properties from schema
        original_required: Set of originally required parameter names
        parameter_overrides: Overrides to apply
        
    Returns:
        A new Pydantic model class with overrides applied.
    """
    from pydantic import create_model, Field
    from typing import Any as TypingAny, Optional
    
    # Map JSON schema types to Python types
    type_map = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    
    field_definitions = {}
    
    for param_name, prop in original_properties.items():
        # Get original values
        param_type_str = prop.get("type", "string")
        param_type = type_map.get(param_type_str, TypingAny)
        param_description = prop.get("description", "")
        param_default = prop.get("default", ...)  # ... means required
        is_required = param_name in original_required
        
        # Apply overrides if present
        override = parameter_overrides.get(param_name)
        if override:
            if override.description is not None:
                param_description = override.description
            if override.required is not None:
                is_required = override.required
                # If changing from required to optional, set default to None
                if not is_required and param_default is ...:
                    param_default = None
                # If changing from optional to required, set default to ...
                elif is_required and param_default is not ...:
                    param_default = ...
        
        # Build Field
        if is_required:
            field_definitions[param_name] = (
                param_type,
                Field(description=param_description),
            )
        else:
            # Optional field with default
            if param_default is ... or param_default is None:
                field_definitions[param_name] = (
                    Optional[param_type],
                    Field(default=None, description=param_description),
                )
            else:
                field_definitions[param_name] = (
                    param_type,
                    Field(default=param_default, description=param_description),
                )
    
    # Create the model
    model_name = f"{tool_name}_input_override"
    return create_model(model_name, **field_definitions)


__all__ = [
    "load_tool_from_function",
    "resolve_tool_ref",
]
