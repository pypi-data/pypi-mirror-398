import functools

from nlbone.adapters.auth import KeycloakAuthService
from nlbone.interfaces.api.exceptions import ForbiddenException, UnauthorizedException
from nlbone.utils.context import current_request

from .auth import client_has_access_func, client_or_user_has_access_func


async def current_user_id() -> int:
    user_id = current_request().state.user_id
    if user_id is not None:
        return int(user_id)
    raise UnauthorizedException()


async def current_client_id() -> str:
    request = current_request()
    if client_id := KeycloakAuthService().get_client_id(request.state.token):
        return str(client_id)
    raise UnauthorizedException()


def client_has_access(*, permissions=None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            client_has_access_func(permissions=permissions)
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def user_authenticated(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not await current_user_id():
            raise UnauthorizedException()
        return await func(*args, **kwargs)

    return wrapper


def has_access(*, permissions=None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = current_request()
            if not await current_user_id():
                raise UnauthorizedException()
            if not KeycloakAuthService().has_access(request.state.token, permissions=permissions):
                raise ForbiddenException(f"Forbidden {permissions}")

            return await func(*args, **kwargs)

        return wrapper

    return decorator

def client_or_user_has_access(*, permissions=None, client_permissions=None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            client_or_user_has_access_func(permissions=permissions, client_permissions=client_permissions)
            return await func(*args, **kwargs)

        return wrapper

    return decorator

