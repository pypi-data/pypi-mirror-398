"""Middleware utilities for AG-UI servers."""
from __future__ import annotations

import asyncio
import logging

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


class HealthCheckFilter(logging.Filter):
    """Filter out health check endpoint logs to reduce noise."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if '"GET /health ' in message or '"GET /ready ' in message:
            return False
        return True


class ConcurrencyLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit concurrent requests."""

    def __init__(self, app, max_concurrent: int = 100):
        super().__init__(app)
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._max_concurrent = max_concurrent
        self._current_count = 0

    async def dispatch(self, request: Request, call_next):
        if request.url.path in (
            "/health",
            "/ready",
            "/api/session-stats",
            "/api/ui-config",
            "/api/verify-passcode",
        ):
            return await call_next(request)

        acquired = self._semaphore.locked() is False
        if not acquired and self._current_count >= self._max_concurrent:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Server at capacity ({self._max_concurrent} concurrent requests). "
                    "Please retry later."
                ),
            )

        async with self._semaphore:
            self._current_count += 1
            try:
                return await call_next(request)
            finally:
                self._current_count -= 1


__all__ = ["ConcurrencyLimitMiddleware", "HealthCheckFilter"]
