"""
Payment Links resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, List, Tuple

from ..types import PaymentLink, PaginatedResponse
from ..http_client import HTTPClient


class PaymentLinksResource:
    """Payment link operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        title: str,
        amount: str,
        currency: str = "GMD",
        description: Optional[str] = None,
        is_variable_amount: bool = False,
        min_amount: Optional[str] = None,
        max_amount: Optional[str] = None,
        expiration_date: Optional[str] = None,
        max_usage_count: Optional[int] = None,
        success_url: Optional[str] = None,
        failure_url: Optional[str] = None,
        collect_customer_info: bool = False,
        custom_fields: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[PaymentLink], Optional[str]]:
        """
        Create a payment link

        Args:
            title: Payment link title
            amount: Fixed amount or "0.00" for customer-specified (variable amount)
            currency: Currency code (default: GMD)
            description: Payment link description
            is_variable_amount: Whether customers can specify their own amount
            min_amount: Minimum amount for variable-amount links
            max_amount: Maximum amount for variable-amount links
            expiration_date: Optional expiration date (ISO 8601 format)
            max_usage_count: Maximum number of times this link can be used
            success_url: URL to redirect to after successful payment
            failure_url: URL to redirect to after failed payment
            collect_customer_info: Whether to collect customer information
            custom_fields: Custom fields to collect from customers
            metadata: Additional metadata as key-value pairs

        Returns:
            Tuple of (PaymentLink object, error) where error is None on success
        """
        data: Dict[str, Any] = {
            "title": title,
            "amount": amount,
            "currency": currency,
        }

        if description:
            data["description"] = description
        if is_variable_amount:
            data["is_variable_amount"] = is_variable_amount
        if min_amount:
            data["min_amount"] = min_amount
        if max_amount:
            data["max_amount"] = max_amount
        if expiration_date:
            data["expiration_date"] = expiration_date
        if max_usage_count is not None:
            data["max_usage_count"] = max_usage_count
        if success_url:
            data["success_url"] = success_url
        if failure_url:
            data["failure_url"] = failure_url
        if collect_customer_info:
            data["collect_customer_info"] = collect_customer_info
        if custom_fields:
            data["custom_fields"] = custom_fields
        if metadata:
            data["metadata"] = metadata

        response, error = self._http.post("/v1/pay/payment-links", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, link_id: str) -> Tuple[Optional[PaymentLink], Optional[str]]:
        """
        Get payment link details

        Args:
            link_id: Payment link ID

        Returns:
            Tuple of (PaymentLink object, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/pay/payment-links/{link_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """
        List payment links

        Args:
            offset: Number of items to skip
            limit: Maximum number of items to return
            status: Filter by status (active, inactive)

        Returns:
            Tuple of (PaginatedResponse, error) where error is None on success
        """
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status

        response, error = self._http.get("/v1/pay/payment-links", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        link_id: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        expiration_date: Optional[str] = None,
        max_usage_count: Optional[int] = None,
        success_url: Optional[str] = None,
        failure_url: Optional[str] = None,
        status: Optional[str] = None,
        collect_customer_info: Optional[bool] = None,
        custom_fields: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[PaymentLink], Optional[str]]:
        """
        Update a payment link

        Args:
            link_id: Payment link ID
            title: Payment link title
            description: Description
            expiration_date: Expiration date for the payment link
            max_usage_count: Maximum number of times this link can be used
            success_url: URL to redirect to after successful payment
            failure_url: URL to redirect to after failed payment
            status: Status (active, inactive)
            collect_customer_info: Whether to collect customer information
            custom_fields: Custom fields to collect from customers
            metadata: Additional metadata

        Returns:
            Tuple of (PaymentLink object, error) where error is None on success
        """
        data: Dict[str, Any] = {}

        if title is not None:
            data["title"] = title
        if description is not None:
            data["description"] = description
        if expiration_date is not None:
            data["expiration_date"] = expiration_date
        if max_usage_count is not None:
            data["max_usage_count"] = max_usage_count
        if success_url is not None:
            data["success_url"] = success_url
        if failure_url is not None:
            data["failure_url"] = failure_url
        if status is not None:
            data["status"] = status
        if collect_customer_info is not None:
            data["collect_customer_info"] = collect_customer_info
        if custom_fields is not None:
            data["custom_fields"] = custom_fields
        if metadata is not None:
            data["metadata"] = metadata

        response, error = self._http.put(f"/v1/pay/payment-links/{link_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(self, link_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Delete a payment link

        Args:
            link_id: Payment link ID

        Returns:
            Tuple of (success dict, error) where error is None on success
        """
        response, error = self._http.delete(f"/v1/pay/payment-links/{link_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
