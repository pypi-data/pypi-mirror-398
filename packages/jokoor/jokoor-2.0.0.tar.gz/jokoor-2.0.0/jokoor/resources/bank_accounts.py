"""
Bank Accounts resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, List, Tuple

from ..types import BankAccount
from ..http_client import HTTPClient


class BankAccountsResource:
    """Bank account operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        account_number: str,
        account_name: str,
        bank_name: str,
        bank_code: str,
        otp_code: str,
    ) -> Tuple[Optional[BankAccount], Optional[str]]:
        """Create a bank account (requires OTP)"""
        data = {
            "account_number": account_number,
            "account_name": account_name,
            "bank_name": bank_name,
            "bank_code": bank_code,
            "otp_code": otp_code,
        }
        response, error = self._http.post("/v1/payouts/bank-accounts", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(self) -> Tuple[Optional[List[BankAccount]], Optional[str]]:
        """List bank accounts"""
        response, error = self._http.get("/v1/payouts/bank-accounts")
        if error:
            return (None, str(error))
        # Response is a dict with 'data' containing array
        if isinstance(response, dict) and "data" in response:
            return (response["data"], None)  # type: ignore
        return (response, None)  # type: ignore

    def set_default(
        self, bank_account_id: str, otp_code: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Set a bank account as default (requires OTP)"""
        data = {"otp_code": otp_code}
        response, error = self._http.put(
            f"/v1/payouts/bank-accounts/{bank_account_id}/set-default", data
        )
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(
        self, bank_account_id: str, otp_code: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Delete a bank account (requires OTP)"""
        data = {"otp_code": otp_code}
        response, error = self._http.request(
            "DELETE", f"/v1/payouts/bank-accounts/{bank_account_id}", data=data
        )
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
