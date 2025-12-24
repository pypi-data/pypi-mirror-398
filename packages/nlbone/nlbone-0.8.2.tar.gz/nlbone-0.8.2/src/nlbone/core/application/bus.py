import traceback
from typing import Any, Callable, Coroutine, List, Optional, Protocol

from nlbone.core.application.registry import AsyncHandlerRegistry, HandlerRegistry
from nlbone.core.domain.base import Command, DomainEvent, Message
from nlbone.core.ports import AsyncUnitOfWork, UnitOfWork
from nlbone.core.ports.event_bus import AsyncOutboxPublisher, OutboxPublisher
from nlbone.interfaces.api.middleware.access_log import logger


class SyncMiddleware(Protocol):
    def __call__(self, message: Message, next_: Callable[[Message], None]) -> None:  # noqa: D401
        ...


class AsyncMiddleware(Protocol):
    async def __call__(self, message: Message, next_: Callable[[Message], Coroutine[Any, Any, None]]) -> None: ...


class SyncMessageBus:
    def __init__(
        self,
        uow: UnitOfWork,
        registry: HandlerRegistry,
        middlewares: Optional[List[SyncMiddleware]] = None,
        outbox: Optional[OutboxPublisher] = None,
    ) -> None:
        self.uow = uow
        self.registry = registry
        self.middlewares = middlewares or []
        self.outbox = outbox
        self._queue: List[Message] = []

    def handle(self, message: Message) -> None:
        self._queue.append(message)
        while self._queue:
            msg = self._queue.pop(0)
            self._dispatch_with_pipeline(msg)

    # pipeline that wraps dispatch
    def _dispatch_with_pipeline(self, message: Message) -> None:
        def terminal(m: Message) -> None:
            self._dispatch(m)

        # build chain right-to-left
        next_callable = terminal
        for mw in reversed(self.middlewares):
            current_mw = mw

            def make_next(nxt: Callable[[Message], None]):  # closure helper
                def _mw_call(m: Message) -> None:
                    return current_mw(m, nxt)

                return _mw_call

            next_callable = make_next(next_callable)
        next_callable(message)

    def _dispatch(self, message: Message) -> None:
        if isinstance(message, DomainEvent):
            self._handle_event(message)
        elif isinstance(message, Command):
            self._handle_command(message)
        else:
            raise TypeError(f"Unknown message type: {type(message)!r}")

    def _handle_event(self, event: DomainEvent) -> None:
        handlers = self.registry.for_event(type(event))
        for handler in handlers:
            try:
                logger.debug("handling event %s with %s", event, handler)
                produced = handler(event)
                if produced:
                    self._queue.extend(produced)
                self._queue.extend(self.uow.collect_new_events())
            except Exception:  # noqa: BLE001
                logger.exception("Exception handling event %s\n%s", event, traceback.format_exc())
                continue

    def _handle_command(self, command: Command) -> None:
        handler = self.registry.for_command(type(command))
        try:
            logger.debug("handling command %s with %s", command, handler)
            produced = handler(command)
            if produced:
                self._queue.extend(produced)
            # commit (and gather/emit domain events)
            self._queue.extend(self.uow.collect_new_events())
            if self.outbox:
                self.outbox.publish(self._queue)  # best-effort; in real systems use a DB-backed outbox
        except Exception:  # noqa: BLE001
            logger.exception("Exception handling command %s\n%s", command, traceback.format_exc())
            raise


# ==========================
# MessageBus (async)
# ==========================
class AsyncMessageBus:
    def __init__(
        self,
        uow: AsyncUnitOfWork,
        registry: AsyncHandlerRegistry,
        middlewares: Optional[List[AsyncMiddleware]] = None,
        outbox: Optional[AsyncOutboxPublisher] = None,
    ) -> None:
        self.uow = uow
        self.registry = registry
        self.middlewares = middlewares or []
        self.outbox = outbox
        self._queue: List[Message] = []

    async def handle(self, message: Message) -> None:
        self._queue.append(message)
        while self._queue:
            msg = self._queue.pop(0)
            await self._dispatch_with_pipeline(msg)

    async def _dispatch_with_pipeline(self, message: Message) -> None:
        async def terminal(m: Message) -> None:
            await self._dispatch(m)

        next_callable = terminal
        for mw in reversed(self.middlewares):
            current_mw = mw

            def make_next(nxt: Callable[[Message], Coroutine[Any, Any, None]]):
                async def _mw_call(m: Message) -> None:
                    return await current_mw(m, nxt)

                return _mw_call

            next_callable = make_next(next_callable)
        await next_callable(message)

    async def _dispatch(self, message: Message) -> None:
        if isinstance(message, DomainEvent):
            await self._handle_event(message)
        elif isinstance(message, Command):
            await self._handle_command(message)
        else:
            raise TypeError(f"Unknown message type: {type(message)!r}")

    async def _handle_event(self, event: DomainEvent) -> None:
        handlers = self.registry.for_event(type(event))
        for handler in handlers:
            try:
                logger.debug("handling event %s with %s", event, handler)
                produced = await handler(event)
                if produced:
                    self._queue.extend(produced)
                self._queue.extend(await self.uow.collect_new_events())
            except Exception:  # noqa: BLE001
                logger.exception("Exception handling event %s\n%s", event, traceback.format_exc())
                continue

    async def _handle_command(self, command: Command) -> None:
        handler = self.registry.for_command(type(command))
        try:
            logger.debug("handling command %s with %s", command, handler)
            produced = await handler(command)
            if produced:
                self._queue.extend(produced)
            self._queue.extend(await self.uow.collect_new_events())
            if self.outbox:
                await self.outbox.publish(self._queue)
        except Exception:  # noqa: BLE001
            logger.exception("Exception handling command %s\n%s", command, traceback.format_exc())
            raise
