"""
Payout Recipients resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, List, Tuple, BinaryIO

from ..types import (
    PayoutRecipient,
    RecipientPayout,
    PaginatedResponse,
    BulkPayoutItem,
    BulkPayoutBatch,
    CSVUpload,
)
from ..http_client import HTTPClient


class RecipientsResource:
    """Payout recipient operations (Wave B2P)"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        name: str,
        payout_phone: str,
        email: Optional[str] = None,
        payout_method: str = "wave",
        recipient_type: str = "other",
        internal_reference: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[PayoutRecipient], Optional[str]]:
        """Create a payout recipient"""
        data: Dict[str, Any] = {
            "name": name,
            "payout_phone": payout_phone,
            "payout_method": payout_method,
            "recipient_type": recipient_type,
        }
        if email:
            data["email"] = email
        if internal_reference:
            data["internal_reference"] = internal_reference
        if notes:
            data["notes"] = notes
        if metadata:
            data["metadata"] = metadata

        response, error = self._http.post("/v1/payouts/recipients", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, recipient_id: str) -> Tuple[Optional[PayoutRecipient], Optional[str]]:
        """Get recipient details"""
        response, error = self._http.get(f"/v1/payouts/recipients/{recipient_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        active_only: bool = True,
        payout_phone: Optional[str] = None,
        email: Optional[str] = None,
        query: Optional[str] = None,
        recipient_type: Optional[str] = None,
        internal_reference: Optional[str] = None,
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """List payout recipients with optional search filters

        Args:
            offset: Pagination offset (default: 0)
            limit: Number of results to return (default: 20)
            active_only: Show only active recipients (default: True)
            payout_phone: Filter by payout phone number (exact match)
            email: Filter by email (exact match)
            query: Search in name, email, and payout phone (partial match)
            recipient_type: Filter by type (employee, contractor, member, vendor, other)
            internal_reference: Filter by internal reference (exact match)
        """
        params: Dict[str, Any] = {"offset": offset, "limit": limit, "active_only": active_only}
        if payout_phone:
            params["payout_phone"] = payout_phone
        if email:
            params["email"] = email
        if query:
            params["query"] = query
        if recipient_type:
            params["recipient_type"] = recipient_type
        if internal_reference:
            params["internal_reference"] = internal_reference

        response, error = self._http.get("/v1/payouts/recipients", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        recipient_id: str,
        *,
        name: Optional[str] = None,
        payout_phone: Optional[str] = None,
        email: Optional[str] = None,
        payout_method: Optional[str] = None,
        recipient_type: Optional[str] = None,
        internal_reference: Optional[str] = None,
        notes: Optional[str] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[PayoutRecipient], Optional[str]]:
        """Update recipient information"""
        data: Dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if payout_phone is not None:
            data["payout_phone"] = payout_phone
        if email is not None:
            data["email"] = email
        if payout_method is not None:
            data["payout_method"] = payout_method
        if recipient_type is not None:
            data["recipient_type"] = recipient_type
        if internal_reference is not None:
            data["internal_reference"] = internal_reference
        if notes is not None:
            data["notes"] = notes
        if is_active is not None:
            data["is_active"] = is_active
        if metadata is not None:
            data["metadata"] = metadata

        response, error = self._http.put(f"/v1/payouts/recipients/{recipient_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(self, recipient_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Delete a payout recipient"""
        response, error = self._http.delete(f"/v1/payouts/recipients/{recipient_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def send_payout(
        self,
        *,
        recipient_id: str,
        amount: str,
        description: Optional[str] = None,
        verification_id: Optional[str] = None,
        otp: Optional[str] = None,
    ) -> Tuple[Optional[RecipientPayout], Optional[str]]:
        """Send payout to recipient

        For API key authentication: Only recipient_id and amount are required.
        For session authentication: verification_id and otp are required.

        Args:
            recipient_id: ID of the recipient
            amount: Payout amount (e.g., "100.00")
            description: Optional payout description
            verification_id: OTP verification ID (session auth only)
            otp: 6-digit OTP code (session auth only)
        """
        data: Dict[str, Any] = {"recipient_id": recipient_id, "amount": amount}
        if description:
            data["description"] = description
        if verification_id:
            data["verification_id"] = verification_id
        if otp:
            data["otp"] = otp

        response, error = self._http.post("/v1/payouts/recipients/send", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list_payouts(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        recipient_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """List recipient payouts"""
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if recipient_id:
            params["recipient_id"] = recipient_id
        if status:
            params["status"] = status

        response, error = self._http.get("/v1/payouts/recipients/payouts", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get_payout(self, payout_id: str) -> Tuple[Optional[RecipientPayout], Optional[str]]:
        """Get recipient payout details"""
        response, error = self._http.get(f"/v1/payouts/recipients/payouts/{payout_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def reverse_payout(
        self, payout_id: str, *, otp_code: str, reason: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Reverse a recipient payout (requires OTP)"""
        data: Dict[str, Any] = {"otp_code": otp_code}
        if reason:
            data["reason"] = reason

        response, error = self._http.post(
            f"/v1/payouts/recipients/payouts/{payout_id}/reverse", data
        )
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def send_bulk_payouts(
        self, payouts: List[BulkPayoutItem]
    ) -> Tuple[Optional[BulkPayoutBatch], Optional[str]]:
        """
        Send payouts to multiple recipients in a single batch operation.

        Process up to 100 recipients per batch with Wave B2P.
        Minimum amount per recipient: 100 GMD.

        Note: For API key requests, no OTP required. For session requests,
        use the OTP flow first.

        Args:
            payouts: List of payout items with recipient_id, amount, and optional description

        Returns:
            Tuple of (BulkPayoutBatch with batch status, error message)

        Example:
            >>> payouts = [
            ...     {"recipient_id": "rec_abc123", "amount": "500.00", "description": "Monthly pay"},
            ...     {"recipient_id": "rec_def456", "amount": "750.00", "description": "Bonus"},
            ... ]
            >>> batch, error = client.payout_recipients.send_bulk_payouts(payouts)
            >>> if not error:
            ...     print(f"Batch ID: {batch['id']}")
            ...     print(f"Total: {batch['total_amount']} GMD for {batch['total_count']} recipients")
        """
        # Validate payouts array
        if not payouts or len(payouts) == 0:
            return (None, "At least one payout is required")

        if len(payouts) > 100:
            return (None, "Maximum 100 payouts per batch")

        # Validate each payout has required fields
        for payout in payouts:
            if not payout.get("recipient_id"):
                return (None, "Recipient ID is required for all payouts")
            if not payout.get("amount"):
                return (None, "Amount is required for all payouts")

        data = {"payouts": payouts}
        response, error = self._http.post("/v1/payouts/recipients/send-bulk", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get_bulk_payout_batch(
        self, batch_id: str
    ) -> Tuple[Optional[BulkPayoutBatch], Optional[str]]:
        """
        Get the status and details of a bulk payout batch.

        Returns the batch overview and individual payout statuses.

        Args:
            batch_id: The ID of the bulk payout batch

        Returns:
            Tuple of (BulkPayoutBatch with status details, error message)

        Example:
            >>> batch, error = client.payout_recipients.get_bulk_payout_batch('batch_abc123')
            >>> if not error:
            ...     print(f"Status: {batch['status']}")
            ...     print(f"Successful: {batch['successful_count']}/{batch['total_count']}")
            ...     for payout in batch['payouts']:
            ...         print(f"  {payout['recipient_id']}: {payout['status']}")
        """
        if not batch_id:
            return (None, "Batch ID is required")

        response, error = self._http.get(f"/v1/payouts/recipients/batches/{batch_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def upload_bulk_payout_csv(
        self, file: BinaryIO
    ) -> Tuple[Optional[CSVUpload], Optional[str]]:
        """
        Upload a CSV file containing recipient payout data.

        The CSV will be validated and stored for processing.

        CSV Format:
            recipient_id,amount,description
            rec_abc123,500.00,Monthly payment
            rec_def456,750.00,Bonus payment

        Requirements:
        - Maximum file size: 5MB
        - Maximum 1000 rows
        - Required columns: recipient_id, amount
        - Optional column: description

        Args:
            file: File object (opened in binary mode) containing CSV data

        Returns:
            Tuple of (CSVUpload with upload_id and validation results, error message)

        Example:
            >>> with open('payouts.csv', 'rb') as f:
            ...     upload, error = client.payout_recipients.upload_bulk_payout_csv(f)
            >>> if not error:
            ...     print(f"Upload ID: {upload['upload_id']}")
            ...     print(f"Rows: {upload['rows_count']}")
            ...     print(f"Total: {upload['total_amount']} GMD")
            ...     if upload.get('validation_errors'):
            ...         print(f"Errors: {upload['validation_errors']}")
        """
        if file is None:
            return (None, "File is required")

        # Validate file size (5MB max)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > 5 * 1024 * 1024:  # 5MB
            return (None, "File size exceeds 5MB limit")

        response, error = self._http.upload_file(
            "/v1/payouts/recipients/send-bulk/upload-csv", file
        )
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def process_bulk_payout_csv(
        self, upload_id: str
    ) -> Tuple[Optional[BulkPayoutBatch], Optional[str]]:
        """
        Process a previously uploaded CSV file to create bulk payouts.

        Note: For API key requests, no OTP required. For session requests,
        use the OTP flow first.

        Args:
            upload_id: The ID returned from upload_bulk_payout_csv()

        Returns:
            Tuple of (BulkPayoutBatch created from CSV, error message)

        Example:
            >>> # First upload CSV
            >>> with open('payouts.csv', 'rb') as f:
            ...     upload, error = client.payout_recipients.upload_bulk_payout_csv(f)
            >>> # Then process it
            >>> if not error:
            ...     batch, error = client.payout_recipients.process_bulk_payout_csv(upload['upload_id'])
            ...     if not error:
            ...         print(f"Batch created: {batch['id']}")
        """
        if not upload_id:
            return (None, "Upload ID is required")

        data = {"upload_id": upload_id}
        response, error = self._http.post("/v1/payouts/recipients/send-bulk/csv", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def send_bulk_payouts_by_type(
        self,
        *,
        recipient_type: str,
        amount_per_recipient: str,
        description: Optional[str] = None,
    ) -> Tuple[Optional[BulkPayoutBatch], Optional[str]]:
        """
        Send the same amount to all recipients of a specific type.

        Use cases:
        - Monthly salary payments to all employees
        - Bonus payments to all active vendors
        - Uniform distribution to a category

        Note: For API key requests, no OTP required. For session requests,
        use the OTP flow first.

        Args:
            recipient_type: Type of recipients to send to (e.g., "employee", "vendor")
            amount_per_recipient: Amount to send to each recipient (minimum 100 GMD)
            description: Optional payment description

        Returns:
            Tuple of (BulkPayoutBatch with batch status, error message)

        Example:
            >>> batch, error = client.payout_recipients.send_bulk_payouts_by_type(
            ...     recipient_type="employee",
            ...     amount_per_recipient="5000.00",
            ...     description="Monthly salary - December 2024"
            ... )
            >>> if not error:
            ...     print(f"Sent {batch['total_amount']} GMD to {batch['total_count']} employees")
        """
        if not recipient_type:
            return (None, "Recipient type is required")

        if not amount_per_recipient:
            return (None, "Amount per recipient is required")

        data: Dict[str, Any] = {
            "recipient_type": recipient_type,
            "amount_per_recipient": amount_per_recipient,
        }
        if description:
            data["description"] = description

        response, error = self._http.post(
            "/v1/payouts/recipients/send-bulk/by-type", data
        )
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
