from typing import Optional, Any
from pydantic import BaseModel
from Osdental.Shared.Enums.Code import Code
from Osdental.Shared.Enums.Message import Message

class Response(BaseModel):
    status: str = Code.PROCESS_SUCCESS_CODE
    message: str = Message.PROCESS_SUCCESS_MSG
    data: Optional[Any] = None 


    def send(self):
        return self.model_dump()