"""Settings API module"""

from typing import Dict
from eshopbox.api.base import BaseAPI


class SettingsAPI(BaseAPI):
    """Handle product-related operations"""

    def get_portals(self) -> Dict:
        """Fetch all products with optional filters."""
        url = f"{self.base_url}/api/v1/portal"
        return self._make_request("GET", url)

    def create_workspace(self, data: Dict) -> Dict:
        """Fetch a single product by SKU."""
        url = f"{self.base_url}/api/v1/account"
        return self._make_request("POST", url, json=data)

    def get_all_workspace(self, params: Dict) -> Dict:
        """Create a new product."""
        url = f"{self.base_url}/api/v1/account"
        return self._make_request("GET", url, params=params)

    def get_workspace(self) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/account/profile"
        return self._make_request("GET", url)

    def update_workspace(self, data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/account/profile"
        return self._make_request("PUT", url, json=data)

    def create_sales_channel(self, data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/channel"
        return self._make_request("POST", url, json=data)

    def update_sales_channel(self, id, data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/channel/{id}"
        return self._make_request("PUT", url, json=data)

    def get_all_sales_channel(self) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/channel"
        return self._make_request("GET", url)

    def get_sales_channel(self, id: int) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/channel/{id}"
        return self._make_request("GET", url)

    def create_fc_submission(self, product_data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/subscription"
        return self._make_request("POST", url, json=product_data)

    def get_all_fc_submission(self) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/warehouse"
        return self._make_request("GET", url)

    def get_fc_submission(self, id: int) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/platform/v1/client-webhook/{id}"
        return self._make_request("GET", url)

    def update_fc_submission(self, id: int, data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/subscription/{id}"
        return self._make_request("PUT", url, json=data)

    def create_contact(self, data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/contact"
        return self._make_request("POST", url, json=data)

    def get_all_contact(self) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/contacts"
        return self._make_request("GET", url)

    def get_contact(self, params: Dict = {}) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/contact"
        return self._make_request("GET", url, params=params)

    def update_contact(self, contactCode: str, data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/contact/{contactCode}"
        return self._make_request("PUT", url, json=data)

    def create_team_member(self, data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/user-account-mapping"
        return self._make_request("POST", url, json=data)

    def update_team_member(self, id, data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/user-account-mapping/{id}"
        return self._make_request("PUT", url, json=data)

    def get_team_member(self, id,) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/user-account-mapping/{id}"
        return self._make_request("GET", url)

    def get_all_team_member(self) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/user"
        return self._make_request("GET", url)
