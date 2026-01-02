from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy import (
    delete,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from nlbone.core.domain.models import Outbox, OutboxStatus
from nlbone.core.ports.outbox import AsyncOutboxRepository, OutboxRepository


class SQLAlchemyOutboxRepository(OutboxRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def enqueue(self, topic: str, payload: Dict[str, Any], *, headers=None, key=None, available_at=None) -> Outbox:
        row = Outbox(
            topic=topic,
            payload=payload,
            headers=headers or {},
            key=key,
            available_at=available_at or self._now(),
        )
        self.session.add(row)
        # Do not commit here; caller's transaction should commit
        self.session.flush()
        return row

    def enqueue_many(
        self, items: Iterable[Tuple[str, Dict[str, Any]]], *, headers=None, available_at=None
    ) -> List[Outbox]:
        rows = [
            Outbox(topic=t, payload=p, headers=headers or {}, available_at=available_at or self._now())
            for t, p in items
        ]
        self.session.add_all(rows)
        self.session.flush()
        return [r for r in rows]

    def claim_batch(
        self, *, topics: list[str] = None, limit: int = 100, now: Optional[datetime] = None
    ) -> List[Outbox]:
        now = now or self._now()
        # Select candidates eligible to process
        stmt = (
            select(Outbox)
            .where(
                Outbox.topic.in_(topics),
                Outbox.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]),
                Outbox.available_at <= now,
                (Outbox.next_attempt_at.is_(None)) | (Outbox.next_attempt_at <= now),
            )
            .order_by(Outbox.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        rows = self.session.execute(stmt).scalars().all()
        if not rows:
            return []
        # Mark as PROCESSING and increment attempts
        ids = [r.id for r in rows]
        self.session.execute(
            update(Outbox)
            .where(Outbox.id.in_(ids))
            .values(status=OutboxStatus.PROCESSING, attempts=Outbox.attempts + 1)
        )
        self.session.flush()
        return [r for r in rows]

    def mark_published(self, ids: Iterable[int]) -> None:
        ids = list(ids)
        if not ids:
            return
        self.session.execute(
            update(Outbox)
            .where(Outbox.id.in_(ids))
            .values(status=OutboxStatus.PUBLISHED, last_error=None, next_attempt_at=None)
        )

    def mark_failed(self, id: int, error: str, *, backoff: timedelta = timedelta(seconds=30)) -> None:
        self.session.execute(
            update(Outbox)
            .where(Outbox.id == id)
            .values(
                status=OutboxStatus.FAILED,
                last_error=error,
                next_attempt_at=self._now() + backoff,
            )
        )

    def delete_older_than(self, *, before: datetime, status: Optional[OutboxStatus] = None) -> int:
        conds = [Outbox.created_at < before]
        if status is not None:
            conds.append(Outbox.status == status)
        stmt = delete(Outbox).where(*conds)
        res = self.session.execute(stmt)
        return res.rowcount or 0


class SQLAlchemyAsyncOutboxRepository(AsyncOutboxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def enqueue(
        self, topic: str, payload: Dict[str, Any], *, headers=None, key=None, available_at=None
    ) -> Outbox:
        row = Outbox(
            topic=topic,
            payload=payload,
            headers=headers or {},
            key=key,
            available_at=available_at or self._now(),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def enqueue_many(
        self, items: Iterable[Tuple[str, Dict[str, Any]]], *, headers=None, available_at=None
    ) -> List[Outbox]:
        rows = [
            Outbox(topic=t, payload=p, headers=headers or {}, available_at=available_at or self._now())
            for t, p in items
        ]
        self.session.add_all(rows)
        await self.session.flush()
        return [r for r in rows]

    async def claim_batch(self, *, limit: int = 100, now: Optional[datetime] = None) -> List[Outbox]:
        now = now or self._now()
        stmt = (
            select(Outbox)
            .where(
                Outbox.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]),
                Outbox.available_at <= now,
                (Outbox.next_attempt_at.is_(None)) | (Outbox.next_attempt_at <= now),
            )
            .order_by(Outbox.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        if not rows:
            return []
        ids = [r.id for r in rows]
        await self.session.execute(
            update(Outbox)
            .where(Outbox.id.in_(ids))
            .values(status=OutboxStatus.PROCESSING, attempts=Outbox.attempts + 1)
        )
        await self.session.flush()
        return [r.to_domain() for r in rows]

    async def mark_published(self, ids: Iterable[int]) -> None:
        ids = list(ids)
        if not ids:
            return
        await self.session.execute(
            update(Outbox)
            .where(Outbox.id.in_(ids))
            .values(status=OutboxStatus.PUBLISHED, last_error=None, next_attempt_at=None)
        )

    async def mark_failed(self, id: int, error: str, *, backoff: timedelta = timedelta(seconds=30)) -> None:
        await self.session.execute(
            update(Outbox)
            .where(Outbox.id == id)
            .values(
                status=OutboxStatus.FAILED,
                last_error=error,
                next_attempt_at=self._now() + backoff,
            )
        )

    async def delete_older_than(self, *, before: datetime, status: Optional[OutboxStatus] = None) -> int:
        conds = [Outbox.created_at < before]
        if status is not None:
            conds.append(Outbox.status == status)
        res = await self.session.execute(delete(Outbox).where(*conds))
        return res.rowcount or 0
