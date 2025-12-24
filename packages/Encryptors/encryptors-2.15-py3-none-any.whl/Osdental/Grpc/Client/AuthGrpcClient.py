from Osdental.Models.GrpcResponse import GrpcResponse
from Osdental.Grpc.Client.GrpcConnection import GrpcConnection
from Osdental.Decorators.Retry import grpc_retry
from Osdental.Grpc.Generated import Auth_pb2_grpc, Auth_pb2


class AuthGrpcClient:

    def __init__(self, connection: GrpcConnection):
        self.connection = connection
        self.stub = None

    async def _ensure_stub(self):
        if not self.stub:
            channel = await self.connection.connect()
            self.stub = Auth_pb2_grpc.AuthStub(channel)


    @grpc_retry
    async def call_validate_auth_token(self, data: str) -> GrpcResponse:
        await self._ensure_stub()
        request = Auth_pb2.AuthTokenRequest(data=data)
        response = await self.stub.ValidateAuthToken(request)
        return GrpcResponse(
            status=response.status, 
            message=response.message, 
            data=response.data
        )
