import grpc
from typing import Optional

class GrpcConnection:
    
    def __init__(self, host: str, secure: bool = True):
        self.host = host
        self.secure = secure
        self._channel: Optional[grpc.aio.Channel] = None

    async def connect(self):
        if not self._channel:
            if self.secure:
                creds = grpc.ssl_channel_credentials()
                self._channel = grpc.aio.secure_channel(self.host, creds)
            else:
                self._channel = grpc.aio.insecure_channel(self.host)

        return self._channel
    
    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
