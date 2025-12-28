"""Products API module"""

from typing import Dict
from eshopbox.api.base import BaseAPI


class ProductsAPI(BaseAPI):
    """Handle product-related operations"""

    def get_all(self, params) -> Dict:
        """Fetch all products with optional filters."""
        url = f"{self.base_url}/product-engine/api/v1/products"
        return self._make_request("GET", url, params=params)

    def get(self, sku: str) -> Dict:
        """Fetch a single product by SKU."""
        url = f"{self.base_url}/product-engine/api/v1/products/{sku}"
        return self._make_request("GET", url)

    def create(self, product_data: Dict) -> Dict:
        """Create a new product."""
        url = f"{self.base_url}/product-engine/api/v1/products"
        return self._make_request("POST", url, json=product_data)

    def update(self, sku: str, product_data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/product-engine/api/v1/products/{sku}"
        return self._make_request("PUT", url, json=product_data)

    def delete(self, sku: str) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/product-engine/api/v1/products/{sku}"
        return self._make_request("DELETE", url)

    def merge_product(self, product_data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/product-engine/api/v1/mergeProducts"
        return self._make_request("POST", url, json=product_data)

    def product_availability(self, product_data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/product-engine/api/v2/productListing"
        return self._make_request("POST", url, json=product_data)

    def get_all_brands(self) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/brand"
        return self._make_request("GET", url)

    def get_brand(self, id: int) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/brand"
        params = {
            "id": id
        }
        return self._make_request("GET", url, params=params)

    def create_brand(self, product_data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/brand"
        return self._make_request("POST", url, json=product_data)

    def update_brand(self, id, product_data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/brand/{id}"
        return self._make_request("PUT", url, json=product_data)

    def get_inventory_for_given_product_v1(self, product_data: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/productListing"
        return self._make_request("POST", url, json=product_data)

    def get_inventory_for_given_product_v2(self, params: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v2/productListing"
        return self._make_request("GET", url, params=params)

    def get_inventory_summary(self, params: Dict) -> Dict:
        """Update an existing product."""
        url = f"{self.base_url}/api/v1/productListing"
        return self._make_request("GET", url, params=params)
