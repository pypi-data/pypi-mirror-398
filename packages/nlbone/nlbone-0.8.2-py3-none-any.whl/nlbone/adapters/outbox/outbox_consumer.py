from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager, contextmanager
from datetime import timedelta
from typing import AsyncIterator, Iterable, Iterator, Optional

from nlbone.adapters.outbox.outbox_repo import AsyncOutboxRepository, OutboxRepository
from nlbone.core.domain.models import Outbox
from nlbone.core.ports import UnitOfWork


async def outbox_stream(
    repo: AsyncOutboxRepository,
    *,
    batch_size: int = 100,
    idle_sleep: float = 1.0,
    stop_event: Optional[asyncio.Event] = None,
) -> AsyncIterator[Outbox]:
    """
    Yields Outbox one-by-one. If none available, waits (idle_sleep) and tries again.
    Designed to run forever until stop_event is set.
    """
    while True:
        if stop_event and stop_event.is_set():
            return
        batch: list[Outbox] = await repo.claim_batch(limit=batch_size)
        if not batch:
            await asyncio.sleep(idle_sleep)
            continue
        for msg in batch:
            yield msg


@asynccontextmanager
async def process_message(
    repo: AsyncOutboxRepository,
    msg: Outbox,
    *,
    backoff: timedelta = timedelta(seconds=30),
):
    """
    Usage:
        async with process_message(repo, msg):
            ... do work ...
    On success -> mark_published
    On exception -> mark_failed with backoff
    """
    try:
        yield msg
    except Exception as e:  # noqa: BLE001
        await repo.mark_failed(msg.id, str(e), backoff=backoff)
        raise
    else:
        await repo.mark_published([msg.id])


async def process_batch(
    repo: AsyncOutboxRepository,
    messages: Iterable[Outbox],
    *,
    backoff: timedelta = timedelta(seconds=30),
    concurrency: int = 1,
    handler=None,
):
    """
    Optional helper: run a handler concurrently on a batch.
    handler: async callable(msg) -> None/… ; ack/nack handled via context manager.
    """
    sem = asyncio.Semaphore(concurrency)

    async def _run(m: Outbox):
        async with sem:
            async with process_message(repo, m, backoff=backoff):
                if handler:
                    await handler(m)

    await asyncio.gather(*(_run(m) for m in messages))


def outbox_stream_sync(
    repo: OutboxRepository,
    *,
    topics: list[str] = None,
    batch_size: int = 100,
    idle_sleep: float = 1.0,
    stop_flag: Optional[callable] = None,
) -> Iterator[Outbox]:
    while True:
        if stop_flag and stop_flag():
            return
        batch = repo.claim_batch(limit=batch_size, topics=topics)
        if not batch:
            time.sleep(idle_sleep)
            continue
        for msg in batch:
            yield msg


@contextmanager
def process_message_sync(uow: UnitOfWork, msg: Outbox, *, backoff: timedelta = timedelta(seconds=30)):
    try:
        yield msg
    except Exception as e:
        uow.rollback()
        msg.mark_failed(str(e), backoff=backoff)
        uow.commit()
        raise
    else:
        msg.mark_published()
        uow.commit()
