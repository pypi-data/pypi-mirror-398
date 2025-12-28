"""Tests for middleware_loader module."""
from __future__ import annotations

import pytest
from agent_framework import FunctionMiddleware

from agentic_ai.middleware.loader import load_middleware, load_middlewares


class DummyMiddleware(FunctionMiddleware):
    """Test middleware for unit tests."""

    async def process(self, context, next):
        await next(context)


def create_dummy_middleware() -> FunctionMiddleware:
    """Factory function for creating middleware."""
    return DummyMiddleware()


# Instance for testing direct instance detection
dummy_instance = DummyMiddleware()


class NotAMiddleware:
    """A class that is not a middleware for testing."""
    pass


def bad_factory() -> str:
    """Factory that returns wrong type."""
    return "not a middleware"


class TestLoadMiddleware:
    """Tests for load_middleware function."""

    def test_load_class_with_colon_format(self):
        """Test loading middleware class using module:ClassName format."""
        middleware = load_middleware("tests.test_middleware_loader:DummyMiddleware")
        assert isinstance(middleware, DummyMiddleware)

    def test_load_factory_function(self):
        """Test loading middleware from factory function."""
        middleware = load_middleware("tests.test_middleware_loader:create_dummy_middleware")
        assert isinstance(middleware, DummyMiddleware)

    def test_load_instance_directly(self):
        """Test loading middleware instance directly."""
        middleware = load_middleware("tests.test_middleware_loader:dummy_instance")
        assert middleware is dummy_instance

    def test_load_legacy_dot_format(self):
        """Test loading middleware using legacy module.name format."""
        middleware = load_middleware("tests.test_middleware_loader.DummyMiddleware")
        assert isinstance(middleware, DummyMiddleware)

    def test_invalid_path_no_separator(self):
        """Test that invalid path without separator raises ValueError."""
        with pytest.raises(ValueError, match="Invalid middleware path"):
            load_middleware("invalid_path")

    def test_module_not_found(self):
        """Test that non-existent module raises ImportError."""
        with pytest.raises(ImportError, match="Failed to import"):
            load_middleware("nonexistent_module:SomeClass")

    def test_attribute_not_found(self):
        """Test that non-existent attribute raises AttributeError."""
        with pytest.raises(AttributeError, match="not found in module"):
            load_middleware("tests.test_middleware_loader:NonExistentClass")

    def test_non_middleware_class(self):
        """Test that non-middleware class raises ValueError."""
        with pytest.raises(ValueError, match="not a FunctionMiddleware subclass"):
            load_middleware("tests.test_middleware_loader:NotAMiddleware")

    def test_bad_factory_return_type(self):
        """Test that factory returning wrong type raises ValueError."""
        with pytest.raises(ValueError, match="returned.*expected FunctionMiddleware"):
            load_middleware("tests.test_middleware_loader:bad_factory")


class TestLoadMiddlewares:
    """Tests for load_middlewares function."""

    def test_load_multiple_middlewares(self):
        """Test loading multiple middlewares."""
        paths = [
            "tests.test_middleware_loader:DummyMiddleware",
            "tests.test_middleware_loader:create_dummy_middleware",
        ]
        middlewares = load_middlewares(paths)
        assert len(middlewares) == 2
        assert all(isinstance(m, DummyMiddleware) for m in middlewares)

    def test_load_empty_list(self):
        """Test loading empty list returns empty list."""
        middlewares = load_middlewares([])
        assert middlewares == []

    def test_load_none(self):
        """Test loading None returns empty list."""
        middlewares = load_middlewares(None)
        assert middlewares == []
