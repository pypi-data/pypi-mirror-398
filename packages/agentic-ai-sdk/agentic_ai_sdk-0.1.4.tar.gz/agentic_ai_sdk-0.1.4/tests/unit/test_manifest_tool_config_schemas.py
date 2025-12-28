"""Tests for declarative tool config schema registration via tools.yaml.

Tests cover three modes of schema resolution:
1. Explicit registration via config_schemas in tools.yaml
2. Convention-based auto-inference from toolset modules
3. Schema-less fallback (returns raw dict)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agentic_ai.config import ConfigError
from agentic_ai.runtime.bootstrap import RuntimeBootstrap


def _write_test_module(tmp_path: Path, module_name: str = "dummy_tools") -> str:
    """Write a test module with a tool function and config schema."""
    module_path = tmp_path / f"{module_name}.py"
    module_path.write_text(
        """
from __future__ import annotations

from pydantic import BaseModel

class ExampleToolConfig(BaseModel):
    value: int

def dummy_tool() -> str:
    return "ok"
""",
        encoding="utf-8",
    )
    return module_name


def _write_test_toolset(tmp_path: Path, package_name: str = "test_toolset") -> str:
    """Write a toolset package with tools.py and config.py for convention-based inference."""
    pkg_dir = tmp_path / package_name
    pkg_dir.mkdir()
    
    # __init__.py
    (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
    
    # config.py with ExampleConfig (uses CONFIG_SECTION for explicit section name)
    (pkg_dir / "config.py").write_text(
        """
from __future__ import annotations
from typing import ClassVar
from pydantic import BaseModel

class ExampleConfig(BaseModel):
    CONFIG_SECTION: ClassVar[str] = "example"
    value: int

class AnotherSectionConfig(BaseModel):
    CONFIG_SECTION: ClassVar[str] = "another_section"
    name: str
""",
        encoding="utf-8",
    )
    
    # tools.py
    (pkg_dir / "tools.py").write_text(
        """
def example_tool() -> str:
    return "ok"
""",
        encoding="utf-8",
    )
    
    return package_name


def _write_manifests(tmp_path: Path, tools_yaml: str, env_yaml: str) -> tuple[Path, Path]:
    manifest_dir = tmp_path / "manifest"
    manifest_dir.mkdir()

    (manifest_dir / "agents.yaml").write_text(
        """
version: "1.0"
agents:
  agentic_analyst:
    llm_profile_name: "default"
""",
        encoding="utf-8",
    )
    (manifest_dir / "tools.yaml").write_text(tools_yaml, encoding="utf-8")
    config_path = tmp_path / "env.yaml"
    config_path.write_text(env_yaml, encoding="utf-8")
    return config_path, manifest_dir


def _reset_registry():
    """Reset the global tool config registry between tests."""
    from agentic_ai.config.registry import _REGISTRY
    _REGISTRY._schemas.clear()


@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure clean registry state for each test."""
    _reset_registry()
    yield
    _reset_registry()


