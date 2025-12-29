"""Repositories API methods."""

from typing import Dict, Any, List, Optional


class RepositoriesAPI:
    """Repositories API methods."""
    
    def __init__(self, client):
        """Initialize RepositoriesAPI with client instance."""
        self.client = client
    
    def list(self, volume_id: int) -> List[Dict[str, Any]]:
        """
        List all repositories for a volume.
        
        Args:
            volume_id: Volume ID
        
        Returns:
            list: List of repositories
        
        Example:
            >>> repositories = client.repositories.list(volume_id=1)
            >>> for repo in repositories:
            ...     print(repo['name'])
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/repositories"
        )
    
    def create(self, volume_id: int, repository_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new repository in a volume.
        
        Args:
            volume_id: Volume ID
            repository_data: Repository configuration including:
                - name (str): Repository name
                - type (str): Repository type (e.g., 'local', 'sftp', 's3', etc.)
                - config (dict): Repository-specific configuration
                - password (str): Repository password (optional, auto-generated if not provided)
        
        Returns:
            dict: Created repository information
        
        Example:
            >>> repo = client.repositories.create(
            ...     volume_id=1,
            ...     repository_data={
            ...         "name": "my-backup-repo",
            ...         "type": "local",
            ...         "config": {
            ...             "path": "/backups/repo1"
            ...         }
            ...     }
            ... )
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/volumes/{volume_id}/repositories",
            data=repository_data
        )
    
    def get(self, volume_id: int, repository_id: int) -> Dict[str, Any]:
        """
        Get a specific repository.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
        
        Returns:
            dict: Repository information
        
        Example:
            >>> repo = client.repositories.get(volume_id=1, repository_id=1)
            >>> print(repo['name'])
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}"
        )
    
    def update(
        self,
        volume_id: int,
        repository_id: int,
        repository_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a repository.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            repository_data: Updated repository configuration
        
        Returns:
            dict: Updated repository information
        
        Example:
            >>> repo = client.repositories.update(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     repository_data={"name": "updated-repo-name"}
            ... )
        """
        return self.client._make_request(
            "PUT",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}",
            data=repository_data
        )
    
    def delete(self, volume_id: int, repository_id: int) -> Dict[str, Any]:
        """
        Delete a repository.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
        
        Returns:
            dict: Deletion response
        
        Example:
            >>> response = client.repositories.delete(volume_id=1, repository_id=1)
        """
        return self.client._make_request(
            "DELETE",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}"
        )
    
    def doctor(self, volume_id: int, repository_id: int) -> Dict[str, Any]:
        """
        Run doctor command on a repository to check and repair issues.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
        
        Returns:
            dict: Doctor command result
        
        Example:
            >>> result = client.repositories.doctor(volume_id=1, repository_id=1)
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/doctor"
        )
