"""
Invoices resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from ..types import Invoice, InvoiceLineItem, PaginatedResponse
from ..http_client import HTTPClient


class InvoicesResource:
    """Invoice operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        items: List[InvoiceLineItem],
        currency: str,
        due_date: datetime,
        customer_id: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_address: Optional[str] = None,
        customer_phone: Optional[str] = None,
        tax_rate: float = 0.0,
        notes: Optional[str] = None,
        is_draft: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Invoice], Optional[str]]:
        """
        Create an invoice

        Args:
            items: List of invoice line items (required, minimum 1)
            currency: Currency code (e.g., "GMD")
            due_date: Invoice due date (ISO 8601 format)
            customer_id: ID of existing customer (if provided, customer data is auto-filled)
            customer_email: Customer email (required if customer_id not provided)
            customer_name: Customer name (required if customer_id not provided)
            customer_address: Customer address (optional)
            customer_phone: Customer phone number (optional)
            tax_rate: Tax rate as percentage (0-100), defaults to 0
            notes: Additional notes or terms
            is_draft: Create as draft if true
            metadata: Additional metadata

        Returns:
            Tuple of (Invoice object, error) where error is None on success
        """
        data: Dict[str, Any] = {
            "items": items,
            "currency": currency,
            "due_date": (
                due_date.isoformat() if isinstance(due_date, datetime) else due_date
            ),
        }

        if customer_id:
            data["customer_id"] = customer_id
        if customer_email:
            data["customer_email"] = customer_email
        if customer_name:
            data["customer_name"] = customer_name
        if customer_address:
            data["customer_address"] = customer_address
        if customer_phone:
            data["customer_phone"] = customer_phone
        if tax_rate != 0.0:
            data["tax_rate"] = tax_rate
        if notes:
            data["notes"] = notes
        if is_draft:
            data["is_draft"] = is_draft
        if metadata:
            data["metadata"] = metadata

        response, error = self._http.post("/v1/pay/invoices", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, invoice_id: str) -> Tuple[Optional[Invoice], Optional[str]]:
        """
        Get invoice details

        Args:
            invoice_id: Invoice ID

        Returns:
            Tuple of (Invoice object, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/pay/invoices/{invoice_id}")
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
        List invoices

        Args:
            offset: Number of items to skip
            limit: Maximum number of items to return
            status: Filter by status (draft, open, paid, cancelled, uncollectible)

        Returns:
            Tuple of (PaginatedResponse, error) where error is None on success
        """
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status

        response, error = self._http.get("/v1/pay/invoices", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        invoice_id: str,
        *,
        items: Optional[List[InvoiceLineItem]] = None,
        due_date: Optional[datetime] = None,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_address: Optional[str] = None,
        customer_phone: Optional[str] = None,
        tax_rate: Optional[float] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Invoice], Optional[str]]:
        """
        Update a draft invoice

        Args:
            invoice_id: Invoice ID
            items: Invoice line items
            due_date: Due date
            customer_email: Customer email
            customer_name: Customer name
            customer_address: Customer address
            customer_phone: Customer phone
            tax_rate: Tax rate (0-100)
            notes: Additional notes
            metadata: Additional metadata

        Returns:
            Tuple of (Invoice object, error) where error is None on success
        """
        data: Dict[str, Any] = {}

        if items is not None:
            data["items"] = items
        if due_date is not None:
            data["due_date"] = (
                due_date.isoformat() if isinstance(due_date, datetime) else due_date
            )
        if customer_email is not None:
            data["customer_email"] = customer_email
        if customer_name is not None:
            data["customer_name"] = customer_name
        if customer_address is not None:
            data["customer_address"] = customer_address
        if customer_phone is not None:
            data["customer_phone"] = customer_phone
        if tax_rate is not None:
            data["tax_rate"] = tax_rate
        if notes is not None:
            data["notes"] = notes
        if metadata is not None:
            data["metadata"] = metadata

        response, error = self._http.put(f"/v1/pay/invoices/{invoice_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def finalize(self, invoice_id: str) -> Tuple[Optional[Invoice], Optional[str]]:
        """
        Finalize a draft invoice

        Args:
            invoice_id: Invoice ID

        Returns:
            Tuple of (Invoice object, error) where error is None on success
        """
        response, error = self._http.post(f"/v1/pay/invoices/{invoice_id}/finalize")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def send(self, invoice_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Send an invoice to the customer via email

        Args:
            invoice_id: Invoice ID

        Returns:
            Tuple of (success dict, error) where error is None on success
        """
        response, error = self._http.post(f"/v1/pay/invoices/{invoice_id}/send")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def cancel(self, invoice_id: str) -> Tuple[Optional[Invoice], Optional[str]]:
        """
        Cancel an open invoice

        Args:
            invoice_id: Invoice ID

        Returns:
            Tuple of (Invoice object, error) where error is None on success
        """
        response, error = self._http.post(f"/v1/pay/invoices/{invoice_id}/cancel")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def download_pdf(self, invoice_id: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Download invoice as PDF

        Args:
            invoice_id: Invoice ID

        Returns:
            Tuple of (PDF bytes, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/pay/invoices/{invoice_id}/pdf")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def record_payment(
        self,
        invoice_id: str,
        *,
        amount: str,
        payment_method: str,
        transaction_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Tuple[Optional[Invoice], Optional[str]]:
        """
        Record a payment against an invoice

        Args:
            invoice_id: Invoice ID
            amount: Payment amount
            payment_method: Payment method used
            transaction_id: Optional external transaction ID
            notes: Optional payment notes

        Returns:
            Tuple of (Invoice object, error) where error is None on success

        Example:
            ```python
            data, error = jokoor.invoices.record_payment(
                'inv_123',
                amount='500.00',
                payment_method='bank_transfer',
                transaction_id='TXN123456',
                notes='Payment received via bank transfer'
            )
            ```
        """
        if not invoice_id:
            return (None, "Invoice ID is required")

        if not amount:
            return (None, "Payment amount is required")

        if not payment_method:
            return (None, "Payment method is required")

        data: Dict[str, Any] = {
            "amount": amount,
            "payment_method": payment_method,
        }

        if transaction_id:
            data["transaction_id"] = transaction_id
        if notes:
            data["notes"] = notes

        response, error = self._http.post(
            f"/v1/pay/invoices/{invoice_id}/payments", data
        )
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list_payments(
        self, invoice_id: str
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        List all payments recorded against an invoice

        Args:
            invoice_id: Invoice ID

        Returns:
            Tuple of (list of payments, error) where error is None on success

        Example:
            ```python
            payments, error = jokoor.invoices.list_payments('inv_123')
            if error:
                print(f"Error: {error}")
            else:
                for payment in payments:
                    print(f"Payment: {payment['amount']}")
            ```
        """
        if not invoice_id:
            return (None, "Invoice ID is required")

        response, error = self._http.get(f"/v1/pay/invoices/{invoice_id}/payments")
        if error:
            return (None, str(error))

        # Extract payments array from response
        if response and isinstance(response, list):
            return (response, None)

        return (response, None)  # type: ignore

    def get_receipts(
        self, invoice_id: str
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Get all payment receipts associated with an invoice

        Args:
            invoice_id: Invoice ID

        Returns:
            Tuple of (list of receipts, error) where error is None on success

        Example:
            ```python
            receipts, error = jokoor.invoices.get_receipts('inv_123')
            if error:
                print(f"Error: {error}")
            else:
                for receipt in receipts:
                    print(f"Receipt: {receipt['receipt_number']}")
            ```
        """
        if not invoice_id:
            return (None, "Invoice ID is required")

        response, error = self._http.get(f"/v1/pay/invoices/{invoice_id}/receipts")
        if error:
            return (None, str(error))

        # Extract receipts array from response
        if response and isinstance(response, list):
            return (response, None)

        return (response, None)  # type: ignore
