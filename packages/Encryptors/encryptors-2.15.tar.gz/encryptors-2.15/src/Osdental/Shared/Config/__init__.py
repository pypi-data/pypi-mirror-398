import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env', override=True)

class Config:
    SECURITY_GRPC_HOST = os.getenv('SECURITY_GRPC_HOST')
    SECURITY_GRPC_PORT = os.getenv('SECURITY_GRPC_PORT', None)
    SHARED_GRPC_HOST = os.getenv('SHARED_GRPC_HOST')
    
    BLOB_CONNECTION_STRING = os.getenv('BLOB_CONNECTION_STRING')
    BLOB_CONTAINER_NAME = os.getenv('BLOB_CONTAINER_NAME')
    APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
    
    CONNECTION_STRING = os.getenv('CONNECTION_STRING')
    AUDIT_QUEUE = os.getenv('QUEUE')