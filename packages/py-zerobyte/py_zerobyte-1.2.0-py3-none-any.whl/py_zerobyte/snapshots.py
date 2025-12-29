"""Snapshots API methods."""

from typing import Dict, Any, List, Optional


class SnapshotsAPI:
    """Snapshots API methods."""
    
    def __init__(self, client):
        """Initialize SnapshotsAPI with client instance."""
        self.client = client
    
    def list(self, volume_id: int, repository_id: int) -> List[Dict[str, Any]]:
        """
        List all snapshots in a repository.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
        
        Returns:
            list: List of snapshots
        
        Example:
            >>> snapshots = client.snapshots.list(volume_id=1, repository_id=1)
            >>> for snapshot in snapshots:
            ...     print(f"{snapshot['id']}: {snapshot['time']}")
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/snapshots"
        )
    
    def get_details(
        self,
        volume_id: int,
        repository_id: int,
        snapshot_id: str
    ) -> Dict[str, Any]:
        """
        Get details of a specific snapshot.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            snapshot_id: Snapshot ID
        
        Returns:
            dict: Snapshot details
        
        Example:
            >>> details = client.snapshots.get_details(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     snapshot_id="abc123"
            ... )
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/snapshots/{snapshot_id}"
        )
    
    def delete(
        self,
        volume_id: int,
        repository_id: int,
        snapshot_id: str
    ) -> Dict[str, Any]:
        """
        Delete a snapshot.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            snapshot_id: Snapshot ID
        
        Returns:
            dict: Deletion response
        
        Example:
            >>> response = client.snapshots.delete(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     snapshot_id="abc123"
            ... )
        """
        return self.client._make_request(
            "DELETE",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/snapshots/{snapshot_id}"
        )
    
    def list_files(
        self,
        volume_id: int,
        repository_id: int,
        snapshot_id: str,
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List files in a snapshot.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            snapshot_id: Snapshot ID
            path: Path within snapshot (optional)
        
        Returns:
            dict: File listing
        
        Example:
            >>> files = client.snapshots.list_files(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     snapshot_id="abc123",
            ...     path="/data"
            ... )
        """
        params = {}
        if path:
            params['path'] = path
        
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/snapshots/{snapshot_id}/files",
            params=params
        )
    
    def restore(
        self,
        volume_id: int,
        repository_id: int,
        snapshot_id: str,
        restore_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Restore a snapshot.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            snapshot_id: Snapshot ID
            restore_data: Restore configuration including:
                - target (str): Target path for restoration
                - include (list): Paths to include (optional)
                - exclude (list): Paths to exclude (optional)
        
        Returns:
            dict: Restore response
        
        Example:
            >>> response = client.snapshots.restore(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     snapshot_id="abc123",
            ...     restore_data={
            ...         "target": "/restore/path",
            ...         "include": ["/data"],
            ...         "exclude": ["/data/temp"]
            ...     }
            ... )
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/snapshots/{snapshot_id}/restore",
            data=restore_data
        )
