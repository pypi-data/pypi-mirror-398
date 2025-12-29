"""Snapshots API methods."""

from typing import Dict, Any, List, Optional


class SnapshotsAPI:
    """Snapshots API methods."""
    
    def __init__(self, client):
        """Initialize SnapshotsAPI with client instance."""
        self.client = client
    
    def list(self, repository_name: str, backup_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all snapshots in a repository.
        
        Args:
            repository_name: Repository name
            backup_id: Optional backup ID to filter snapshots
        
        Returns:
            list: List of snapshots
        
        Example:
            >>> snapshots = client.snapshots.list(repository_name="my-backup-repo")
            >>> for snapshot in snapshots:
            ...     print(f"{snapshot['short_id']}: {snapshot['time']}")
        """
        params = {}
        if backup_id:
            params['backupId'] = backup_id
        
        return self.client._make_request(
            "GET",
            f"/api/v1/repositories/{repository_name}/snapshots",
            params=params if params else None
        )
    
    def get_details(
        self,
        repository_name: str,
        snapshot_id: str
    ) -> Dict[str, Any]:
        """
        Get details of a specific snapshot.
        
        Args:
            repository_name: Repository name
            snapshot_id: Snapshot ID
        
        Returns:
            dict: Snapshot details
        
        Example:
            >>> details = client.snapshots.get_details(
            ...     repository_name="my-backup-repo",
            ...     snapshot_id="abc123"
            ... )
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/repositories/{repository_name}/snapshots/{snapshot_id}"
        )
    
    def delete(
        self,
        repository_name: str,
        snapshot_id: str
    ) -> Dict[str, Any]:
        """
        Delete a snapshot.
        
        Args:
            repository_name: Repository name
            snapshot_id: Snapshot ID
        
        Returns:
            dict: Deletion response
        
        Example:
            >>> response = client.snapshots.delete(
            ...     repository_name="my-backup-repo",
            ...     snapshot_id="abc123"
            ... )
        """
        return self.client._make_request(
            "DELETE",
            f"/api/v1/repositories/{repository_name}/snapshots/{snapshot_id}"
        )
    
    def list_files(
        self,
        repository_name: str,
        snapshot_id: str,
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List files in a snapshot.
        
        Args:
            repository_name: Repository name
            snapshot_id: Snapshot ID
            path: Path within snapshot (optional)
        
        Returns:
            dict: File listing
        
        Example:
            >>> files = client.snapshots.list_files(
            ...     repository_name="my-backup-repo",
            ...     snapshot_id="abc123",
            ...     path="/data"
            ... )
        """
        params = {}
        if path:
            params['path'] = path
        
        return self.client._make_request(
            "GET",
            f"/api/v1/repositories/{repository_name}/snapshots/{snapshot_id}/files",
            params=params if params else None
        )
    
    def restore(
        self,
        repository_name: str,
        restore_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Restore from a repository.
        
        Args:
            repository_name: Repository name
            restore_data: Restore configuration including:
                - target (str): Target path for restoration
                - include (list): Paths to include (optional)
                - exclude (list): Paths to exclude (optional)
                - snapshotId (str): Specific snapshot ID to restore (optional)
        
        Returns:
            dict: Restore response
        
        Example:
            >>> response = client.snapshots.restore(
            ...     repository_name="my-backup-repo",
            ...     restore_data={
            ...         "target": "/restore/path",
            ...         "include": ["/data"],
            ...         "exclude": ["/data/temp"],
            ...         "snapshotId": "abc123"
            ...     }
            ... )
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/repositories/{repository_name}/restore",
            data=restore_data
        )
