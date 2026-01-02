import requests

from nlbone.config.settings import get_settings
from nlbone.core.ports.auth import AuthService as BaseAuthService
from nlbone.utils.cache import cached
from nlbone.utils.http import normalize_https_base


class AuthService(BaseAuthService):
    def __init__(self):
        s = get_settings()
        self.client_id = s.KEYCLOAK_CLIENT_ID
        self.client_secret = s.CLIENT_SECRET.get_secret_value().strip()
        self._base_url = normalize_https_base(s.AUTH_SERVICE_URL.unicode_string(), enforce_https=False)
        self._timeout = float(s.HTTP_TIMEOUT_SECONDS)
        self._client = requests.session()

    def has_access(self, token: str, permissions: list[str]) -> bool: ...

    @cached(ttl=15 * 60)
    def verify_token(self, token: str) -> dict:
        url = f"{self._base_url}/introspect"
        result = self._client.post(url, data={"token": token})
        if result.status_code == 200:
            return result.json()
        return None

    def get_client_id(self, token: str):
        data = self.verify_token(token)
        if data:
            return data["sub"] if data["sub"].startswith("service-account") else None
        return None

    def get_client_token(self) -> dict | None:
        url = f"{self._base_url}/token"
        result = self._client.post(
            url,
            data={"client_id": self.client_id, "client_secret": self.client_secret, "grant_type": "client_credentials"},
        )
        if result.status_code == 200:
            return result.json()
        return None

    def is_client_token(self, token: str, allowed_clients: set[str] | None = None) -> bool: ...

    def client_has_access(self, token: str, permissions: list[str], allowed_clients: set[str] | None = None) -> bool:
        data = self.verify_token(token)
        if not data:
            return False
        has_access = [self.client_id + "#" + perm in data.get("allowed_permissions", []) for perm in permissions]
        return all(has_access)

    def get_permissions(self, token: str) -> list[str]: ...
