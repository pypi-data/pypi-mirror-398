"""
Refunds resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, Tuple

from ..types import Refund, PaginatedResponse
from ..http_client import HTTPClient


class RefundsResource:
    """Refund operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self, transaction_id: str, *, amount: Optional[str] = None, reason: Optional[str] = None
    ) -> Tuple[Optional[Refund], Optional[str]]:
        """Refund a transaction"""
        data: Dict[str, Any] = {}
        if amount:
            data["amount"] = amount
        if reason:
            data["reason"] = reason

        response, error = self._http.post(f"/v1/pay/transactions/{transaction_id}/refund", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, refund_id: str) -> Tuple[Optional[Refund], Optional[str]]:
        """Get refund details"""
        response, error = self._http.get(f"/v1/pay/refunds/{refund_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self, *, offset: int = 0, limit: int = 20
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """List refunds"""
        params = {"offset": offset, "limit": limit}
        response, error = self._http.get("/v1/pay/refunds", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
