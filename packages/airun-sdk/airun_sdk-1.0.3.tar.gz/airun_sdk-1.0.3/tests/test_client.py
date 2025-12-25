"""
Tests for the AIRUN Python SDK Client
"""

import pytest
from unittest.mock import Mock, patch
from airun import AIRUN
from airun.exceptions import AuthenticationError, APIError


class TestAIRUNClient:
    """Test cases for AIRUN client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server_url = "http://test-server:5500"
        self.api_key = "test-api-key"

    @patch('airun.client.HTTPClient')
    def test_client_initialization_with_params(self, mock_http_client):
        """Test client initialization with parameters."""
        mock_http_client.return_value = Mock()

        client = AIRUN(
            server_url=self.server_url,
            api_key=self.api_key,
            timeout=60
        )

        mock_http_client.assert_called_once_with(
            base_url=self.server_url,
            api_key=self.api_key,
            timeout=60,
            max_retries=3
        )
        assert client.client is not None
        assert hasattr(client, 'chat')
        assert hasattr(client, 'code')
        assert hasattr(client, 'rag')
        assert hasattr(client, 'web')

    @patch('airun.client.HTTPClient')
    def test_client_initialization_without_api_key(self, mock_http_client):
        """Test that client initialization fails without API key."""
        mock_http_client.side_effect = AuthenticationError("API key is required")

        with pytest.raises(AuthenticationError):
            AIRUN(api_key=None)

    @patch('airun.client.HTTPClient')
    def test_validate_key_success(self, mock_http_client):
        """Test successful API key validation."""
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = {"success": True}
        mock_http_client.return_value = mock_client_instance

        client = AIRUN(api_key=self.api_key)
        result = client.validate_key()

        assert result is True
        mock_client_instance.post.assert_called_once_with(
            "/auth/validate-key",
            data={"apiKey": self.api_key}
        )

    @patch('airun.client.HTTPClient')
    def test_validate_key_failure(self, mock_http_client):
        """Test API key validation failure."""
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = {"success": False}
        mock_http_client.return_value = mock_client_instance

        client = AIRUN(api_key=self.api_key)
        result = client.validate_key()

        assert result is False

    @patch('airun.client.HTTPClient')
    def test_get_status(self, mock_http_client):
        """Test getting API status."""
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = {"status": "healthy"}
        mock_http_client.return_value = mock_client_instance

        client = AIRUN(api_key=self.api_key)
        status = client.get_status()

        assert status["status"] == "healthy"
        mock_client_instance.get.assert_called_once_with("/health")

    @patch('airun.client.HTTPClient')
    def test_context_manager(self, mock_http_client):
        """Test client as context manager."""
        mock_client_instance = Mock()
        mock_http_client.return_value = mock_client_instance

        with AIRUN(api_key=self.api_key) as client:
            assert client is not None

        mock_client_instance.close.assert_called_once()

    @patch('airun.client.HTTPClient')
    def test_convenience_methods(self, mock_http_client):
        """Test convenience methods."""
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = {"success": True, "data": {"response": "test"}}
        mock_http_client.return_value = mock_client_instance

        client = AIRUN(api_key=self.api_key)

        # Mock the chat resource
        client.chat = Mock()
        client.chat.create_sync.return_value = {"success": True, "data": {"response": "test"}}

        # Test chat_sync convenience method
        response = client.chat_sync("Hello")

        client.chat.create_sync.assert_called_once_with("Hello")
        assert response["success"] is True