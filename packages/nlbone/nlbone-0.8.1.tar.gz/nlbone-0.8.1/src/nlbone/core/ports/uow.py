from __future__ import annotations

from typing import AsyncIterator, Iterator, Protocol, runtime_checkable

from nlbone.core.domain.base import DomainEvent
from nlbone.core.ports.outbox import AsyncOutboxRepository, OutboxRepository


@runtime_checkable
class UnitOfWork(Protocol):
    outbox: list
    outbox_repo: OutboxRepository

    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type, exc, tb) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def collect_new_events(self) -> Iterator[DomainEvent]: ...


@runtime_checkable
class AsyncUnitOfWork(Protocol):
    outbox: list
    outbox_repo: AsyncOutboxRepository

    async def __aenter__(self) -> "AsyncUnitOfWork": ...

    async def __aexit__(self, exc_type, exc, tb) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def collect_new_events(self) -> AsyncIterator[DomainEvent]: ...
