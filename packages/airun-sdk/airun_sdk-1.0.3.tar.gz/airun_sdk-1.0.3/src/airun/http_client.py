"""
HTTP Client for AIRUN SDK

Handles HTTP requests to the AIRUN API.
"""

import os
import json
from typing import Optional, Dict, Any, Union
from datetime import datetime

import requests
from requests import Response, Session
from dotenv import load_dotenv

from .exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ServerError,
    NotFoundError,
    ValidationError,
)


class HTTPClient:
    """HTTP client for making requests to the AIRUN API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        session: Optional[Session] = None
    ):
        """
        Initialize the HTTP client.

        Args:
            base_url: Base URL for the API. Defaults to AIRUN_SERVER_URL env var.
            api_key: API key for authentication. Defaults to AIRUN_API_KEY env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            session: Custom requests session to use.
        """
        # Load environment variables
        load_dotenv()

        # Set base URL
        self.base_url = base_url or os.getenv("AIRUN_SERVER_URL", "http://localhost:5500")
        if not self.base_url.startswith("http"):
            self.base_url = f"https://{self.base_url}"
        self.base_url = self.base_url.rstrip("/")

        # Set API key
        self.api_key = api_key or os.getenv("AIRUN_API_KEY")
        if not self.api_key:
            raise AuthenticationError("API key is required. Set AIRUN_API_KEY environment variable or pass api_key parameter.")

        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize session
        self.session = session or requests.Session()
        self.session.headers.update(self._default_headers())

    def _default_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AIRUN-Python-SDK/1.0.0",
            "X-API-Key": self.api_key,
        }

    def _handle_response(self, response: Response) -> Dict[str, Any]:
        """
        Handle API response and extract JSON data.

        Args:
            response: The HTTP response object.

        Returns:
            Parsed JSON response data.

        Raises:
            APIError: For various API error conditions.
        """
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            raise APIError(f"Invalid JSON response: {e}")

        # Handle error responses
        if not response.ok:
            error_info = response_data.get("error", {})
            message = error_info.get("message", f"HTTP {response.status_code}")
            code = error_info.get("code")

            if response.status_code == 401:
                raise AuthenticationError(message)
            elif response.status_code == 403:
                raise AuthenticationError(f"Access forbidden: {message}")
            elif response.status_code == 404:
                raise NotFoundError(message)
            elif response.status_code == 422:
                raise ValidationError(message)
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(message, int(retry_after) if retry_after else None)
            elif 500 <= response.status_code < 600:
                raise ServerError(message)
            else:
                raise APIError(message, code, response.status_code)

        return response_data

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False
    ) -> Union[Dict[str, Any], Response]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.).
            endpoint: API endpoint path.
            params: Query parameters.
            data: Request body data.
            files: Files to upload.
            headers: Additional headers.
            stream: Whether to stream the response.

        Returns:
            Parsed JSON response or raw response if streaming.

        Raises:
            NetworkError: For network-related errors.
            APIError: For API errors.
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)

        # If files are being uploaded, don't set Content-Type automatically
        if files:
            request_headers.pop("Content-Type", None)

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data if isinstance(data, dict) and not files else None,
                    data=data if files else None,
                    files=files,
                    headers=request_headers,
                    timeout=self.timeout,
                    stream=stream
                )

                if stream:
                    return response
                else:
                    return self._handle_response(response)

            except requests.exceptions.Timeout as e:
                last_exception = NetworkError(f"Request timeout after {self.timeout}s", e)
            except requests.exceptions.ConnectionError as e:
                last_exception = NetworkError(f"Connection error: {e}", e)
            except requests.exceptions.RequestException as e:
                last_exception = NetworkError(f"Request failed: {e}", e)

            # Retry on network errors (except for the last attempt)
            if attempt < self.max_retries:
                continue

        # All retries failed
        raise last_exception or NetworkError("Request failed")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return self._make_request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return self._make_request("POST", endpoint, params=params, data=data, files=files, headers=headers)

    def put(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        return self._make_request("PUT", endpoint, params=params, data=data, headers=headers)

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self._make_request("DELETE", endpoint, params=params, headers=headers)

    def download(
        self,
        endpoint: str,
        file_path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Download a file from the API.

        Args:
            endpoint: API endpoint path.
            file_path: Local path to save the file.
            params: Query parameters.
            headers: Additional headers.

        Returns:
            Path to the downloaded file.
        """
        response = self._make_request("GET", endpoint, params=params, headers=headers, stream=True)

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return file_path

    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()