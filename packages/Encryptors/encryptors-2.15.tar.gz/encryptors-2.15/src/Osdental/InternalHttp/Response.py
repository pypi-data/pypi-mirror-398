from typing import Mapping, Dict
from json import dumps
from fastapi import Response, BackgroundTasks
from Osdental.Shared.Enums.Constant import Constant
from Osdental.Shared.Instance import Instance

class CustomResponse(Response):

    def __init__(
        self, content: Dict | str | None, 
        status_code: int = 200, 
        headers: Mapping | None = None, 
        media_type: str | None = None, 
        background: BackgroundTasks | None = None, 
        batch: str | None = None 
    ):
        """ Custom Response constructor for FastAPI """
        self.content = content 
        self.batch = batch

        # Use FastAPI Response constructor for standard attributes (status_code, media_type, etc.)
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

    async def send_to_service_bus(self) -> None:
        """ Send the response to the Service Bus asynchronously """
        id_message_log = self.headers.get('Idmessagelog') 
        message_json = {
            'idMessageLog': id_message_log,
            'type': 'RESPONSE',
            'httpResponseCode': str(self.status_code),
            'messageOut': dumps(self.content) if isinstance(self.content, dict) else self.content,
            'batch': self.batch if self.batch else Constant.DEFAULT_EMPTY_VALUE,
            'errorProducer': Constant.DEFAULT_EMPTY_VALUE,
            'auditLog': Constant.MESSAGE_LOG_INTERNAL
        }
        await Instance.sb_audit.enqueue(message_json)
