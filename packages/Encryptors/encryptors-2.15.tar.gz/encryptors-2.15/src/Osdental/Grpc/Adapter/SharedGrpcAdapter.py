import json
from Osdental.Grpc.Client.SharedGrpcClient import SharedGrpcClient
from Osdental.Models.Encryptor import Encryptor
from Osdental.Models.ShardResource import ShardResource

class SharedGrpcAdapter:

    def __init__(self, client: SharedGrpcClient):
        self.client = client
    
    
    async def get_shared_encryptions(self) -> Encryptor:
        response = await self.client.call_get_shared_encryptions()
        if response.status != 200:
            raise ValueError(response.message)
        
        data_dict = json.loads(response.data)
        return Encryptor.model_validate(data_dict)
    

    async def get_shared_resources(self, id_external_enterprise: str, microservice_name: str) -> ShardResource:
        response = await self.client.call_get_shared_resources(id_external_enterprise, microservice_name)
        if response.status != 200:
            raise ValueError(response.message)
        
        data_dict = json.loads(response.data)
        return ShardResource.model_validate(data_dict)
    