"""
Main AIRUN SDK Client

The main client class that provides access to all AIRUN API resources.
"""

import os
from typing import Optional, Dict, Any, Union
from .http_client import HTTPClient
from .exceptions import AIRUNError, AuthenticationError

# Import all resources
from .resources.chat import ChatResource
from .resources.code import CodeResource
from .resources.rag import RAGResource
from .resources.web import WebResource
from .resources.report import ReportResource
from .resources.user import UserResource
from .resources.sessions import SessionsResource


class AIRUN:
    """
    Main AIRUN SDK client.

    Provides access to all AIRUN API endpoints and resources.

    Example:
        >>> client = AIRUN(
        ...     server_url="http://localhost:5500",
        ...     api_key="your-api-key-here"
        ... )
        >>> response = client.chat.create("Hello, world!")
        >>> print(response.data.response)
    """

    def __init__(
        self,
        server_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the AIRUN client.

        Args:
            server_url: Base URL for the AIRUN API.
                       Can also be set via AIRUN_SERVER_URL environment variable.
            api_key: API key for authentication.
                     Can also be set via AIRUN_API_KEY environment variable.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts for failed requests.

        Raises:
            AuthenticationError: If no API key is provided.
        """
        # Initialize HTTP client
        self.client = HTTPClient(
            base_url=server_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries
        )

        # Initialize all API resources
        self._init_resources()

    def _init_resources(self):
        """Initialize all API resource objects."""
        self.chat = ChatResource(self.client)
        self.code = CodeResource(self.client)
        self.rag = RAGResource(self.client)
        self.web = WebResource(self.client)
        self.report = ReportResource(self.client)
        self.user = UserResource(self.client)
        self.sessions = SessionsResource(self.client)

    def validate_key(self) -> bool:
        """
        Validate the API key.

        Returns:
            True if the key is valid.

        Raises:
            AuthenticationError: If the key is invalid.
        """
        try:
            response = self.client.post("/api/v1/auth/validate-key", data={"apiKey": self.client.api_key})
            return response.get("success", False)
        except Exception as e:
            if "401" in str(e) or "authentication" in str(e).lower():
                raise AuthenticationError("Invalid API key")
            raise AIRUNError(f"Failed to validate API key: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the AIRUN API and its services.

        Returns:
            Status information including service health.
        """
        response = self.client.get("/api/v1/health")
        return response

    def close(self):
        """Close the HTTP client and clean up resources."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    # Convenience methods for quick access
    def chat_sync(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Convenience method for synchronous chat."""
        return self.chat.create_sync(prompt, **kwargs)

    def code_sync(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Convenience method for synchronous code generation."""
        return self.code.create_sync(prompt, **kwargs)

    def web_search_sync(self, query: str, **kwargs) -> Dict[str, Any]:
        """Convenience method for synchronous web search."""
        return self.web.search_sync(query, **kwargs)

    def rag_search_sync(self, query: str, **kwargs) -> Dict[str, Any]:
        """Convenience method for synchronous RAG search."""
        return self.rag.search_sync(query, **kwargs)