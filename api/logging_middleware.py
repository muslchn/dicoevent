"""Request/response logging middleware for API observability."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger("api.request")


class RequestResponseLoggingMiddleware:
    """Log API request metadata and response timing."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        start = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        user_id = getattr(request.user, "id", None)
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": elapsed_ms,
                "user_id": str(user_id) if user_id else "anonymous",
            },
        )

        return response
