"""Repositories API methods."""

from typing import Dict, Any, List, Optional


class RepositoriesAPI:
    """Repositories API methods."""
    
    def __init__(self, client):
        """Initialize RepositoriesAPI with client instance."""
        self.client = client
    
    def list(self, volume_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all repositories, optionally filtered by volume ID.
        
        Args:
            volume_id: Optional volume ID to filter repositories (client-side filtering)
        
        Returns:
            list: List of repositories
        
        Example:
            >>> # List all repositories
            >>> repositories = client.repositories.list()
            >>> # List repositories for a specific volume
            >>> repositories = client.repositories.list(volume_id=1)
            >>> for repo in repositories:
            ...     print(repo['name'])
        """
        repos = self.client._make_request("GET", "/api/v1/repositories")
        
        # Client-side filtering by volume_id if provided
        if volume_id is not None:
            # Note: This assumes repositories have a volumeId field
            # If not present in the API response, this won't filter
            repos = [r for r in repos if r.get('volumeId') == volume_id]
        
        return repos
    
    def create(self, repository_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new repository.
        
        Args:
            repository_data: Repository configuration including:
                - name (str): Repository name
                - config (dict): Repository-specific configuration with:
                    - backend (str): Backend type ('local', 'sftp', 's3', 'r2', 'azure', 'gcs', 'rest', 'rclone')
                    - Additional backend-specific fields
                - compressionMode (str, optional): 'auto', 'max', or 'off'
        
        Returns:
            dict: Created repository information
        
        Example:
            >>> repo = client.repositories.create(
            ...     repository_data={
            ...         "name": "my-backup-repo",
            ...         "compressionMode": "auto",
            ...         "config": {
            ...             "backend": "local",
            ...             "name": "my-backup-repo",
            ...             "path": "/backups/repo1"
            ...         }
            ...     }
            ... )
        """
        return self.client._make_request(
            "POST",
            "/api/v1/repositories",
            data=repository_data
        )
    
    def get(self, name: str) -> Dict[str, Any]:
        """
        Get a specific repository by name.
        
        Args:
            name: Repository name
        
        Returns:
            dict: Repository information
        
        Example:
            >>> repo = client.repositories.get(name="my-backup-repo")
            >>> print(repo['name'])
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/repositories/{name}"
        )
    
    def update(
        self,
        name: str,
        repository_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a repository.
        
        Args:
            name: Repository name
            repository_data: Updated repository configuration
        
        Returns:
            dict: Updated repository information
        
        Example:
            >>> repo = client.repositories.update(
            ...     name="my-backup-repo",
            ...     repository_data={"compressionMode": "max"}
            ... )
        """
        return self.client._make_request(
            "PUT",
            f"/api/v1/repositories/{name}",
            data=repository_data
        )
    
    def delete(self, name: str) -> Dict[str, Any]:
        """
        Delete a repository.
        
        Args:
            name: Repository name
        
        Returns:
            dict: Deletion response
        
        Example:
            >>> response = client.repositories.delete(name="my-backup-repo")
        """
        return self.client._make_request(
            "DELETE",
            f"/api/v1/repositories/{name}"
        )
    
    def doctor(self, name: str) -> Dict[str, Any]:
        """
        Run doctor command on a repository to check and repair issues.
        
        Args:
            name: Repository name
        
        Returns:
            dict: Doctor command result
        
        Example:
            >>> result = client.repositories.doctor(name="my-backup-repo")
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/repositories/{name}/doctor"
        )
