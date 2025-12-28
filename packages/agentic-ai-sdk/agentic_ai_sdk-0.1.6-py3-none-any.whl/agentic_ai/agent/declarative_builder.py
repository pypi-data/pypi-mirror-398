"""Declarative agent builder using manifest/agents.yaml manifest."""
from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from .core import DeepAgentSession, build_agent_session
from ..config.manifest import AgentManifest
from .sub_agent import SubAgentController
from ..tools.provider import resolve_tool_refs
from ..tools.manifest import ToolsManifest

LOGGER = logging.getLogger("agentic_ai.declarative_builder")


@dataclass(slots=True)
class DeclarativeBuildResult:
    session: DeepAgentSession
    subagent_controllers: dict[str, SubAgentController]
    cleanup_functions: list[Callable[[], None]]


class DeclarativeAgentBuilder:
    """Build agents from declarative manifest."""

    def __init__(
        self,
        ctx: Any,
        workspace: Any,
        manifest: AgentManifest,
        tools_manifest: ToolsManifest | None = None,
    ) -> None:
        self.ctx = ctx
        self.workspace = workspace
        self.manifest = manifest
        self.tools_manifest = tools_manifest
        self._controllers: dict[str, SubAgentController] = {}
        self._cleanup: list[Callable[[], None]] = []

    def build_master_agent(self, agent_id: str) -> DeclarativeBuildResult:
        agent_config = self.ctx.get_agent_config(agent_id)

        direct_tools = resolve_tool_refs(
            agent_config.tools,
            manifest=self.manifest,
            mcp_manifest=getattr(self.ctx, "mcp_manifest", None),
            tools_manifest=self.tools_manifest,
        )
        subagent_tools = self._build_subagent_tools(agent_config.subagents or [])

        session = build_agent_session(
            ctx=self.ctx,
            agent_id=agent_id,
            workspace=self.workspace,
            tools=direct_tools + subagent_tools,
        )

        return DeclarativeBuildResult(
            session=session,
            subagent_controllers=dict(self._controllers),
            cleanup_functions=list(self._cleanup),
        )

    def _build_subagent_tools(self, subagent_ids: Iterable[str]) -> list[Callable]:
        tools: list[Callable] = []
        for subagent_id in subagent_ids:
            config = self.ctx.get_agent_config(subagent_id)
            sub_cfg = config.as_subagent
            
            if sub_cfg is None:
                raise ValueError(
                    f"Agent '{subagent_id}' cannot be used as subagent: "
                    f"missing 'as_subagent' configuration"
                )
            
            controller = self._build_subagent_controller(subagent_id, config, sub_cfg)
            # Get response_handling as string value (handle both enum and string)
            response_handling = sub_cfg.response_handling
            if hasattr(response_handling, "value"):
                response_handling = response_handling.value
            tool = controller.as_tool(
                name=sub_cfg.tool_name or subagent_id,
                description=sub_cfg.tool_description or config.description,
                parameters=sub_cfg.tool_parameters,
                response_handling=response_handling,
                auto_load_artifacts=sub_cfg.auto_load_artifacts,
            )
            tools.append(tool)
        return tools

    def _build_subagent_controller(
        self, subagent_id: str, config: Any, sub_cfg: Any
    ) -> SubAgentController:
        if subagent_id in self._controllers:
            return self._controllers[subagent_id]

        if sub_cfg.builder:
            controller = _build_custom_controller(sub_cfg.builder, self.ctx, self.workspace)
        else:
            tools = resolve_tool_refs(
                config.tools,
                manifest=self.manifest,
                mcp_manifest=getattr(self.ctx, "mcp_manifest", None),
                tools_manifest=self.tools_manifest,
            )
            session = build_agent_session(
                ctx=self.ctx,
                agent_id=subagent_id,
                workspace=self.workspace,
                tools=tools,
            )
            controller = _GenericSubAgentController(
                session=session,
                parameters=sub_cfg.tool_parameters,
                user_message_template=sub_cfg.user_message_template,
            )

        self._controllers[subagent_id] = controller
        self._cleanup.append(controller.close)
        return controller


class _GenericSubAgentController(SubAgentController[dict[str, Any]]):
    """Generic controller for declarative sub-agents.
    
    Supports optional user_message_template for custom prompt rendering.
    If user_message_template is provided, it uses Python's str.format() with task fields.
    Otherwise, falls back to key: value format.
    """

    def __init__(
        self,
        session: DeepAgentSession,
        parameters: dict[str, Any] | None,
        user_message_template: str | None = None,
    ) -> None:
        super().__init__(session=session)
        self._parameter_names = list(parameters.keys()) if parameters else []
        self._user_message_template = user_message_template

    def _task_to_dict(self, task: Any) -> dict[str, Any]:
        """Convert task to dictionary, handling both Pydantic models and dicts."""
        if task is None:
            return {}
        if isinstance(task, dict):
            return task
        # Handle Pydantic models
        if hasattr(task, "model_dump"):
            return task.model_dump()
        # Handle dataclasses or objects with __dict__
        if hasattr(task, "__dict__"):
            return vars(task)
        # Fallback: try to convert to dict
        try:
            return dict(task)
        except (TypeError, ValueError):
            return {}

    def render_prompt(self, task: Any) -> str:
        task_dict = self._task_to_dict(task)
        if not task_dict:
            return ""
        
        # Use template if provided
        if self._user_message_template:
            try:
                return self._user_message_template.format(**task_dict)
            except KeyError as e:
                LOGGER.warning(
                    "user_message_template missing key %s, falling back to default | agent=%s",
                    e,
                    self.session.agent_id,
                )
        
        # Default: key: value format
        parts = []
        for name in self._parameter_names or task_dict.keys():
            value = task_dict.get(name)
            if value is not None and value != "":
                parts.append(f"{name}: {value}")
        return "\n".join(parts)


def _build_custom_controller(path: str, ctx: Any, workspace: Any) -> SubAgentController:
    if ":" in path:
        module_path, func_name = path.split(":", 1)
    else:
        module_path, func_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    builder = getattr(module, func_name)
    if not callable(builder):
        raise ValueError(f"Sub-agent builder '{path}' is not callable")
    controller = builder(ctx, workspace)
    if not isinstance(controller, SubAgentController):
        raise ValueError(f"Builder '{path}' did not return a SubAgentController")
    return controller


__all__ = ["DeclarativeAgentBuilder", "DeclarativeBuildResult"]
