from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, TYPE_CHECKING

from agent_framework import AgentThread

from ..agent import DeepAgentSession

if TYPE_CHECKING:
    from ..runtime.session_factory import SessionFactory, ThreadSession

LOGGER = logging.getLogger("agentic_ai.ag_ui")

# Type alias for session provider
SessionProvider = Callable[[str], Awaitable["ThreadSession"]]


class DeepAgentProtocolAdapter:
    """Expose a DeepAgentSession as an Agent Framework compatible agent."""

    def __init__(self, session: DeepAgentSession):
        self._session = session

    @property
    def session(self) -> DeepAgentSession:
        return self._session

    @property
    def agent(self):  # pragma: no cover - simple proxy
        return self._session.agent

    @property
    def id(self) -> str:
        agent_id = getattr(self.agent, "id", None)
        return agent_id or self._session.agent_id

    @property
    def name(self) -> str:
        return getattr(self.agent, "name", None) or self._session.agent_id

    @property
    def display_name(self) -> str:
        return getattr(self.agent, "display_name", None) or self.name

    @property
    def description(self) -> str | None:
        return getattr(self.agent, "description", None)

    def get_new_thread(self, **kwargs) -> AgentThread:
        return self.agent.get_new_thread(**kwargs)

    async def run(self, messages=None, *, thread: AgentThread | None = None, **kwargs):
        if messages is None:
            raise ValueError("messages must be provided when invoking DeepAgentProtocolAdapter.run")
        return await self._session.run(messages, thread=thread, **kwargs)

    def run_stream(self, messages=None, *, thread: AgentThread | None = None, **kwargs):
        if messages is None:
            raise ValueError("messages must be provided when invoking DeepAgentProtocolAdapter.run_stream")
        return self._session.run_stream(messages, thread=thread, **kwargs)


class MultiTenantAgentAdapter:
    """Adapter that dynamically routes to thread-specific sessions.
    
    This adapter supports multi-tenant scenarios where each AG-UI thread_id
    should get its own isolated session with separate workspace.
    
    The session is resolved lazily when run_stream is called, using the
    thread_id from the AgentThread's metadata.
    """
    
    def __init__(
        self,
        session_provider: SessionProvider,
        *,
        name: str = "agentic_analyst",
        description: str = "Agentic Analyst (Multi-Tenant)",
        fallback_session: DeepAgentSession | None = None,
    ):
        """Initialize multi-tenant adapter.
        
        Args:
            session_provider: Async function that takes thread_id and returns ThreadSession
            name: Agent name
            description: Agent description
            fallback_session: Optional fallback session for when thread_id is not available
        """
        self._session_provider = session_provider
        self._name = name
        self._description = description
        self._fallback_session = fallback_session
        self._current_session: DeepAgentSession | None = None
    
    @property
    def id(self) -> str:
        return self._name
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def display_name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def agent(self):
        """Return the current session's agent if available, otherwise fallback."""
        if self._current_session:
            return self._current_session.agent
        if self._fallback_session:
            return self._fallback_session.agent
        raise RuntimeError("No session available - run_stream must be called first")
    
    def get_new_thread(self, **kwargs) -> AgentThread:
        """Create a new thread."""
        if self._current_session:
            return self._current_session.agent.get_new_thread(**kwargs)
        if self._fallback_session:
            return self._fallback_session.agent.get_new_thread(**kwargs)
        # Create a bare AgentThread if no session is available yet
        return AgentThread()
    
    async def run(self, messages=None, *, thread: AgentThread | None = None, **kwargs):
        """Run agent (non-streaming)."""
        if messages is None:
            raise ValueError("messages must be provided")
        
        session = await self._resolve_session(thread)
        return await session.run(messages, thread=thread, **kwargs)
    
    async def run_stream(self, messages=None, *, thread: AgentThread | None = None, **kwargs):
        """Run agent with streaming.
        
        Resolves the session based on thread_id from thread metadata,
        then delegates to the resolved session's run_stream.
        
        Handles client disconnection (CancelledError) gracefully to prevent
        service disruption when browser refreshes or closes the connection.
        """
        if messages is None:
            raise ValueError("messages must be provided")
        
        session = await self._resolve_session(thread)
        thread_id = self._extract_thread_id(thread) or "unknown"
        
        # Delegate to the resolved session's run_stream with cancellation handling
        try:
            async for update in session.run_stream(messages, thread=thread, **kwargs):
                yield update
        except asyncio.CancelledError:
            # Client disconnected (browser refresh/close) - this is normal
            LOGGER.info(
                "Client disconnected during streaming | thread_id=%s",
                thread_id,
            )
            # Don't re-raise - allow graceful cleanup
            return
        except GeneratorExit:
            # Generator was closed by the caller - this is normal for client disconnect
            LOGGER.info(
                "Stream generator closed | thread_id=%s",
                thread_id,
            )
            return
    
    async def _resolve_session(self, thread: AgentThread | None) -> DeepAgentSession:
        """Resolve session from thread metadata or fallback."""
        thread_id = self._extract_thread_id(thread)
        
        if thread_id:
            LOGGER.debug("Resolving session for thread_id=%s", thread_id)
            thread_session = await self._session_provider(thread_id)
            self._current_session = thread_session.master
            return thread_session.master
        
        if self._fallback_session:
            LOGGER.warning("No thread_id found, using fallback session")
            return self._fallback_session
        
        raise RuntimeError(
            "Cannot resolve session: no thread_id in thread metadata "
            "and no fallback_session configured"
        )
    
    def _extract_thread_id(self, thread: AgentThread | None) -> str | None:
        """Extract AG-UI thread_id from AgentThread metadata."""
        if thread is None:
            return None
        
        metadata = getattr(thread, "metadata", None)
        if metadata is None:
            return None
        
        # AG-UI framework stores thread_id in ag_ui_thread_id
        return metadata.get("ag_ui_thread_id")


