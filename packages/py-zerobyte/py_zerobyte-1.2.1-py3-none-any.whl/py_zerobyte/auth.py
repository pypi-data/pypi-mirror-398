"""Authentication API methods."""

from typing import Dict, Any, Optional


class AuthAPI:
    """Authentication API methods."""
    
    def __init__(self, client):
        """Initialize AuthAPI with client instance."""
        self.client = client
    
    def register(self, username: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            username: Username (minimum 3 characters)
            password: Password (minimum 8 characters)
        
        Returns:
            dict: Registration response with user information
        
        Example:
            >>> response = client.auth.register("newuser", "password123")
        """
        return self.client._make_request(
            "POST",
            "/api/v1/auth/register",
            data={"username": username, "password": password}
        )
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login with username and password.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            dict: Login response with user information
        
        Example:
            >>> response = client.auth.login("admin", "password123")
        """
        return self.client._make_request(
            "POST",
            "/api/v1/auth/login",
            data={"username": username, "password": password}
        )
    
    def logout(self) -> Dict[str, Any]:
        """
        Logout current user.
        
        Returns:
            dict: Logout response
        
        Example:
            >>> response = client.auth.logout()
        """
        return self.client._make_request("POST", "/api/v1/auth/logout")
    
    def get_me(self) -> Dict[str, Any]:
        """
        Get current authenticated user information.
        
        Returns:
            dict: Current user information
        
        Example:
            >>> user = client.auth.get_me()
            >>> print(user['username'])
        """
        return self.client._make_request("GET", "/api/v1/auth/me")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get authentication system status.
        
        Returns:
            dict: Authentication system status (e.g., hasUsers)
        
        Example:
            >>> status = client.auth.get_status()
            >>> if not status['hasUsers']:
            ...     # First time setup
            ...     pass
        """
        return self.client._make_request("GET", "/api/v1/auth/status")
    
    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change current user password.
        
        Args:
            current_password: Current password
            new_password: New password (minimum 8 characters)
        
        Returns:
            dict: Password change response
        
        Example:
            >>> response = client.auth.change_password("oldpass", "newpass123")
        """
        return self.client._make_request(
            "POST",
            "/api/v1/auth/change-password",
            data={
                "currentPassword": current_password,
                "newPassword": new_password
            }
        )
