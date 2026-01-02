from __future__ import annotations

from abc import ABC
from typing import Any, Callable, Iterable, List, Optional, Sequence

from sqlalchemy import delete as sqla_delete
from sqlalchemy import desc as sa_desc
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from nlbone.core.ports.repository import ID, AsyncRepository, Repository, T
from nlbone.interfaces.api.exceptions import NotFoundException


# -----------------------------
# Helper utilities
# -----------------------------
def _apply_python_filters(
    items: Sequence[T],
    *,
    where: Optional[Callable[[T], bool]] = None,
    order_by: Optional[Callable[[T], object]] = None,
    reverse: bool = False,
    offset: int = 0,
    limit: Optional[int] = None,
) -> List[T]:
    data = list(items)
    if where:
        data = [x for x in data if where(x)]
    if order_by:
        data.sort(key=order_by, reverse=reverse)
    else:
        if reverse:
            data.reverse()
    if offset:
        data = data[offset:]
    if limit is not None:
        data = data[:limit]
    return data


def _has_attr_id(entity: Any) -> bool:
    return hasattr(entity, "id")


# -----------------------------
# SQLAlchemy (sync)
# -----------------------------
class SQLAlchemyRepository(Repository, ABC):
    """
    Concrete Repository[T, ID] backed by SQLAlchemy Session (sync).
    Assumes entities have an `id` attribute and are mapped.
    """

    def __init__(self, session: Session, *, autocommit: bool = False):
        self.session = session
        self.autocommit = autocommit

    def get(self, id: ID) -> Optional[T]:
        return self.session.get(self.model, id)

    def get_or_raise(self, id: ID) -> T:
        entity = self.get(id)
        if entity is None:
            raise NotFoundException(f"Entity with id={id!r} not found")
        return entity

    def list(
        self,
        *,
        offset: int = 0,
        limit: Optional[int] = None,
        where: Optional[Callable[[T], bool]] = None,
        order_by: Optional[Callable[[T], object]] = None,
        reverse: bool = False,
    ) -> List[T]:
        # If where/order_by look like SQLAlchemy expressions (not callables), push down to DB.
        if where is None and (order_by is None or callable(order_by)):
            stmt = select(self.model)
        elif callable(where) or (order_by is not None and callable(order_by)):
            # Fallback to Python-side filtering
            stmt = select(self.model)
        else:
            stmt = select(self.model).where(where)  # type: ignore[arg-type]
            if order_by is not None:
                stmt = stmt.order_by(sa_desc(order_by) if reverse else order_by)  # type: ignore[arg-type]
        if where is None and (order_by is None or not callable(order_by)):
            if offset:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)
            result = self.session.execute(stmt)
            rows = result.scalars().all()
            # If order_by was a Python callable, apply now
            if order_by is not None and callable(order_by):
                return _apply_python_filters(rows, order_by=order_by, reverse=reverse, offset=0, limit=None)
            return rows
        # Python-side filtering path
        rows = self.session.execute(select(self.model)).scalars().all()
        return _apply_python_filters(rows, where=where, order_by=order_by, reverse=reverse, offset=offset, limit=limit)

    def count(self, *, where: Optional[Callable[[T], bool]] = None) -> int:
        if where is None:
            stmt = select(func.count()).select_from(self.model)
            return self.session.execute(stmt).scalar_one()
        # Python-side when `where` is a callable
        rows = self.session.execute(select(self.model)).scalars().all()
        return sum(1 for x in rows if where(x))

    def exists(self, id: ID) -> bool:
        return self.get(id) is not None

    # --- Write ---
    def add(self, entity: T) -> T:
        if not _has_attr_id(entity):
            raise ValueError("Entity must have an `id` attribute.")
        if self.exists(getattr(entity, "id")):
            raise ValueError(f"Entity with id={getattr(entity, 'id')!r} already exists")
        self.session.add(entity)
        self.session.flush()
        if self.autocommit:
            self.session.commit()
        return entity

    def add_many(self, entities: Iterable[T]) -> List[T]:
        data = list(entities)
        for e in data:
            if not _has_attr_id(e):
                raise ValueError("All entities must have an `id` attribute.")
        # Basic duplicate check in memory (best-effort)
        ids = [getattr(e, "id") for e in data]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate IDs in input batch.")
        self.session.add_all(data)
        if self.autocommit:
            self.session.commit()
        return data

    def update(self, entity: T) -> T:
        if not _has_attr_id(entity):
            raise ValueError("Entity must have an `id` attribute.")
        id_value = getattr(entity, "id")
        if not self.exists(id_value):
            raise NotFoundException(f"Entity with id={id_value!r} not found")
        merged = self.session.merge(entity)
        if self.autocommit:
            self.session.commit()
        return merged

    def delete(self, id: ID) -> bool:
        obj = self.get(id)
        if not obj:
            return False
        self.session.delete(obj)
        if self.autocommit:
            self.session.commit()
        return True

    def clear(self) -> None:
        self.session.execute(sqla_delete(self.model))
        if self.autocommit:
            self.session.commit()


