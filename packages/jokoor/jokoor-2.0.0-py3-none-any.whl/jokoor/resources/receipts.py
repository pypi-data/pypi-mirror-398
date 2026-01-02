"""
Receipts resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, Tuple

from ..types import Receipt, PaginatedResponse
from ..http_client import HTTPClient


class ReceiptsResource:
    """Receipt operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """
        List all payment receipts

        Args:
            offset: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            Tuple of (PaginatedResponse, error) where error is None on success

        Example:
            ```python
            data, error = jokoor.receipts.list(offset=0, limit=20)
            if error:
                print(f"Error: {error}")
            else:
                for receipt in data['receipts']:
                    print(f"Receipt {receipt['receipt_number']}: {receipt['amount']}")
            ```
        """
        params: Dict[str, Any] = {"offset": offset, "limit": limit}

        response, error = self._http.get("/v1/pay/receipts", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, receipt_id: str) -> Tuple[Optional[Receipt], Optional[str]]:
        """
        Get receipt details by ID

        Args:
            receipt_id: Receipt ID

        Returns:
            Tuple of (Receipt object, error) where error is None on success

        Example:
            ```python
            data, error = jokoor.receipts.get('rec_1a2b3c4d5e6f')
            if error:
                print(f"Error: {error}")
            else:
                print(f"Receipt: {data['receipt_number']}")
            ```
        """
        if not receipt_id:
            return (None, "Receipt ID is required")

        response, error = self._http.get(f"/v1/pay/receipts/{receipt_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get_by_number(
        self, receipt_number: str
    ) -> Tuple[Optional[Receipt], Optional[str]]:
        """
        Get receipt by receipt number

        Args:
            receipt_number: Receipt number (e.g., "RCT-2024-001")

        Returns:
            Tuple of (Receipt object, error) where error is None on success

        Example:
            ```python
            data, error = jokoor.receipts.get_by_number('RCT-2024-001')
            if error:
                print(f"Error: {error}")
            else:
                print(f"Receipt found: {data['id']}")
            ```
        """
        if not receipt_number:
            return (None, "Receipt number is required")

        response, error = self._http.get(f"/v1/pay/receipts/number/{receipt_number}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def download(self, receipt_id: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Download receipt as PDF

        Args:
            receipt_id: Receipt ID

        Returns:
            Tuple of (PDF bytes, error) where error is None on success

        Example:
            ```python
            pdf_data, error = jokoor.receipts.download('rec_1a2b3c4d5e6f')
            if error:
                print(f"Error: {error}")
            else:
                with open('receipt.pdf', 'wb') as f:
                    f.write(pdf_data)
            ```
        """
        if not receipt_id:
            return (None, "Receipt ID is required")

        response, error = self._http.get(f"/v1/pay/receipts/{receipt_id}/download")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
