"""Shipments API module"""

from typing import Dict
from eshopbox.api.base import BaseAPI


class ShipmentsAPI(BaseAPI):
    """Handle shipment-related operations"""

    def get_all(self, page: int = 1) -> Dict:
        """Get all shipments."""
        url = f"{self.eshopbox_url}/api/order/shipment"
        params = {"page": page}
        return self._make_request("GET", url, params=params)

    def get(self, externalShipmentId: str) -> Dict:
        """Get a shipment."""
        url = f"{self.eshopbox_url}/api/order/shipment/{externalShipmentId}"
        return self._make_request("GET", url)

    def create(self, payload: Dict) -> Dict:
        """Create a shipment."""
        url = f"{self.eshopbox_url}/api/order/shipment"
        return self._make_request("POST", url, json=payload)

    def update(self, externalShipmentID: str, status: str) -> Dict:
        """Create a shipment."""
        url = f"{self.eshopbox_url}/api/order/shipment/{externalShipmentID}/mark{status}"
        return self._make_request("PUT", url)
