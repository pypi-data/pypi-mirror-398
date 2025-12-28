"""Returns API module"""

from typing import Dict
from eshopbox.api.base import BaseAPI


class ReturnsAPI(BaseAPI):
    """Handle returns operations"""

    def get_all(self, page: int = 1) -> Dict:
        """Fetch all returns."""
        url = f"{self.base_url}/api/v1/returns"
        params = {"page": page}
        return self._make_request("GET", url, params=params)

    def get(self, return_id: str) -> Dict:
        """Fetch return details."""
        url = f"{self.eshopbox_url}/api/return/{return_id}"
        return self._make_request("GET", url)

    def create(self, return_data: Dict) -> Dict:
        """Create a return request."""
        url = f"{self.eshopbox_url}/api/return"
        return self._make_request("POST", url, json=return_data)
