"""Webhooks API module"""

from typing import Dict
from eshopbox.api.base import BaseAPI


class WebhooksAPI(BaseAPI):
    """Manage webhooks"""

    def list(self) -> Dict:
        """List all registered webhooks."""
        url = f"{self.base_url}/api/platform/v1/client-webhook"
        return self._make_request("GET", url)

    def create(self, webhook_data: Dict) -> Dict:
        """Create a webhook."""
        url = f"{self.base_url}/api/v1/webhook"
        return self._make_request("POST", url, json=webhook_data)

    def get(self, webhook_id: str) -> Dict:
        """Delete a webhook."""
        url = f"{self.base_url}/api/platform/v1/client-webhook/{webhook_id}"
        return self._make_request("GET", url)

    def update(self, webhook_id: str) -> Dict:
        """Delete a webhook."""
        url = f"{self.base_url}/api/platform/v1/client-webhook"
        return self._make_request("PUT", url)
