"""
Unit tests for Zerobyte SDK.

This is a basic test structure. Expand as needed.
"""

import pytest
from unittest.mock import Mock, patch
from py_zerobyte import ZerobyteClient, AuthenticationError, APIError


class TestZerobyteClient:
    """Tests for ZerobyteClient class."""
    
    @patch('py_zerobyte.client.requests.Session')
    def test_client_initialization(self, mock_session):
        """Test client initialization."""
        # Mock the login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "user": {"id": 1, "username": "test"}
        }
        mock_session.return_value.request.return_value = mock_response
        
        client = ZerobyteClient(
            url="http://localhost:4096",
            username="test",
            password="test123"
        )
        
        assert client.base_url == "http://localhost:4096"
        assert client.username == "test"
        assert client.password == "test123"
    
    @patch('py_zerobyte.client.requests.Session')
    def test_authentication_error(self, mock_session):
        """Test authentication error handling."""
        # Mock failed login
        mock_response = Mock()
        mock_response.status_code = 401
        mock_session.return_value.request.return_value = mock_response
        
        with pytest.raises(AuthenticationError):
            ZerobyteClient(
                url="http://localhost:4096",
                username="wrong",
                password="wrong"
            )


class TestAuthAPI:
    """Tests for AuthAPI."""
    
    @patch('py_zerobyte.client.requests.Session')
    def test_get_me(self, mock_session):
        """Test get_me method."""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "user": {"id": 1, "username": "test"}
        }
        mock_session.return_value.request.return_value = mock_response
        
        client = ZerobyteClient(
            url="http://localhost:4096",
            username="test",
            password="test123"
        )
        
        user = client.auth.get_me()
        assert user['success'] is True
        assert user['user']['username'] == "test"


class TestVolumesAPI:
    """Tests for VolumesAPI."""
    
    @patch('py_zerobyte.client.requests.Session')
    def test_list_volumes(self, mock_session):
        """Test list volumes method."""
        # Setup mock for login
        login_response = Mock()
        login_response.status_code = 200
        login_response.json.return_value = {"success": True}
        
        # Setup mock for list volumes
        volumes_response = Mock()
        volumes_response.status_code = 200
        volumes_response.json.return_value = [
            {"id": 1, "name": "volume1"},
            {"id": 2, "name": "volume2"}
        ]
        
        mock_session.return_value.request.side_effect = [
            login_response,
            volumes_response
        ]
        
        client = ZerobyteClient(
            url="http://localhost:4096",
            username="test",
            password="test123"
        )
        
        volumes = client.volumes.list()
        assert len(volumes) == 2
        assert volumes[0]['name'] == "volume1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