def build_ag_ui_agent(
    session: DeepAgentSession,
    *,
    name: str | None = None,
    description: str | None = None,
    state_schema: dict[str, Any] | None = None,
    predict_state_config: dict[str, dict[str, str]] | None = None,
    require_confirmation: bool = True,
    orchestrators: list[Any] | None = None,
    confirmation_strategy: Any | None = None,
):
    """Wrap a DeepAgentSession in an AgentFrameworkAgent for AG-UI servers."""

    from agent_framework_ag_ui import AgentFrameworkAgent

    adapter = DeepAgentProtocolAdapter(session)
    return AgentFrameworkAgent(
        agent=adapter,
        name=name or adapter.name,
        description=description or adapter.description,
        state_schema=state_schema,
        predict_state_config=predict_state_config,
        require_confirmation=require_confirmation,
        orchestrators=orchestrators,
        confirmation_strategy=confirmation_strategy,
    )


def build_multi_tenant_ag_ui_agent(
    session_provider: SessionProvider,
    *,
    name: str = "agentic_analyst",
    description: str = "Agentic Analyst (Multi-Tenant)",
    fallback_session: DeepAgentSession | None = None,
    state_schema: dict[str, Any] | None = None,
    predict_state_config: dict[str, dict[str, str]] | None = None,
    require_confirmation: bool = False,
    orchestrators: list[Any] | None = None,
    confirmation_strategy: Any | None = None,
):
    """Build a multi-tenant AG-UI agent that routes to thread-specific sessions.
    
    This is the recommended way to create an AG-UI agent for production
    multi-user scenarios.
    
    Args:
        session_provider: Async function that takes thread_id and returns ThreadSession
        name: Agent name
        description: Agent description
        fallback_session: Optional fallback for requests without thread_id
        state_schema: State schema for CopilotKit shared state
        predict_state_config: Predictive state update configuration
        require_confirmation: Whether to require confirmation for tool calls
        orchestrators: Custom orchestrators
        confirmation_strategy: Custom confirmation strategy
        
    Returns:
        AgentFrameworkAgent configured for multi-tenant operation
    """
    from agent_framework_ag_ui import AgentFrameworkAgent
    
    adapter = MultiTenantAgentAdapter(
        session_provider=session_provider,
        name=name,
        description=description,
        fallback_session=fallback_session,
    )
    
    return AgentFrameworkAgent(
        agent=adapter,
        name=name,
        description=description,
        state_schema=state_schema,
        predict_state_config=predict_state_config,
        require_confirmation=require_confirmation,
        orchestrators=orchestrators,
        confirmation_strategy=confirmation_strategy,
    )


__all__ = [
    "DeepAgentProtocolAdapter",
    "MultiTenantAgentAdapter",
    "build_ag_ui_agent",
    "build_multi_tenant_ag_ui_agent",
    "SessionProvider",
]
