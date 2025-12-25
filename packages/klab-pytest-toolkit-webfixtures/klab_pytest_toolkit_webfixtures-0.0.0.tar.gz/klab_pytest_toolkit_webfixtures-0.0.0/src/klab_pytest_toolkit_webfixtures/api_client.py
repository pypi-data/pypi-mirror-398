import requests
from typing import Dict, Any, Optional


class ApiClient:
    """Abstract base class for API clients."""

    def close(self) -> None:
        """Close any resources held by the client."""
        raise NotImplementedError

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to this object."""
        self.close()


class RestApiClient(ApiClient):
    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize REST API client.

        Args:
            base_url: Base URL for API requests
            headers: Optional default headers for all requests
        """
        self.base_url = base_url
        self.headers = headers or {}
        self.session = requests.Session()

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            timeout: Optional timeout in seconds for this request

        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        return self.session.get(
            url,
            params=params,
            headers=self.headers,
            timeout=timeout,
        )

    def post(
        self,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint path
            payload: Optional JSON payload
            timeout: Optional timeout in seconds for this request

        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        return self.session.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=timeout,
        )

    def put(
        self,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        """
        Make a PUT request.

        Args:
            endpoint: API endpoint path
            payload: Optional JSON payload
            timeout: Optional timeout in seconds for this request

        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        return self.session.put(
            url,
            json=payload,
            headers=self.headers,
            timeout=timeout,
        )

    def patch(
        self,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        """
        Make a PATCH request.

        Args:
            endpoint: API endpoint path
            payload: Optional JSON payload
            timeout: Optional timeout in seconds for this request

        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        return self.session.patch(
            url,
            json=payload,
            headers=self.headers,
            timeout=timeout,
        )

    def delete(
        self,
        endpoint: str,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        """
        Make a DELETE request.

        Args:
            endpoint: API endpoint path
            timeout: Optional timeout in seconds for this request

        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        return self.session.delete(
            url,
            headers=self.headers,
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the session."""
        self.session.close()


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
