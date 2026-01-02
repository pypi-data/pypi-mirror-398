import grpc
from typing import Optional, Any, List, Tuple, Callable, Dict
from pathlib import Path
import importlib.util
import tempfile
import sys
from grpc_tools import protoc
from klab_pytest_toolkit_web._api_client_types import ApiClient


class GrpcClient(ApiClient):
    """
    gRPC client with dynamic method binding.

    Supports proto file loading for service discovery.
    Methods are dynamically bound to the client instance for easy access.

    Examples:
        client = GrpcClient(
            target="localhost:50051",
            proto_file="service.proto"
        )
        response = client.call("SayHello", name="World")
        # or
        response = client.SayHello(name="World")
    """

    def __init__(
        self,
        target: str,
        proto_file: str,
        credentials: Optional[grpc.ChannelCredentials] = None,
        options: Optional[List[Tuple[str, Any]]] = None,
        metadata: Optional[List[Tuple[str, str]]] = None,
    ):
        self.target = target
        self.metadata = metadata or []
        self._stubs: Dict[str, Any] = {}
        self._methods: Dict[str, Any] = {}
        self._request_classes: Dict[str, Any] = {}
        self._channel = None
        self._temp_dir = None  # Keep temp dir alive!

        # Create channel
        if credentials:
            self._channel = grpc.secure_channel(target, credentials, options=options)
        else:
            self._channel = grpc.insecure_channel(target, options=options)

        # Load service definitions from proto file
        self._load_from_proto(proto_file)

    def _load_from_proto(self, proto_file: str) -> None:
        """Load service definition from proto file."""
        proto_path = Path(proto_file)
        if not proto_path.exists():
            raise FileNotFoundError(f"Proto file not found: {proto_file}")

        # Keep temp directory alive for the lifetime of the client
        self._temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(self._temp_dir.name)

        # Compile proto file
        result = protoc.main(
            [
                "grpc_tools.protoc",
                f"--proto_path={proto_path.parent}",
                f"--python_out={temp_path}",
                f"--grpc_python_out={temp_path}",
                proto_path.name,
            ]
        )

        if result != 0:
            raise RuntimeError(f"Proto compilation failed with exit code: {result}")

        # Load generated modules
        proto_name = proto_path.stem
        pb2_file = temp_path / f"{proto_name}_pb2.py"
        grpc_file = temp_path / f"{proto_name}_pb2_grpc.py"

        spec_pb2 = importlib.util.spec_from_file_location(f"{proto_name}_pb2", pb2_file)
        spec_grpc = importlib.util.spec_from_file_location(f"{proto_name}_pb2_grpc", grpc_file)

        if not spec_pb2 or not spec_grpc:
            raise RuntimeError("Failed to load generated proto modules")

        pb2_module = importlib.util.module_from_spec(spec_pb2)
        grpc_module = importlib.util.module_from_spec(spec_grpc)

        sys.modules[f"{proto_name}_pb2"] = pb2_module
        sys.modules[f"{proto_name}_pb2_grpc"] = grpc_module

        if spec_pb2.loader and spec_grpc.loader:
            spec_pb2.loader.exec_module(pb2_module)
            spec_grpc.loader.exec_module(grpc_module)
        else:
            raise RuntimeError("Failed to load proto module loaders")

        # Register services
        self._register_services(pb2_module, grpc_module)

    def _register_services(self, pb2_module: Any, grpc_module: Any) -> None:
        """Register services from compiled proto modules."""

        method_to_request_class: Dict[str, Any] = {}

        descriptor = pb2_module.DESCRIPTOR
        for service_name, service_desc in descriptor.services_by_name.items():
            for method in service_desc.methods:
                # Get the request class name from the descriptor
                request_class_name = method.input_type.name
                request_class = getattr(pb2_module, request_class_name)
                method_to_request_class[method.name] = request_class

        # Find and instantiate stub classes
        for name in dir(grpc_module):
            if name.endswith("Stub") and not name.startswith("_"):
                stub_class = getattr(grpc_module, name)
                service_name = name[:-4]  # Remove "Stub" suffix

                stub = stub_class(self._channel)
                self._stubs[service_name] = stub

                # Register methods
                for method_name in dir(stub):
                    if not method_name.startswith("_"):
                        method = getattr(stub, method_name)
                        if callable(method):
                            self._methods[method_name] = method

                            # Use the descriptor-based mapping
                            if method_name in method_to_request_class:
                                self._request_classes[method_name] = method_to_request_class[
                                    method_name
                                ]
                            else:
                                print(f"  Warning: No request class found for {method_name}")

                            # Pre-bind method
                            setattr(
                                self,
                                method_name,
                                self._create_method_wrapper(method_name, method),
                            )

    def call(self, method_name: str, request_dict: Optional[dict] = None, **kwargs) -> Any:
        """
        Call a gRPC method by name with parameters.

        Args:
            method_name: Name of the gRPC method to call
            request_dict: Optional dictionary of request parameters
            **kwargs: Request parameters as keyword arguments

        Returns:
            The response from the gRPC method

        Examples:
            response = client.call("SayHello", name="World")
            response = client.call("SayHello", {"name": "World"})
        """
        if method_name not in self._methods:
            from difflib import get_close_matches

            suggestions = get_close_matches(method_name, self._methods.keys(), n=3, cutoff=0.6)
            suggestion_text = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
            raise AttributeError(
                f"Method '{method_name}' not found.{suggestion_text} "
                f"Available methods: {list(self._methods.keys())}"
            )

        params = {**(request_dict or {}), **kwargs}
        grpc_method = self._methods[method_name]
        request_class = self._request_classes[method_name]

        try:
            request = request_class(**params)
            return grpc_method(request, metadata=self.metadata)
        except grpc.RpcError as e:
            details = e.details() if hasattr(e, "details") and callable(e.details) else str(e)
            raise RuntimeError(f"gRPC call to {method_name} failed: {details}") from e
        except Exception as e:
            raise RuntimeError(f"Error calling {method_name}: {str(e)}") from e

    def _create_method_wrapper(self, method_name: str, grpc_method: Any) -> Callable[..., Any]:
        """Create a wrapper for gRPC method that delegates to call()."""

        def wrapper(*args, **kwargs):
            if args:
                if len(args) > 1:
                    raise ValueError(f"Expected 0 or 1 positional arguments, got {len(args)}")
                request = args[0]
                try:
                    return grpc_method(request, metadata=self.metadata)
                except grpc.RpcError as e:
                    details = (
                        e.details() if hasattr(e, "details") and callable(e.details) else str(e)
                    )
                    raise RuntimeError(f"gRPC call to {method_name} failed: {details}") from e
            else:
                return self.call(method_name, **kwargs)

        wrapper.__name__ = method_name
        return wrapper

    def get_available_methods(self) -> List[str]:
        """Get list of available RPC methods."""
        return list(self._methods.keys())

    def get_request_class(self, method_name: str) -> Any:
        """Get the request class for a method."""
        return self._request_classes.get(method_name)

    def close(self) -> None:
        """Close the gRPC channel and cleanup."""
        if self._channel:
            self._channel.close()
            self._channel = None
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None

    def __del__(self):
        self.close()

    def __repr__(self) -> str:
        methods = ", ".join(self._methods.keys()) if self._methods else "No methods loaded"
        return f"<GrpcClient(target='{self.target}', methods=[{methods}])>"
