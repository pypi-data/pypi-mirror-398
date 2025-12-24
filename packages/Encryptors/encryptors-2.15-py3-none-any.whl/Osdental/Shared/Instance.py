import httpx
from Osdental.Encryptor.Aes import AES
from Osdental.Messaging.AuditServiceBus import AuditServiceBus
from Osdental.Grpc.Client.AuthGrpcClient import AuthGrpcClient
from Osdental.Grpc.Adapter.AuthGrpcAdapter import AuthGrpcAdapter
from Osdental.Grpc.Client.GrpcConnection import GrpcConnection
from Osdental.Grpc.Client.SharedGrpcClient import SharedGrpcClient
from Osdental.Grpc.Adapter.SharedGrpcAdapter import SharedGrpcAdapter
from Osdental.Shared.Config import Config

class Instance:

    # Service bus audit log
    sb_audit = AuditServiceBus(Config.CONNECTION_STRING, Config.AUDIT_QUEUE)
    # Grpc Security
    grpc_auth_conn = GrpcConnection(Config.SECURITY_GRPC_HOST)
    grpc_auth_client = AuthGrpcClient(grpc_auth_conn)
    grpc_auth_adapter = AuthGrpcAdapter(grpc_auth_client)

    # Grpc Shared Resources
    grpc_shared_conn = GrpcConnection(Config.SHARED_GRPC_HOST)
    grpc_shared_client = SharedGrpcClient(grpc_shared_conn)
    grpc_shared_adapter = SharedGrpcAdapter(grpc_shared_client)

    # AES Encryptor
    aes = AES()

    # http_client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect=5.0,
            read=10.0,
            write=10.0,
            pool=5.0
        )
    )
