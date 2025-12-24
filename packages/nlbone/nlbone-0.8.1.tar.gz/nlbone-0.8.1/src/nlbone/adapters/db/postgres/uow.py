from __future__ import annotations

from typing import AsyncIterator, Iterator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from nlbone.adapters.outbox.outbox_repo import SQLAlchemyAsyncOutboxRepository, SQLAlchemyOutboxRepository
from nlbone.core.domain.base import DomainEvent
from nlbone.core.ports.repository import AsyncRepository, Repository
from nlbone.core.ports.uow import AsyncUnitOfWork as AsyncUnitOfWorkPort
from nlbone.core.ports.uow import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    """sync UoW for SQLAlchemy."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.outbox_repo = SQLAlchemyOutboxRepository(self.session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            if self.session is not None:
                self.session.close()
                self.session = None

    def commit(self) -> None:
        if self.session:
            self.session.commit()
        # if self.event_bus:
        #     for obj in self.session:
        #         events = getattr(obj, "events", None)
        #         if events:
        #             for evt in list(events):
        #                 self.event_bus.publish(evt)
        #             obj.clear_events()

    def rollback(self) -> None:
        if self.session:
            self.session.rollback()

    def collect_new_events(self) -> Iterator[DomainEvent]:
        for name, type_ in self.__annotations__.items():
            if isinstance(type_, type) and issubclass(type_, Repository):
                repo = getattr(self, name, None)
                if not repo:
                    continue
                for entity in repo.seen:
                    for event in entity.events:
                        yield event


class AsyncSqlAlchemyUnitOfWork(AsyncUnitOfWorkPort):
    """Transactional boundary for async SQLAlchemy."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> "AsyncSqlAlchemyUnitOfWork":
        self.session = self._sf()
        self.outbox_repo = SQLAlchemyAsyncOutboxRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
        finally:
            if self.session is not None:
                await self.session.close()
                self.session = None

    async def commit(self) -> None:
        if self.session:
            await self.session.commit()
        if self.event_bus:
            for obj in self.session:
                events = getattr(obj, "events", None)
                if events:
                    for evt in list(events):
                        self.event_bus.publish(evt)
                    obj.clear_events()

    async def rollback(self) -> None:
        if self.session:
            await self.session.rollback()

    async def collect_new_events(self) -> AsyncIterator[DomainEvent]:
        for name, type_ in self.__annotations__.items():
            if isinstance(type_, type) and issubclass(type_, AsyncRepository):
                repo = getattr(self, name)
                for entity in repo.seen:
                    for event in entity.events:
                        yield event
