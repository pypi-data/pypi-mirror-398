from typing import Any, Callable, Coroutine, Dict, Iterable, List, Optional, Type, TypeVar

from nlbone.core.application.di import TypeContainer, bind_handler
from nlbone.core.domain.base import Command, DomainEvent, Message

TMsg = TypeVar("TMsg", bound=Message)
SyncHandler = Callable[[TMsg], Optional[Iterable[Message]]]
AsyncHandler = Callable[[TMsg], Coroutine[Any, Any, Optional[Iterable[Message]]]]


class HandlerRegistry:
    def __init__(self) -> None:
        self._event_handlers: Dict[Type[DomainEvent], List[SyncHandler[Any]]] = {}
        self._command_handlers: Dict[Type[Command], SyncHandler[Any]] = {}

    def register_event(self, event_type: Type[DomainEvent], handler: SyncHandler[Any]) -> None:
        self._event_handlers.setdefault(event_type, []).append(handler)

    def register_command(self, cmd_type: Type[Command], handler: SyncHandler[Any]) -> None:
        if cmd_type in self._command_handlers:
            raise ValueError(f"Command handler already registered for {cmd_type!r}")
        self._command_handlers[cmd_type] = handler

    def for_event(self, event_type: Type[DomainEvent]) -> List[SyncHandler[Any]]:
        return self._event_handlers.get(event_type, [])

    def for_command(self, cmd_type: Type[Command]) -> SyncHandler[Any]:
        try:
            return self._command_handlers[cmd_type]
        except KeyError as e:
            raise KeyError(f"No handler for command {cmd_type.__name__}") from e


class AsyncHandlerRegistry:
    def __init__(self) -> None:
        self._event_handlers: Dict[Type[DomainEvent], List[AsyncHandler[Any]]] = {}
        self._command_handlers: Dict[Type[Command], AsyncHandler[Any]] = {}

    def register_event(self, event_type: Type[DomainEvent], handler: AsyncHandler[Any]) -> None:
        self._event_handlers.setdefault(event_type, []).append(handler)

    def register_command(self, cmd_type: Type[Command], handler: AsyncHandler[Any]) -> None:
        if cmd_type in self._command_handlers:
            raise ValueError(f"Command handler already registered for {cmd_type!r}")
        self._command_handlers[cmd_type] = handler

    def for_event(self, event_type: Type[DomainEvent]) -> List[AsyncHandler[Any]]:
        return self._event_handlers.get(event_type, [])

    def for_command(self, cmd_type: Type[Command]) -> AsyncHandler[Any]:
        try:
            return self._command_handlers[cmd_type]
        except KeyError as e:
            raise KeyError(f"No handler for command {cmd_type.__name__}") from e


def handles_event(event_type: Type[DomainEvent], registry: HandlerRegistry):
    def deco(fn: SyncHandler[Any]) -> SyncHandler[Any]:
        registry.register_event(event_type, fn)
        return fn

    return deco


def handles_command(cmd_type: Type[Command], registry: HandlerRegistry):
    def deco(fn: SyncHandler[Any]) -> SyncHandler[Any]:
        registry.register_command(cmd_type, fn)
        return fn

    return deco


def handles_event_async(event_type: Type[DomainEvent], registry: AsyncHandlerRegistry):
    def deco(fn: AsyncHandler[Any]) -> AsyncHandler[Any]:
        registry.register_event(event_type, fn)
        return fn

    return deco


def handles_command_async(cmd_type: Type[Command], registry: AsyncHandlerRegistry):
    def deco(fn: AsyncHandler[Any]) -> AsyncHandler[Any]:
        registry.register_command(cmd_type, fn)
        return fn

    return deco


def make_sync_decorators(registry: HandlerRegistry, container: TypeContainer):
    def handles_command(cmd_type):
        def deco(h):
            instance_ref = {"inst": None}

            def lazy_handler(message):
                if instance_ref["inst"] is None:
                    instance_ref["inst"] = bind_handler(h, container)
                return instance_ref["inst"](message)

            registry.register_command(cmd_type, lazy_handler)
            return h

        return deco

    def handles_event(evt_type: Type[Any]):
        def deco(h: Any):
            registry.register_event(evt_type, bind_handler(h, container))
            return h

        return deco

    return handles_command, handles_event


def make_async_decorators(registry: AsyncHandlerRegistry, container: TypeContainer):
    def handles_command_async(cmd_type: Type[Any]):
        def deco(h: Any):
            registry.register_command(cmd_type, bind_handler(h, container))
            return h

        return deco

    def handles_event_async(evt_type: Type[Any]):
        def deco(h: Any):
            registry.register_event(evt_type, bind_handler(h, container))
            return h

        return deco

    return handles_command_async, handles_event_async
