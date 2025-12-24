from typing import Any
from Osdental.Messaging import IMessageQueue

class KafkaQueue(IMessageQueue):

    async def enqueue(self, message: Any) -> None:
        print(f'[Kafka] Queuing message: {message}')
    

    async def dequeue(self) -> Any:
        print('[Kafka] Getting a message out')
        return 'Message from Kafka'