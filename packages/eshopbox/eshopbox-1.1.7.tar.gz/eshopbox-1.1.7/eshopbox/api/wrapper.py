"""Wrapper API module"""

from typing import Dict, Optional, List
from eshopbox.api.base import BaseAPI


class WrapperAPI(BaseAPI):
    """Handle order-related operations"""

    def order(self, payload: Dict) -> Dict:
        """
        Get all orders with optional filters

        Args:
            payload: Dictionary containing filter parameters and pagination info

        Returns:
            Dict containing order data
        """
        url = f"{self.eshopbox_url}/api/v1/shipping/order"
        return self._make_request("POST", url, json=payload)

    def shipping_return(self, payload: Dict) -> Dict:
        """
        Process a shipping return

        Args:
            payload: Return details including order number and return information

        Returns:
            Dict containing return confirmation
        """
        url = f"{self.eshopbox_url}/api/v1/shipping/return"
        return self._make_request("POST", url, json=payload)

    def cancel_tracking(self, payload: Dict) -> Dict:
        """
        Cancel tracking for a shipment

        Args:
            payload: Dictionary containing tracking cancellation details (e.g., order number, reason)

        Returns:
            Dict containing cancellation confirmation
        """
        url = f"{self.eshopbox_url}/api/v1/shipping/cancel"
        return self._make_request("POST", url, json=payload)

    def tracking_details(self, trackingIds: str) -> Dict:
        """
        Get tracking details for a shipment

        Args:
            params: Dictionary containing tracking query parameters (e.g., order number, shipment ID)

        Returns:
            Dict containing tracking information
        """
        url = f"{self.eshopbox_url}/api/v1/shipping/trackingDetails?={trackingIds}"
        return self._make_request("GET", url)

    def webhook_register(self, body: Dict, ProxyHost: str) -> Dict:
        """
        Registering webhook for tracking shipment

        Args:
            params: Dictionary containing tracking query parameters (e.g., order number, shipment ID)

        Returns:
            Dict containing tracking information
        """
        headers = {
            "ProxyHost": ProxyHost
        }
        url = f"{self.base_url}/api/v1/webhook"
        return self._make_request("POST", url, json=body, headers=headers)
