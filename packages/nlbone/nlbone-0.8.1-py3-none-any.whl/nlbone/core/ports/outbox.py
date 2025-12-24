from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Protocol, Tuple

from nlbone.core.domain.models import Outbox, OutboxStatus


class OutboxRepository(Protocol):
    def enqueue(
        self,
        topic: str,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, Any]] = None,
        key: Optional[str] = None,
        available_at: Optional[datetime] = None,
    ) -> Outbox: ...

    def enqueue_many(
        self,
        items: Iterable[Tuple[str, Dict[str, Any]]],
        *,
        headers: Optional[Dict[str, Any]] = None,
        available_at: Optional[datetime] = None,
    ) -> List[Outbox]: ...

    def claim_batch(
        self,
        *,
        topics: list[str] = None,
        limit: int = 100,
        now: Optional[datetime] = None,
    ) -> List[Outbox]: ...

    def mark_published(self, ids: Iterable[int]) -> None: ...

    def mark_failed(self, id: int, error: str, *, backoff: timedelta = timedelta(seconds=30)) -> None: ...

    def delete_older_than(self, *, before: datetime, status: Optional[OutboxStatus] = None) -> int: ...


class AsyncOutboxRepository(Protocol):
    async def enqueue(
        self,
        topic: str,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, Any]] = None,
        key: Optional[str] = None,
        available_at: Optional[datetime] = None,
    ) -> Outbox: ...

    async def enqueue_many(
        self,
        items: Iterable[Tuple[str, Dict[str, Any]]],
        *,
        headers: Optional[Dict[str, Any]] = None,
        available_at: Optional[datetime] = None,
    ) -> List[Outbox]: ...

    async def claim_batch(
        self,
        *,
        limit: int = 100,
        now: Optional[datetime] = None,
    ) -> List[Outbox]: ...

    async def mark_published(self, ids: Iterable[int]) -> None: ...

    async def mark_failed(self, id: int, error: str, *, backoff: timedelta = timedelta(seconds=30)) -> None: ...

    async def delete_older_than(self, *, before: datetime, status: Optional[OutboxStatus] = None) -> int: ...
