"""
SMS Templates resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, Tuple

from ..types import Template, PaginatedResponse
from ..http_client import HTTPClient


class TemplatesResource:
    """SMS template operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        name: str,
        body: str,
        description: Optional[str] = None,
    ) -> Tuple[Optional[Template], Optional[str]]:
        """
        Create an SMS template

        Args:
            name: Template name
            body: Template body with {{variable}} placeholders
            description: Template description

        Returns:
            Tuple of (Template object, error) where error is None on success
        """
        data: Dict[str, Any] = {"name": name, "body": body}
        if description:
            data["description"] = description

        response, error = self._http.post("/v1/sms/templates", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, template_id: str) -> Tuple[Optional[Template], Optional[str]]:
        """
        Get template details

        Args:
            template_id: Template ID

        Returns:
            Tuple of (Template object, error) where error is None on success
        """
        response, error = self._http.get(f"/v1/sms/templates/{template_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self, *, offset: int = 0, limit: int = 20
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """
        List SMS templates

        Args:
            offset: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            Tuple of (PaginatedResponse, error) where error is None on success
        """
        params = {"offset": offset, "limit": limit}
        response, error = self._http.get("/v1/sms/templates", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        template_id: str,
        *,
        name: Optional[str] = None,
        body: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tuple[Optional[Template], Optional[str]]:
        """
        Update an SMS template

        Args:
            template_id: Template ID
            name: Template name
            body: Template body
            description: Template description

        Returns:
            Tuple of (Template object, error) where error is None on success
        """
        data: Dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if body is not None:
            data["body"] = body
        if description is not None:
            data["description"] = description

        response, error = self._http.put(f"/v1/sms/templates/{template_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(
        self, template_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Delete an SMS template

        Args:
            template_id: Template ID

        Returns:
            Tuple of (success dict, error) where error is None on success
        """
        response, error = self._http.delete(f"/v1/sms/templates/{template_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
