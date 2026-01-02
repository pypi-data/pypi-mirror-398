"""
SMS Contact Groups resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, List, Tuple

from ..types import ContactGroup, PaginatedResponse
from ..http_client import HTTPClient


class ContactGroupsResource:
    """SMS contact group operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        name: str,
        description: Optional[str] = None,
    ) -> Tuple[Optional[ContactGroup], Optional[str]]:
        """
        Create a contact group

        Args:
            name: Group name
            description: Group description

        Returns:
            Tuple of (ContactGroup object, error) where error is None on success
        """
        data: Dict[str, Any] = {"name": name}
        if description:
            data["description"] = description

        response, error = self._http.post("/v1/sms/groups", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, group_id: str) -> Tuple[Optional[ContactGroup], Optional[str]]:
        """
        Get contact group details

        Args:
            group_id: Group ID

        Returns:
            Tuple of (ContactGroup object, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/sms/groups/{group_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self, *, offset: int = 0, limit: int = 20
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """
        List contact groups

        Args:
            offset: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            Tuple of (PaginatedResponse, error) where error is None on success
        """
        params = {"offset": offset, "limit": limit}
        response, error = self._http.get("/v1/sms/groups", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        group_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tuple[Optional[ContactGroup], Optional[str]]:
        """
        Update a contact group

        Args:
            group_id: Group ID
            name: Group name
            description: Group description

        Returns:
            Tuple of (ContactGroup object, error) where error is None on success
        """
        data: Dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        response, error = self._http.put(f"/v1/sms/groups/{group_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(self, group_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Delete a contact group

        Args:
            group_id: Group ID

        Returns:
            Tuple of (success dict, error) where error is None on success
        """
        response, error = self._http.delete(f"/v1/sms/groups/{group_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def add_contacts(
        self, group_id: str, contact_ids: List[str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Add contacts to a group

        Args:
            group_id: Group ID
            contact_ids: List of contact IDs to add

        Returns:
            Tuple of (success dict, error) where error is None on success
        """
        data = {"contact_ids": contact_ids}
        response, error = self._http.post(f"/v1/sms/groups/{group_id}/contacts", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def remove_contacts(
        self, group_id: str, contact_ids: List[str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Remove contacts from a group

        Args:
            group_id: Group ID
            contact_ids: List of contact IDs to remove

        Returns:
            Tuple of (success dict, error) where error is None on success
        """
        data = {"contact_ids": contact_ids}
        response, error = self._http.request(
            "DELETE", f"/v1/sms/groups/{group_id}/contacts", data=data
        )
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
