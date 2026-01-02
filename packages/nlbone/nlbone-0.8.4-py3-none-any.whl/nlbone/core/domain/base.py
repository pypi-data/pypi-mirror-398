from __future__ import annotations

from _decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, ClassVar, Generic, List, TypeVar
from uuid import uuid4

from nlbone.adapters.snowflake import SNOWFLAKE

TId = TypeVar("TId")


class DomainError(Exception):
    """Base domain exception."""


class Message:
    pass


class DomainEvent(Message):
    """Immutable domain event."""

    occurred_at: datetime = datetime.now(timezone.utc)
    event_id: str = uuid4()

    @property
    def name(self):
        return self.__class__.__name__

    def model_dump(self):
        d = self.__dict__
        for k, v in d.items():
            if isinstance(v, BaseId):
                d[k] = v.value
            elif isinstance(v, Decimal):
                d[k] = str(v)
        return d


@dataclass(frozen=True)
class Command:
    pass


class ValueObject:
    """Base for value objects (immutable in practice)."""

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __hash__(self) -> int:  # allow in sets/dicts
        return hash(tuple(sorted(self.__dict__.items())))


class Entity(Generic[TId]):
    id: TId


class AggregateRoot(Entity[TId]):
    """Aggregate root with domain event collection."""

    def __init__(self) -> None:
        self._events: List[DomainEvent] = []

    @property
    def events(self) -> List[DomainEvent]:
        return self._events

    def _raise(self, event: DomainEvent) -> None:
        self._events.append(event)

    def clear_events(self) -> None:
        self._events.clear()


class BaseEnum(Enum):
    pass


ID = TypeVar("ID", bound="BaseId")


@dataclass(frozen=True)
class BaseId(ValueObject):
    value: int

    _generator: ClassVar[Callable[[], int]] = lambda: SNOWFLAKE.next_id()

    def __post_init__(self):
        if not isinstance(self.value, int):
            raise TypeError("BaseId.value must be int")
        if self.value <= 0:
            raise ValueError("BaseId must be a positive integer")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def set_generator(cls, gen: Callable[[], int]) -> None:
        cls._generator = gen

    @classmethod
    def new(cls: type[ID]) -> ID:
        return cls(cls._generator())

    @classmethod
    def from_int(cls: type[ID], v: int) -> ID:
        return cls(v)

    def __repr__(self):
        return f"<{self.value}>"
