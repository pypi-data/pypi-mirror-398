"""
Products resource for the Jokoor SDK
"""

from typing import Optional, Dict, Any, List, Tuple

from ..types import Product, PaginatedResponse
from ..http_client import HTTPClient


class ProductsResource:
    """Product operations"""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http = http_client

    def create(
        self,
        *,
        name: str,
        price: str,
        currency: str = "GMD",
        description: Optional[str] = None,
        images: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Product], Optional[str]]:
        """
        Create a product

        Args:
            name: Product name (required)
            price: Product price (required)
            currency: Currency code (default: GMD)
            description: Product description
            images: List of image URLs
            metadata: Additional metadata

        Returns:
            Tuple of (Product object, error) where error is None on success
        """
        data: Dict[str, Any] = {"name": name, "price": price, "currency": currency}

        if description:
            data["description"] = description
        if images:
            data["images"] = images
        if metadata:
            data["metadata"] = metadata

        response, error = self._http.post("/v1/pay/products", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def get(self, product_id: str) -> Tuple[Optional[Product], Optional[str]]:
        """Get product details"""
        response, error = self._http.get(f"/v1/pay/products/{product_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def list(
        self, *, offset: int = 0, limit: int = 20, active: Optional[bool] = None
    ) -> Tuple[Optional[PaginatedResponse], Optional[str]]:
        """List products"""
        params: Dict[str, Any] = {"offset": offset, "limit": limit}
        if active is not None:
            params["active"] = active

        response, error = self._http.get("/v1/pay/products", params)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def update(
        self,
        product_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[str] = None,
        is_active: Optional[bool] = None,
        images: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Product], Optional[str]]:
        """
        Update product information

        Args:
            product_id: Product ID
            name: Product name
            description: Product description
            price: Product price
            is_active: Whether product is active
            images: List of image URLs
            metadata: Additional metadata

        Returns:
            Tuple of (Product object, error) where error is None on success
        """
        data: Dict[str, Any] = {}

        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if price is not None:
            data["price"] = price
        if is_active is not None:
            data["is_active"] = is_active
        if images is not None:
            data["images"] = images
        if metadata is not None:
            data["metadata"] = metadata

        response, error = self._http.put(f"/v1/pay/products/{product_id}", data)
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore

    def delete(self, product_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Delete a product"""
        response, error = self._http.delete(f"/v1/pay/products/{product_id}")
        if error:
            return (None, str(error))
        return (response, None)  # type: ignore
