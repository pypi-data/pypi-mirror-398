from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse, urlunparse

from nlbone.utils.context import current_request


def auth_headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def build_list_query(
        limit: int, offset: int, filters: dict[str, Any] | None, sort: list[tuple[str, str]] | None
) -> dict[str, Any]:
    q: dict[str, Any] = {"limit": limit, "offset": offset}
    if filters:
        q["filters"] = json.dumps(filters)
    if sort:
        q["sort"] = ",".join([f"{f}:{o}" for f, o in sort])
    return q


def normalize_https_base(url: str, enforce_https: bool = True) -> str:
    p = urlparse(url.strip())
    if enforce_https:
        p = p._replace(scheme="https")  # enforce https
    if p.path.endswith("/"):
        p = p._replace(path=p.path.rstrip("/"))
    return str(urlunparse(p))


def get_service_base_url() -> str:
    req = current_request()          # Starlette Request
    url = req.base_url               # URL object
    return str(url.replace(scheme="https"))
