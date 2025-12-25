"""Dolivroo SDK Main Client"""

from typing import Optional
from .http_client import HttpClient
from .resources import Parcels, Rates, Wilayas, Bulk, Schema, Centers
from .exceptions import DolivrooError


class Dolivroo:
    """
    Dolivroo SDK Client
    
    Official Python SDK for the Dolivroo Delivery API.
    Provides a unified interface for shipping operations across multiple carriers in Algeria.
    
    Args:
        api_key: Your Dolivroo API key
        base_url: Custom API endpoint (optional, for self-hosted)
        timeout: Request timeout in seconds (default: 30)
        verify_ssl: Whether to verify SSL certificates (default: True)
    
    Example:
        >>> from dolivroo import Dolivroo
        >>> 
        >>> client = Dolivroo('your-api-key')
        >>> 
        >>> # Create a parcel
        >>> parcel = client.parcels.create('yalidine', {
        ...     'customer': {'first_name': 'Mohamed', 'last_name': 'Ali', 'phone': '0555000000'},
        ...     'destination': {'wilaya': 'Alger', 'commune': 'Bab El Oued'},
        ...     'package': {'products': 'T-Shirt x2'},
        ...     'payment': {'amount': 2500}
        ... })
        >>> print(parcel['tracking_id'])
    """
    
    VERSION = "1.0.0"
    DEFAULT_BASE_URL = "https://dolivroo.com/api/v1/unified"

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        if not api_key:
            raise DolivrooError("API key is required", "MISSING_API_KEY")
        
        self._http = HttpClient(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            timeout=timeout,
            verify_ssl=verify_ssl
        )
        
        # Initialize resources
        self.parcels = Parcels(self._http)
        self.rates = Rates(self._http)
        self.wilayas = Wilayas(self._http)
        self.bulk = Bulk(self._http)
        self.schema = Schema(self._http)
        self.centers = Centers(self._http)

    def ping(self) -> bool:
        """Check API connectivity"""
        try:
            self.schema.get()
            return True
        except Exception:
            return False

    def translate(self, company_code: str, order: dict) -> dict:
        """Translate unified order to provider-specific format"""
        return self._http.post("/translate", {
            "company_code": company_code,
            "order": order
        })

    @property
    def version(self) -> str:
        """Get SDK version"""
        return self.VERSION
