"""Serviceability API module"""

from typing import Dict
from eshopbox.api.base import BaseAPI


class ServiceabilityAPI(BaseAPI):
    """Check whether a PIN code or region is serviceable"""

    def pincodeserviceability(self, payload: Dict) -> Dict:
        """Get serviceability based on drop pincode, pickup pincode and product dimension."""
        url = f"{self.base_url}/api/v2/pincodeserviceability"
        return self._make_request("POST", url, json=payload)

    def productserviceability(self, payload: Dict) -> Dict:
        """Get Serviciability for Drop pincode and product sku."""
        url = f"{self.base_url}/api/v2/check/product/serviceability"
        return self._make_request("POST", url, json=payload)

    def checkpincodeserviceability(self, payload: Dict) -> Dict:
        """Get serviceability for pickup and drop pincode."""
        url = f"{self.base_url}/api/v1/checkpincodeserviceability"
        return self._make_request("POST", url, json=payload)

    def bulkPincodeServiceability(self, params: Dict) -> Dict:
        """Get Bulk Pincode Serviceability."""
        url = f"{self.base_url}/shipping-wms/api/v1/bulkPincodeServiceability"
        return self._make_request("GET", url, params=params)
