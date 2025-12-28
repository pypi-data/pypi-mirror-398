"""Session Factory for multi-tenant AG-UI server.

This module provides thread-isolated sessions for concurrent users.
Each thread_id gets its own workspace and session instance.

Example:
    from agentic_ai import SessionFactory, create_session_factory
    
    # Simple usage with custom session builder
    factory = SessionFactory(
        session_builder=my_session_builder,
        workspace_root=Path(".ws"),
    )
    
    # Get or create session for a thread
    session = await factory.get_session("thread-123")
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Generic, Protocol, TypeVar

if TYPE_CHECKING:
    from ..agent import DeepAgentSession
    from ..agent.declarative_builder import DeclarativeBuildResult

from ..workspace import WorkspaceHandle, WorkspaceManager

LOGGER = logging.getLogger("agentic_ai.session_factory")

# Default session TTL: 1 hour
DEFAULT_SESSION_TTL_SECONDS = 3600.0

# Type variable for custom session data
SessionT = TypeVar("SessionT", bound="ThreadSession")


@dataclass(slots=True)
class ThreadSession:
    """A session bound to a specific thread_id.
    
    This is the base session class. Applications can extend this
    with custom fields for their specific needs.
    
    Attributes:
        thread_id: Unique identifier for this session/thread
        master: The main agent session
        workspace: Workspace handle for file operations
        subagent_controllers: Dictionary of sub-agent controllers by ID
        created_at: Timestamp when session was created
        last_accessed_at: Timestamp of last access
    """
    
    thread_id: str
    master: DeepAgentSession
    workspace: WorkspaceHandle
    subagent_controllers: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_accessed_at: float = field(default_factory=time.time)
    
    def touch(self) -> None:
        """Update last accessed time."""
        self.last_accessed_at = time.time()
    
    def is_expired(self, ttl_seconds: float) -> bool:
        """Check if this session has expired."""
        return (time.time() - self.last_accessed_at) > ttl_seconds

    def get_controller(self, controller_id: str) -> Any:
        """Get a sub-agent controller by ID.
        
        Args:
            controller_id: The ID of the sub-agent controller
            
        Returns:
            The controller instance
            
        Raises:
            KeyError: If controller not found
        """
        if controller_id not in self.subagent_controllers:
            raise KeyError(f"Sub-agent controller '{controller_id}' not found")
        return self.subagent_controllers[controller_id]


class SessionBuilder(Protocol):
    """Protocol for session builder callables.
    
    Implementations must accept a workspace and return a DeclarativeBuildResult.
    """
    
    def __call__(self, workspace: WorkspaceHandle) -> DeclarativeBuildResult:
        """Build a session for the given workspace."""
        ...


class SessionFactory(Generic[SessionT]):
    """Factory for creating and managing thread-isolated sessions.
    
    Each thread_id gets its own:
    - Workspace directory: <workspace_root>/<thread_id>/
    - DeepAgentSession with isolated state
    - Sub-agent controllers
    
    Sessions are cached and reused for the same thread_id.
    Expired sessions are automatically cleaned up.
    
    Example:
        factory = SessionFactory(
            session_builder=my_builder,
            workspace_root=Path(".ws"),
            session_ttl_seconds=3600,
        )
        
        session = await factory.get_session("thread-123")
        master = session.master
        discovery = session.get_controller("data_discovery")
    """
    
    def __init__(
        self,
        session_builder: SessionBuilder,
        workspace_root: Path,
        session_ttl_seconds: float = DEFAULT_SESSION_TTL_SECONDS,
        session_class: type[SessionT] | None = None,
    ):
        """Initialize the session factory.
        
        Args:
            session_builder: Callable that builds sessions from workspace
            workspace_root: Root directory for thread workspaces
            session_ttl_seconds: Session TTL in seconds (default: 1 hour)
            session_class: Optional custom session class (must be ThreadSession subclass)
        """
        self._session_builder = session_builder
        self._workspace_root = workspace_root
        self._session_ttl = session_ttl_seconds
        self._session_class: type = session_class or ThreadSession
        self._sessions: dict[str, SessionT] = {}
        self._lock = asyncio.Lock()
        self._workspace_manager = WorkspaceManager(workspace_root)
        
        LOGGER.info(
            "SessionFactory initialized | workspace_root=%s | session_ttl=%ds",
            workspace_root,
            session_ttl_seconds,
        )
    
    async def get_session(self, thread_id: str) -> SessionT:
        """Get or create a session for the given thread_id.
        
        This method is thread-safe and will:
        1. Return cached session if it exists and is not expired
        2. Create a new session if needed
        3. Clean up expired sessions periodically
        
        Args:
            thread_id: The AG-UI thread identifier
            
        Returns:
            ThreadSession bound to the thread_id
        """
        async with self._lock:
            # Check for existing session
            if thread_id in self._sessions:
                session = self._sessions[thread_id]
                if not session.is_expired(self._session_ttl):
                    session.touch()
                    LOGGER.debug("Reusing cached session | thread_id=%s", thread_id)
                    return session
                else:
                    LOGGER.info("Session expired, creating new | thread_id=%s", thread_id)
                    del self._sessions[thread_id]
            
            # Create new session
            session = self._create_session(thread_id)
            self._sessions[thread_id] = session
            
            # Opportunistically clean up expired sessions
            self._cleanup_expired_sessions()
            
            LOGGER.info(
                "Created new session | thread_id=%s | active_sessions=%d",
                thread_id,
                len(self._sessions),
            )
            return session
    
    def _create_session(self, thread_id: str) -> SessionT:
        """Create a new session for the given thread_id."""
        # Create workspace for this thread
        workspace = self._workspace_manager.ensure(thread_id)
        
        # Build session using the provided builder
        build_result = self._session_builder(workspace)
        
        # Create session instance
        return self._session_class(
            thread_id=thread_id,
            master=build_result.session,
            workspace=workspace,
            subagent_controllers=build_result.subagent_controllers,
        )
    
    def _cleanup_expired_sessions(self) -> None:
        """Remove expired sessions from cache."""
        expired_ids = [
            tid for tid, session in self._sessions.items()
            if session.is_expired(self._session_ttl)
        ]
        for tid in expired_ids:
            del self._sessions[tid]
            LOGGER.debug("Cleaned up expired session | thread_id=%s", tid)
        
        if expired_ids:
            LOGGER.info(
                "Cleaned up %d expired sessions | remaining=%d",
                len(expired_ids),
                len(self._sessions),
            )
    
    @property
    def active_session_count(self) -> int:
        """Number of active (non-expired) sessions."""
        return len(self._sessions)
    
    def get_stats(self) -> dict[str, Any]:
        """Get factory statistics for monitoring."""
        now = time.time()
        return {
            "active_sessions": len(self._sessions),
            "session_ttl_seconds": self._session_ttl,
            "workspace_root": str(self._workspace_root),
            "sessions": [
                {
                    "thread_id": tid,
                    "age_seconds": now - s.created_at,
                    "idle_seconds": now - s.last_accessed_at,
                }
                for tid, s in self._sessions.items()
            ],
        }


__all__ = [
    "SessionFactory",
    "SessionBuilder",
    "ThreadSession",
    "DEFAULT_SESSION_TTL_SECONDS",
]
