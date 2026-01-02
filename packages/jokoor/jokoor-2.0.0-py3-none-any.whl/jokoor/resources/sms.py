"""
SMS resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from ..types import SMS, PaginatedResponse
from ..http_client import HTTPClient


class SMSResource:
    """SMS message operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def send(
        self,
        *,
        recipient_phone: Optional[str] = None,
        contact_id: Optional[str] = None,
        message_body: Optional[str] = None,
        template_id: Optional[str] = None,
        template_params: Optional[Dict[str, str]] = None,
        sender_id: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        is_draft: bool = False,
    ) -> Tuple[Optional[SMS], Optional[str]]:
        """
        Send an SMS message

        Either recipient_phone or contact_id must be provided.
        Either message_body or template_id must be provided.

        Args:
            recipient_phone: Recipient phone number in E.164 format (e.g., '+2207654321')
            contact_id: Contact ID (alternative to recipient_phone)
            message_body: SMS message text (required if template_id not provided)
            template_id: Template ID to use (required if message_body not provided)
            template_params: Template parameters for variable substitution
            sender_id: Custom sender ID
            scheduled_at: Schedule message for future delivery (ISO 8601)
            is_draft: Save as draft without sending

        Returns:
            Tuple of (SMS object, error) where error is None on success

        Example:
            >>> sms, error = client.sms.send(
            ...     recipient_phone='+2207654321',
            ...     message_body='Hello from Jokoor!'
            ... )
            >>> if error:
            ...     print(f"Error: {error}")
            ... else:
            ...     print(f"SMS sent: {sms['id']}")
        """
        data: Dict[str, Any] = {"is_draft": is_draft}

        if recipient_phone:
            data["recipient_phone"] = recipient_phone
        if contact_id:
            data["contact_id"] = contact_id
        if message_body:
            data["message_body"] = message_body
        if template_id:
            data["template_id"] = template_id
        if template_params:
            data["template_params"] = template_params
        if sender_id:
            data["sender_id"] = sender_id
        if scheduled_at:
            data["scheduled_at"] = self._format_datetime(scheduled_at)

        response, error = self._http.post("/v1/sms", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, sms_id: str) -> Tuple[Optional[SMS], Optional[str]]:
        """
        Get SMS message details

        Args:
            sms_id: SMS message ID

        Returns:
            Tuple of (SMS object, error) where error is None on success
        """
        if not sms_id:
            return (None, "SMS ID is required")

        response, error = self._http.get(f"/v1/sms/{sms_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        contact_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """
        List SMS messages

        Args:
            offset: Number of items to skip (default: 0)
            limit: Maximum number of items to return (default: 20, max: 100)
            status: Filter by status (draft, queued, sending, sent, delivered, failed, cancelled)
            contact_id: Filter by contact ID
            start_date: Filter messages created after this date
            end_date: Filter messages created before this date

        Returns:
            Tuple of (PaginatedResponse with SMS objects, error) where error is None on success
        """
        params: Dict[str, Any] = {"offset": offset, "limit": limit}

        if status:
            params["status"] = status
        if contact_id:
            params["contact_id"] = contact_id
        if start_date:
            params["start_date"] = self._format_datetime(start_date)
        if end_date:
            params["end_date"] = self._format_datetime(end_date)

        response, error = self._http.get("/v1/sms", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def send_draft(
        self, sms_id: str, scheduled_at: Optional[datetime] = None
    ) -> Tuple[Optional[SMS], Optional[str]]:
        """
        Send a draft SMS message

        Args:
            sms_id: Draft SMS message ID
            scheduled_at: Optional time to schedule the message

        Returns:
            Tuple of (SMS object, error) where error is None on success
        """
        data: Dict[str, Any] = {}
        if scheduled_at:
            data["scheduled_at"] = self._format_datetime(scheduled_at)

        response, error = self._http.post(f"/v1/sms/{sms_id}/send-draft", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def resend(self, sms_id: str) -> Tuple[Optional[SMS], Optional[str]]:
        """
        Resend a failed SMS message

        Args:
            sms_id: SMS message ID to resend

        Returns:
            Tuple of (SMS object, error) where error is None on success
        """
        response, error = self._http.post(f"/v1/sms/{sms_id}/resend")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def resend_batch(
        self, message_ids: List[str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Batch resend failed SMS messages

        Args:
            message_ids: List of message IDs to resend

        Returns:
            Tuple of (batch results, error) where error is None on success
        """
        data = {"message_ids": message_ids}
        response, error = self._http.post("/v1/sms/resend-failed", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get_dashboard(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get SMS dashboard data with overview statistics

        Returns:
            Tuple of (dashboard data, error) where error is None on success
        """
        response, error = self._http.get("/v1/sms/dashboard")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime to ISO 8601 string"""
        if dt.tzinfo is None:
            # Add UTC timezone if naive datetime
            from datetime import timezone

            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
