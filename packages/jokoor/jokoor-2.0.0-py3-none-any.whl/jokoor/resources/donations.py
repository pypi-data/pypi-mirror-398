"""
Donations resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from ..types import DonationCampaign, PaginatedResponse
from ..http_client import HTTPClient


class DonationsResource:
    """Donation campaign operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        title: str,
        description: str = "",
        target_amount: Optional[str] = None,
        currency: str = "GMD",
        tags: Optional[List[str]] = None,
        is_recurring: bool = False,
        recurring_interval: Optional[str] = None,
        end_date: Optional[datetime] = None,
        slug: Optional[str] = None,
        image_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[DonationCampaign], Optional[str]]:
        """
        Create a donation campaign

        Args:
            title: Campaign title (required)
            description: Campaign description
            target_amount: Target amount to raise (optional)
            currency: Currency code (default: GMD)
            tags: List of tags for categorization
            is_recurring: Whether campaign accepts recurring donations
            recurring_interval: Interval for recurring donations (monthly, quarterly, yearly)
            end_date: Campaign end date
            slug: Custom URL slug
            image_url: Cover image URL
            metadata: Additional metadata

        Returns:
            Tuple of (DonationCampaign object, error) where error is None on success
        """
        data: Dict[str, Any] = {"title": title, "currency": currency}

        if description:
            data["description"] = description
        if target_amount:
            data["target_amount"] = target_amount
        if tags:
            data["tags"] = tags
        if is_recurring:
            data["is_recurring"] = is_recurring
        if recurring_interval:
            data["recurring_interval"] = recurring_interval
        if end_date:
            data["end_date"] = end_date.isoformat() if isinstance(end_date, datetime) else end_date
        if slug:
            data["slug"] = slug
        if image_url:
            data["image_url"] = image_url
        if metadata:
            data["metadata"] = metadata

        response, error = self._http.post("/v1/pay/donations", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, campaign_id: str) -> Tuple[Optional[DonationCampaign], Optional[str]]:
        """Get donation campaign details"""
        response, error = self._http.get(f"/v1/pay/donations/{campaign_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self, *, offset: int = 0, limit: int = 20, status: Optional[str] = None
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """List donation campaigns"""
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status

        response, error = self._http.get("/v1/pay/donations", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        campaign_id: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        target_amount: Optional[str] = None,
        tags: Optional[List[str]] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        slug: Optional[str] = None,
        image_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[DonationCampaign], Optional[str]]:
        """
        Update a donation campaign

        Args:
            campaign_id: Campaign ID
            title: Campaign title
            description: Campaign description
            target_amount: Target amount to raise
            tags: List of tags
            end_date: Campaign end date
            status: Campaign status
            slug: Custom URL slug
            image_url: Cover image URL
            metadata: Additional metadata

        Returns:
            Tuple of (DonationCampaign object, error) where error is None on success
        """
        data: Dict[str, Any] = {}

        if title is not None:
            data["title"] = title
        if description is not None:
            data["description"] = description
        if target_amount is not None:
            data["target_amount"] = target_amount
        if tags is not None:
            data["tags"] = tags
        if end_date is not None:
            data["end_date"] = end_date.isoformat() if isinstance(end_date, datetime) else end_date
        if status is not None:
            data["status"] = status
        if slug is not None:
            data["slug"] = slug
        if image_url is not None:
            data["image_url"] = image_url
        if metadata is not None:
            data["metadata"] = metadata

        response, error = self._http.put(f"/v1/pay/donations/{campaign_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(self, campaign_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Delete a donation campaign"""
        response, error = self._http.delete(f"/v1/pay/donations/{campaign_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
