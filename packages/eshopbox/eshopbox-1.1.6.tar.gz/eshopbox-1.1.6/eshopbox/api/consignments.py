"""Consignments API module"""

from typing import Dict
from eshopbox.api.base import BaseAPI


class ConsignmentsAPI(BaseAPI):
    """Handle consignments operations"""

    def get_all(self, page: int = 1) -> Dict:
        """Fetch all consignments."""
        url = f"{self.base_url}/api/v1/consignments"
        params = {"page": page}
        return self._make_request("GET", url, params=params)

    def get(self, consignment_id: str) -> Dict:
        """Fetch consignment details by ID."""
        url = f"{self.eshopbox_url}/api/consignment/{consignment_id}"
        return self._make_request("GET", url)

    def create(self, consignment_data: Dict) -> Dict:
        """Create a new consignment."""
        url = f"{self.eshopbox_url}/api/consignment"
        return self._make_request("POST", url, json=consignment_data)
