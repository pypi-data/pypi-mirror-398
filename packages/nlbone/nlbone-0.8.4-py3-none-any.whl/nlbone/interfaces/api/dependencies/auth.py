import functools

from nlbone.core.domain.models import CurrentUserData
from nlbone.adapters.auth import KeycloakAuthService
from nlbone.adapters.auth.keycloak import get_auth_service
from nlbone.config.settings import get_settings
from nlbone.interfaces.api.exceptions import ForbiddenException, UnauthorizedException
from nlbone.utils.context import current_request


@functools.lru_cache()
def bypass_authz() -> bool:
    if get_settings().ENV != "prod":
        return True
    return False


def current_user_id() -> int:
    user_id = current_request().state.user_id
    if user_id is not None:
        return int(user_id)
    raise UnauthorizedException()


def current_user() -> CurrentUserData:
    user = current_request().state.user
    if not user or user.id is None:
        raise UnauthorizedException()
    return user


def current_client_id() -> str:
    request = current_request()
    if client_id := KeycloakAuthService().get_client_id(request.state.token):
        return str(client_id)
    raise UnauthorizedException()


def client_has_access_func(*, permissions=None):
    request = current_request()
    if not KeycloakAuthService().client_has_access(request.state.token, permissions=permissions):
        raise ForbiddenException(f"Forbidden {permissions}")
    return True


def client_has_access(*, permissions=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            client_has_access_func(permissions=permissions)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def user_authenticated(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user_id():
            raise UnauthorizedException()
        return func(*args, **kwargs)

    return wrapper


def user_has_access_func(*, permissions=None):
    if bypass_authz():
        return
    request = current_request()
    if not current_user_id():
        raise UnauthorizedException()
    user_permissions = get_auth_service().get_permissions(request.state.token)
    for p in permissions or []:
        if p not in user_permissions:
            raise ForbiddenException(f"Forbidden {permissions}")
    return True


def has_access(*, permissions=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user_has_access_func(permissions=permissions)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def client_or_user_has_access_func(permissions=None, client_permissions=None):
    if bypass_authz():
        return
    request = current_request()
    token = getattr(request.state, "token", None)
    if not token:
        raise UnauthorizedException()
    needed = client_permissions or permissions
    try:
        client_has_access_func(permissions=needed)
    except Exception:
        user_has_access_func(permissions=needed)


def client_or_user_has_access(*, permissions=None, client_permissions=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            client_or_user_has_access_func(permissions=permissions, client_permissions=client_permissions)
            return func(*args, **kwargs)

        return wrapper

    return decorator
