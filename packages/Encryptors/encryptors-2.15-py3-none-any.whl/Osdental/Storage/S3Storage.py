from Osdental.Storage import IStorageService

class S3Storage(IStorageService):

    def __init__(self, bucket_name: str, aws_config: dict):
        self.bucket_name = bucket_name
        self.aws_config = aws_config

    async def upload(self, file_path: str, file_bytes: bytes | str) -> str | bool:
        raise NotImplementedError()

    async def download(self, file_path: str) -> bytes | None:
        raise NotImplementedError()

    async def delete(self, file_path: str) -> bool:
        raise NotImplementedError()
