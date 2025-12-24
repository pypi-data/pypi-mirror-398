"""
APIVerve API Client.

Low-level client for making API requests to APIVerve.
"""

import asyncio
from typing import Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

import requests


class APIVerveError(Exception):
    """Base exception for APIVerve errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class APIVerveClient:
    """
    Client for making requests to APIVerve APIs.

    Example:
        >>> client = APIVerveClient(api_key="your-api-key")
        >>> result = client.call_api("emailvalidator", {"email": "test@example.com"})
        >>> print(result)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.apiverve.com/v1",
        timeout: int = 30,
    ):
        """
        Initialize the APIVerve client.

        Args:
            api_key: Your APIVerve API key
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._session: Optional[requests.Session] = None
        self._executor = ThreadPoolExecutor(max_workers=4)

    @property
    def session(self) -> requests.Session:
        """Get or create the requests session."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "x-api-key": self.api_key,
                "Accept": "application/json",
                "User-Agent": "langchain-apiverve/0.1.0",
            })
        return self._session

    def call_api(
        self,
        api_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Dict[str, Any]:
        """
        Call an APIVerve API synchronously.

        Args:
            api_id: The API identifier (e.g., "emailvalidator", "dnslookup")
            parameters: Parameters to pass to the API
            method: HTTP method (GET or POST)

        Returns:
            API response as a dictionary

        Raises:
            APIVerveError: If the API call fails
        """
        url = f"{self.base_url}/{api_id}"
        params = parameters or {}

        try:
            if method.upper() == "POST":
                response = self.session.post(url, json=params, timeout=self.timeout)
            else:
                response = self.session.get(url, params=params, timeout=self.timeout)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"API request failed: {e}"
            try:
                error_response = response.json()
                if "error" in error_response:
                    error_msg = error_response["error"]
            except Exception:
                pass
            raise APIVerveError(error_msg, status_code=response.status_code)
        except requests.exceptions.RequestException as e:
            raise APIVerveError(f"Request failed: {e}")

    async def acall_api(
        self,
        api_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Dict[str, Any]:
        """
        Call an APIVerve API asynchronously.

        Args:
            api_id: The API identifier (e.g., "emailvalidator", "dnslookup")
            parameters: Parameters to pass to the API
            method: HTTP method (GET or POST)

        Returns:
            API response as a dictionary

        Raises:
            APIVerveError: If the API call fails
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.call_api(api_id, parameters, method)
        )

    def close(self):
        """Close the client and release resources."""
        if self._session:
            self._session.close()
            self._session = None
        self._executor.shutdown(wait=False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
