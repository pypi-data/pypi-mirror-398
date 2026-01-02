from __future__ import annotations

from typing import Optional
from uuid import uuid4

from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request

from nlbone.config.settings import get_settings
from nlbone.utils.context import bind_context, request_ctx, request_id_ctx, reset_context


def mock_request(user=None, token: Optional[str] = None):
    request = Request(
        {
            "type": "http",
            "headers": Headers({"User-Agent": "Testing-Agent"}).raw,
            "client": {"host": "192.168.1.1", "port": 80},
            "method": "GET",
            "path": "/__test__",
        }
    )
    request.state.user = user
    request.state.token = token
    return request


def current_request() -> Optional[Request]:
    req = request_ctx.get()
    if get_settings().ENV == "local" and req is None:
        return mock_request()
    return req


def current_request_id() -> Optional[str]:
    return request_id_ctx.get()


class AddRequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        incoming_req_id = request.headers.get("X-Request-ID")
        req_id = incoming_req_id or str(uuid4())

        user_id = getattr(getattr(request, "state", None), "user_id", None) or request.headers.get("X-User-Id")
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
        locale = request.headers.get("Accept-Language", 'fa-IR')
        request.state.locale = locale

        tokens = bind_context(request=request, request_id=req_id, user_id=user_id, ip=ip, user_agent=ua, locale=locale)
        try:
            response = await call_next(request)
            response.headers.setdefault("X-Request-ID", req_id)
            return response
        finally:
            reset_context(tokens)
