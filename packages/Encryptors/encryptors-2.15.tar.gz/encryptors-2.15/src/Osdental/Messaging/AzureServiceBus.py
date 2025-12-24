import json
import datetime
from typing import List, Dict, Any
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import AutoLockRenewer
from Osdental.Messaging import IMessageQueue
from Osdental.Shared.Logger import logger

class AzureServiceBusQueue(IMessageQueue):

    def __init__(self, conn_str: str, queue_name: str):
        self.conn_str = conn_str
        self.queue_name = queue_name

    async def enqueue(self, message: Dict | str) -> None:
        data = json.dumps(message) if isinstance(message, dict) else message
        async with ServiceBusClient.from_connection_string(self.conn_str) as servicebus_client:
            async with servicebus_client.get_queue_sender(queue_name=self.queue_name) as sender:
                message = ServiceBusMessage(data)
                await sender.send_messages(message)


    async def dequeue(self, max_messages: int = 1) -> List[Any]:
        async with ServiceBusClient.from_connection_string(self.conn_str) as client:
            async with client.get_queue_receiver(
                queue_name=self.queue_name,
                max_wait_time=5
            ) as receiver:
                messages = await receiver.receive_messages(
                    max_message_count=max_messages
                )
                if not messages:
                    return []
                
                results = []
                async with AutoLockRenewer() as renewer:
                    for msg in messages:
                        renewer.register(
                            receiver,
                            msg,
                            max_lock_renewal_duration=datetime.timedelta(minutes=5)
                        )
                    for msg in messages:
                        try:
                            body = str(msg)
                            try:
                                body = json.loads(body)
                            except json.JSONDecodeError:
                                pass
                            results.append(body)
                            await receiver.complete_message(msg)
                        except Exception as e:
                            logger.exception("Processing message failed")
                            await receiver.abandon_message(msg)
                            
                return results