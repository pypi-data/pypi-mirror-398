"""
Webhooks resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, List, Tuple

from ..types import WebhookEndpoint, PaginatedResponse
from ..http_client import HTTPClient


class WebhooksResource:
    """Webhook endpoint operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        url: str,
        enabled_events: List[str],
        description: Optional[str] = None,
    ) -> Tuple[Optional[WebhookEndpoint], Optional[str]]:
        """Create a webhook endpoint"""
        data: Dict[str, Any] = {"url": url, "enabled_events": enabled_events}
        if description:
            data["description"] = description

        response, error = self._http.post("/v1/webhook_endpoints", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, endpoint_id: str) -> Tuple[Optional[WebhookEndpoint], Optional[str]]:
        """Get webhook endpoint details"""
        response, error = self._http.get(f"/v1/webhook_endpoints/{endpoint_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self, *, offset: int = 0, limit: int = 20
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """List webhook endpoints"""
        params = {"offset": offset, "limit": limit}
        response, error = self._http.get("/v1/webhook_endpoints", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        endpoint_id: str,
        *,
        url: Optional[str] = None,
        enabled_events: Optional[List[str]] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[Optional[WebhookEndpoint], Optional[str]]:
        """Update a webhook endpoint"""
        data: Dict[str, Any] = {}
        if url is not None:
            data["url"] = url
        if enabled_events is not None:
            data["enabled_events"] = enabled_events
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status

        response, error = self._http.post(f"/v1/webhook_endpoints/{endpoint_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(self, endpoint_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Delete a webhook endpoint"""
        response, error = self._http.delete(f"/v1/webhook_endpoints/{endpoint_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def test(self, endpoint_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Send a test event to a webhook endpoint"""
        response, error = self._http.post(f"/v1/webhook_endpoints/{endpoint_id}/test")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
