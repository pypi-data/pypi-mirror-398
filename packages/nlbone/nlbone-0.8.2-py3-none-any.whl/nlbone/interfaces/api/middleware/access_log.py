import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from nlbone.config.logging import get_logger

logger = get_logger(__name__)


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        status_code = None
        try:
            response = await call_next(request)
            status_code = getattr(response, "status_code", None)
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            dur_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                {
                    "event": "access",
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": dur_ms,
                    "query": request.url.query,
                }
            )
