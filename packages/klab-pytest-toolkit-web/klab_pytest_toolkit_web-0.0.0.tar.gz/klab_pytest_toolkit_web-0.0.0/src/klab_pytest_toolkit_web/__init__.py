"""Klab Pytest Toolkit - Web Fixtures"""

from klab_pytest_toolkit_web.validators import (
    JsonResponseValidator,
    ResponseValidatorFactory,
)

from klab_pytest_toolkit_web.api_client import ApiClientFactory

from klab_pytest_toolkit_web.web_client import (
    WebClientFactory,
    WebClient,
)

from klab_pytest_toolkit_web._api_client_types.grpc_client import GrpcClient
from klab_pytest_toolkit_web._api_client_types.rest_client import RestApiClient

__version__ = "0.0.0"

__all__ = [
    "JsonResponseValidator",
    "ResponseValidatorFactory",
    "RestApiClient",
    "GrpcClient",
    "ApiClientFactory",
    "WebClient",
    "WebClientFactory",
]
