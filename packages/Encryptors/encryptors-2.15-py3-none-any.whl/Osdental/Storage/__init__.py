from abc import ABC, abstractmethod

class IStorageService(ABC): 

    @abstractmethod
    async def upload(self, blob_name: str, data: bytes | str) -> str | bool:
        """ Upload a file to blob storage """
        pass


    @abstractmethod
    async def download(self, blob_name: str) -> bytes | None:
        """ Download a file from blob storage """
        pass


    @abstractmethod
    async def delete(self, blob_name: str) -> bool:
        """ Delete a file from blob storage """
        pass