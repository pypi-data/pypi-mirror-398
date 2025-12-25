"""
Web Search API Resource

Provides access to web search endpoints.
"""

from typing import Optional, Dict, Any, List
from ..http_client import HTTPClient
from ..models import WebSearchOptions, APIResponse


class WebResource:
    """Web search API resource for web content retrieval."""

    def __init__(self, http_client: HTTPClient):
        """Initialize web resource."""
        self.client = http_client

    def search(
        self,
        query: str,
        engine: str = "auto",
        max_results: int = 6,
        async_mode: bool = True
    ) -> Any:
        """
        Search the web.

        Args:
            query: Search query.
            engine: Search engine to use (auto, google, bing, duckduckgo, etc.).
            max_results: Maximum number of results to return (default: 6).
            async_mode: Whether to process asynchronously (queue) or sync.

        Returns:
            Web search results.

        Example:
            >>> response = web.search(
            ...     query="Python best practices 2024",
            ...     engine="auto",
            ...     max_results=10
            ... )
            >>> for result in response.data:
            ...     print(result.get('title'), result.get('url'))
        """
        endpoint = "/api/v1/web/search/sync" if not async_mode else "/api/v1/web/search"

        payload = {
            "query": query,
            "engine": engine,
            "maxResults": max_results
        }

        response = self.client.post(endpoint, data=payload)
        return response

    def search_sync(
        self,
        query: str,
        engine: str = "auto",
        max_results: int = 6
    ) -> Any:
        """
        Search the web synchronously.

        Args:
            query: Search query.
            engine: Search engine to use (default: "auto").
            max_results: Maximum number of results to return (default: 6).

        Returns:
            Web search results.
        """
        return self.search(query, engine, max_results, async_mode=False)

    def get_image(self, filename: str, save_path: Optional[str] = None) -> str:
        """
        Get an image by filename.

        Args:
            filename: The image filename.
            save_path: Local path to save the image.

        Returns:
            Path to the saved image.
        """
        import os

        if not save_path:
            save_path = os.path.join(os.getcwd(), filename)

        return self.client.download(f"/api/v1/images/{filename}", save_path)