# -----------------------------
# SQLAlchemy (async)
# -----------------------------
class SQLAlchemyAsyncRepository(AsyncRepository, ABC):
    """
    Concrete AsyncRepository[T, ID] backed by SQLAlchemy AsyncSession.
    Assumes entities have an `id` attribute and are mapped.
    """

    def __init__(self, session: AsyncSession, *, autocommit: bool = True):
        self.session = session
        self.autocommit = autocommit

    # --- Read ---
    async def get(self, id: ID) -> Optional[T]:
        return await self.session.get(self.model, id)

    async def get_or_raise(self, id: ID) -> T:
        entity = await self.get(id)
        if entity is None:
            raise NotFoundException(f"Entity with id={id!r} not found")
        return entity

    async def list(
        self,
        *,
        offset: int = 0,
        limit: Optional[int] = None,
        where: Optional[Callable[[T], bool]] = None,
        order_by: Optional[Callable[[T], object]] = None,
        reverse: bool = False,
    ) -> List[T]:
        if where is None and (order_by is None or callable(order_by)):
            stmt = select(self.model)
        elif callable(where) or (order_by is not None and callable(order_by)):
            stmt = select(self.model)
        else:
            stmt = select(self.model).where(where)  # type: ignore[arg-type]
            if order_by is not None:
                stmt = stmt.order_by(sa_desc(order_by) if reverse else order_by)  # type: ignore[arg-type]
        if where is None and (order_by is None or not callable(order_by)):
            if offset:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)
            result = await self.session.execute(stmt)
            rows = result.scalars().all()
            if order_by is not None and callable(order_by):
                return _apply_python_filters(rows, order_by=order_by, reverse=reverse, offset=0, limit=None)
            return rows
        result = await self.session.execute(select(self.model))
        rows = result.scalars().all()
        return _apply_python_filters(rows, where=where, order_by=order_by, reverse=reverse, offset=offset, limit=limit)

    async def count(self, *, where: Optional[Callable[[T], bool]] = None) -> int:
        if where is None:
            stmt = select(func.count()).select_from(self.model)
            result = await self.session.execute(stmt)
            return result.scalar_one()
        result = await self.session.execute(select(self.model))
        rows = result.scalars().all()
        return sum(1 for x in rows if where(x))

    async def exists(self, id: ID) -> bool:
        return (await self.get(id)) is not None

    # --- Write ---
    async def add(self, entity: T) -> T:
        if not _has_attr_id(entity):
            raise ValueError("Entity must have an `id` attribute.")
        if await self.exists(getattr(entity, "id")):
            raise ValueError(f"Entity with id={getattr(entity, 'id')!r} already exists")
        self.session.add(entity)
        if self.autocommit:
            await self.session.commit()
        return entity

    async def add_many(self, entities: Iterable[T]) -> List[T]:
        data = list(entities)
        for e in data:
            if not _has_attr_id(e):
                raise ValueError("All entities must have an `id` attribute.")
        ids = [getattr(e, "id") for e in data]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate IDs in input batch.")
        self.session.add_all(data)
        if self.autocommit:
            await self.session.commit()
        return data

    async def update(self, entity: T) -> T:
        if not _has_attr_id(entity):
            raise ValueError("Entity must have an `id` attribute.")
        id_value = getattr(entity, "id")
        if not await self.exists(id_value):
            raise NotFoundException(f"Entity with id={id_value!r} not found")
        merged = await self.session.merge(entity)
        if self.autocommit:
            await self.session.commit()
        return merged

    async def delete(self, id: ID) -> bool:
        obj = await self.get(id)
        if not obj:
            return False
        await self.session.delete(obj)
        if self.autocommit:
            await self.session.commit()
        return True

    async def clear(self) -> None:
        await self.session.execute(sqla_delete(self.model))
        if self.autocommit:
            await self.session.commit()
