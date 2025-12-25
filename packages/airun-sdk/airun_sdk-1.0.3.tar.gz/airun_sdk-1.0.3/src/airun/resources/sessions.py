"""
Sessions API Resource

Provides access to session management endpoints.
"""

from typing import Optional, Dict, Any, List
from ..http_client import HTTPClient
from ..models import SessionCreate, SessionUpdate, APIResponse


class SessionsResource:
    """Sessions API resource for session management."""

    def __init__(self, http_client: HTTPClient):
        """Initialize sessions resource."""
        self.client = http_client

    def create(
        self,
        type: str = "chat",
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create a new session.

        Args:
            type: Session type (e.g., "chat", "code").
            title: Session title.
            metadata: Additional metadata.

        Returns:
            Created session data.

        Example:
            >>> response = sessions.create(
            ...     type="chat",
            ...     title="My Conversation"
            ... )
            >>> session_id = response.data.session_id
        """
        payload = {"type": type}
        if title:
            payload["title"] = title
        if metadata:
            payload["metadata"] = metadata

        response = self.client.post("/api/v1/sessions/create", data=payload)
        return response

    def get_sessions(self, type: Optional[str] = None) -> Any:
        """
        Get all sessions.

        Args:
            type: Filter by session type.

        Returns:
            List of sessions.

        Example:
            >>> response = sessions.get_sessions(type="chat")
            >>> for session in response.data.sessions:
            ...     print(session.title)
        """
        params = {}
        if type:
            params["type"] = type

        response = self.client.get("/api/v1/sessions", params=params)
        return response

    def get_session(self, session_id: str) -> Any:
        """
        Get a specific session.

        Args:
            session_id: Session ID.

        Returns:
            Session data.
        """
        response = self.client.get(f"/api/v1/sessions/{session_id}")
        return response

    def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Update a session.

        Args:
            session_id: Session ID.
            title: New title.
            metadata: New metadata.

        Returns:
            Updated session data.
        """
        payload = {}
        if title:
            payload["title"] = title
        if metadata:
            payload["metadata"] = metadata

        response = self.client.put(f"/api/v1/sessions/{session_id}", data=payload)
        return response

    def delete_session(self, session_id: str) -> Any:
        """
        Delete a session.

        Args:
            session_id: Session ID.

        Returns:
            Delete response.
        """
        response = self.client.delete(f"/api/v1/sessions/{session_id}")
        return response

    def delete_all_sessions(self) -> Any:
        """
        Delete all sessions.

        Returns:
            Delete response.
        """
        response = self.client.delete("/api/v1/sessions")
        return response