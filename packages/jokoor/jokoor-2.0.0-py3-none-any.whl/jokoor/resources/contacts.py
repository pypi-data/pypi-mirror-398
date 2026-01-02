"""
SMS Contacts resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, Tuple

from ..types import Contact, PaginatedResponse
from ..http_client import HTTPClient


class ContactsResource:
    """SMS contact operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        phone_number: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        custom_fields: Optional[Dict[str, str]] = None,
    ) -> Tuple[Optional[Contact], Optional[str]]:
        """
        Create an SMS contact

        Args:
            phone_number: Phone number in E.164 format
            first_name: First name
            last_name: Last name
            email: Email address
            custom_fields: Custom fields

        Returns:
            Tuple of (Contact object, error) where error is None on success
        """
        data: Dict[str, Any] = {"phone_number": phone_number}
        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        if email:
            data["email"] = email
        if custom_fields:
            data["custom_fields"] = custom_fields

        response, error = self._http.post("/v1/sms/contacts", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, contact_id: str) -> Tuple[Optional[Contact], Optional[str]]:
        """
        Get contact details

        Args:
            contact_id: Contact ID

        Returns:
            Tuple of (Contact object, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/sms/contacts/{contact_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        group_id: Optional[str] = None,
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """
        List SMS contacts

        Args:
            offset: Number of items to skip
            limit: Maximum number of items to return
            group_id: Filter by contact group ID

        Returns:
            Tuple of (PaginatedResponse, error) where error is None on success
        """
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if group_id:
            params["group_id"] = group_id

        response, error = self._http.get("/v1/sms/contacts", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        contact_id: str,
        *,
        phone_number: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        custom_fields: Optional[Dict[str, str]] = None,
    ) -> Tuple[Optional[Contact], Optional[str]]:
        """
        Update an SMS contact

        Args:
            contact_id: Contact ID
            phone_number: Phone number
            first_name: First name
            last_name: Last name
            email: Email address
            custom_fields: Custom fields

        Returns:
            Tuple of (Contact object, error) where error is None on success
        """
        data: Dict[str, Any] = {}
        if phone_number is not None:
            data["phone_number"] = phone_number
        if first_name is not None:
            data["first_name"] = first_name
        if last_name is not None:
            data["last_name"] = last_name
        if email is not None:
            data["email"] = email
        if custom_fields is not None:
            data["custom_fields"] = custom_fields

        response, error = self._http.put(f"/v1/sms/contacts/{contact_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(self, contact_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Delete an SMS contact

        Args:
            contact_id: Contact ID

        Returns:
            Tuple of (success dict, error) where error is None on success
        """
        response, error = self._http.delete(f"/v1/sms/contacts/{contact_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
