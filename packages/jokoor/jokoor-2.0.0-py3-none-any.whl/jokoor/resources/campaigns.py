"""
SMS Campaigns resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from ..types import Campaign, CampaignStats, PaginatedResponse
from ..http_client import HTTPClient


class CampaignsResource:
    """SMS campaign operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        name: str,
        message_body: Optional[str] = None,
        template_id: Optional[str] = None,
        template_params: Optional[Dict[str, str]] = None,
        sender_id: Optional[str] = None,
        contact_ids: Optional[List[str]] = None,
        group_ids: Optional[List[str]] = None,
        scheduled_at: Optional[datetime] = None,
        is_draft: bool = False,
    ) -> Tuple[Optional[Campaign], Optional[str]]:
        """
        Create an SMS campaign

        Args:
            name: Campaign name
            message_body: Campaign message text (or use template_id)
            template_id: Template ID (or use message_body)
            template_params: Template parameters
            sender_id: Custom sender ID
            contact_ids: List of contact IDs to send to
            group_ids: List of group IDs to send to
            scheduled_at: Schedule campaign for future delivery
            is_draft: Save as draft without sending

        Returns:
            Tuple of (Campaign object, error) where error is None on success
        """
        data: Dict[str, Any] = {"name": name, "is_draft": is_draft}

        if message_body:
            data["message_body"] = message_body
        if template_id:
            data["template_id"] = template_id
        if template_params:
            data["template_params"] = template_params
        if sender_id:
            data["sender_id"] = sender_id
        if contact_ids:
            data["contact_ids"] = contact_ids
        if group_ids:
            data["group_ids"] = group_ids
        if scheduled_at:
            data["scheduled_at"] = self._format_datetime(scheduled_at)

        response, error = self._http.post("/v1/sms/campaigns", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, campaign_id: str) -> Tuple[Optional[Campaign], Optional[str]]:
        """
        Get campaign details

        Args:
            campaign_id: Campaign ID

        Returns:
            Tuple of (Campaign object, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/sms/campaigns/{campaign_id}")
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
        List SMS campaigns

        Args:
            offset: Number of items to skip
            limit: Maximum number of items to return
            status: Filter by status (draft, scheduled, sending, completed, failed, cancelled)

        Returns:
            Tuple of (PaginatedResponse, error) where error is None on success
        """
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status

        response, error = self._http.get("/v1/sms/campaigns", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        campaign_id: str,
        *,
        name: Optional[str] = None,
        message_body: Optional[str] = None,
        template_id: Optional[str] = None,
        template_params: Optional[Dict[str, str]] = None,
        sender_id: Optional[str] = None,
        contact_ids: Optional[List[str]] = None,
        group_ids: Optional[List[str]] = None,
    ) -> Tuple[Optional[Campaign], Optional[str]]:
        """
        Update a draft campaign

        Args:
            campaign_id: Campaign ID
            name: Campaign name
            message_body: Campaign message
            template_id: Template ID
            template_params: Template parameters
            sender_id: Custom sender ID
            contact_ids: List of contact IDs
            group_ids: List of group IDs

        Returns:
            Tuple of (Campaign object, error) where error is None on success
        """
        data: Dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if message_body is not None:
            data["message_body"] = message_body
        if template_id is not None:
            data["template_id"] = template_id
        if template_params is not None:
            data["template_params"] = template_params
        if sender_id is not None:
            data["sender_id"] = sender_id
        if contact_ids is not None:
            data["contact_ids"] = contact_ids
        if group_ids is not None:
            data["group_ids"] = group_ids

        response, error = self._http.put(f"/v1/sms/campaigns/{campaign_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(
        self, campaign_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Delete a draft campaign

        Args:
            campaign_id: Campaign ID

        Returns:
            Tuple of (success dict, error) where error is None on success
        """
        response, error = self._http.delete(f"/v1/sms/campaigns/{campaign_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def send(
        self, campaign_id: str, scheduled_at: Optional[datetime] = None
    ) -> Tuple[Optional[Campaign], Optional[str]]:
        """
        Send a campaign

        Args:
            campaign_id: Campaign ID
            scheduled_at: Optional time to schedule the campaign

        Returns:
            Tuple of (Campaign object, error) where error is None on success
        """
        data: Dict[str, Any] = {}
        if scheduled_at:
            data["scheduled_at"] = self._format_datetime(scheduled_at)

        response, error = self._http.post(f"/v1/sms/campaigns/{campaign_id}/send", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def send_draft(
        self, campaign_id: str, scheduled_at: Optional[datetime] = None
    ) -> Tuple[Optional[Campaign], Optional[str]]:
        """
        Send a draft campaign

        Args:
            campaign_id: Campaign ID
            scheduled_at: Optional time to schedule the campaign

        Returns:
            Tuple of (Campaign object, error) where error is None on success
        """
        data: Dict[str, Any] = {}
        if scheduled_at:
            data["scheduled_at"] = self._format_datetime(scheduled_at)

        response, error = self._http.post(
            f"/v1/sms/campaigns/{campaign_id}/send-draft", data
        )
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def send_async(
        self, campaign_id: str, scheduled_at: Optional[datetime] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Send campaign asynchronously (for large campaigns)

        Args:
            campaign_id: Campaign ID
            scheduled_at: Optional time to schedule the campaign

        Returns:
            Tuple of (response dict, error) where error is None on success
        """
        data: Dict[str, Any] = {}
        if scheduled_at:
            data["scheduled_at"] = self._format_datetime(scheduled_at)

        response, error = self._http.post(
            f"/v1/sms/campaigns/{campaign_id}/send-async", data
        )
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get_messages(
        self,
        campaign_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """
        Get messages sent in a campaign

        Args:
            campaign_id: Campaign ID
            offset: Number of items to skip
            limit: Maximum number of items to return
            status: Filter by status

        Returns:
            Tuple of (PaginatedResponse, error) where error is None on success
        """
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status

        response, error = self._http.get(
            f"/v1/sms/campaigns/{campaign_id}/messages", params
        )
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get_statistics(
        self, campaign_id: str
    ) -> Tuple[Optional[CampaignStats], Optional[str]]:
        """
        Get campaign statistics

        Args:
            campaign_id: Campaign ID

        Returns:
            Tuple of (CampaignStats object, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/sms/campaigns/{campaign_id}/statistics")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def resend_failed(
        self, campaign_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Resend all failed messages in a campaign

        Args:
            campaign_id: Campaign ID

        Returns:
            Tuple of (batch results, error) where error is None on success
        """
        response, error = self._http.post(
            f"/v1/sms/campaigns/{campaign_id}/resend-failed"
        )
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime to ISO 8601 string"""
        if dt.tzinfo is None:
            from datetime import timezone

            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
