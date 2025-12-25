"""Dolivroo SDK API Resources"""

from typing import Any, Dict, List, Optional
from .http_client import HttpClient


class Parcels:
    """Parcel management operations"""
    
    def __init__(self, http: HttpClient):
        self._http = http

    def create(self, company_code: str, order: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new parcel"""
        return self._http.post("/parcels", {
            "company_code": company_code,
            "order": order
        })

    def get(self, tracking_id: str, company_code: str) -> Dict[str, Any]:
        """Get parcel details"""
        return self._http.get(f"/parcels/{tracking_id}", {"company_code": company_code})

    def list(self, company_code: str, page: int = 1, per_page: int = 25) -> Dict[str, Any]:
        """List all parcels"""
        return self._http.get("/parcels", {
            "company_code": company_code,
            "page": page,
            "per_page": per_page
        })

    def update(self, tracking_id: str, company_code: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a parcel"""
        return self._http.put(f"/parcels/{tracking_id}", {
            "company_code": company_code,
            "order": updates
        })

    def cancel(self, tracking_id: str, company_code: str) -> Dict[str, Any]:
        """Cancel a parcel"""
        return self._http.delete(f"/parcels/{tracking_id}", {"company_code": company_code})

    def get_label(self, tracking_id: str, company_code: str) -> Dict[str, Any]:
        """Get shipping label"""
        return self._http.get(f"/parcels/{tracking_id}/label", {"company_code": company_code})

    def track(self, tracking_id: str, company_code: str) -> Dict[str, Any]:
        """Track parcel status"""
        return self._http.get(f"/parcels/{tracking_id}/track", {"company_code": company_code})


class Rates:
    """Shipping rates operations"""
    
    def __init__(self, http: HttpClient):
        self._http = http

    def get(self, company_code: str, from_wilaya: str, to_wilaya: str) -> Dict[str, Any]:
        """Get shipping rates for a route"""
        return self._http.get("/rates", {
            "company_code": company_code,
            "from_wilaya": from_wilaya,
            "to_wilaya": to_wilaya
        })

    def compare(self, from_wilaya: str, to_wilaya: str) -> Dict[str, Any]:
        """Compare rates across all providers"""
        return self._http.get("/rates/compare", {
            "from_wilaya": from_wilaya,
            "to_wilaya": to_wilaya
        })


class Wilayas:
    """Wilaya (province) operations"""
    
    def __init__(self, http: HttpClient):
        self._http = http

    def list(self, company_code: Optional[str] = None) -> Dict[str, Any]:
        """List all wilayas"""
        params = {"company_code": company_code} if company_code else {}
        return self._http.get("/wilayas", params)

    def get_communes(self, wilaya_id: int, company_code: Optional[str] = None) -> Dict[str, Any]:
        """Get communes for a wilaya"""
        params = {"company_code": company_code} if company_code else {}
        return self._http.get(f"/wilayas/{wilaya_id}/communes", params)


class Bulk:
    """Bulk operations"""
    
    def __init__(self, http: HttpClient):
        self._http = http

    def create_parcels(self, company_code: str, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple parcels at once"""
        return self._http.post("/bulk/parcels", {
            "company_code": company_code,
            "orders": orders
        })


class Schema:
    """API Schema operations"""
    
    def __init__(self, http: HttpClient):
        self._http = http

    def get(self) -> Dict[str, Any]:
        """Get API schema"""
        return self._http.get("/schema")


class Centers:
    """StopDesk centers operations"""
    
    def __init__(self, http: HttpClient):
        self._http = http

    def list(self, company_code: str, wilaya: Optional[str] = None) -> Dict[str, Any]:
        """List delivery centers"""
        params = {"company_code": company_code}
        if wilaya:
            params["wilaya"] = wilaya
        return self._http.get("/centers", params)
