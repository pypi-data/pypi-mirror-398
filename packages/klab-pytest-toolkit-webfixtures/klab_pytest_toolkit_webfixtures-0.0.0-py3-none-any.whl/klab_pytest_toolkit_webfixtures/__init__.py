"""Klab Pytest Toolkit - Web Fixtures"""

from klab_pytest_toolkit_webfixtures.validators import (
    JsonResponseValidator,
    ResponseValidatorFactory,
)

from klab_pytest_toolkit_webfixtures.api_client import ApiClientFactory, RestApiClient

from klab_pytest_toolkit_webfixtures.web_client import (
    WebClientFactory,
    WebClient,
)

__version__ = "0.0.0"

__all__ = [
    "JsonResponseValidator",
    "ResponseValidatorFactory",
    "RestApiClient",
    "ApiClientFactory",
    "WebClient",
    "WebClientFactory",
]
