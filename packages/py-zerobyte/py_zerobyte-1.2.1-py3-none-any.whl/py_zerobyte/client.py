"""Main client for Zerobyte API."""

import requests
from typing import Optional, Dict, Any
from .exceptions import (
    ZerobyteError,
    AuthenticationError,
    APIError,
    NotFoundError,
    ValidationError,
)
from .auth import AuthAPI
from .volumes import VolumesAPI
from .repositories import RepositoriesAPI
from .snapshots import SnapshotsAPI
from .backup_schedules import BackupSchedulesAPI
from .notifications import NotificationsAPI
from .system import SystemAPI


class ZerobyteClient:
    """
    Main client for interacting with the Zerobyte API.
    
    Args:
        url: The base URL of the Zerobyte API (e.g., "http://localhost:4096")
        username: Username for authentication
        password: Password for authentication
        auto_login: Whether to automatically login on initialization (default: True)
    
    Example:
        >>> client = ZerobyteClient(
        ...     url="http://localhost:4096",
        ...     username="admin",
        ...     password="password123"
        ... )
        >>> volumes = client.volumes.list()
    """
    
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        auto_login: bool = True
    ):
        """Initialize the Zerobyte client."""
        self.base_url = url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        
        # Initialize API modules
        self.auth = AuthAPI(self)
        self.volumes = VolumesAPI(self)
        self.repositories = RepositoriesAPI(self)
        self.snapshots = SnapshotsAPI(self)
        self.backup_schedules = BackupSchedulesAPI(self)
        self.notifications = NotificationsAPI(self)
        self.system = SystemAPI(self)
        
        # Auto-login if requested
        if auto_login:
            self.login()
    
    def login(self) -> Dict[str, Any]:
        """
        Login to the Zerobyte API.
        
        Returns:
            dict: Login response containing user information
        
        Raises:
            AuthenticationError: If login fails
        """
        return self.auth.login(self.username, self.password)
    
    def logout(self) -> Dict[str, Any]:
        """
        Logout from the Zerobyte API.
        
        Returns:
            dict: Logout response
        """
        return self.auth.logout()
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (e.g., "/api/v1/volumes")
            data: JSON data to send in the request body
            params: Query parameters
            **kwargs: Additional arguments to pass to requests
        
        Returns:
            Response data (JSON parsed)
        
        Raises:
            AuthenticationError: If authentication fails (401)
            NotFoundError: If resource not found (404)
            ValidationError: If validation fails (400)
            APIError: For other API errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                **kwargs
            )
            
            # Handle different status codes
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed. Please check your credentials.")
            elif response.status_code == 404:
                raise NotFoundError(
                    f"Resource not found: {endpoint}",
                    status_code=404,
                    response=response
                )
            elif response.status_code == 400:
                error_msg = "Validation error"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict) and 'message' in error_data:
                        error_msg = error_data['message']
                except:
                    pass
                raise ValidationError(
                    error_msg,
                    status_code=400,
                    response=response
                )
            elif response.status_code >= 400:
                error_msg = f"API error: {response.status_code}"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict) and 'message' in error_data:
                        error_msg = error_data['message']
                except:
                    pass
                raise APIError(
                    error_msg,
                    status_code=response.status_code,
                    response=response
                )
            
            # Return JSON response if available
            if response.content:
                try:
                    return response.json()
                except ValueError:
                    return response.text
            
            return None
            
        except requests.RequestException as e:
            raise ZerobyteError(f"Request failed: {str(e)}")
