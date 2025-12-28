"""Tests for SessionFactory."""

import asyncio
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from agentic_ai.runtime.session_factory import (
    SessionFactory,
    ThreadSession,
    DEFAULT_SESSION_TTL_SECONDS,
)


@pytest.fixture
def mock_build_result():
    """Create a mock DeclarativeBuildResult."""
    mock_session = MagicMock()
    mock_session.agent_id = "test_agent"
    mock_session.close = MagicMock()
    
    mock_controller = MagicMock()
    mock_controller.session = MagicMock()
    mock_controller.session.agent_id = "sub_agent"
    mock_controller.close = MagicMock()
    
    result = MagicMock()
    result.session = mock_session
    result.subagent_controllers = {"sub_agent": mock_controller}
    return result


@pytest.fixture
def mock_session_builder(mock_build_result):
    """Create a mock session builder."""
    def builder(workspace):
        return mock_build_result
    return builder


def test_thread_session_touch_updates_timestamp():
    """Test that touch() updates last_accessed_at."""
    session = ThreadSession(
        thread_id="test-1",
        master=MagicMock(),
        workspace=MagicMock(),
    )
    original_time = session.last_accessed_at
    time.sleep(0.01)
    session.touch()
    assert session.last_accessed_at > original_time


def test_thread_session_is_expired():
    """Test session expiration detection."""
    session = ThreadSession(
        thread_id="test-1",
        master=MagicMock(),
        workspace=MagicMock(),
    )
    # Not expired with long TTL
    assert not session.is_expired(3600)
    # Expired with zero TTL
    assert session.is_expired(0)


def test_thread_session_get_controller():
    """Test getting sub-agent controller by ID."""
    mock_controller = MagicMock()
    session = ThreadSession(
        thread_id="test-1",
        master=MagicMock(),
        workspace=MagicMock(),
        subagent_controllers={"discovery": mock_controller},
    )
    assert session.get_controller("discovery") is mock_controller
    with pytest.raises(KeyError):
        session.get_controller("nonexistent")


def test_session_factory_creates_new_session(tmp_path, mock_session_builder):
    """Test creating a new session."""
    async def _run():
        factory = SessionFactory(
            session_builder=mock_session_builder,
            workspace_root=tmp_path,
        )
        
        session = await factory.get_session("thread-1")
        
        assert session.thread_id == "thread-1"
        assert factory.active_session_count == 1
    
    asyncio.run(_run())


def test_session_factory_reuses_session(tmp_path, mock_session_builder):
    """Test that same thread_id returns cached session."""
    async def _run():
        factory = SessionFactory(
            session_builder=mock_session_builder,
            workspace_root=tmp_path,
        )
        
        session1 = await factory.get_session("thread-1")
        session2 = await factory.get_session("thread-1")
        
        assert session1 is session2
        assert factory.active_session_count == 1
    
    asyncio.run(_run())


def test_session_factory_different_threads(tmp_path, mock_session_builder):
    """Test that different thread_ids get different sessions."""
    async def _run():
        factory = SessionFactory(
            session_builder=mock_session_builder,
            workspace_root=tmp_path,
        )
        
        session1 = await factory.get_session("thread-1")
        session2 = await factory.get_session("thread-2")
        
        assert session1 is not session2
        assert factory.active_session_count == 2
    
    asyncio.run(_run())


def test_session_factory_expires_session(tmp_path, mock_session_builder):
    """Test that expired sessions are replaced."""
    async def _run():
        factory = SessionFactory(
            session_builder=mock_session_builder,
            workspace_root=tmp_path,
            session_ttl_seconds=0.001,  # Very short TTL
        )
        
        session1 = await factory.get_session("thread-1")
        await asyncio.sleep(0.01)  # Wait for expiration
        session2 = await factory.get_session("thread-1")
        
        # Should be a new session since the first expired
        assert session1 is not session2
    
    asyncio.run(_run())


def test_session_factory_get_stats(tmp_path, mock_session_builder):
    """Test factory statistics."""
    factory = SessionFactory(
        session_builder=mock_session_builder,
        workspace_root=tmp_path,
        session_ttl_seconds=3600,
    )
    
    stats = factory.get_stats()
    
    assert stats["active_sessions"] == 0
    assert stats["session_ttl_seconds"] == 3600
    assert str(tmp_path) in stats["workspace_root"]


def test_default_session_ttl():
    """Test default TTL value."""
    assert DEFAULT_SESSION_TTL_SECONDS == 3600.0
