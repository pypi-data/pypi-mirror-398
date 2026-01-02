"""Pytest plugin to register web fixtures."""

import pytest
from klab_pytest_toolkit_web import (
    ApiClientFactory,
    ResponseValidatorFactory,
    WebClientFactory,
)


def pytest_configure(config):
    """Register custom markers and configure web fixtures."""
    pass


def pytest_addoption(parser):
    """Add command line and ini file options."""
    pass


@pytest.fixture
def response_validator_factory() -> ResponseValidatorFactory:
    """
    Factory fixture to create multiple validators with different schemas.

    Useful when you need multiple validators in a single test.

    Example:
        def test_multiple_schemas(response_validator_factory: JsonResponseValidatorFactory):
            user_validator = response_validator_factory.create(user_schema)
            post_validator = response_validator_factory.create(post_schema)

            assert user_validator.validate_response(user_data)
            assert post_validator.validate_response(post_data)

    Returns:
        JsonResponseValidatorFactory: Factory to create JsonResponseValidator instances
    """

    return ResponseValidatorFactory()


@pytest.fixture
def api_client_factory() -> ApiClientFactory:
    """
    Fixture to provide an API client factory for making web requests.

    Returns:
        ApiClientFactory: Factory to create API client instances
    """
    return ApiClientFactory()


@pytest.fixture
def web_client_factory() -> WebClientFactory:
    """
    Fixture to provide a Web client factory for making web requests.

    Returns:
        WebClientFactory: Factory to create Web client instances
    """
    return WebClientFactory()
