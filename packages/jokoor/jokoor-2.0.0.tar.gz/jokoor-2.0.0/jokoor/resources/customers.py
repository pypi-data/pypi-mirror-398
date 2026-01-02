"""
Customers resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, Tuple

from ..types import Customer, PaginatedResponse
from ..http_client import HTTPClient


class CustomersResource:
    """Customer operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        email: str,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Customer], Optional[str]]:
        """
        Create or retrieve a customer

        Args:
            email: Customer email (required)
            phone: Customer phone number
            name: Customer name
            metadata: Additional metadata

        Returns:
            Tuple of (Customer object, error) where error is None on success
        """
        data: Dict[str, Any] = {"email": email}

        if phone:
            data["phone"] = phone
        if name:
            data["name"] = name
        if metadata:
            data["metadata"] = metadata

        response, error = self._http.post("/v1/pay/customers", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, customer_id: str) -> Tuple[Optional[Customer], Optional[str]]:
        """Get customer details"""
        response, error = self._http.get(f"/v1/pay/customers/{customer_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self, *, offset: int = 0, limit: int = 20
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """List customers"""
        params = {"offset": offset, "limit": limit}
        response, error = self._http.get("/v1/pay/customers", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        customer_id: str,
        *,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Customer], Optional[str]]:
        """Update customer information"""
        data: Dict[str, Any] = {}
        if email is not None:
            data["email"] = email
        if phone is not None:
            data["phone"] = phone
        if name is not None:
            data["name"] = name
        if metadata is not None:
            data["metadata"] = metadata

        response, error = self._http.put(f"/v1/pay/customers/{customer_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(self, customer_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Delete a customer"""
        response, error = self._http.delete(f"/v1/pay/customers/{customer_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
