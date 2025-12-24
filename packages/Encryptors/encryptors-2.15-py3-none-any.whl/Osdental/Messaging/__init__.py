from abc import ABC, abstractmethod
from typing import Any

class IMessageQueue(ABC):

    @abstractmethod
    async def enqueue(self, message: Any) -> None:
        pass

    @abstractmethod
    async def dequeue(self) -> Any:
        pass