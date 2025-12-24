from Osdental.Grpc.Client.GrpcConnection import GrpcConnection
from Osdental.Grpc.Generated import Shared_pb2_grpc, Shared_pb2
from Osdental.Models.GrpcResponse import GrpcResponse

class SharedGrpcClient:
    
    def __init__(self, connection: GrpcConnection):
        self.connection = connection
        self.stub = None

    async def _ensure_stub(self):
        if not self.stub:
            channel = await self.connection.connect()
            self.stub = Shared_pb2_grpc.ShardResourceStub(channel)

    async def call_get_shared_resources(self, id_external_enterprise: str, microservice_name: str) -> GrpcResponse:
        await self._ensure_stub()
        request = Shared_pb2.GetUserRequest(
            idExternalEnterprise=id_external_enterprise,
            microserviceName=microservice_name
        )
        response = await self.stub.GetShardResourcesByMicroservice(request)
        return GrpcResponse(
            status=response.status, 
            message=response.message, 
            data=response.data
        )

    async def call_get_shared_encryptions(self) -> GrpcResponse:
        await self._ensure_stub()
        request = Shared_pb2.EmptyRequest()
        response = await self.stub.GetShardEncryptionData(request)
        return GrpcResponse(
            status=response.status, 
            message=response.message, 
            data=response.data
        )