"""Simple in-memory rate limiter middleware for FastAPI.

Uses a sliding-window counter per IP address.  For production at scale,
replace with Redis-backed rate limiting (e.g. fastapi-limiter).
"""

import time
from collections import defaultdict
from typing import Dict, List, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding-window rate limiter."""

    def __init__(self, app, requests_per_minute: int = 0):
        super().__init__(app)
        self.rpm = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.window = 60  # seconds
        # ip -> list of timestamps
        self._hits: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        path = request.url.path
        if path.endswith("/health") or "/docs" in path or "/redoc" in path or "/openapi" in path:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Prune old entries
        self._hits[ip] = [
            ts for ts in self._hits[ip] if ts > now - self.window
        ]

        if len(self._hits[ip]) >= self.rpm:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Muitas requisições. Tente novamente em 1 minuto.",
                },
                headers={"Retry-After": str(self.window)},
            )

        self._hits[ip].append(now)
        response = await call_next(request)
        return response
