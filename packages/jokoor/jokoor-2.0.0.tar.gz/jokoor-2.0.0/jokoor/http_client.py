"""
HTTP client for the Jokoor SDK with retry logic
"""

import json
from typing import Optional, Dict, Any, Tuple, BinaryIO
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .errors import JokoorError, create_error_from_response
from .result import Result, Ok, Err


class HTTPClient:
    """HTTP client with automatic retries and error handling"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.jokoor.com",
        timeout: int = 30,
        max_retries: int = 3,
        debug: bool = False,
    ) -> None:
        """
        Initialize HTTP client

        Args:
            api_key: Jokoor API key
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            debug: Enable debug logging
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.debug = debug

        # Setup session with retry strategy
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()

        # Set default headers
        session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "jokoor-python/1.0.0",
            }
        )

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "OPTIONS",
                "TRACE",
                "POST",
            ],
            backoff_factor=1,
            respect_retry_after_header=True,
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=10
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Result[Any]:
        """
        Make an HTTP request to the API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (e.g., '/v1/sms')
            data: Request body data
            params: Query parameters
            headers: Additional headers

        Returns:
            Result tuple: (data, error) where data is the parsed response or None on error
        """
        url = urljoin(self.base_url, endpoint)

        # Prepare request kwargs
        kwargs: Dict[str, Any] = {"timeout": self.timeout, "params": params}

        if headers:
            # Merge with session headers
            kwargs["headers"] = headers

        if data is not None:
            kwargs["json"] = data

        if self.debug:
            print(f"Jokoor SDK Request: {method} {url}")
            if data:
                print(f"Request data: {json.dumps(data, indent=2)}")
            if params:
                print(f"Request params: {json.dumps(params, indent=2)}")

        try:
            response = self.session.request(method, url, **kwargs)

            if self.debug:
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                print(f"Response data: {response.text[:500]}")

            # Handle 204 No Content response
            if response.status_code == 204:
                return Ok({"success": True})

            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                # If it's a successful response without JSON, return success
                if 200 <= response.status_code < 300:
                    return Ok({"success": True, "raw": response.text})
                # For errors, create error response
                response_data = {
                    "error": f"Invalid JSON response: {response.text[:100]}"
                }

            # Check for errors
            if response.status_code >= 400:
                error = create_error_from_response(response_data, response.status_code)
                return Err(error)

            # Return data from response wrapper if present
            if isinstance(response_data, dict) and "data" in response_data:
                return Ok(response_data["data"])
            return Ok(response_data)

        except requests.exceptions.Timeout:
            return Err(f"Request to {url} timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            return Err(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            return Err(f"Request failed: {str(e)}")
        except JokoorError as e:
            return Err(e)
        except Exception as e:
            return Err(f"Unexpected error: {str(e)}")

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Result[Any]:
        """Make a GET request"""
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Result[Any]:
        """Make a POST request"""
        return self.request("POST", endpoint, data=data)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Result[Any]:
        """Make a PUT request"""
        return self.request("PUT", endpoint, data=data)

    def delete(self, endpoint: str) -> Result[Any]:
        """Make a DELETE request"""
        return self.request("DELETE", endpoint)

    def upload_file(
        self, endpoint: str, file: BinaryIO, field_name: str = "file"
    ) -> Result[Any]:
        """
        Upload a file using multipart/form-data

        Args:
            endpoint: API endpoint
            file: File object to upload
            field_name: Form field name (default: "file")

        Returns:
            Result tuple: (data, error)
        """
        url = urljoin(self.base_url, endpoint)

        # Create multipart form data
        files = {field_name: file}

        # Prepare custom headers (don't set Content-Type, let requests handle it)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "jokoor-python/1.0.0",
        }

        if self.debug:
            print(f"Jokoor SDK Request: POST {url} (file upload)")

        try:
            response = self.session.post(
                url, files=files, headers=headers, timeout=self.timeout
            )

            if self.debug:
                print(f"Response status: {response.status_code}")
                print(f"Response data: {response.text[:500]}")

            # Handle 204 No Content response
            if response.status_code == 204:
                return Ok({"success": True})

            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                # If it's a successful response without JSON, return success
                if 200 <= response.status_code < 300:
                    return Ok({"success": True, "raw": response.text})
                # For errors, create error response
                response_data = {
                    "error": f"Invalid JSON response: {response.text[:100]}"
                }

            # Check for errors
            if response.status_code >= 400:
                error = create_error_from_response(response_data, response.status_code)
                return Err(error)

            # Return data from response wrapper if present
            if isinstance(response_data, dict) and "data" in response_data:
                return Ok(response_data["data"])
            return Ok(response_data)

        except requests.exceptions.Timeout:
            return Err(f"Request to {url} timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            return Err(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            return Err(f"Request failed: {str(e)}")
        except JokoorError as e:
            return Err(e)
        except Exception as e:
            return Err(f"Unexpected error: {str(e)}")

    def close(self) -> None:
        """Close the HTTP session"""
        self.session.close()

    def __enter__(self) -> "HTTPClient":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit"""
        self.close()
