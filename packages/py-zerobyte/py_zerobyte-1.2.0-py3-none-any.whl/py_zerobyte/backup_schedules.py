"""Backup Schedules API methods."""

from typing import Dict, Any, List, Optional


class BackupSchedulesAPI:
    """Backup Schedules API methods."""
    
    def __init__(self, client):
        """Initialize BackupSchedulesAPI with client instance."""
        self.client = client
    
    def list(self, volume_id: int, repository_id: int) -> List[Dict[str, Any]]:
        """
        List all backup schedules for a repository.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
        
        Returns:
            list: List of backup schedules
        
        Example:
            >>> schedules = client.backup_schedules.list(volume_id=1, repository_id=1)
            >>> for schedule in schedules:
            ...     print(f"{schedule['name']}: {schedule['schedule']}")
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules"
        )
    
    def create(
        self,
        volume_id: int,
        repository_id: int,
        schedule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new backup schedule.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_data: Schedule configuration including:
                - name (str): Schedule name
                - schedule (str): Cron expression for schedule
                - enabled (bool): Whether schedule is enabled
                - backupPaths (list): Paths to backup
                - excludePaths (list): Paths to exclude (optional)
                - retention (dict): Retention policy (optional)
                - tags (list): Tags for the backup (optional)
        
        Returns:
            dict: Created backup schedule
        
        Example:
            >>> schedule = client.backup_schedules.create(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_data={
            ...         "name": "Daily Backup",
            ...         "schedule": "0 2 * * *",
            ...         "enabled": True,
            ...         "backupPaths": ["/data"],
            ...         "excludePaths": ["/data/temp"],
            ...         "retention": {
            ...             "keepLast": 7,
            ...             "keepDaily": 7,
            ...             "keepWeekly": 4,
            ...             "keepMonthly": 12
            ...         }
            ...     }
            ... )
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules",
            data=schedule_data
        )
    
    def get(
        self,
        volume_id: int,
        repository_id: int,
        schedule_id: int
    ) -> Dict[str, Any]:
        """
        Get a specific backup schedule.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_id: Schedule ID
        
        Returns:
            dict: Backup schedule details
        
        Example:
            >>> schedule = client.backup_schedules.get(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_id=1
            ... )
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/{schedule_id}"
        )
    
    def update(
        self,
        volume_id: int,
        repository_id: int,
        schedule_id: int,
        schedule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a backup schedule.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_id: Schedule ID
            schedule_data: Updated schedule configuration
        
        Returns:
            dict: Updated backup schedule
        
        Example:
            >>> schedule = client.backup_schedules.update(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_id=1,
            ...     schedule_data={"enabled": False}
            ... )
        """
        return self.client._make_request(
            "PUT",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/{schedule_id}",
            data=schedule_data
        )
    
    def delete(
        self,
        volume_id: int,
        repository_id: int,
        schedule_id: int
    ) -> Dict[str, Any]:
        """
        Delete a backup schedule.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_id: Schedule ID
        
        Returns:
            dict: Deletion response
        
        Example:
            >>> response = client.backup_schedules.delete(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_id=1
            ... )
        """
        return self.client._make_request(
            "DELETE",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/{schedule_id}"
        )
    
    def get_for_volume(self, volume_id: int) -> List[Dict[str, Any]]:
        """
        Get all backup schedules for a volume across all repositories.
        
        Args:
            volume_id: Volume ID
        
        Returns:
            list: List of backup schedules for the volume
        
        Example:
            >>> schedules = client.backup_schedules.get_for_volume(volume_id=1)
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/backup-schedules"
        )
    
    def run_now(
        self,
        volume_id: int,
        repository_id: int,
        schedule_id: int
    ) -> Dict[str, Any]:
        """
        Run a backup schedule immediately.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_id: Schedule ID
        
        Returns:
            dict: Backup execution response
        
        Example:
            >>> response = client.backup_schedules.run_now(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_id=1
            ... )
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/{schedule_id}/run-now"
        )
    
    def stop_backup(
        self,
        volume_id: int,
        repository_id: int,
        schedule_id: int
    ) -> Dict[str, Any]:
        """
        Stop a running backup.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_id: Schedule ID
        
        Returns:
            dict: Stop response
        
        Example:
            >>> response = client.backup_schedules.stop_backup(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_id=1
            ... )
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/{schedule_id}/stop"
        )
    
    def run_forget(
        self,
        volume_id: int,
        repository_id: int,
        schedule_id: int
    ) -> Dict[str, Any]:
        """
        Run the forget command to apply retention policy.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_id: Schedule ID
        
        Returns:
            dict: Forget command response
        
        Example:
            >>> response = client.backup_schedules.run_forget(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_id=1
            ... )
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/{schedule_id}/forget"
        )
    
    def get_notifications(
        self,
        volume_id: int,
        repository_id: int,
        schedule_id: int
    ) -> Dict[str, Any]:
        """
        Get notification settings for a backup schedule.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_id: Schedule ID
        
        Returns:
            dict: Notification settings
        
        Example:
            >>> notifications = client.backup_schedules.get_notifications(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_id=1
            ... )
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/{schedule_id}/notifications"
        )
    
    def update_notifications(
        self,
        volume_id: int,
        repository_id: int,
        schedule_id: int,
        notifications_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update notification settings for a backup schedule.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_id: Schedule ID
            notifications_data: Notification configuration
        
        Returns:
            dict: Updated notification settings
        
        Example:
            >>> notifications = client.backup_schedules.update_notifications(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_id=1,
            ...     notifications_data={
            ...         "onSuccess": True,
            ...         "onFailure": True,
            ...         "destinations": [1, 2]
            ...     }
            ... )
        """
        return self.client._make_request(
            "PUT",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/{schedule_id}/notifications",
            data=notifications_data
        )
    
    def get_mirrors(
        self,
        volume_id: int,
        repository_id: int,
        schedule_id: int
    ) -> Dict[str, Any]:
        """
        Get mirror settings for a backup schedule.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_id: Schedule ID
        
        Returns:
            dict: Mirror settings
        
        Example:
            >>> mirrors = client.backup_schedules.get_mirrors(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_id=1
            ... )
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/{schedule_id}/mirrors"
        )
    
    def update_mirrors(
        self,
        volume_id: int,
        repository_id: int,
        schedule_id: int,
        mirrors_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update mirror settings for a backup schedule.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_id: Schedule ID
            mirrors_data: Mirror configuration
        
        Returns:
            dict: Updated mirror settings
        
        Example:
            >>> mirrors = client.backup_schedules.update_mirrors(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_id=1,
            ...     mirrors_data={
            ...         "enabled": True,
            ...         "repositories": [2, 3]
            ...     }
            ... )
        """
        return self.client._make_request(
            "PUT",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/{schedule_id}/mirrors",
            data=mirrors_data
        )
    
    def get_mirror_compatibility(
        self,
        volume_id: int,
        repository_id: int,
        schedule_id: int
    ) -> Dict[str, Any]:
        """
        Check mirror compatibility for a backup schedule.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            schedule_id: Schedule ID
        
        Returns:
            dict: Mirror compatibility information
        
        Example:
            >>> compatibility = client.backup_schedules.get_mirror_compatibility(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     schedule_id=1
            ... )
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/{schedule_id}/mirror-compatibility"
        )
    
    def reorder(
        self,
        volume_id: int,
        repository_id: int,
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reorder backup schedules.
        
        Args:
            volume_id: Volume ID
            repository_id: Repository ID
            order_data: New order configuration with schedule IDs
        
        Returns:
            dict: Reorder response
        
        Example:
            >>> response = client.backup_schedules.reorder(
            ...     volume_id=1,
            ...     repository_id=1,
            ...     order_data={"scheduleIds": [3, 1, 2]}
            ... )
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/volumes/{volume_id}/repositories/{repository_id}/backup-schedules/reorder",
            data=order_data
        )
