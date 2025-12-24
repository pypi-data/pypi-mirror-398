from __future__ import annotations

from collections.abc import Iterator
from typing import AsyncIterator

from fastapi import Request

from nlbone.adapters.db.postgres import AsyncSqlAlchemyUnitOfWork
from nlbone.core.ports.uow import AsyncUnitOfWork, UnitOfWork


def get_uow(request: Request) -> Iterator[UnitOfWork]:
    """
    Uses DI container mounted at app.state.container to create a UoW per request.
    Assumes container.uow is a provider returning SqlAlchemyUnitOfWork(session_factory).
    """
    container = getattr(request.app.state, "container", None)
    if container is None or not hasattr(container, "uow"):
        raise RuntimeError("Container with 'uow' provider not configured on app.state.container")

    uow = container.uow()
    with uow as _uow:
        yield _uow


async def get_async_uow(request: Request) -> AsyncIterator[AsyncUnitOfWork]:
    container = getattr(request.app.state, "container", None)
    if container is None or not hasattr(container, "async_uow"):
        raise RuntimeError("Container.async_uow provider not configured")
    uow: AsyncSqlAlchemyUnitOfWork = container.async_uow()
    async with uow as _uow:
        yield _uow
