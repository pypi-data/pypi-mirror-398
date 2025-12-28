"""OrderStatusUpdate API module"""

from typing import Dict
from eshopbox.api.base import BaseAPI


class OrderStatusUpdateAPI(BaseAPI):
    """Handle shipment-related operations"""

    def create_label_and_awb(self, payload: Dict) -> Dict:
        """Create Label And Awb."""
        url = f"{self.eshopbox_url}/api/unicommerce/orders/labels"
        return self._make_request("POST", url, json=payload)

    def get_awb_and_courier_name(self, params: Dict) -> Dict:
        """Get Awb And Courier Name."""
        url = f"{self.eshopbox_url}/api/unicommerce/courierDetails"
        return self._make_request("GET", url, params=params)

    def dispatch_shipment(self, payload: Dict) -> Dict:
        """Dispatch Shipment."""
        url = f"{self.eshopbox_url}/api/unicommerce/orders/dispatch"
        return self._make_request("POST", url, json=payload)

    def courier_details_for_return(self, externalShipmentID: str) -> Dict:
        """Courier Details For Return."""
        url = f"{self.eshopbox_url}/api/get-return-courier/{externalShipmentID}"
        return self._make_request("GET", url)

    def update(self, payload: Dict) -> Dict:
        """Update Order Status."""
        url = f"{self.eshopbox_url}/api/update-status"
        return self._make_request("POST", url, json=payload)
