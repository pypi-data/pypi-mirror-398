from __future__ import annotations

from typing import Any, Optional

import httpx
import requests

from nlbone.adapters.auth.token_provider import ClientTokenProvider
from nlbone.config.settings import get_settings
from nlbone.core.ports.files import FileServicePort
from nlbone.utils.http import auth_headers, build_list_query, normalize_https_base


class UploadchiError(RuntimeError):
    def __init__(self, status: int, detail: Any | None = None):
        super().__init__(f"Uploadchi HTTP {status}: {detail}")
        self.status = status
        self.detail = detail


def _resolve_token(explicit: str | None) -> str | None:
    if explicit is not None:
        return explicit
    s = get_settings()
    return s.UPLOADCHI_TOKEN.get_secret_value() if s.UPLOADCHI_TOKEN else None


def _filename_from_cd(cd: str | None, fallback: str) -> str:
    if not cd:
        return fallback
    if "filename=" in cd:
        return cd.split("filename=", 1)[1].strip("\"'")
    return fallback


class UploadchiClient(FileServicePort):
    def __init__(
        self,
        token_provider: ClientTokenProvider | None = None,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        client: httpx.Client | None = None,
    ) -> None:
        s = get_settings()
        self._base_url = normalize_https_base(base_url or str(s.UPLOADCHI_BASE_URL))
        self._timeout = timeout_seconds or float(s.HTTP_TIMEOUT_SECONDS)
        self._client = client or requests.session()
        self._token_provider = token_provider

    def close(self) -> None:
        self._client.close()

    def upload_file(
        self, file_bytes: bytes, filename: str, params: dict[str, Any] | None = None, token: str | None = None
    ) -> dict:
        tok = _resolve_token(token)
        files = {"file": (filename, file_bytes)}
        data = (params or {}).copy()
        r = self._client.post(self._base_url, files=files, data=data, headers=auth_headers(tok))
        if r.status_code >= 400:
            raise UploadchiError(r.status_code, r.text)
        return r.json()

    def commit_file(self, file_id: str, token: str | None = None) -> None:
        if not token and not self._token_provider:
            raise UploadchiError(detail="token_provider is not provided", status=400)
        tok = _resolve_token(token)
        r = self._client.post(
            f"{self._base_url}/{file_id}/commit",
            headers=auth_headers(tok or self._token_provider.get_access_token()),
        )
        if r.status_code not in (204, 200):
            raise UploadchiError(r.status_code, r.text)

    def rollback(self, file_id: str, token: str | None = None) -> None:
        if not token and not self._token_provider:
            raise UploadchiError(detail="token_provider is not provided", status=400)
        tok = _resolve_token(token)
        r = self._client.post(
            f"{self._base_url}/{file_id}/rollback",
            headers=auth_headers(tok or self._token_provider.get_access_token()),
        )
        if r.status_code not in (204, 200):
            raise UploadchiError(r.status_code, r.text)

    def list_files(
        self,
        limit: int = 10,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
        sort: list[tuple[str, str]] | None = None,
        token: str | None = None,
    ) -> dict:
        tok = _resolve_token(token)
        q = build_list_query(limit, offset, filters, sort)
        r = self._client.get(self._base_url, params=q, headers=auth_headers(tok))
        if r.status_code >= 400:
            raise UploadchiError(r.status_code, r.text)
        return r.json()

    def get_file(self, file_id: str, token: str | None = None) -> dict:
        tok = _resolve_token(token)
        r = self._client.get(f"{self._base_url}/{file_id}", headers=auth_headers(tok))
        if r.status_code >= 400:
            raise UploadchiError(r.status_code, r.text)
        return r.json()

    def download_file(self, file_id: str, token: str | None = None) -> tuple[bytes, str, str]:
        tok = _resolve_token(token)
        r = self._client.get(f"{self._base_url}/{file_id}/download", headers=auth_headers(tok))
        if r.status_code >= 400:
            raise UploadchiError(r.status_code, r.text)
        filename = _filename_from_cd(r.headers.get("content-disposition"), fallback=f"file-{file_id}")
        media_type = r.headers.get("content-type", "application/octet-stream")
        return r.content, filename, media_type

    def delete_file(self, file_id: str, token: str | None = None) -> None:
        tok = _resolve_token(token)
        r = self._client.delete(
            f"{self._base_url}/{file_id}", headers=auth_headers(tok or self._token_provider.get_access_token())
        )
        if r.status_code not in (204, 200):
            raise UploadchiError(r.status_code, r.text)
