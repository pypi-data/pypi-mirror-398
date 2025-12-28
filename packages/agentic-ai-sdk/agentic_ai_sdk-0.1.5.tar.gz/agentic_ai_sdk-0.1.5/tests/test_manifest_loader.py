from __future__ import annotations

import os

from agentic_ai.config import AgentManifestLoader
from agentic_ai.config.store import create_agent_config_store_from_manifest


def test_manifest_reference_resolution(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    agent_path = tmp_path / "agent.yaml"

    config_path.write_text(
        """
default_llm: default
openmetadata:
  sample_limit: 5
""",
        encoding="utf-8",
    )

    agent_path.write_text(
        """
version: "1.0"
agents:
  data_discovery:
    llm_profile_name: "${default_llm}"
    as_subagent:
      tool_parameters:
        sample_limit:
          type: integer
          default: "${openmetadata.sample_limit}"
""",
        encoding="utf-8",
    )

    loader = AgentManifestLoader(config_path, agent_path)
    manifest = loader.load_resolved_manifest()
    assert manifest is not None
    assert manifest.agents["data_discovery"]["llm_profile_name"] == "default"
    assert manifest.agents["data_discovery"]["as_subagent"]["tool_parameters"]["sample_limit"]["default"] == 5


def test_manifest_env_override(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    agent_path = tmp_path / "agent.yaml"

    config_path.write_text(
        """
default_llm: default
""",
        encoding="utf-8",
    )

    agent_path.write_text(
        """
version: "1.0"
agents:
  agentic_analyst:
    llm_profile_name: "${CUSTOM_LLM:default}"
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("CUSTOM_LLM", "reasoning")
    loader = AgentManifestLoader(config_path, agent_path)
    manifest = loader.load_resolved_manifest()
    assert manifest is not None
    assert manifest.agents["agentic_analyst"]["llm_profile_name"] == "reasoning"


def test_manifest_to_agent_store(tmp_path):
    config_path = tmp_path / "config.yaml"
    agent_path = tmp_path / "agent.yaml"

    config_path.write_text("llm_profiles: []\n", encoding="utf-8")
    agent_path.write_text(
        """
version: "1.0"
agents:
  master:
    llm_profile_name: "default"
  worker:
    llm_profile_name: "default"
    as_subagent:
      tool_name: "worker_tool"
""",
        encoding="utf-8",
    )

    loader = AgentManifestLoader(config_path, agent_path)
    manifest = loader.load_resolved_manifest()
    store = create_agent_config_store_from_manifest(manifest)
    assert store.has_config("master")
    assert store.has_config("worker")
    assert not store.get_config("master").can_be_subagent
    assert store.get_config("worker").can_be_subagent
