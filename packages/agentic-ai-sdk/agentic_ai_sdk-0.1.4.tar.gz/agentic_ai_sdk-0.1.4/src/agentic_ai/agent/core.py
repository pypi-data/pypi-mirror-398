from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
from dataclasses import dataclass
from collections.abc import Sequence
from typing import Any, Awaitable, Callable, Iterable

from agent_framework import (
    AgentThread,
    AgentRunResponse,
    AgentRunResponseUpdate,
    BaseChatClient,
    ChatAgent,
    ChatMessage,
    ContextProvider,
    FunctionMiddleware,
    ToolProtocol,
)
from agent_framework import AIFunction
from pydantic import Field, create_model

LOGGER = logging.getLogger("agentic_ai.agent")


ChatInput = str | ChatMessage | Sequence[str | ChatMessage]


def _sanitize_name(name: str | None) -> str | None:
    r"""Sanitize agent name to comply with OpenAI API naming pattern.
    
    OpenAI API requires names to match ^[^\s<|\\/>]+$ pattern.
    This function replaces invalid characters with underscores.
    """
    if name is None:
        return None
    import re
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[\s<|\\/>]+', '_', name)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized if sanitized else None


def _preview(value: Any, limit: int = 300) -> str:
    """Create a preview of a value for logging."""
    if value is None:
        return "None"
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        text = str(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _message_text(value: str | ChatMessage | Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, ChatMessage):
        if value.text:
            return value.text
        if value.contents:
            for content in value.contents:
                text = getattr(content, "text", None)
                if text:
                    return text
                name = getattr(content, "name", None)
                if name:
                    return f"[tool_call:{name}]"
        role = getattr(value, "role", None)
        return f"[{role}]" if role else "[message]"
    return str(value)


def _summarize_chat_input(messages: ChatInput) -> tuple[int, str]:
    if isinstance(messages, str):
        return len(messages), messages
    if isinstance(messages, ChatMessage):
        snippet = _message_text(messages)
        role = getattr(messages, "role", None)
        prefix = f"{role}: " if role else ""
        return len(snippet), prefix + snippet
    if isinstance(messages, Sequence):
        tail = list(messages)[-3:]
        parts: list[str] = []
        total = 0
        for item in tail:
            snippet = _message_text(item)
            total += len(snippet)
            role = getattr(item, "role", None)
            if role:
                parts.append(f"{role}: {snippet}")
            else:
                parts.append(snippet)
        preview_text = " | ".join(parts) if parts else "<empty>"
        return total, preview_text
    text = _message_text(messages)
    return len(text), text

from ..artifacts.core import ArtifactStore
from ..runtime.context_compaction import (
    CompactionConfig,
    ContextCompactor,
    HeuristicSummarizer,
    CompactionSummarizer,
)
from ..middleware import ToolResultPersistenceMiddleware
from ..planning.core import PlanStore, build_update_plan_tool
from ..workspace.core import (
    WorkspaceContextProvider,
    WorkspaceHandle,
    inject_workspace_kwargs,
)
from ..workspace.middleware import WorkspaceParameterInjectionMiddleware
from ..runtime.tool_runtime import cleanup_session, set_session_context, reset_session_context


@dataclass(slots=True)
class DeepAgentSession:
    agent: ChatAgent
    agent_id: str
    workspace: WorkspaceHandle
    plan_store: PlanStore | None = None
    context_compactor: ContextCompactor | None = None

    @property
    def session_id(self) -> str:
        """Get session ID (uses workspace_id for resource scoping)."""
        return self.workspace.workspace_id

    def close(self) -> None:
        """Close the session and cleanup all associated resources.
        
        This triggers cleanup of all tool resources registered with ToolRuntimeRegistry
        that are scoped to this session's workspace_id.
        """
        cleanup_session(self.session_id)
        LOGGER.debug("Session closed | agent=%s | session=%s", self.agent_id, self.session_id)

    def __enter__(self) -> "DeepAgentSession":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def _base_kwargs(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        inject_workspace_kwargs(
            payload,
            workspace=self.workspace,
            agent_id=self.agent_id,
            plan_path=str(self.plan_store.path) if self.plan_store else None,
        )
        return payload

    def ensure_thread(self, thread: AgentThread | None = None) -> AgentThread:
        return thread or self.agent.get_new_thread()

    async def run(
        self,
        messages: ChatInput | None = None,
        *,
        thread: AgentThread | None = None,
        **kwargs: Any,
    ):
        # Start timing for error logging
        start_time = time.time()
        if messages is None:
            raise ValueError("messages must be provided for DeepAgentSession.run")

        # Set session context so tools can access session_id via get_current_session_id()
        token = set_session_context(self.session_id)
        
        # MAF observability automatically traces invoke_agent span with agent_id, instructions, duration, etc.
        # We only log errors here since MAF doesn't capture full exception stack traces
        try:
            runtime_kwargs = self._merge_kwargs(kwargs)
            thread = self.ensure_thread(thread)
            response = await self.agent.run(messages, thread=thread, **runtime_kwargs)
            await self._maybe_compact(thread=thread, response=response)
            return response
        except Exception as exc:
            # ERROR level: Agent RUN ERROR with full traceback
            # This supplements MAF observability which only records error events
            duration = time.time() - start_time
            error_type = type(exc).__name__
            error_msg = str(exc)
            LOGGER.error(
                "💥 Agent RUN ERROR | agent=%s | duration=%.3fs | error=%s: %s",
                self.agent_id,
                duration,
                error_type,
                error_msg,
                exc_info=True,  # Include full exception traceback
            )
            
            # Re-raise the exception
            raise
        finally:
            reset_session_context(token)

    async def run_stream(
        self,
        messages: ChatInput | None = None,
        *,
        thread: AgentThread | None = None,
        **kwargs: Any,
    ):
        if messages is None:
            raise ValueError("messages must be provided for DeepAgentSession.run_stream")
        
        # Set session context so tools can access session_id via get_current_session_id()
        token = set_session_context(self.session_id)
        
        # MAF observability automatically traces invoke_agent span
        # We only keep streaming-specific details that MAF doesn't capture
        runtime_kwargs = self._merge_kwargs(kwargs)
        thread = self.ensure_thread(thread)
        updates: list[AgentRunResponseUpdate] = []
        cancelled = False

        async def _stream():
            nonlocal cancelled
            try:
                async for update in self.agent.run_stream(messages, thread=thread, **runtime_kwargs):
                    updates.append(update)
                    yield update
            except asyncio.CancelledError:
                # Client disconnected - mark as cancelled and allow finally to run
                cancelled = True
                LOGGER.info("Stream cancelled by client | agent=%s", self.agent_id)
                raise
            finally:
                # Always attempt compaction, even on cancellation
                try:
                    response = (
                        AgentRunResponse.from_agent_run_response_updates(updates)
                        if updates
                        else None
                    )
                    await self._maybe_compact(thread=thread, response=response)
                except Exception as compact_exc:
                    # Don't let compaction errors affect the main flow
                    if not cancelled:
                        LOGGER.warning(
                            "Context compaction failed | agent=%s | error=%s",
                            self.agent_id,
                            compact_exc,
                        )
                # Reset session context when stream completes
                reset_session_context(token)

        async for update in _stream():
            yield update

    def as_tool(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        arg_name: str = "task",
        arg_description: str | None = None,
        stream_callback: Callable[[AgentRunResponseUpdate], None]
        | Callable[[AgentRunResponseUpdate], Awaitable[None]]
        | None = None,
    ) -> AIFunction[Any, str]:
        tool_name = name or self.agent.name or self.agent_id
        tool_description = description or self.agent.description or ""
        argument_description = arg_description or f"Task for {tool_name}"

        field_info = Field(..., description=argument_description)
        model_name = f"{tool_name}_input"
        input_model = create_model(model_name, **{arg_name: (str, field_info)})

        is_async_callback = stream_callback is not None and inspect.iscoroutinefunction(stream_callback)

        async def agent_wrapper(**kwargs: Any) -> str:
            task = kwargs.get(arg_name, "")
            if stream_callback is None:
                response: AgentRunResponse = await self.run(task)
                return response.text or ""

            updates: list[AgentRunResponseUpdate] = []
            async for update in self.run_stream(task):
                updates.append(update)
                if stream_callback is not None:
                    if is_async_callback:
                        await stream_callback(update)  # type: ignore[arg-type]
                    else:
                        stream_callback(update)
            final_response = AgentRunResponse.from_agent_run_response_updates(updates)
            return final_response.text or ""

        return AIFunction(
            name=tool_name,
            description=tool_description,
            func=agent_wrapper,
            input_model=input_model,  # type: ignore[arg-type]
        )

    def artifact_store(self) -> ArtifactStore:
        return ArtifactStore(self.workspace.path)

    def _merge_kwargs(self, overrides: dict[str, Any]) -> dict[str, Any]:
        base = self._base_kwargs()
        reserved = set(base)
        reserved.add("agent_id")
        conflicts = reserved.intersection(overrides)
        if conflicts:
            raise ValueError(
                f"Reserved Deep Agent kwargs cannot be overridden: {', '.join(sorted(conflicts))}"
            )
        merged = {**base, **overrides}
        # Ensure downstream handlers still have a consistent set in case overrides deleted them
        inject_workspace_kwargs(
            merged,
            workspace=self.workspace,
            agent_id=self.agent_id,
            plan_path=str(self.plan_store.path) if self.plan_store else None,
            thread=overrides.get("thread"),
        )
        # NOTE: Remove kwargs that agent-framework's observability layer explicitly passes
        # to _get_span_attributes, to avoid "got multiple values for keyword argument" error.
        # Similar to thread_id handling in workspace/core.py
        observability_reserved_kwargs = {"agent_id", "agent_name", "agent_description", "thread_id"}
        for key in observability_reserved_kwargs:
            merged.pop(key, None)
        return merged

    async def _maybe_compact(
        self,
        *,
        thread: AgentThread,
        response: AgentRunResponse | None,
    ) -> None:
        if not self.context_compactor:
            return
        await self.context_compactor.maybe_compact(thread=thread, response=response)


def _resolve_instructions(
    *,
    agent_id: str,
    instructions: str | None,
    system_prompt_file: str | None = None,
    allow_autoload: bool = True,
) -> str | None:
    """Resolve instructions with consistent precedence.

    Order: explicit instructions > system_prompt_file > prompts/{agent_id}.md (if allow_autoload)
    """
    if instructions:
        return instructions

    from pathlib import Path
    from ..prompt_loader import load_prompt_from_file

    prompt_candidates: list[Path] = []
    if system_prompt_file:
        prompt_candidates.append(Path(system_prompt_file))
    if allow_autoload:
        prompt_candidates.append(Path(f"prompts/{agent_id}.md"))

    for prompt_path in prompt_candidates:
        if prompt_path.exists():
            try:
                loaded = load_prompt_from_file(prompt_path)
                LOGGER.debug("📄 Loaded system prompt from %s", prompt_path)
                return loaded
            except Exception as exc:
                LOGGER.warning("Failed to load system prompt from %s: %s", prompt_path, exc)
    return instructions


def _build_agent_session_core(
    *,
    chat_client: BaseChatClient,
    workspace: WorkspaceHandle,
    agent_id: str,
    tools: Sequence[ToolProtocol | Any],
    instructions: str | None,
    name: str | None,
    description: str | None,
    planning_enabled: bool,
    inject_workspace_instructions: bool,
    auto_persist_tools: bool,
    context_providers: Iterable[ContextProvider] | None,
    function_middlewares: Iterable[FunctionMiddleware] | None,
    additional_chat_options: dict[str, Any] | None,
    compaction_config: CompactionConfig | None,
    compaction_summarizer: CompactionSummarizer | None,
) -> DeepAgentSession:
    plan_store = PlanStore(workspace.path, agent_id) if planning_enabled else None
    workspace_provider = WorkspaceContextProvider(
        workspace,
        inject_instructions=inject_workspace_instructions,
        plan_path=plan_store.path if plan_store else None,
        agent_id=agent_id,  # Pass agent_id to provider for kwargs injection
    )
    provider_list: list[ContextProvider] = [workspace_provider]
    if context_providers:
        provider_list.extend(context_providers)

    workspace_param_middleware = WorkspaceParameterInjectionMiddleware(
        workspace=workspace,
        agent_id=agent_id,
        plan_path=str(plan_store.path) if plan_store else None,
    )

    middleware_list: list[FunctionMiddleware] = [
        ToolResultPersistenceMiddleware(auto_persist=auto_persist_tools)
    ]
    if function_middlewares:
        middleware_list.extend(function_middlewares)

    tool_list: list[Any] = list(tools)
    if plan_store:
        plan_tool = build_update_plan_tool(plan_store, agent_id=agent_id)
        tool_list.append(plan_tool)

    final_config = compaction_config or CompactionConfig()
    compactor: ContextCompactor | None = None
    if final_config.enabled:
        summarizer = compaction_summarizer or HeuristicSummarizer()
        compactor = ContextCompactor(config=final_config, summarizer=summarizer)

    all_middleware = [workspace_param_middleware] + middleware_list

    # Sanitize name to comply with OpenAI API naming pattern
    sanitized_name = _sanitize_name(name)
    
    agent = ChatAgent(
        chat_client=chat_client,
        instructions=instructions,
        name=sanitized_name,
        description=description,
        context_providers=provider_list,
        middleware=all_middleware,
        tools=tool_list,
        additional_chat_options=additional_chat_options,
    )
    setattr(agent, "instructions", instructions)
    return DeepAgentSession(
        agent=agent,
        agent_id=agent_id,
        workspace=workspace,
        plan_store=plan_store,
        context_compactor=compactor,
    )


def build_agent(
    *,
    chat_client: BaseChatClient,
    workspace: WorkspaceHandle,
    agent_id: str,
    tools: Sequence[ToolProtocol | Any],
    instructions: str | None = None,
    name: str | None = None,
    description: str | None = None,
    planning_enabled: bool = True,
    inject_workspace_instructions: bool = True,
    auto_persist_tools: bool = False,
    context_providers: Iterable[ContextProvider] | None = None,
    function_middlewares: Iterable[FunctionMiddleware] | None = None,
    additional_chat_options: dict[str, Any] | None = None,
    compaction_config: CompactionConfig | None = None,
    compaction_summarizer: CompactionSummarizer | None = None,
) -> DeepAgentSession:
    """Create a Deep Agent session bound to a workspace."""
    resolved_instructions = _resolve_instructions(
        agent_id=agent_id,
        instructions=instructions,
        allow_autoload=True,
    )
    return _build_agent_session_core(
        chat_client=chat_client,
        workspace=workspace,
        agent_id=agent_id,
        tools=tools,
        instructions=resolved_instructions,
        name=name,
        description=description,
        planning_enabled=planning_enabled,
        inject_workspace_instructions=inject_workspace_instructions,
        auto_persist_tools=auto_persist_tools,
        context_providers=context_providers,
        function_middlewares=function_middlewares,
        additional_chat_options=additional_chat_options,
        compaction_config=compaction_config,
        compaction_summarizer=compaction_summarizer,
    )


def build_agent_with_llm(
    *,
    llm_factory: Any,  # LLMClientFactory (avoid circular import)
    llm_name: str,
    workspace: WorkspaceHandle,
    agent_id: str,
    tools: Sequence[ToolProtocol | Any],
    instructions: str | None = None,
    name: str | None = None,
    description: str | None = None,
    planning_enabled: bool = True,
    inject_workspace_instructions: bool = True,
    auto_persist_tools: bool = False,
    context_providers: Iterable[ContextProvider] | None = None,
    function_middlewares: Iterable[FunctionMiddleware] | None = None,
    override_model: str | None = None,
    compaction_config: CompactionConfig | None = None,
    compaction_summarizer: CompactionSummarizer | None = None,
) -> DeepAgentSession:
    """
    Create a Deep Agent session using an LLM client from the factory.
    
    Args:
        llm_factory: Factory instance for creating LLM clients.
        llm_name: Name of the LLM configuration to use.
        workspace: Workspace handle for the agent.
        agent_id: Unique identifier for the agent.
        tools: List of tools available to the agent.
        instructions: System instructions for the agent.
        name: Agent name.
        description: Agent description.
        planning_enabled: Whether to enable planning functionality.
        inject_workspace_instructions: Whether to inject workspace context.
        auto_persist_tools: Whether to auto-persist tool results.
        context_providers: Additional context providers.
        function_middlewares: Additional function middlewares.
        override_model: Optional model override.
        compaction_config: Configuration for context compaction.
        compaction_summarizer: Custom summarizer for compaction.
    
    Returns:
        Configured DeepAgentSession instance.
    """
    from ..llm.factory import LLMClientFactory
    from ..llm.client import build_agent_chat_options
    
    # Get the chat client from factory
    chat_client = llm_factory.get_client(llm_name, override_model=override_model)
    
    # Get the config for building chat options
    llm_config = llm_factory.get_config(llm_name)
    additional_chat_options = build_agent_chat_options(
        llm_config,
        model_override=override_model,
    )
    
    resolved_instructions = _resolve_instructions(
        agent_id=agent_id,
        instructions=instructions,
        allow_autoload=True,
    )

    return _build_agent_session_core(
        chat_client=chat_client,
        workspace=workspace,
        agent_id=agent_id,
        tools=tools,
        instructions=resolved_instructions,
        name=name,
        description=description,
        planning_enabled=planning_enabled,
        inject_workspace_instructions=inject_workspace_instructions,
        auto_persist_tools=auto_persist_tools,
        context_providers=context_providers,
        function_middlewares=function_middlewares,
        additional_chat_options=additional_chat_options,
        compaction_config=compaction_config,
        compaction_summarizer=compaction_summarizer,
    )


def build_agent_from_config(
    *,
    agent_config: Any,  # AgentConfig (avoid circular import)
    llm_factory: Any,  # LLMClientFactory (avoid circular import)
    workspace: WorkspaceHandle,
    tools: Sequence[ToolProtocol | Any],
    instructions: str | None = None,
    context_providers: Iterable[ContextProvider] | None = None,
    function_middlewares: Iterable[FunctionMiddleware] | None = None,
    compaction_summarizer: CompactionSummarizer | None = None,
    allow_prompt_autoload: bool = True,
) -> DeepAgentSession:
    """
    Create a Deep Agent session using AgentConfig and LLM factory.
    
    Args:
        agent_config: Agent configuration containing all settings.
        llm_factory: Factory instance for creating LLM clients.
        workspace: Workspace handle for the agent.
        tools: List of tools available to the agent.
        instructions: System instructions for the agent (overrides config if provided).
        context_providers: Additional context providers.
        function_middlewares: Additional function middlewares (appended after config middlewares).
        compaction_summarizer: Custom summarizer for compaction.
    
    Returns:
        Configured DeepAgentSession instance.
    """
    from ..llm.factory import LLMClientFactory
    from ..llm.client import build_agent_chat_options
    from ..config.agent import AgentConfig
    from ..middleware.loader import load_middlewares
    
    # Get the chat client from factory using the configured LLM profile name
    chat_client = llm_factory.get_client(agent_config.llm_profile_name)
    
    # Get the LLM config for building chat options
    llm_config = llm_factory.get_config(agent_config.llm_profile_name)
    additional_chat_options = build_agent_chat_options(llm_config)
    
    # Apply max_tool_iterations to chat client
    chat_client.additional_properties["max_iterations"] = agent_config.max_tool_iterations
    
    # Build compaction config from agent config
    compaction_config: CompactionConfig | None = None
    if agent_config.context_compaction:
        compaction_config = CompactionConfig(
            enabled=agent_config.context_compaction.enabled,
            max_messages=agent_config.context_compaction.max_messages,
            token_limit=agent_config.context_compaction.max_tokens,
        )
    
    # Load middlewares from config and merge with explicit middlewares
    config_middlewares = load_middlewares(getattr(agent_config, "middlewares", None))
    all_middlewares: list[FunctionMiddleware] = list(config_middlewares)
    if function_middlewares:
        all_middlewares.extend(function_middlewares)
    
    resolved_instructions = _resolve_instructions(
        agent_id=agent_config.id,
        instructions=instructions,
        system_prompt_file=agent_config.system_prompt_file,
        allow_autoload=allow_prompt_autoload,
    )
    
    return _build_agent_session_core(
        chat_client=chat_client,
        workspace=workspace,
        agent_id=agent_config.id,
        tools=tools,
        instructions=resolved_instructions,
        name=agent_config.name,
        description=agent_config.description,
        planning_enabled=agent_config.planning_enabled,
        inject_workspace_instructions=agent_config.inject_workspace_instructions,
        auto_persist_tools=agent_config.auto_persist_tools,
        context_providers=context_providers,
        function_middlewares=all_middlewares or None,
        additional_chat_options=additional_chat_options,
        compaction_config=compaction_config,
        compaction_summarizer=compaction_summarizer,
    )


def build_agent_from_store(
    *,
    agent_id: str,
    agent_config_store: Any,  # AgentConfigStore (avoid circular import)
    llm_factory: Any,  # LLMClientFactory (avoid circular import)
    workspace: WorkspaceHandle,
    tools: Sequence[ToolProtocol | Any],
    instructions: str | None = None,
    context_providers: Iterable[ContextProvider] | None = None,
    function_middlewares: Iterable[FunctionMiddleware] | None = None,
    compaction_summarizer: CompactionSummarizer | None = None,
) -> DeepAgentSession:
    """
    Create a Deep Agent session by retrieving config from store using agent_id.
    
    Args:
        agent_id: ID of the agent configuration to use.
        agent_config_store: Store containing agent configurations.
        llm_factory: Factory instance for creating LLM clients.
        workspace: Workspace handle for the agent.
        tools: List of tools available to the agent.
        instructions: System instructions for the agent (overrides config if provided).
        context_providers: Additional context providers.
        function_middlewares: Additional function middlewares.
        compaction_summarizer: Custom summarizer for compaction.
    
    Returns:
        Configured DeepAgentSession instance.
    
    Raises:
        ValueError: If agent_id is not found in the store.
    """
    from ..config.store import AgentConfigStore
    
    # Get the agent config from store
    agent_config = agent_config_store.get_config(agent_id)
    
    # Delegate to build_agent_from_config
    return build_agent_from_config(
        agent_config=agent_config,
        llm_factory=llm_factory,
        workspace=workspace,
        tools=tools,
        instructions=instructions,
        context_providers=context_providers,
        function_middlewares=function_middlewares,
        compaction_summarizer=compaction_summarizer,
    )


def build_agent_session(
    *,
    ctx: Any,  # BaseAppContext - provides config, llm_factory, agent_store
    agent_id: str,
    workspace: WorkspaceHandle,
    tools: Sequence[ToolProtocol | Any],
    function_middlewares: Iterable[FunctionMiddleware] | None = None,
    compaction_summarizer: CompactionSummarizer | None = None,
) -> DeepAgentSession:
    """
    Simplified agent session builder using application context.
    
    This is the recommended way to build agent sessions. It:
    1. Gets agent config from ctx.agent_store
    2. Loads system prompt from agent config
    3. Creates SystemPromptContextProvider to inject prompt dynamically
    4. Builds the agent session with all standard settings
    
    Args:
        ctx: Application context (must have llm_factory and get_agent_config method)
        agent_id: ID of the agent configuration to use
        workspace: Workspace handle for the agent
        tools: List of tools available to the agent
        function_middlewares: Optional additional function middlewares
        compaction_summarizer: Optional custom summarizer for compaction
    
    Returns:
        Configured DeepAgentSession instance.
    
    Example:
        session = build_agent_session(
            ctx=app_context,
            agent_id="my_agent",
            workspace=workspace,
            tools=[tool1, tool2],
        )
    """
    from ..prompt_loader import load_prompt_from_agent_config
    from ..system_prompt_provider import SystemPromptContextProvider
    
    agent_config = ctx.get_agent_config(agent_id)
    
    # Load and inject system prompt via provider (avoids duplication)
    system_prompt = load_prompt_from_agent_config(agent_config)
    context_providers = [SystemPromptContextProvider(system_prompt)]
    
    LOGGER.debug(
        "Building agent session | agent=%s | tools=%d | prompt_len=%d",
        agent_id,
        len(tools),
        len(system_prompt) if system_prompt else 0,
    )
    
    # Keep autoload disabled here because the provider supplies the prompt
    return build_agent_from_config(
        agent_config=agent_config,
        llm_factory=ctx.llm_factory,
        workspace=workspace,
        tools=tools,
        instructions="",  # Empty to prevent auto-load; provider injects dynamically
        context_providers=context_providers,
        function_middlewares=function_middlewares,
        compaction_summarizer=compaction_summarizer,
        allow_prompt_autoload=False,
    )


__all__ = [
    "DeepAgentSession",
    "build_agent",
    "build_agent_with_llm",
    "build_agent_from_config",
    "build_agent_from_store",
    "build_agent_session",
]
