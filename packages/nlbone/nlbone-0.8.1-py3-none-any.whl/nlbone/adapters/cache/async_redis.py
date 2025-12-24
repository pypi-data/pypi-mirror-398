import asyncio
import json
import os
from typing import Any, Iterable, Mapping, Optional, Sequence

from redis.asyncio import Redis

from nlbone.core.ports.cache import AsyncCachePort


def _nsver_key(ns: str) -> str:
    return f"nsver:{ns}"


def _tag_key(tag: str) -> str:
    return f"tag:{tag}"


class AsyncRedisCache(AsyncCachePort):
    def __init__(self, url: str, *, invalidate_channel: str | None = None):
        self._r = Redis.from_url(url, decode_responses=False)
        self._ch = invalidate_channel or os.getenv("NLBONE_REDIS_INVALIDATE_CHANNEL", "cache:invalidate")

    @property
    def redis(self) -> Redis:
        return self._r

    async def _current_ver(self, ns: str) -> int:
        v = await self._r.get(_nsver_key(ns))
        return int(v) if v else 1

    async def _full_key(self, key: str) -> str:
        try:
            ns, rest = key.split(":", 1)
        except ValueError:
            ns, rest = "app", key
        ver = await self._current_ver(ns)
        return f"{ns}:{ver}:{rest}"

    # -------- basic --------
    async def get(self, key: str) -> Optional[bytes]:
        fk = await self._full_key(key)
        return await self._r.get(fk)

    async def set(
        self, key: str, value: bytes, *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None
    ) -> None:
        fk = await self._full_key(key)
        if ttl is None:
            await self._r.set(fk, value)
        else:
            await self._r.setex(fk, ttl, value)
        if tags:
            pipe = self._r.pipeline()
            for t in tags:
                pipe.sadd(_tag_key(t), fk)
            await pipe.execute()

    async def delete(self, key: str) -> None:
        fk = await self._full_key(key)
        await self._r.delete(fk)

    async def exists(self, key: str) -> bool:
        return (await self.get(key)) is not None

    async def ttl(self, key: str) -> Optional[int]:
        fk = await self._full_key(key)
        t = await self._r.ttl(fk)
        return None if t < 0 else int(t)

        # -------- multi --------

    async def mget(self, keys: Sequence[str]) -> list[Optional[bytes]]:
        fks = [await self._full_key(k) for k in keys]
        return await self._r.mget(fks)

    async def mset(
        self, items: Mapping[str, bytes], *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None
    ) -> None:
        pipe = self._r.pipeline()
        if ttl is None:
            for k, v in items.items():
                fk = await self._full_key(k)
                pipe.set(fk, v)
        else:
            for k, v in items.items():
                fk = await self._full_key(k)
                pipe.setex(fk, ttl, v)
        await pipe.execute()

        if tags:
            pipe = self._r.pipeline()
            for t in tags:
                for k in items.keys():
                    fk = await self._full_key(k)
                    pipe.sadd(_tag_key(t), fk)
            await pipe.execute()

        # -------- json --------

    async def get_json(self, key: str) -> Optional[Any]:
        b = await self.get(key)
        return None if b is None else json.loads(b)

    async def set_json(
        self, key: str, value: Any, *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None
    ) -> None:
        await self.set(key, json.dumps(value).encode("utf-8"), ttl=ttl, tags=tags)

        # -------- invalidation --------

    async def invalidate_tags(self, tags: Iterable[str]) -> int:
        removed = 0
        pipe = self._r.pipeline()
        key_sets: list[tuple[str, set[bytes]]] = []
        for t in tags:
            tk = _tag_key(t)
            members = await self._r.smembers(tk)
            if members:
                pipe.delete(*members)
            pipe.delete(tk)
            key_sets.append((tk, members))
            removed += len(members or [])
        await pipe.execute()

        # publish notification for other processes
        try:
            payload = json.dumps({"tags": list(tags)}).encode("utf-8")
            await self._r.publish(self._ch, payload)
        except Exception:
            pass

        return removed

    async def bump_namespace(self, namespace: str) -> int:
        v = await self._r.incr(_nsver_key(namespace))
        # اطلاع‌رسانی اختیاری
        try:
            await self._r.publish(self._ch, json.dumps({"ns_bump": namespace}).encode("utf-8"))
        except Exception:
            pass
        return int(v)

    async def clear_namespace(self, namespace: str) -> int:
        cnt = 0
        cursor = 0
        pattern = f"{namespace}:*"
        while True:
            cursor, keys = await self._r.scan(cursor=cursor, match=pattern, count=1000)
            if keys:
                await self._r.delete(*keys)
                cnt += len(keys)
            if cursor == 0:
                break
        try:
            await self._r.publish(self._ch, json.dumps({"ns_clear": namespace}).encode("utf-8"))
        except Exception:
            pass
        return cnt

        # -------- dogpile-safe get_or_set --------

    async def get_or_set(self, key: str, producer, *, ttl: int, tags=None) -> bytes:
        fk = await self._full_key(key)
        val = await self._r.get(fk)
        if val is not None:
            return val

        lock_key = f"lock:{fk}"
        got = await self._r.set(lock_key, b"1", ex=10, nx=True)
        if got:
            try:
                produced = await producer() if asyncio.iscoroutinefunction(producer) else producer()
                if isinstance(produced, str):
                    produced = produced.encode("utf-8")
                await self.set(key, produced, ttl=ttl, tags=tags)
                return produced
            finally:
                await self._r.delete(lock_key)

        await asyncio.sleep(0.05)
        val2 = await self._r.get(fk)
        if val2 is not None:
            return val2
        # fallback
        produced = await producer() if asyncio.iscoroutinefunction(producer) else producer()
        if isinstance(produced, str):
            produced = produced.encode("utf-8")
        await self.set(key, produced, ttl=ttl, tags=tags)
        return produced
