"""Dolivroo SDK HTTP Client"""

from typing import Any, Dict, Optional
import requests
from .exceptions import (
    DolivrooError,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    NotFoundError,
)


class HttpClient:
    """HTTP client for API requests"""
    
    VERSION = "1.0.0"
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dolivroo.com/api/v1/unified",
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"Dolivroo-Python/{self.VERSION}"
        })

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions"""
        try:
            data = response.json() if response.text else {}
        except ValueError:
            data = {"message": response.text}
        
        if response.status_code == 200 or response.status_code == 201:
            return data
        
        message = data.get("message", "Unknown error")
        
        if response.status_code == 401:
            raise AuthenticationError(message)
        elif response.status_code == 404:
            raise NotFoundError(message)
        elif response.status_code == 422:
            raise ValidationError(message, data.get("errors"))
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(message, int(retry_after) if retry_after else None)
        else:
            raise DolivrooError(message, "API_ERROR", response.status_code, data)

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(
            url, 
            params=params, 
            timeout=self.timeout,
            verify=self.verify_ssl
        )
        return self._handle_response(response)

    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(
            url, 
            json=data, 
            timeout=self.timeout,
            verify=self.verify_ssl
        )
        return self._handle_response(response)

    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PUT request"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(
            url, 
            json=data, 
            timeout=self.timeout,
            verify=self.verify_ssl
        )
        return self._handle_response(response)

    def delete(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make DELETE request"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(
            url, 
            params=params, 
            timeout=self.timeout,
            verify=self.verify_ssl
        )
        return self._handle_response(response)
