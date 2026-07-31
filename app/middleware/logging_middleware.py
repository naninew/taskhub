# [Ngày 4] Middleware log mỗi request: method, path, status_code, latency_ms

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Ghi log thông tin request/response cho mọi endpoint."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "Request: method=%s path=%s status_code=%s latency_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
        )
        return response
