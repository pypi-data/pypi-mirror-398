import asyncio
from typing import Callable

from makefun import wraps as mf_wraps

from nlbone.adapters.auth.auth_service import AuthService
from nlbone.interfaces.api.exceptions import ForbiddenException, UnauthorizedException
from nlbone.utils.context import current_request


def current_client_id() -> str:
    request = current_request()
    if client_id := AuthService().get_client_id(request.state.token):
        return str(client_id)
    raise UnauthorizedException()


def client_has_access_func(*, permissions=None):
    request = current_request()
    if not AuthService().client_has_access(request.state.token, permissions=permissions):
        raise ForbiddenException(f"Forbidden {permissions}")
    return True


def client_has_access(*, permissions=None):
    def deco(func: Callable):
        is_async_func = asyncio.iscoroutinefunction(func)

        if is_async_func:

            @mf_wraps(func)
            async def aw(*args, **kwargs):
                client_has_access_func(permissions=permissions)
                return await func(*args, **kwargs)

            return aw

        @mf_wraps(func)
        def sw(*args, **kwargs):
            client_has_access_func(permissions=permissions)
            return func(*args, **kwargs)

        return sw

    return deco
