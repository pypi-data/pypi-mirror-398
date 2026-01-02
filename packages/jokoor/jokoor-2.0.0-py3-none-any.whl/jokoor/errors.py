"""
Error types for the Jokoor SDK
"""

from typing import Optional, Dict, Any


class JokoorError(Exception):
    """Base exception for all Jokoor SDK errors"""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class JokoorAPIError(JokoorError):
    """General API error"""

    pass


class JokoorAuthenticationError(JokoorError):
    """Authentication failed - invalid or missing API key"""

    pass


class JokoorPermissionError(JokoorError):
    """Permission denied - insufficient permissions"""

    pass


class JokoorNotFoundError(JokoorError):
    """Resource not found"""

    pass


class JokoorValidationError(JokoorError):
    """Invalid request parameters"""

    pass


class JokoorRateLimitError(JokoorError):
    """Rate limit exceeded"""

    pass


class JokoorServerError(JokoorError):
    """Server-side error"""

    pass


class JokoorNetworkError(JokoorError):
    """Network/connection error"""

    pass


class JokoorTimeoutError(JokoorError):
    """Request timeout"""

    pass


def create_error_from_response(
    response_data: Dict[str, Any], status_code: int
) -> JokoorError:
    """
    Create an appropriate error from API response

    Args:
        response_data: Response data from API
        status_code: HTTP status code

    Returns:
        Appropriate JokoorError subclass
    """
    # Extract error message
    error_message = "Unknown error"
    if isinstance(response_data, dict):
        if "error" in response_data:
            error_obj = response_data["error"]
            if isinstance(error_obj, str):
                error_message = error_obj
            elif isinstance(error_obj, dict):
                error_message = error_obj.get("message", str(error_obj))
        elif "message" in response_data:
            error_message = response_data["message"]

    # Map status code to error type
    if status_code == 400:
        return JokoorValidationError(error_message, status_code)
    elif status_code == 401:
        return JokoorAuthenticationError(error_message, status_code)
    elif status_code == 403:
        return JokoorPermissionError(error_message, status_code)
    elif status_code == 404:
        return JokoorNotFoundError(error_message, status_code)
    elif status_code == 429:
        return JokoorRateLimitError(error_message, status_code)
    elif status_code >= 500:
        return JokoorServerError(error_message, status_code)
    else:
        return JokoorAPIError(error_message, status_code)
