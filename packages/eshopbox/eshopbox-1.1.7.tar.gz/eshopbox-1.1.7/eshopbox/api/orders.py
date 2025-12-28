"""Orders API module"""

from typing import Dict, Optional, List
from eshopbox.api.base import BaseAPI


class OrdersAPI(BaseAPI):
    """Handle order-related operations"""
    
    def get_all(self, page: int = 1, **filters) -> Dict:
        """
        Get all orders with optional filters
        
        Args:
            page: Page number for pagination
            **filters: Additional filter parameters
            
        Returns:
            Dict containing order data
        """
        url = f"{self.base_url}/api/v1/orders/erp"
        params = {"filters": f"page={page}"}
        params.update(filters)
        return self._make_request("GET", url, params=params)
    
    def get(self, customer_order_number: str) -> Dict:
        """
        Get a specific order by customer order number
        
        Args:
            customer_order_number: Unique order identifier
            
        Returns:
            Dict containing order details
        """
        url = f"{self.eshopbox_url}/api/order/{customer_order_number}"
        return self._make_request("GET", url)
    
    def create(self, order_data: Dict) -> Dict:
        """
        Create a new order
        
        Args:
            order_data: Order information including items, addresses, etc.
            
        Returns:
            Dict containing created order details
            
        Example:
            >>> order = {
            ...     "externalChannelID": "CH1234",
            ...     "customerOrderNumber": "ORD123",
            ...     "items": [...],
            ...     "shippingAddress": {...}
            ... }
            >>> result = api.orders.create(order)
        """
        url = f"{self.eshopbox_url}/api/order"
        return self._make_request("POST", url, json=order_data)
    
    def cancel(self, cancel_data: Dict) -> Dict:
        """
        Cancel an order
        
        Args:
            cancel_data: Cancellation details including order number and reason
            
        Returns:
            Dict containing cancellation confirmation
        """
        url = f"{self.eshopbox_url}/api/cancel-order"
        return self._make_request("POST", url, json=cancel_data)
    
    def get_invoice(self, order_number: str) -> Dict:
        """
        Get invoice details for an order
        
        Args:
            order_number: Order number
            
        Returns:
            Dict containing invoice details
        """
        url = f"{self.eshopbox_url}/api/invoice-detail/{order_number}"
        return self._make_request("GET", url)
