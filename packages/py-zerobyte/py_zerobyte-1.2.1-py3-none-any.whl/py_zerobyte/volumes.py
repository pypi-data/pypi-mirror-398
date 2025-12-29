"""Volumes API methods."""

from typing import Dict, Any, List, Optional


class VolumesAPI:
    """Volumes API methods."""
    
    def __init__(self, client):
        """Initialize VolumesAPI with client instance."""
        self.client = client
    
    def list(self) -> List[Dict[str, Any]]:
        """
        List all volumes.
        
        Returns:
            list: List of volumes
        
        Example:
            >>> volumes = client.volumes.list()
            >>> for volume in volumes:
            ...     print(volume['name'])
        """
        return self.client._make_request("GET", "/api/v1/volumes")
    
    def create(self, volume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new volume.
        
        Args:
            volume_data: Volume configuration including:
                - autoRemount (bool): Auto remount on system startup
                - device (str): Device path or identifier
                - filesystem (str): Filesystem type (e.g., 'ext4', 'ntfs', 'exfat')
                - mountPoint (str): Mount point path
                - name (str): Volume name
                - options (list): Mount options
                - readonly (bool): Mount as readonly
        
        Returns:
            dict: Created volume information
        
        Example:
            >>> volume = client.volumes.create({
            ...     "name": "my-backup",
            ...     "device": "/dev/sdb1",
            ...     "mountPoint": "/mnt/backup",
            ...     "filesystem": "ext4",
            ...     "autoRemount": True,
            ...     "readonly": False,
            ...     "options": []
            ... })
        """
        return self.client._make_request(
            "POST",
            "/api/v1/volumes",
            data=volume_data
        )
    
    def test_connection(self, volume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test connection to a volume before creating it.
        
        Args:
            volume_data: Volume configuration to test
        
        Returns:
            dict: Test result
        
        Example:
            >>> result = client.volumes.test_connection({
            ...     "device": "/dev/sdb1",
            ...     "filesystem": "ext4"
            ... })
        """
        return self.client._make_request(
            "POST",
            "/api/v1/volumes/test-connection",
            data=volume_data
        )
    
    def get(self, volume_id: int) -> Dict[str, Any]:
        """
        Get a specific volume by ID.
        
        Args:
            volume_id: Volume ID
        
        Returns:
            dict: Volume information
        
        Example:
            >>> volume = client.volumes.get(1)
            >>> print(volume['name'])
        """
        return self.client._make_request("GET", f"/api/v1/volumes/{volume_id}")
    
    def update(self, volume_id: int, volume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a volume.
        
        Args:
            volume_id: Volume ID
            volume_data: Updated volume configuration
        
        Returns:
            dict: Updated volume information
        
        Example:
            >>> volume = client.volumes.update(1, {
            ...     "name": "updated-name",
            ...     "autoRemount": True
            ... })
        """
        return self.client._make_request(
            "PUT",
            f"/api/v1/volumes/{volume_id}",
            data=volume_data
        )
    
    def delete(self, volume_id: int) -> Dict[str, Any]:
        """
        Delete a volume.
        
        Args:
            volume_id: Volume ID
        
        Returns:
            dict: Deletion response
        
        Example:
            >>> response = client.volumes.delete(1)
        """
        return self.client._make_request("DELETE", f"/api/v1/volumes/{volume_id}")
    
    def mount(self, volume_id: int) -> Dict[str, Any]:
        """
        Mount a volume.
        
        Args:
            volume_id: Volume ID
        
        Returns:
            dict: Mount response
        
        Example:
            >>> response = client.volumes.mount(1)
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/volumes/{volume_id}/mount"
        )
    
    def unmount(self, volume_id: int) -> Dict[str, Any]:
        """
        Unmount a volume.
        
        Args:
            volume_id: Volume ID
        
        Returns:
            dict: Unmount response
        
        Example:
            >>> response = client.volumes.unmount(1)
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/volumes/{volume_id}/unmount"
        )
    
    def health_check(self, volume_id: int) -> Dict[str, Any]:
        """
        Perform health check on a volume.
        
        Args:
            volume_id: Volume ID
        
        Returns:
            dict: Health check result
        
        Example:
            >>> health = client.volumes.health_check(1)
            >>> print(health['status'])
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/volumes/{volume_id}/health-check"
        )
    
    def list_files(self, volume_id: int, path: Optional[str] = None) -> Dict[str, Any]:
        """
        List files in a volume.
        
        Args:
            volume_id: Volume ID
            path: Path within the volume (optional)
        
        Returns:
            dict: File listing
        
        Example:
            >>> files = client.volumes.list_files(1, path="/backups")
        """
        params = {}
        if path:
            params['path'] = path
        
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/files",
            params=params
        )
    
    def browse_filesystem(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Browse the filesystem.
        
        Args:
            path: Filesystem path (optional)
        
        Returns:
            dict: Directory listing
        
        Example:
            >>> listing = client.volumes.browse_filesystem(path="/mnt")
        """
        params = {}
        if path:
            params['path'] = path
        
        return self.client._make_request(
            "GET",
            "/api/v1/volumes/browse-filesystem",
            params=params
        )
    
    def list_rclone_remotes(self) -> List[str]:
        """
        List available rclone remotes.
        
        Returns:
            list: List of rclone remote names
        
        Example:
            >>> remotes = client.volumes.list_rclone_remotes()
            >>> for remote in remotes:
            ...     print(remote)
        """
        return self.client._make_request("GET", "/api/v1/volumes/rclone-remotes")
