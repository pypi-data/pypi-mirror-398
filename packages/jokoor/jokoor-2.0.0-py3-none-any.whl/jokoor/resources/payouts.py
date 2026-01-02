"""
Payouts resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, Tuple

from ..types import PayoutBalance, PayoutRequest, PaginatedResponse, DepositTransaction
from ..http_client import HTTPClient


class PayoutsResource:
    """Payout operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def get_balance(self) -> Tuple[Optional[PayoutBalance], Optional[str]]:
        """Get payout balance"""
        response, error = self._http.get("/v1/payouts/balance")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def create_request(
        self, *, amount: str, bank_account_id: str, otp_code: str
    ) -> Tuple[Optional[PayoutRequest], Optional[str]]:
        """Create a payout request (requires OTP)"""
        data = {"amount": amount, "bank_account_id": bank_account_id, "otp_code": otp_code}
        response, error = self._http.post("/v1/payouts/requests", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get_request(self, request_id: str) -> Tuple[Optional[PayoutRequest], Optional[str]]:
        """Get payout request details"""
        response, error = self._http.get(f"/v1/payouts/requests/{request_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list_requests(
        self, *, offset: int = 0, limit: int = 20, status: Optional[str] = None
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """List payout requests"""
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status

        response, error = self._http.get("/v1/payouts/requests", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def cancel_request(
        self, request_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Cancel a pending payout request"""
        response, error = self._http.put(f"/v1/payouts/requests/{request_id}/cancel")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list_deposits(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """
        List deposit transactions that added funds to payout balance.

        Deposits are created when:
        - Payments are settled to your balance
        - Refunds are reversed and returned to your balance
        - Manual deposits are made

        Args:
            offset: Number of items to skip (default: 0)
            limit: Maximum number of items to return (default: 20, max: 100)
            start_date: Filter deposits after this date (ISO 8601 format)
            end_date: Filter deposits before this date (ISO 8601 format)

        Returns:
            Tuple of (PaginatedResponse with deposit items, error message)

        Example:
            >>> deposits, error = client.payouts.list_deposits(limit=50)
            >>> if not error:
            ...     for deposit in deposits['items']:
            ...         print(f"{deposit['amount']} from {deposit['source']}")
        """
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response, error = self._http.get("/v1/payouts/deposits", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get_deposit(
        self, transaction_id: str
    ) -> Tuple[Optional[DepositTransaction], Optional[str]]:
        """
        Get details of a specific deposit transaction.

        Args:
            transaction_id: The ID of the deposit transaction

        Returns:
            Tuple of (DepositTransaction, error message)

        Example:
            >>> deposit, error = client.payouts.get_deposit('txn_abc123')
            >>> if not error:
            ...     print(f"Deposit: {deposit['amount']} {deposit['currency']}")
            ...     print(f"Source: {deposit['source']} ({deposit['source_id']})")
            ...     print(f"Status: {deposit['status']}")
        """
        if not transaction_id:
            return (None, "Transaction ID is required")

        response, error = self._http.get(f"/v1/payouts/deposits/{transaction_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
