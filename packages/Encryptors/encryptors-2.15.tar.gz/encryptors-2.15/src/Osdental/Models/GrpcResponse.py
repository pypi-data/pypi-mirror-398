from typing import Optional, Any
from pydantic import BaseModel

class GrpcResponse(BaseModel):
    status: Optional[Any] = None
    message: Optional[str] = None
    data: Optional[Any] = None