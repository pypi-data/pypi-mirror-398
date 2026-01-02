import json
import threading
import time
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Set

from nlbone.core.ports.cache import CachePort


class InMemoryCache(CachePort):
    def __init__(self):
        self._data: Dict[str, tuple[bytes, Optional[float]]] = {}
        self._tags: Dict[str, Set[str]] = {}
        self._ns_ver: Dict[str, int] = {}
        self._lock = threading.RLock()

    def _expired(self, key: str) -> bool:
        v = self._data.get(key)
        if not v:
            return True
        _, exp = v
        return exp is not None and time.time() > exp

    def _gc(self, key: str) -> None:
        if self._expired(key):
            self._data.pop(key, None)

    def _attach_tags(self, key: str, tags: Optional[Iterable[str]]) -> None:
        if not tags:
            return
        for t in tags:
            self._tags.setdefault(t, set()).add(key)

    def get(self, key: str) -> Optional[bytes]:
        with self._lock:
            self._gc(key)
            v = self._data.get(key)
            return v[0] if v else None

    def set(self, key: str, value: bytes, *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None) -> None:
        with self._lock:
            exp = None if ttl is None else time.time() + ttl
            self._data[key] = (value, exp)
            self._attach_tags(key, tags)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)
            for s in self._tags.values():
                s.discard(key)

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def ttl(self, key: str) -> Optional[int]:
        with self._lock:
            self._gc(key)
            v = self._data.get(key)
            if not v:
                return None
            _, exp = v
            if exp is None:
                return None
            rem = int(exp - time.time())
            return rem if rem >= 0 else 0

    def mget(self, keys: Sequence[str]) -> list[Optional[bytes]]:
        return [self.get(k) for k in keys]

    def mset(
        self, items: Mapping[str, bytes], *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None
    ) -> None:
        for k, v in items.items():
            self.set(k, v, ttl=ttl, tags=tags)

    def get_json(self, key: str) -> Optional[Any]:
        b = self.get(key)
        return None if b is None else json.loads(b)

    def set_json(
        self, key: str, value: Any, *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None
    ) -> None:
        self.set(key, json.dumps(value).encode("utf-8"), ttl=ttl, tags=tags)

    def invalidate_tags(self, tags: Iterable[str]) -> int:
        removed = 0
        with self._lock:
            for t in tags:
                keys = self._tags.pop(t, set())
                for k in keys:
                    if k in self._data:
                        self._data.pop(k, None)
                        removed += 1
        return removed

    def bump_namespace(self, namespace: str) -> int:
        with self._lock:
            self._ns_ver[namespace] = self._ns_ver.get(namespace, 0) + 1
            return self._ns_ver[namespace]

    def clear_namespace(self, namespace: str) -> int:
        with self._lock:
            keys = [k for k in self._data.keys() if k.startswith(namespace + ":")]
            for k in keys:
                self.delete(k)
            return len(keys)

    def get_or_set(self, key: str, producer, *, ttl: int, tags=None) -> bytes:
        with self._lock:
            b = self.get(key)
            if b is not None:
                return b
        val: bytes = producer()
        self.set(key, val, ttl=ttl, tags=tags)
        return val
