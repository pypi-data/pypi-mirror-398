"""
Payments resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, Tuple

from ..types import PaymentSession
from ..http_client import HTTPClient


class PaymentsResource:
    """Payment operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def initialize(
        self,
        *,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        session_id: Optional[str] = None,
        payment_method: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_name: Optional[str] = None,
    ) -> Tuple[Optional[PaymentSession], Optional[str]]:
        """
        Initialize a payment session

        Supports two authentication methods:
        - Secret API key (sk_test_xxx or sk_live_xxx): Full access
        - Publishable API key (pk_test_xxx or pk_live_xxx): Limited access with client_secret

        Args:
            object_type: Type of object (payment_link, invoice, checkout, donation, topup)
            object_id: Object ID
            client_secret: Client secret for checkout (alternative to object_type/object_id)
            session_id: Existing session ID to update
            payment_method: Payment method (wave, card, afrimoney, qmoney)
            customer_email: Customer email
            customer_phone: Customer phone
            customer_name: Customer name

        Returns:
            Tuple of (PaymentSession object, error) where error is None on success
        """
        data: Dict[str, Any] = {}

        if object_type:
            data["object_type"] = object_type
        if object_id:
            data["object_id"] = object_id
        if client_secret:
            data["client_secret"] = client_secret
        if session_id:
            data["session_id"] = session_id
        if payment_method:
            data["payment_method"] = payment_method
        if customer_email:
            data["customer_email"] = customer_email
        if customer_phone:
            data["customer_phone"] = customer_phone
        if customer_name:
            data["customer_name"] = customer_name

        response, error = self._http.post("/v1/pay/initialize", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get_status(
        self, session_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get payment status

        Args:
            session_id: Payment session ID (ps_xxx)

        Returns:
            Tuple of (status dict, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/pay/status/{session_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get_session(
        self, session_id: str
    ) -> Tuple[Optional[PaymentSession], Optional[str]]:
        """
        Get payment session details

        Args:
            session_id: Payment session ID (ps_xxx)

        Returns:
            Tuple of (PaymentSession object, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/pay/session/{session_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get_dashboard(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get payment dashboard data

        Returns:
            Tuple of (dashboard data, error) where error is None on success
        """
        response, error = self._http.get("/v1/pay/dashboard")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list_methods(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        List enabled payment methods

        Returns:
            Tuple of (payment methods list, error) where error is None on success
        """
        response, error = self._http.get("/v1/pay/methods")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update_settings(
        self, enabled_methods: list
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Update payment settings

        Args:
            enabled_methods: List of enabled payment methods

        Returns:
            Tuple of (settings dict, error) where error is None on success
        """
        data = {"enabled_methods": enabled_methods}
        response, error = self._http.put("/v1/pay/settings", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
