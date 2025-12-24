"""
ClientFactory convenience function tests.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from unittest.mock import MagicMock, patch

from embed_client.client_factory import (
    SecurityMode,
    create_client,
    create_client_from_config,
    create_client_from_env,
    detect_security_mode,
)


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("embed_client.client_factory.ClientFactory.create_client")
    def test_create_client_function(self, mock_create_client):
        """Test create_client convenience function."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        client = create_client("http://localhost", 8001)

        mock_create_client.assert_called_once_with("http://localhost", 8001, None, None)
        assert client == mock_client

    @patch("embed_client.client_factory.ClientFactory.from_config_file")
    def test_create_client_from_config_function(self, mock_from_config_file):
        """Test create_client_from_config convenience function."""
        mock_client = MagicMock()
        mock_from_config_file.return_value = mock_client

        client = create_client_from_config("config.json")

        mock_from_config_file.assert_called_once_with("config.json")
        assert client == mock_client

    @patch("embed_client.client_factory.ClientFactory.from_environment")
    def test_create_client_from_env_function(self, mock_from_environment):
        """Test create_client_from_env convenience function."""
        mock_client = MagicMock()
        mock_from_environment.return_value = mock_client

        client = create_client_from_env()

        mock_from_environment.assert_called_once()
        assert client == mock_client

    @patch("embed_client.client_factory.ClientFactory.detect_security_mode")
    def test_detect_security_mode_function(self, mock_detect_mode):
        """Test detect_security_mode convenience function."""
        mock_detect_mode.return_value = SecurityMode.HTTPS

        mode = detect_security_mode("https://localhost")

        mock_detect_mode.assert_called_once_with(
            "https://localhost", None, None, None, None
        )
        assert mode == SecurityMode.HTTPS
