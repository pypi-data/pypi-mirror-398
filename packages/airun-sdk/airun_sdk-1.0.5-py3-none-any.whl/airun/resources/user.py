"""
User API Resource

Provides access to user management and system prompt endpoints.
"""

from typing import Optional, Dict, Any
from ..http_client import HTTPClient
from ..models import SystemPrompt


class UserResource:
    """User API resource for user management."""

    def __init__(self, http_client: HTTPClient):
        """Initialize user resource."""
        self.client = http_client

    def get_system_prompt(self, user_id: Optional[str] = None) -> Any:
        """
        Get system prompt for a user.

        Args:
            user_id: Optional User ID (uses API key user if not provided).

        Returns:
            System prompt data.
        """
        params = {}
        if user_id:
            params["userId"] = user_id
        response = self.client.get("/api/v1/user/system-prompt", params=params)
        return response

    def update_system_prompt(
        self,
        content: str,
        user_id: Optional[str] = None
    ) -> Any:
        """
        Update system prompt for a user.

        Args:
            content: New system prompt content.
            user_id: Optional User ID (uses API key user if not provided).

        Returns:
            Update response.
        """
        payload = {"content": content}
        if user_id:
            payload["userId"] = user_id
        response = self.client.put("/api/v1/user/system-prompt", data=payload)
        return response