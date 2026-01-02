from typing import Protocol, TypeVar

InT = TypeVar("InT")
OutT = TypeVar("OutT")


class UseCase(Protocol):
    def __call__(self, command: InT) -> OutT: ...


class AsyncUseCase(Protocol):
    async def __call__(self, command: InT) -> OutT: ...
