import grpc
from klab_pytest_toolkit_web._api_client_types.rest_client import RestApiClient
from typing import Dict, Any, Optional, List, Tuple
from klab_pytest_toolkit_web._api_client_types.grpc_client import GrpcClient


class ApiClientFactory:
    def create_rest_client(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> RestApiClient:
        """
        Create a REST API client instance.

        Args:
            base_url: Base URL for API requests
            headers: Optional default headers

        Returns:
            RestApiClient instance

        Example:
            >>> factory = ApiClientFactory()
            >>> client = factory.create_rest_client(
            ...     base_url="https://api.example.com",
            ...     headers={"Authorization": "Bearer token"}
            ... )
            >>> response = client.get("/users/1")
            >>> # Set timeout per request when needed
            >>> response = client.get("/slow-endpoint", timeout=120)
        """
        return RestApiClient(base_url=base_url, headers=headers)

    def create_grpc_client(
        self,
        target: str,
        proto_file: str,
        credentials: Optional[grpc.ChannelCredentials] = None,
        options: Optional[List[Tuple[str, Any]]] = None,
        metadata: Optional[List[Tuple[str, str]]] = None,
    ) -> GrpcClient:
        """
        Create a gRPC client instance with dynamic method binding.

        Args:
            target: gRPC server address (e.g., "localhost:50051")
            proto_file: Path to .proto file for service definition
            credentials: Optional channel credentials for secure connection
            options: Optional channel options (e.g., [('grpc.max_receive_message_length', -1)])
            metadata: Optional metadata to send with each request

        Returns:
            GrpcClient instance with dynamically bound methods

        Raises:
            ValueError: If neither proto_file nor use_reflection is provided

        Example:
            >>> # Using proto file
            >>> factory = ApiClientFactory()
            >>> client = factory.create_grpc_client(
            ...     target="localhost:50051",
            ...     proto_file="path/to/service.proto"
            ... )
            >>> response = client.GetUser(id=123)
            >>>
            >>> # With SSL/TLS
            >>> creds = grpc.ssl_channel_credentials()
            >>> client = factory.create_grpc_client(
            ...     target="secure.example.com:443",
            ...     proto_file="service.proto",
            ...     credentials=creds
            ... )
        """

        return GrpcClient(
            target=target,
            proto_file=proto_file,
            credentials=credentials,
            options=options,
            metadata=metadata,
        )
