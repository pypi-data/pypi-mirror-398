"""Payments API module"""

from typing import Dict
from eshopbox.api.base import BaseAPI


class PaymentsAPI(BaseAPI):
    """Handle product-related operations"""

    def get_payouts(self) -> Dict:
        """Fetch all products with optional filters."""
        url = f"{self.base_url}/payments/api/v1/payout"
        return self._make_request("GET", url)

    def get_payout(self, params: Dict) -> Dict:
        """Fetch a single product by SKU."""
        url = f"{self.base_url}/payments/api/v1/payout"
        return self._make_request("GET", url, params=params)

    def create_payout(self, payload: Dict) -> Dict:
        """Create a new product."""
        url = f"{self.base_url}/payments/api/v1/payout"
        return self._make_request("POST", url, json=payload)

    def update_fee(self, payload) -> Dict:
        """Create a new product."""
        url = f"{self.base_url}/payments/api/v1/fee"
        return self._make_request("PUT", url, json=payload)

    def create_fee(self, payload: Dict) -> Dict:
        """Create a new product."""
        url = f"{self.base_url}/payments/api/v1/fee"
        return self._make_request("POST", url, json=payload)

    def get_all_fee(self) -> Dict:
        """Create a new product."""
        url = f"{self.base_url}/payments/api/v1/fee"
        return self._make_request("GET", url)

    def get_fee(self, params: Dict) -> Dict:
        """Create a new product."""
        url = f"{self.base_url}/payments/api/v1/fee"
        return self._make_request("GET", url, params=params)

    def get_all_transaction_rules(self) -> Dict:
        """Create a new product."""
        url = f"{self.base_url}/payments/api/v1/transactionRules"
        return self._make_request("GET", url)

    def get_transaction_rule(self, params: Dict) -> Dict:
        """Create a new product."""
        url = f"{self.base_url}/payments/api/v1/transactionRules"
        return self._make_request("GET", url, params=params)

    def create_transaction_rule(self, payload: Dict) -> Dict:
        """Create a new product."""
        url = f"{self.base_url}/payments/api/v1/transactionRules"
        return self._make_request("POST", url, json=payload)

    def update_transaction_rule(self, payload: Dict) -> Dict:
        """Create a new product."""
        url = f"{self.base_url}/payments/api/v1/transactionRules"
        return self._make_request("PUT", url, json=payload)
