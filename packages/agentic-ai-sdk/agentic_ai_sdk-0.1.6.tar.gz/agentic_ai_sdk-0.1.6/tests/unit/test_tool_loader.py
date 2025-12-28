"""Tests for plugin-style tool loading from tools.yaml."""
from __future__ import annotations

import pytest
from agent_framework import ai_function

from agentic_ai.tools.manifest import (
    ToolConfig,
    ToolParameterOverride,
    ToolsManifest,
)
from agentic_ai.tools.loader import (
    load_tool_from_function,
    resolve_tool_ref,
)


# Test fixtures
@ai_function(name="test_tool", description="Original description")
def sample_tool(query: str, limit: int = 10) -> dict:
    """A sample tool for testing."""
    return {"query": query, "limit": limit}


class TestToolsManifest:
    """Tests for ToolsManifest parsing."""

    def test_empty_manifest(self):
        manifest = ToolsManifest()
        assert manifest.version == "1.0"
        assert manifest.tools == {}

    def test_manifest_with_tools(self):
        manifest = ToolsManifest(
            tools={
                "my_tool": ToolConfig(
                    function="mymodule:my_function",
                    description="Custom description",
                    config_section="openmetadata",
                )
            }
        )
        assert "my_tool" in manifest.tools
        assert manifest.tools["my_tool"].function == "mymodule:my_function"
        assert manifest.tools["my_tool"].description == "Custom description"
        assert manifest.tools["my_tool"].config_section == "openmetadata"


class TestLoadToolFromFunction:
    """Tests for loading individual tools."""

    def test_load_tool_without_overrides(self):
        from agent_framework import AIFunction
        
        # Use the module path to our test function
        func = load_tool_from_function(
            f"{__name__}:sample_tool",
        )
        assert callable(func)
        # Should be an AIFunction object
        assert isinstance(func, AIFunction)
        assert func.name == "test_tool"
        assert func.description == "Original description"

    def test_load_tool_with_description_override(self):
        from agent_framework import AIFunction
        
        # AIFunction should be recreated with new description
        func = load_tool_from_function(
            f"{__name__}:sample_tool",
            description_override="New custom description",
        )
        assert callable(func)
        assert isinstance(func, AIFunction)
        # Description should be overridden
        assert func.description == "New custom description"
        # Name should remain the same
        assert func.name == "test_tool"

    def test_load_tool_with_parameter_override(self):
        from agent_framework import AIFunction
        
        func = load_tool_from_function(
            f"{__name__}:sample_tool",
            parameter_overrides={
                "query": ToolParameterOverride(
                    description="Custom query description",
                ),
            },
        )
        assert callable(func)
        assert isinstance(func, AIFunction)
        
        # Check the schema has the overridden description
        schema = func.to_json_schema_spec()
        params = schema["function"]["parameters"]
        assert params["properties"]["query"]["description"] == "Custom query description"

    def test_load_tool_with_required_override(self):
        from agent_framework import AIFunction
        
        # Make 'limit' required (it's optional by default)
        func = load_tool_from_function(
            f"{__name__}:sample_tool",
            parameter_overrides={
                "limit": ToolParameterOverride(
                    required=True,
                ),
            },
        )
        assert callable(func)
        
        # Check the schema has 'limit' in required
        schema = func.to_json_schema_spec()
        params = schema["function"]["parameters"]
        assert "limit" in params.get("required", [])

    @pytest.mark.anyio
    async def test_load_tool_injects_tool_config(self):
        from agent_framework import ai_function
        from agentic_ai.runtime.tool_runtime import get_tool_config

        @ai_function(name="config_echo", description="Return tool config")
        def config_echo() -> dict:
            return get_tool_config()

        # Expose to module namespace for tool loader resolution
        globals()["config_echo"] = config_echo

        func = load_tool_from_function(
            f"{__name__}:config_echo",
            config_section="openmetadata",
            tool_config={"foo": "bar"},
        )
        result = await func.invoke()
        assert result["config_section"] == "openmetadata"
        assert result["config"] == {"foo": "bar"}

        # Cleanup to avoid leaking into other tests
        globals().pop("config_echo", None)


class TestResolveToolRef:
    """Tests for resolving tool references."""

    def test_resolve_individual_tool(self):
        manifest = ToolsManifest(
            tools={
                "my_tool": ToolConfig(
                    function=f"{__name__}:sample_tool",
                )
            }
        )
        tools = resolve_tool_ref(
            "my_tool",
            manifest=manifest,
        )
        assert len(tools) == 1
        assert callable(tools[0])

    def test_resolve_unknown_ref_raises(self):
        manifest = ToolsManifest()
        with pytest.raises(ValueError, match="not found"):
            resolve_tool_ref(
                "unknown_tool",
                manifest=manifest,
            )


class TestToolParameterOverrides:
    """Tests for parameter override functionality."""

    def test_parameter_override_model(self):
        override = ToolParameterOverride(
            description="Custom parameter description",
            required=True,
        )
        assert override.description == "Custom parameter description"
        assert override.required is True

    def test_tool_config_with_parameter_overrides(self):
        config = ToolConfig(
            function="mymodule:my_func",
            parameters={
                "query": ToolParameterOverride(
                    description="The search query",
                    required=True,
                ),
            },
        )
        assert "query" in config.parameters
        assert config.parameters["query"].description == "The search query"
