from typing import Optional

from pydantic import BaseModel

from nlbone.adapters.messaging.rabbitmq import RabbitMQEventBus
from nlbone.config.settings import get_settings


class CreateTicketIn(BaseModel):
    assignee_id: str | None = None
    category_id: int
    channel: str
    direction: str
    entity_id: str
    entity_type: str
    message: str
    priority: str
    product_id: int
    status: str
    title: str
    user_id: int


class TicketingClient:
    def __init__(self):
        settings = get_settings()
        self._bus = RabbitMQEventBus(settings.RABBITMQ_URL)
        self._exchange = settings.RABBITMQ_TICKETING_EXCHANGE
        self._rk_create_v1 = settings.RABBITMQ_TICKETING_ROUTING_KEY_CREATE_V1

    async def create_ticket(
        self,
        payload: CreateTicketIn,
        created_by_id: int,
        *,
        override_exchange: Optional[str] = None,
        override_routing_key: Optional[str] = None,
    ) -> None:
        exchange = override_exchange or self._exchange
        routing_key = override_routing_key or self._rk_create_v1
        payload = payload.model_dump()
        payload.update({"created_by_id": created_by_id})
        print(payload)
        await self._bus.publish(exchange=exchange, routing_key=routing_key, payload=payload)
