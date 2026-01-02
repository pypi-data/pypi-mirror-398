"""
SMS Sender IDs resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, Tuple

from ..types import SenderID, PaginatedResponse
from ..http_client import HTTPClient


class SenderIDsResource:
    """Sender ID operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        sender_id: str,
        purpose: Optional[str] = None,
        use_case: Optional[str] = None,
    ) -> Tuple[Optional[SenderID], Optional[str]]:
        """
        Apply for a custom sender ID

        Args:
            sender_id: Desired sender ID (3-11 alphanumeric characters)
            purpose: Purpose for using this sender ID
            use_case: Description of use case

        Returns:
            Tuple of (SenderID object, error) where error is None on success
        """
        data: Dict[str, Any] = {"sender_id": sender_id}
        if purpose:
            data["purpose"] = purpose
        if use_case:
            data["use_case"] = use_case

        response, error = self._http.post("/v1/sms/senders", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, sender_id_id: str) -> Tuple[Optional[SenderID], Optional[str]]:
        """
        Get sender ID details

        Args:
            sender_id_id: Sender ID record ID

        Returns:
            Tuple of (SenderID object, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/sms/senders/{sender_id_id}")
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
        List sender IDs

        Args:
            offset: Number of items to skip
            limit: Maximum number of items to return
            status: Filter by status (pending, approved, rejected)

        Returns:
            Tuple of (PaginatedResponse, error) where error is None on success
        """
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status

        response, error = self._http.get("/v1/sms/senders", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        sender_id_id: str,
        *,
        purpose: Optional[str] = None,
        use_case: Optional[str] = None,
    ) -> Tuple[Optional[SenderID], Optional[str]]:
        """
        Update a sender ID application

        Args:
            sender_id_id: Sender ID record ID
            purpose: Purpose for using this sender ID
            use_case: Description of use case

        Returns:
            Tuple of (SenderID object, error) where error is None on success
        """
        data: Dict[str, Any] = {}
        if purpose is not None:
            data["purpose"] = purpose
        if use_case is not None:
            data["use_case"] = use_case

        response, error = self._http.put(f"/v1/sms/senders/{sender_id_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(
        self, sender_id_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Delete a sender ID

        Args:
            sender_id_id: Sender ID record ID

        Returns:
            Tuple of (success dict, error) where error is None on success
        """
        response, error = self._http.delete(f"/v1/sms/senders/{sender_id_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def set_default(
        self, sender_id_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Set a sender ID as the default

        Args:
            sender_id_id: Sender ID record ID

        Returns:
            Tuple of (success dict, error) where error is None on success
        """
        response, error = self._http.post(f"/v1/sms/senders/{sender_id_id}/set-default")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
