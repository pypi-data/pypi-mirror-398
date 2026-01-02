"""
Transactions resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from ..types import Transaction, PaginatedResponse
from ..http_client import HTTPClient


class TransactionsResource:
    """Transaction operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def get(self, transaction_id: str) -> Tuple[Optional[Transaction], Optional[str]]:
        """Get transaction details"""
        response, error = self._http.get(f"/v1/pay/transactions/{transaction_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """List transactions"""
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status
        if start_date:
            params["start_date"] = start_date.isoformat() if isinstance(start_date, datetime) else start_date
        if end_date:
            params["end_date"] = end_date.isoformat() if isinstance(end_date, datetime) else end_date

        response, error = self._http.get("/v1/pay/transactions", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
