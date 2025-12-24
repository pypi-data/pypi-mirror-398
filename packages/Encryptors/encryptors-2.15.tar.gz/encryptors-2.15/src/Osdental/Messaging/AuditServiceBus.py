import json
from typing import Dict
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage


class AuditServiceBus:

    def __init__(self, conn_str: str, queue_name: str):
        self.conn_str = conn_str
        self.queue_name = queue_name


    async def enqueue(self, message: Dict) -> None:
        if isinstance(message, dict):
            if "idMessageLog" not in message:
                raise ValueError("idMessageLog is required for Service Bus Sessions")

            session_id = str(message["idMessageLog"])
            body = json.dumps(message)
        else:
            raise ValueError("Message must be a dict to support sessions")

        async with ServiceBusClient.from_connection_string(self.conn_str) as client:
            async with client.get_queue_sender(queue_name=self.queue_name) as sender:
                msg = ServiceBusMessage(
                    body=body,
                    session_id=session_id,
                    content_type="application/json"
                )
                await sender.send_messages(msg)
