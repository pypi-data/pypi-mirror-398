import functools
from datetime import datetime, timezone
from threading import RLock

from cachetools import LRUCache
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError

from nlbone.config.settings import Settings, get_settings
from nlbone.core.ports.auth import AuthService

_permissions_cache: LRUCache = LRUCache(maxsize=2048)
_permissions_lock = RLock()


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _ttl_from_decoded(decoded: dict) -> int:
    exp = int(decoded.get("exp", 0))
    ttl = max(1, exp - _now_ts())
    return ttl


def _cache_key(sub: str | None, exp: int | None) -> tuple[str | None, int | None]:
    return sub, exp


class KeycloakAuthService(AuthService):
    def __init__(self, settings: Settings | None = None):
        s = settings or get_settings()
        self.keycloak_openid = KeycloakOpenID(
            server_url=s.KEYCLOAK_SERVER_URL.__str__(),
            client_id=s.KEYCLOAK_CLIENT_ID,
            realm_name=s.KEYCLOAK_REALM_NAME,
            client_secret_key=s.KEYCLOAK_CLIENT_SECRET.get_secret_value().strip(),
        )
        self.bypass = s.ENV != "prod"

    def has_access(self, token, permissions):
        if self.bypass:
            return True

        try:
            result = self.keycloak_openid.has_uma_access(token, permissions=permissions)
            return result.is_authorized
        except KeycloakAuthenticationError:
            return False
        except Exception as e:
            print(f"Token verification failed: {e}")
            return False

    def _fetch_permissions_from_keycloak(self, token: str) -> tuple[list[str], dict]:
        permissions = self.keycloak_openid.uma_permissions(token)
        decoded_token = self.keycloak_openid.decode_token(token)
        result: list[str] = []
        for p in permissions or []:
            rsname = p.get("rsname")
            for s in p.get("scopes", []) or []:
                result.append(f"{rsname}#{s}")
        return result, decoded_token

    def get_permissions(self, token: str) -> list[str]:
        try:
            decoded = self.keycloak_openid.decode_token(token)
            sub = decoded.get("sub")
            exp = decoded.get("exp")
            key = _cache_key(sub, exp)

            now = _now_ts()
            with _permissions_lock:
                entry = _permissions_cache.get(key)
                if entry is not None:
                    perms, exp_ts = entry
                    if exp_ts > now:
                        return perms
                    _permissions_cache.pop(key, None)

            perms, decoded2 = self._fetch_permissions_from_keycloak(token)
            decoded_final = decoded2 or decoded
            sub_f = decoded_final.get("sub")
            exp_f = int(decoded_final.get("exp") or 0)
            key_f = _cache_key(sub_f, exp_f)

            with _permissions_lock:
                _permissions_cache[key_f] = (perms, exp_f)

            return perms

        except KeycloakAuthenticationError:
            return []
        except Exception as e:
            print(f"Getting permissions failed: {e}")
            return []

    def verify_token(self, token: str) -> dict | None:
        try:
            result = self.keycloak_openid.introspect(token)
            if not result.get("active"):
                raise KeycloakAuthenticationError("NotActiveSession")
            return result
        except KeycloakAuthenticationError:
            return None
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None

    def get_client_token(self) -> dict | None:
        try:
            return self.keycloak_openid.token(grant_type="client_credentials")
        except Exception as e:
            print(f"Failed to get client token: {e}")
            return None

    def get_client_id(self, token: str):
        data = self.verify_token(token)
        if not data:
            return None

        is_service_account = bool(data.get("username").startswith("service-account-"))
        client_id = data.get("client_id")

        if not is_service_account or not client_id:
            return None

        return client_id

    def is_client_token(self, token: str, allowed_clients: set[str] | None = None) -> bool:
        client_id = self.get_client_id(token)

        if not client_id:
            return False

        if allowed_clients is not None and client_id not in allowed_clients:
            return False

        return True

    def client_has_access(self, token: str, permissions: list[str], allowed_clients: set[str] | None = None) -> bool:
        if not self.is_client_token(token, allowed_clients):
            return False
        return self.has_access(token, permissions)


@functools.lru_cache(maxsize=1)
def get_auth_service() -> KeycloakAuthService:
    return KeycloakAuthService()
