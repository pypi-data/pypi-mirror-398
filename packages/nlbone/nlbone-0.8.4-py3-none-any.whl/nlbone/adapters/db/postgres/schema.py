import importlib
from typing import Sequence

from nlbone.adapters.db.postgres.base import Base
from nlbone.adapters.db.postgres.engine import init_async_engine, init_sync_engine

DEFAULT_MODEL_MODULES: Sequence[str] = ()


def import_model_modules(modules: Sequence[str] | None = None) -> None:
    for m in modules or DEFAULT_MODEL_MODULES:
        importlib.import_module(m)


# --------- Async (SQLAlchemy 2.x) ----------
async def init_db_async(model_modules: Sequence[str] | None = None) -> None:
    """Create tables using AsyncEngine (dev/test). Prefer Alembic in prod."""
    import_model_modules(model_modules)
    engine = init_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# --------- Sync ----------
def init_db_sync(model_modules: Sequence[str] | None = None) -> None:
    """Create tables using Sync Engine (dev/test). Prefer Alembic in prod."""
    import_model_modules(model_modules)
    engine = init_sync_engine()
    Base.metadata.create_all(bind=engine)
