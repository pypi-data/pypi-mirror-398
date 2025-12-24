import json
from typing import Any, Mapping, Optional

import aio_pika
from aio_pika import ExchangeType, Message

from nlbone.core.ports.event_bus import EventBus


class RabbitMQEventBus(EventBus):
    def __init__(self, amqp_url: str, declare_passive: bool = True, exchange_type: ExchangeType = ExchangeType.DIRECT):
        self._amqp_url = amqp_url
        self._declare_passive = declare_passive
        self._exchange_type = exchange_type
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._exchange_cache: dict[str, aio_pika.Exchange] = {}

    async def _ensure_channel(self) -> aio_pika.Channel:
        if not self._connection or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(self._amqp_url)
        if not self._channel or self._channel.is_closed:
            self._channel = await self._connection.channel(publisher_confirms=True)
        return self._channel

    async def _get_exchange(self, name: str) -> aio_pika.Exchange:
        if name in self._exchange_cache:
            return self._exchange_cache[name]
        ch = await self._ensure_channel()
        if self._declare_passive:
            ex = await ch.declare_exchange(name, self._exchange_type, durable=True, passive=True)
        else:
            ex = await ch.declare_exchange(name, self._exchange_type, durable=True, passive=False)
        self._exchange_cache[name] = ex
        return ex

    async def publish(self, *, exchange: str, routing_key: str, payload: Mapping[str, Any]) -> None:
        ex = await self._get_exchange(exchange)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        msg = Message(body=body, content_type="application/json", delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
        await ex.publish(msg, routing_key=routing_key)
