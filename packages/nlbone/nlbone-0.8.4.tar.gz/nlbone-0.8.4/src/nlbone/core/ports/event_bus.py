from typing import Any, Awaitable, Callable, Iterable, Protocol, Type, runtime_checkable

from nlbone.core.domain.base import DomainEvent, Message

EventHandler = Callable[[DomainEvent], Any] | Callable[[DomainEvent], Awaitable[Any]]


class EventBus(Protocol):
    def subscribe(self, event_type: Type[DomainEvent] | str, handler: EventHandler) -> None: ...

    def publish(self, event: DomainEvent) -> None: ...


class EventPublisher(Protocol):
    def publish(self, event: DomainEvent) -> None: ...


@runtime_checkable
class OutboxPublisher(Protocol):
    """Optional: publish integration messages reliably after commit."""

    def publish(self, messages: Iterable[Message]) -> None: ...


@runtime_checkable
class AsyncOutboxPublisher(Protocol):
    async def publish(self, messages: Iterable[Message]) -> None: ...
