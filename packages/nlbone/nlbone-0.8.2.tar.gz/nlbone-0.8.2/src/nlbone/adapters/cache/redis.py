from __future__ import annotations

import json
import os
import time
from typing import Any, Iterable, Mapping, Optional, Sequence

import redis  # redis-py (sync)

from nlbone.core.ports.cache import CachePort


def _nsver_key(ns: str) -> str:
    return f"nsver:{ns}"


def _tag_key(tag: str) -> str:
    return f"tag:{tag}"


class RedisCache(CachePort):
    def __init__(self, url: str):
        self.r = redis.Redis.from_url(url, decode_responses=False)

    def _current_ver(self, ns: str) -> int:
        v = self.r.get(_nsver_key(ns))
        return int(v) if v else 1

    def _full_key(self, key: str) -> str:
        try:
            ns, rest = key.split(":", 1)
        except ValueError:
            ns, rest = "app", key
        ver = self._current_ver(ns)
        return f"{ns}:{ver}:{rest}"

    def get(self, key: str) -> Optional[bytes]:
        fk = self._full_key(key)
        return self.r.get(fk)

    def set(self, key: str, value: bytes, *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None) -> None:
        fk = self._full_key(key)
        if ttl is None:
            self.r.set(fk, value)
        else:
            self.r.setex(fk, ttl, value)
        if tags:
            pipe = self.r.pipeline()
            for t in tags:
                pipe.sadd(_tag_key(t), fk)
            pipe.execute()

    def delete(self, key: str) -> None:
        fk = self._full_key(key)
        self.r.delete(fk)

    def exists(self, key: str) -> bool:
        return bool(self.get(key))

    def ttl(self, key: str) -> Optional[int]:
        fk = self._full_key(key)
        t = self.r.ttl(fk)
        return None if t < 0 else int(t)

    def mget(self, keys: Sequence[str]) -> list[Optional[bytes]]:
        fks = [self._full_key(k) for k in keys]
        return self.r.mget(fks)

    def mset(
        self, items: Mapping[str, bytes], *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None
    ) -> None:
        pipe = self.r.pipeline()
        if ttl is None:
            for k, v in items.items():
                pipe.set(self._full_key(k), v)
        else:
            for k, v in items.items():
                pipe.setex(self._full_key(k), ttl, v)
        pipe.execute()
        if tags:
            pipe = self.r.pipeline()
            for t in tags:
                for k in items.keys():
                    pipe.sadd(_tag_key(t), self._full_key(k))
            pipe.execute()

    def get_json(self, key: str) -> Optional[Any]:
        b = self.get(key)
        return None if b is None else json.loads(b)

    def set_json(
        self, key: str, value: Any, *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None
    ) -> None:
        self.set(key, json.dumps(value).encode("utf-8"), ttl=ttl, tags=tags)

    def invalidate_tags(self, tags: Iterable[str]) -> int:
        removed = 0
        pipe = self.r.pipeline()
        for t in tags:
            tk = _tag_key(t)
            keys = self.r.smembers(tk)
            if keys:
                pipe.delete(*keys)
            pipe.delete(tk)
            removed += len(keys or [])
        pipe.execute()
        try:
            ch = os.getenv("NLBONE_REDIS_INVALIDATE_CHANNEL", "cache:invalidate")
            self.r.publish(ch, json.dumps({"tags": list(tags)}).encode("utf-8"))
        except Exception:
            pass
        return removed

    def bump_namespace(self, namespace: str) -> int:
        v = self.r.incr(_nsver_key(namespace))
        return int(v)

    def clear_namespace(self, namespace: str) -> int:
        cnt = 0
        cursor = 0
        pattern = f"{namespace}:*"
        while True:
            cursor, keys = self.r.scan(cursor=cursor, match=pattern, count=1000)
            if keys:
                self.r.delete(*keys)
                cnt += len(keys)
            if cursor == 0:
                break
        return cnt

    def get_or_set(self, key: str, producer, *, ttl: int, tags=None) -> bytes:
        fk = self._full_key(key)
        val = self.r.get(fk)
        if val is not None:
            return val
        lock_key = f"lock:{fk}"
        got = self.r.set(lock_key, b"1", nx=True, ex=10)
        if got:
            try:
                produced: bytes = producer()
                self.set(key, produced, ttl=ttl, tags=tags)
                return produced
            finally:
                self.r.delete(lock_key)
        time.sleep(0.05)
        val2 = self.r.get(fk)
        if val2 is not None:
            return val2
        produced: bytes = producer()
        self.set(key, produced, ttl=ttl, tags=tags)
        return produced
