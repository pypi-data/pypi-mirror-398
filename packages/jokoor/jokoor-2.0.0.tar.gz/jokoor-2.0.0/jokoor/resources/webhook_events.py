"""
Webhook Events resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from ..types import WebhookEvent, PaginatedResponse
from ..http_client import HTTPClient


class WebhookEventsResource:
    """Webhook event operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def get(self, event_id: str) -> Tuple[Optional[WebhookEvent], Optional[str]]:
        """Get webhook event details"""
        response, error = self._http.get(f"/v1/events/{event_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """List webhook events"""
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if type:
            params["type"] = type
        if start_date:
            params["start_date"] = start_date.isoformat() if isinstance(start_date, datetime) else start_date
        if end_date:
            params["end_date"] = end_date.isoformat() if isinstance(end_date, datetime) else end_date

        response, error = self._http.get("/v1/events", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def retry(self, event_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retry delivery of a failed webhook event"""
        response, error = self._http.post(f"/v1/events/{event_id}/retry")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
