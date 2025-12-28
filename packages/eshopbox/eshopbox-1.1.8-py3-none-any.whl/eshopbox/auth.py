"""Authentication handler for EShopBox API"""

import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
from eshopbox.exceptions import AuthenticationError


class EShopBoxAuth:
    """Handle authentication for EShopBox API"""
    
    AUTH_URL = "https://auth.myeshopbox.com/api/v1/generateToken"
    TOKEN_EXPIRY_BUFFER = 300  # 5 minutes in seconds
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        """
        Initialize authentication handler
        
        Args:
            client_id: API client ID
            client_secret: API client secret
            refresh_token: Refresh token for generating access tokens
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    def generate_token(self) -> str:
        """
        Generate new access token using refresh token
        
        Returns:
            str: Access token
            
        Raises:
            AuthenticationError: If token generation fails
        """
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(self.AUTH_URL, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            self._access_token = data.get("access_token")
            
            # Set token expiry (assuming 1 hour, adjust based on actual response)
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            return self._access_token
            
        except requests.RequestException as e:
            raise AuthenticationError(f"Failed to generate access token: {str(e)}")
    
    def get_token(self) -> str:
        """
        Get valid access token, generating new one if needed
        
        Returns:
            str: Valid access token
        """
        if self._should_refresh_token():
            self.generate_token()
        
        return self._access_token
    
    def _should_refresh_token(self) -> bool:
        """Check if token should be refreshed"""
        if not self._access_token:
            return True
        
        if not self._token_expires_at:
            return True
        
        # Refresh if token expires within buffer time
        time_until_expiry = (self._token_expires_at - datetime.now()).total_seconds()
        return time_until_expiry < self.TOKEN_EXPIRY_BUFFER
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get authorization headers with valid token
        
        Returns:
            Dict containing authorization headers
        """
        token = self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
