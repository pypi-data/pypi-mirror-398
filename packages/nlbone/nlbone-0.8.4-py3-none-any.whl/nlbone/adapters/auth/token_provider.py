import threading
import time
from typing import Any, Dict, Optional

from nlbone.core.ports.auth import AuthService as BaseAuthService


class ClientTokenProvider:
    """Caches Keycloak client-credentials token and refreshes before expiry."""

    def __init__(self, auth: BaseAuthService, *, skew_seconds: int = 30) -> None:
        self._auth = auth
        self._skew = skew_seconds
        self._lock = threading.Lock()
        self._token: Optional[str] = None  # access_token
        self._expires_at: float = 0.0  # epoch seconds

    def _needs_refresh(self) -> bool:
        return not self._token or time.time() >= (self._expires_at - self._skew)

    def get_access_token(self) -> str:
        """Return a valid access token; refresh if needed."""
        if not self._needs_refresh():
            return self._token

        with self._lock:
            if not self._needs_refresh():
                return self._token

            data: Dict[str, Any] = self._auth.get_client_token()
            access_token = data.get("access_token")
            if not access_token:
                raise RuntimeError("Keycloak: missing access_token")
            expires_in = int(data.get("expires_in", 15 * 60))
            self._token = access_token
            self._expires_at = time.time() + max(1, expires_in)
            return self._token

    def get_auth_header(self) -> str:
        return f"Bearer {self.get_access_token()}"
