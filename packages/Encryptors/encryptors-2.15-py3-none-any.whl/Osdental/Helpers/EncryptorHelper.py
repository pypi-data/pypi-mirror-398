import asyncio
from Osdental.Models.Encryptor import Encryptor
from Osdental.Shared.Instance import Instance


class EncryptorHelper:

    _GRPC_ENCRYPTOR_CACHE = {"value": None, "timestamp": 0}
    _GRPC_LOCK = asyncio.Lock()
    
    @staticmethod
    async def get_cached_encryptors() -> Encryptor:
        """Cache the encryptors for X seconds to avoid GRPC calls on every resolver."""
        
        if EncryptorHelper._GRPC_ENCRYPTOR_CACHE["value"] is not None:
            return EncryptorHelper._GRPC_ENCRYPTOR_CACHE["value"]

        async with EncryptorHelper._GRPC_LOCK:
            if EncryptorHelper._GRPC_ENCRYPTOR_CACHE["value"] is not None:
                return EncryptorHelper._GRPC_ENCRYPTOR_CACHE["value"]

            encryptor = await Instance.grpc_shared_adapter.get_shared_encryptions()
            EncryptorHelper._GRPC_ENCRYPTOR_CACHE["value"] = encryptor
            return encryptor