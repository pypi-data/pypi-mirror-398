"""Inventory API module"""

from typing import Dict
from eshopbox.api.base import BaseAPI


class InventoryAPI(BaseAPI):
    """Handle shipment-related operations"""

    def get_inventory(self, payload: Dict) -> Dict:
        """Get inventory listing."""
        url = f"{self.base_url}/api/v1/inventoryListing"
        return self._make_request("POST", url, json=payload)

    def get_inventory_summary(self) -> Dict:
        """Get inventory summary."""
        url = f"{self.base_url}/api/v1/inventorySummary"
        return self._make_request("GET", url)
