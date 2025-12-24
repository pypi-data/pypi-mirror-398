import asyncio
from abc import ABC, abstractmethod
from typing import Any

from nlbone.utils.time import TimeUtility


class BaseWorker(ABC):
    def __init__(self, name, interval):
        self.name = name
        self.interval = interval

    async def run(self, *args, **kwargs):
        while True:
            try:
                print(f"[>>] {self.name} is running. Current time: {TimeUtility.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

                await self.process(*args, **kwargs)

                print(
                    f"[>>] {self.name} is sleeping. Current time: {TimeUtility.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                await asyncio.sleep(self.interval)

            except asyncio.CancelledError:
                print(f"[!!] {self.name} task was cancelled. Shutting down gracefully.\n")
                break

            except Exception as e:
                print(f"[!!]An error occurred in {self.name}:\n{str(e)}\n")
                print(f"[!!] Retrying in {self.interval / 2} seconds...\n")
                await asyncio.sleep(self.interval / 2)

    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        pass
