"""
Checkouts resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, List, Tuple

from ..types import Checkout
from ..http_client import HTTPClient


class CheckoutsResource:
    """Checkout operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        amount: Optional[str] = None,
        currency: str = "GMD",
        items: Optional[List[Dict[str, Any]]] = None,
        payment_method_types: Optional[List[str]] = None,
        automatic_payment_methods: Optional[bool] = None,
        payment_method: Optional[str] = None,
        customer_id: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        expires_in: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        reference: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        success_url: Optional[str] = None,
        failure_url: Optional[str] = None,
    ) -> Tuple[Optional[Checkout], Optional[str]]:
        """
        Create a checkout session

        Args:
            amount: Amount in decimal format (optional if items provided)
            currency: Currency code (default: GMD)
            items: Optional itemized line items
            payment_method_types: List of allowed payment method types
            automatic_payment_methods: Enable automatic payment methods (default: true)
            payment_method: Specify payment method to initialize checkout with.
                When provided, checkout will be immediately ready for payment.
                Options: 'card', 'wave', 'afrimoney'. If omitted, customer selects payment method.
            customer_id: Existing customer ID
            customer_phone: Customer phone number
            customer_email: Customer email
            customer_name: Customer name
            expires_in: Expiration time in seconds (60-86400, default: 86400)
            metadata: Additional metadata
            description: Checkout description
            reference: Your internal reference ID
            idempotency_key: Idempotency key for request deduplication
            success_url: URL to redirect after successful payment
            failure_url: URL to redirect after failed payment

        Returns:
            Tuple of (Checkout object, error) where error is None on success
        """
        data: Dict[str, Any] = {"currency": currency}

        if amount:
            data["amount"] = amount
        if items:
            data["items"] = items
        if payment_method_types:
            data["payment_method_types"] = payment_method_types
        if automatic_payment_methods is not None:
            data["automatic_payment_methods"] = automatic_payment_methods
        if payment_method:
            data["payment_method"] = payment_method
        if customer_id:
            data["customer_id"] = customer_id
        if customer_phone:
            data["customer_phone"] = customer_phone
        if customer_email:
            data["customer_email"] = customer_email
        if customer_name:
            data["customer_name"] = customer_name
        if expires_in is not None:
            data["expires_in"] = expires_in
        if metadata:
            data["metadata"] = metadata
        if description:
            data["description"] = description
        if reference:
            data["reference"] = reference
        if idempotency_key:
            data["idempotency_key"] = idempotency_key
        if success_url:
            data["success_url"] = success_url
        if failure_url:
            data["failure_url"] = failure_url

        response, error = self._http.post("/v1/checkouts", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, checkout_id: str) -> Tuple[Optional[Checkout], Optional[str]]:
        """
        Get checkout session details
        
        Args:
            checkout_id: Checkout ID
        
        Returns:
            Tuple of (Checkout object, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/checkouts/{checkout_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def cancel(self, checkout_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Cancel a pending checkout session
        
        Args:
            checkout_id: Checkout ID
        
        Returns:
            Tuple of (success dict, error) where error is None on success
        """
        response, error = self._http.post(f"/v1/checkouts/{checkout_id}/cancel")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
