"""System API methods."""

from typing import Dict, Any


class SystemAPI:
    """System API methods."""
    
    def __init__(self, client):
        """Initialize SystemAPI with client instance."""
        self.client = client
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get system information.
        
        Returns:
            dict: System information including version, platform, etc.
        
        Example:
            >>> info = client.system.get_info()
            >>> print(f"Version: {info['version']}")
        """
        return self.client._make_request("GET", "/api/v1/system/info")
    
    def download_restic_password(self) -> str:
        """
        Download the Restic password file.
        
        Returns:
            str: Restic password content
        
        Example:
            >>> password = client.system.download_restic_password()
            >>> with open('restic-password.txt', 'w') as f:
            ...     f.write(password)
        """
        return self.client._make_request("GET", "/api/v1/system/download-restic-password")
