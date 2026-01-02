from contextvars import ContextVar
from typing import Any, Optional

request_ctx: ContextVar[Any | None] = ContextVar("request", default=None)
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)
ip_ctx: ContextVar[str | None] = ContextVar("ip", default=None)
user_agent_ctx: ContextVar[str | None] = ContextVar("user_agent", default=None)
_current_locale: ContextVar[str] = ContextVar("current_locale")


def bind_context(
    *,
    request: Any | None = None,
    request_id: str | None = None,
    user_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    locale: str | None = None,
) -> dict[ContextVar, Any]:
    tokens: dict[ContextVar, Any] = {}
    if request is not None:
        tokens[request_ctx] = request_ctx.set(request)
    if request_id is not None:
        tokens[request_id_ctx] = request_id_ctx.set(request_id)
    if user_id is not None:
        tokens[user_id_ctx] = user_id_ctx.set(user_id)
    if ip is not None:
        tokens[ip_ctx] = ip_ctx.set(ip)
    if user_agent is not None:
        tokens[user_agent_ctx] = user_agent_ctx.set(user_agent)
    if locale is not None:
        tokens[_current_locale] = _current_locale.set(locale)
    return tokens


def reset_context(tokens: dict[ContextVar, Any]):
    for var, token in tokens.items():
        var.reset(token)


def current_request():
    return request_ctx.get()


def current_request_id() -> Optional[str]:
    return request_id_ctx.get()


def current_context_dict() -> dict[str, Any]:
    return {
        "request_id": request_id_ctx.get(),
        "user_id": user_id_ctx.get(),
        "ip": ip_ctx.get(),
        "user_agent": user_agent_ctx.get(),
    }


def get_locale():
    return _current_locale.get()
