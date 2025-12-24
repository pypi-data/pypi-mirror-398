from __future__ import annotations

from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from nlbone.adapters.db.postgres.engine import async_session, sync_session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as s:
        yield s


def get_session() -> Generator[Session, None, None]:
    with sync_session() as s:
        yield s
