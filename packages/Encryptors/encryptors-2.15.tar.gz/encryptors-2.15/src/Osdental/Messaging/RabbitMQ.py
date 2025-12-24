from typing import Any
from Osdental.Messaging import IMessageQueue

class RabbitMqQueue(IMessageQueue):

    async def enqueue(self, message: Any) -> None:
        print(f'[RabbitMQ] Queuing message: {message}')
    

    async def dequeue(self) -> Any:
        print('[RabbitMQ] Getting a message out')
        return 'Message from RabbitMQ'