from contextvars import ContextVar
from typing import Callable, Optional, TypeVar

T = TypeVar("T")

_global_resolver: Optional[Callable[[], T]] = None

_ctx_resolver: ContextVar[Optional[Callable[[], T]]] = ContextVar("_ctx_resolver", default=None)


def set_cache_resolver(fn: Callable[[], T]) -> None:
    """Set process-wide cache resolver (e.g., lambda: container.cache())."""
    global _global_resolver
    _global_resolver = fn


def set_context_cache_resolver(fn: Optional[Callable[[], T]]) -> None:
    """Override resolver in current context (useful in tests/background tasks)."""
    _ctx_resolver.set(fn)


def get_cache() -> T:
    fn = _ctx_resolver.get() or _global_resolver
    return fn()
