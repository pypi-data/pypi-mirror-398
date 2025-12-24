import json
from Osdental.Grpc.Client.AuthGrpcClient import AuthGrpcClient

class AuthGrpcAdapter:

    def __init__(self, client: AuthGrpcClient):
        self.client = client


    async def validate_auth_token(self, data: str) -> bool:
        response = await self.client.call_validate_auth_token(data)
        if response.status != 200:
            raise ValueError(response.message)
        
        return response.data