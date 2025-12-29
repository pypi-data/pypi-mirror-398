import grpc
from osdentalMobileLibrary.Models.Response import Response
from osdentalMobileLibrary.Decorators.Retry import grpc_retry
from ..Generated import AuthProto_pb2
from ..Generated import AuthProto_pb2_grpc
from osdentalMobileLibrary.Shared.Config import Config
from osdentalMobileLibrary.Exception.ControlledException import OSDException
from google.protobuf import empty_pb2


class AuthClient:
    def __init__(
        self, host=Config.SECURITY_GRPC_HOSTMOB, port=Config.SECURITY_GRPC_PORTMOB
    ):
        if not host:
            raise OSDException("SECURITY_GRPC_HOST is not set")

        if port:
            self.url = f"{host}:{port}"
            self.secure = False
        else:
            self.url = host
            self.secure = True

        self.channel = None
        self.stub = None

    async def __aenter__(self):
        # Aquí se abre la conexión
        if self.secure:
            creds = grpc.ssl_channel_credentials()
            self.channel = grpc.aio.secure_channel(self.url, creds)
        else:
            self.channel = grpc.aio.insecure_channel(self.url)

        self.stub = AuthProto_pb2_grpc.AuthProtoStub(self.channel)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # Cerrar el canal al salir
        if self.channel:
            await self.channel.close()

    @grpc_retry
    async def validate_auth_token(self, bearer_token: str, agent_mobile: str):
        if not self.stub:
            raise OSDException(
                "gRPC connection not initialized. Use `async with AuthClient()`"
            )

        metadata = [
            ("authorization", f"{bearer_token}"),
            ("agent-mobile", agent_mobile),
        ]

        empty = empty_pb2.Empty()

        return await self.stub.ValidateToken(empty, metadata=metadata)


auth_client = AuthClient()
