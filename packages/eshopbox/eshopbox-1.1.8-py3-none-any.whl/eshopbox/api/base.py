"""Base API class for EShopBox"""

import requests
from typing import Dict, Optional, Any
from eshopbox.auth import EShopBoxAuth
from eshopbox.exceptions import APIError, RateLimitError, NotFoundError


class BaseAPI:
    """Base class for all API modules"""

    def __init__(self, workspace: str, auth: EShopBoxAuth):
        """
        Initialize base API

        Args:
            workspace: EShopBox workspace name
            auth: Authentication handler
        """
        self.workspace = workspace
        self.auth = auth
        self.base_url = f"https://{workspace}.myeshopbox.com"
        self.eshopbox_url = f"https://{workspace}.eshopbox.com"

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """
        Make HTTP request with authentication and error handling

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            params: Query parameters
            json: JSON body
            **kwargs: Additional request arguments

        Returns:
            Response data

        Raises:
            APIError: If API returns an error
            RateLimitError: If rate limit is exceeded
            NotFoundError: If resource is not found
        """
        headers = self.auth.get_headers()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers

        if params:
            kwargs['params'] = params
        if json:
            kwargs['json'] = json

        try:
            response = requests.request(method, url, **kwargs)

            # Handle different status codes
            if response.status_code == 404:
                raise NotFoundError(f"Resource not found: {url}")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Please try again later.")
            elif response.status_code >= 400:
                error_msg = self._extract_error_message(response)
                raise APIError(
                    error_msg,
                    status_code=response.status_code,
                    response=response.text
                )

            response.raise_for_status()

            # Return JSON if content exists, otherwise empty dict
            return response.json() if response.content else {}

        except requests.RequestException as e:
            if isinstance(e, (APIError, RateLimitError, NotFoundError)):
                raise
            raise APIError(f"Request failed: {str(e)}")

    def _extract_error_message(self, response: requests.Response) -> str:
        """Extract error message from response"""
        try:
            error_data = response.json()
            return error_data.get('message', error_data.get('error', response.text))
        except:
            return response.text or f"HTTP {response.status_code} Error"
