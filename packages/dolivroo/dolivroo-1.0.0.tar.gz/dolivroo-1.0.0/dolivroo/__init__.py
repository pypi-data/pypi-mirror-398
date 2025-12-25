"""
Dolivroo Python SDK

Official SDK for the Dolivroo Delivery API.
Unified interface for shipping operations across multiple carriers in Algeria.

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
"""

from .client import Dolivroo
from .exceptions import (
    DolivrooError,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    NotFoundError,
)
from .resources import Parcels, Rates, Wilayas, Bulk, Schema

__version__ = "1.0.0"
__all__ = [
    "Dolivroo",
    "DolivrooError",
    "AuthenticationError", 
    "ValidationError",
    "RateLimitError",
    "NotFoundError",
    "Parcels",
    "Rates",
    "Wilayas",
    "Bulk",
    "Schema",
]
