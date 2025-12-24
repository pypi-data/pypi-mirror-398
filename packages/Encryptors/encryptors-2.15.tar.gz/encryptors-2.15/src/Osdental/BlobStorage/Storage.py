from azure.storage.blob.aio import BlobServiceClient
from Osdental.Shared.Logger import logger
from Osdental.Shared.Config import Config
from Osdental.Decorators.Deprecated import deprecated

@deprecated("Replaced class, use Osdental.Storage.. and implement its port")
class BlobStorage: 

    @staticmethod
    async def get_file(file_path:str) -> bytes | None:
        """ Download a file from blob storage """
        try:
            blob_service_client = BlobServiceClient.from_connection_string(Config.BLOB_CONNECTION_STRING)
            async with blob_service_client:
                container_client = blob_service_client.get_container_client(Config.BLOB_CONTAINER_NAME)
                blob_client = container_client.get_blob_client(file_path)
                blob_data = await blob_client.download_blob()
                file_bytes = await blob_data.readall()
                return file_bytes
        except Exception as e:
            logger.error(f'Unexpected blob storage error when retrieving file: {str(e)}')
            return None

    @staticmethod
    async def store_file(file_bytes:bytes, file_path:str) -> bool:
        """ Upload a file to blob storage """
        try:
            blob_service_client = BlobServiceClient.from_connection_string(Config.BLOB_CONNECTION_STRING)
            async with blob_service_client:
                container_client = blob_service_client.get_container_client(Config.BLOB_CONTAINER_NAME)
                blob_client = container_client.get_blob_client(file_path)
                await blob_client.upload_blob(file_bytes, overwrite=True)
            
            return True
        except Exception as e:
            logger.error(f'Unexpected blob storage error when saving file: {str(e)}')
            return False

    @staticmethod
    async def delete_file(file_path:str) -> bool:
        """ Delete a file from blob storage """
        try:
            blob_service_client = BlobServiceClient.from_connection_string(Config.BLOB_CONNECTION_STRING)
            async with blob_service_client:
                container_client = blob_service_client.get_container_client(Config.BLOB_CONTAINER_NAME)
                blob_client = container_client.get_blob_client(file_path)
                await blob_client.delete_blob()
            
            return True
        except Exception as e:
            logger.error(f'Unexpected blob storage error when deleting file: {str(e)}')
            return False