def test_manifest_config_schemas_registers_and_loads(tmp_path, monkeypatch):
    """Test explicit config_schemas registration works."""
    module_name = _write_test_module(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    tools_yaml = f"""
version: "1.0"
config_schemas:
  example: "{module_name}:ExampleToolConfig"

tools:
  dummy_tool:
    function: "{module_name}:dummy_tool"
    config_section: example
"""
    env_yaml = """
llm_profiles:
  - name: default
    provider: openai
    api_key: test
    model: gpt-4o-mini
example:
  value: 42
"""
    config_path, manifest_dir = _write_manifests(tmp_path, tools_yaml, env_yaml)

    from agentic_ai.config import BaseAppConfig
    bootstrap = RuntimeBootstrap(config_class=BaseAppConfig, config_path=config_path, manifest_dir=manifest_dir)
    ctx = bootstrap.create_context()
    section = ctx.get_config_section("example")
    assert section is not None
    assert section.value == 42


def test_schema_less_mode_returns_raw_dict(tmp_path, monkeypatch):
    """Test schema-less mode returns raw dict when no schema found."""
    module_name = _write_test_module(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    # No config_schemas, no convention-matching schema
    tools_yaml = f"""
version: "1.0"

tools:
  dummy_tool:
    function: "{module_name}:dummy_tool"
    config_section: example
"""
    env_yaml = """
llm_profiles:
  - name: default
    provider: openai
    api_key: test
    model: gpt-4o-mini
example:
  value: 123
  extra_field: "allowed in schema-less"
"""
    config_path, manifest_dir = _write_manifests(tmp_path, tools_yaml, env_yaml)

    from agentic_ai.config import BaseAppConfig
    bootstrap = RuntimeBootstrap(config_class=BaseAppConfig, config_path=config_path, manifest_dir=manifest_dir)
    ctx = bootstrap.create_context()
    section = ctx.get_config_section("example")
    # Schema-less mode returns raw dict
    assert section is not None
    assert isinstance(section, dict)
    assert section["value"] == 123
    assert section["extra_field"] == "allowed in schema-less"


def test_convention_based_auto_inference(tmp_path, monkeypatch):
    """Test convention-based schema auto-inference from toolset config.py."""
    package_name = _write_test_toolset(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    # No explicit config_schemas - should auto-infer ExampleConfig
    tools_yaml = f"""
version: "1.0"

tools:
  example_tool:
    function: "{package_name}.tools:example_tool"
    config_section: example
"""
    env_yaml = """
llm_profiles:
  - name: default
    provider: openai
    api_key: test
    model: gpt-4o-mini
example:
  value: 99
"""
    config_path, manifest_dir = _write_manifests(tmp_path, tools_yaml, env_yaml)

    from agentic_ai.config import BaseAppConfig
    bootstrap = RuntimeBootstrap(config_class=BaseAppConfig, config_path=config_path, manifest_dir=manifest_dir)
    ctx = bootstrap.create_context()
    section = ctx.get_config_section("example")
    # Should be a Pydantic model (auto-inferred)
    assert section is not None
    assert hasattr(section, "value")
    assert section.value == 99


def test_convention_inference_with_underscore_name(tmp_path, monkeypatch):
    """Test convention handles snake_case section names."""
    package_name = _write_test_toolset(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    # "another_section" should map to "AnotherSectionConfig"
    tools_yaml = f"""
version: "1.0"

tools:
  example_tool:
    function: "{package_name}.tools:example_tool"
    config_section: another_section
"""
    env_yaml = """
llm_profiles:
  - name: default
    provider: openai
    api_key: test
    model: gpt-4o-mini
another_section:
  name: "test-name"
"""
    config_path, manifest_dir = _write_manifests(tmp_path, tools_yaml, env_yaml)

    from agentic_ai.config import BaseAppConfig
    bootstrap = RuntimeBootstrap(config_class=BaseAppConfig, config_path=config_path, manifest_dir=manifest_dir)
    ctx = bootstrap.create_context()
    section = ctx.get_config_section("another_section")
    assert section is not None
    assert hasattr(section, "name")
    assert section.name == "test-name"


def test_manifest_invalid_schema_path_raises(tmp_path, monkeypatch):
    module_name = _write_test_module(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    tools_yaml = f"""
version: "1.0"
config_schemas:
  example: "{module_name}:MissingSchema"

tools:
  dummy_tool:
    function: "{module_name}:dummy_tool"
    config_section: example
"""
    env_yaml = """
llm_profiles:
  - name: default
    provider: openai
    api_key: test
    model: gpt-4o-mini
example:
  value: 1
"""
    config_path, manifest_dir = _write_manifests(tmp_path, tools_yaml, env_yaml)

    from agentic_ai.config import BaseAppConfig
    bootstrap = RuntimeBootstrap(config_class=BaseAppConfig, config_path=config_path, manifest_dir=manifest_dir)
    with pytest.raises(ConfigError, match="Schema"):
        bootstrap.create_context()
