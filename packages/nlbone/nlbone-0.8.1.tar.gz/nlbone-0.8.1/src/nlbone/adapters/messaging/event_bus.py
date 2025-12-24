import asyncio
import json
import time
from typing import Callable, Dict, Iterable, List, Type

import redis

from nlbone.core.domain.base import DomainEvent
from nlbone.core.domain.models import Outbox
from nlbone.core.ports.event_bus import EventBus, EventHandler


class InProcessEventBus(EventBus):
    def __init__(self) -> None:
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}

    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        handlers = list(self._handlers.get(type(event), []))
        loop = None
        for h in handlers:
            res = h(event)
            if asyncio.iscoroutine(res):
                loop = loop or asyncio.get_event_loop()
                loop.create_task(res)


class OutboxDispatcher:
    def __init__(self, session_factory, event_bus: EventBus, batch_size: int = 100):
        self._sf = session_factory
        self._bus = event_bus
        self._batch = batch_size

    def run_once(self) -> int:
        sent = 0
        with self._sf() as s:  # type: Session
            rows: Iterable[Outbox] = (
                s.query(Outbox).filter_by(published=False).order_by(Outbox.occurred_at).limit(self._batch).all()
            )
            for r in rows:
                self._bus.publish(type("OutboxEvent", (), r.payload))
                r.published = True
                sent += 1
            s.commit()
        return sent


class RedisStreamsEventBus(EventBus):
    """Topic = stream name. routing_key = event.type"""

    def __init__(self, client: redis.Redis, stream: str = "nlb:domain:events"):
        self.client = client
        self.stream = stream
        self._local_handlers: dict[type[DomainEvent], list[EventHandler]] = {}

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        self._local_handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        self.client.xadd(
            self.stream,
            {
                "type": event.type,
                "payload": json.dumps(event.__dict__, default=str),
            },
            maxlen=10_000,
            approximate=True,
        )
        # optional: local handlers in same process (choreography ترکیبی)
        for h in self._local_handlers.get(type(event), []):
            h(event)


class RedisStreamsConsumer:
    def __init__(self, client: redis.Redis, stream: str, group: str, consumer: str, dlq: str | None = None):
        self.client = client
        self.stream = stream
        self.group = group
        self.consumer = consumer
        self.dlq = dlq or f"{stream}:dlq"

        try:
            self.client.xgroup_create(name=self.stream, groupname=self.group, id="$", mkstream=True)
        except redis.ResponseError:
            pass  # group exists

    def consume_forever(self, handler: Callable[[dict], None], block_ms: int = 2000, count: int = 32):
        while True:
            resp = self.client.xreadgroup(self.group, self.consumer, {self.stream: ">"}, count=count, block=block_ms)
            if not resp:
                continue
            for _stream, messages in resp:
                for msg_id, fields in messages:
                    try:
                        payload = json.loads(fields[b"payload"].decode())
                        handler(payload)
                        self.client.xack(self.stream, self.group, msg_id)
                    except Exception:
                        self.client.xack(self.stream, self.group, msg_id)
                        self.client.xadd(self.dlq, fields)
            time.sleep(0.05)
