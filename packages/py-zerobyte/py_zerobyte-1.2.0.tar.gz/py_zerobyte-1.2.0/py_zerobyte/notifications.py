"""Notifications API methods."""

from typing import Dict, Any, List, Optional


class NotificationsAPI:
    """Notifications API methods."""
    
    def __init__(self, client):
        """Initialize NotificationsAPI with client instance."""
        self.client = client
    
    def list_destinations(self) -> List[Dict[str, Any]]:
        """
        List all notification destinations.
        
        Returns:
            list: List of notification destinations
        
        Example:
            >>> destinations = client.notifications.list_destinations()
            >>> for dest in destinations:
            ...     print(f"{dest['name']} ({dest['type']})")
        """
        return self.client._make_request("GET", "/api/v1/notification-destinations")
    
    def create_destination(self, destination_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new notification destination.
        
        Args:
            destination_data: Destination configuration including:
                - name (str): Destination name
                - type (str): Destination type (e.g., 'email', 'slack', 'webhook', etc.)
                - config (dict): Type-specific configuration
        
        Returns:
            dict: Created notification destination
        
        Example:
            >>> destination = client.notifications.create_destination({
            ...     "name": "Email Alerts",
            ...     "type": "email",
            ...     "config": {
            ...         "to": "admin@example.com",
            ...         "from": "backup@example.com",
            ...         "smtpHost": "smtp.gmail.com",
            ...         "smtpPort": 587,
            ...         "username": "backup@example.com",
            ...         "password": "app-password"
            ...     }
            ... })
        """
        return self.client._make_request(
            "POST",
            "/api/v1/notification-destinations",
            data=destination_data
        )
    
    def get_destination(self, destination_id: int) -> Dict[str, Any]:
        """
        Get a specific notification destination.
        
        Args:
            destination_id: Destination ID
        
        Returns:
            dict: Notification destination details
        
        Example:
            >>> destination = client.notifications.get_destination(1)
            >>> print(destination['name'])
        """
        return self.client._make_request(
            "GET",
            f"/api/v1/notification-destinations/{destination_id}"
        )
    
    def update_destination(
        self,
        destination_id: int,
        destination_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a notification destination.
        
        Args:
            destination_id: Destination ID
            destination_data: Updated destination configuration
        
        Returns:
            dict: Updated notification destination
        
        Example:
            >>> destination = client.notifications.update_destination(
            ...     1,
            ...     {"name": "Updated Email Alerts"}
            ... )
        """
        return self.client._make_request(
            "PUT",
            f"/api/v1/notification-destinations/{destination_id}",
            data=destination_data
        )
    
    def delete_destination(self, destination_id: int) -> Dict[str, Any]:
        """
        Delete a notification destination.
        
        Args:
            destination_id: Destination ID
        
        Returns:
            dict: Deletion response
        
        Example:
            >>> response = client.notifications.delete_destination(1)
        """
        return self.client._make_request(
            "DELETE",
            f"/api/v1/notification-destinations/{destination_id}"
        )
    
    def test_destination(self, destination_id: int) -> Dict[str, Any]:
        """
        Test a notification destination.
        
        Args:
            destination_id: Destination ID
        
        Returns:
            dict: Test result
        
        Example:
            >>> result = client.notifications.test_destination(1)
            >>> if result['success']:
            ...     print("Notification sent successfully!")
        """
        return self.client._make_request(
            "POST",
            f"/api/v1/notification-destinations/{destination_id}/test"
        )
