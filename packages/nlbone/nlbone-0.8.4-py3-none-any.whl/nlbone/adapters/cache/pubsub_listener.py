from __future__ import annotations

import asyncio
import json
from typing import Awaitable, Callable, Optional

from redis.asyncio import Redis


async def run_cache_invalidation_listener(
    redis: Redis,
    channel: str = "cache:invalidate",
    *,
    on_tags: Optional[Callable[[list[str]], Awaitable[None]]] = None,
    on_ns_bump: Optional[Callable[[str], Awaitable[None]]] = None,
    on_ns_clear: Optional[Callable[[str], Awaitable[None]]] = None,
    stop_event: Optional[asyncio.Event] = None,
) -> None:
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    try:
        while True:
            if stop_event and stop_event.is_set():
                break
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if not message:
                await asyncio.sleep(0.05)
                continue
            try:
                data = json.loads(message["data"])
            except Exception:
                continue

            if "tags" in data and on_tags:
                tags = data.get("tags") or []
                await on_tags(list(tags))
            if "ns_bump" in data and on_ns_bump:
                await on_ns_bump(str(data["ns_bump"]))
            if "ns_clear" in data and on_ns_clear:
                await on_ns_clear(str(data["ns_clear"]))
    finally:
        try:
            await pubsub.unsubscribe(channel)
        finally:
            await pubsub.close()
