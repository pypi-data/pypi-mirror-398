from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    Iterable,
    List,
    Optional,
    Type,
    TypeVar,
)

from nlbone.core.domain.base import AggregateRoot
from nlbone.interfaces.api.exceptions import NotFoundException

ID = TypeVar("ID")
T = TypeVar("T")


class Repository(Generic[T, ID], ABC):
    model: ClassVar[Type[Any]]
    seen: set[AggregateRoot] = set()

    @abstractmethod
    def get(self, id: ID) -> Optional[T]: ...

    def get_or_raise(self, id: ID) -> T:
        ...
        entity = self.get(id)
        if entity is None:
            raise NotFoundException(f"Entity with id={id!r} not found")
        return entity

    @abstractmethod
    def list(
        self,
        *,
        offset: int = 0,
        limit: Optional[int] = None,
        where: Optional[Callable[[T], bool]] = None,
        order_by: Optional[Callable[[T], object]] = None,
        reverse: bool = False,
    ) -> List[T]: ...

    @abstractmethod
    def count(self, *, where: Optional[Callable[[T], bool]] = None) -> int: ...

    @abstractmethod
    def exists(self, id: ID) -> bool: ...

    # --- Write ---
    @abstractmethod
    def add(self, entity: T) -> T: ...

    @abstractmethod
    def add_many(self, entities: Iterable[T]) -> List[T]: ...

    @abstractmethod
    def update(self, entity: T) -> T: ...

    @abstractmethod
    def delete(self, id: ID) -> bool: ...

    @abstractmethod
    def clear(self) -> None: ...


# -----------------------------
# Async Repository (Abstract)
# -----------------------------
class AsyncRepository(Generic[T, ID], ABC):
    model: ClassVar[Type[Any]]
    seen: set[AggregateRoot] = set()

    @abstractmethod
    async def get(self, id: ID) -> Optional[T]: ...

    async def get_or_raise(self, id: ID) -> T:
        entity = await self.get(id)
        if entity is None:
            raise NotFoundException(f"Entity with id={id!r} not found")
        return entity

    @abstractmethod
    async def list(
        self,
        *,
        offset: int = 0,
        limit: Optional[int] = None,
        where: Optional[Callable[[T], bool]] = None,
        order_by: Optional[Callable[[T], object]] = None,
        reverse: bool = False,
    ) -> List[T]: ...

    @abstractmethod
    async def count(self, *, where: Optional[Callable[[T], bool]] = None) -> int: ...

    @abstractmethod
    async def exists(self, id: ID) -> bool: ...

    # --- Write ---
    @abstractmethod
    async def add(self, entity: T) -> T: ...

    @abstractmethod
    async def add_many(self, entities: Iterable[T]) -> List[T]: ...

    @abstractmethod
    async def update(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, id: ID) -> bool: ...

    @abstractmethod
    async def clear(self) -> None: ...
