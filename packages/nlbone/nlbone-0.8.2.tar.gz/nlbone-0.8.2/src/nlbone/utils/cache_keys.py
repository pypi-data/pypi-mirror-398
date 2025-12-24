import hashlib
import json
import random
from typing import Any, Mapping


def _stable_params(params: Mapping[str, Any]) -> str:
    return json.dumps(params, sort_keys=True, separators=(",", ":"))


def make_key(ns: str, *parts: str) -> str:
    safe_parts = [p.replace(" ", "_") for p in parts if p]
    return f"{ns}:{':'.join(safe_parts)}" if safe_parts else f"{ns}:root"


def make_param_key(ns: str, base: str, params: Mapping[str, Any]) -> str:
    payload = _stable_params(params)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{ns}:{base}:{digest}"


def tag_entity(ns: str, entity_id: Any) -> str:
    return f"{ns}:{entity_id}"


def tag_list(ns: str, **filters) -> str:
    if not filters:
        return f"{ns}:list"
    payload = _stable_params(filters)
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()[:12]
    return f"{ns}:list:{digest}"


def ttl_with_jitter(base_ttl: int, *, jitter_ratio: float = 0.1) -> int:
    jitter = int(base_ttl * jitter_ratio)
    return base_ttl + random.randint(-jitter, jitter)
