"""Base HTTP client for Dify API."""

from typing import Any, Dict, Optional

import httpx

from ._exceptions import (
    ERROR_CODE_MAPPING,
    DifyAPIError,
    DifyAuthenticationError,
    DifyConflictError,
    DifyConnectionError,
    DifyNotFoundError,
    DifyServerError,
    DifyTimeoutError,
    DifyValidationError,
)


class BaseClient:
    """Base HTTP client for Dify API.

    Provides a foundation for making HTTP requests to the Dify API with
    proper error handling, timeout management, and authentication.

    Attributes:
        api_key (str): API key for authentication
        base_url (str): Base URL for API endpoints
        timeout (float): Request timeout in seconds
    """

    def __init__(self, api_key: str, base_url: str = "https://api.dify.ai", timeout: float = 30.0) -> None:
        """Initialize the base client.

        Args:
            api_key: Dify API key for authentication
            base_url: Base URL for the Dify API (default: https://api.dify.ai)
            timeout: Request timeout in seconds (default: 30.0)

        Raises:
            ValueError: If api_key is empty or None
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=httpx.Timeout(timeout))

    def _safe_parse_error_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Safely parse error response JSON.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON data or empty dict if parsing fails
        """
        if not response.content:
            return {}

        try:
            return response.json()  # type: ignore[no-any-return]
        except ValueError:
            return {"message": "Failed to parse error response"}

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for API requests.

        Returns:
            Dictionary containing standard headers for Dify API requests
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "dify-dataset-sdk/0.4.0",
        }

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle HTTP response and raise appropriate exceptions.

        Args:
            response: HTTP response object from httpx

        Returns:
            Parsed JSON response data or success status

        Raises:
            DifyValidationError: For 400, 403, 413, 415 status codes
            DifyAuthenticationError: For 401 status code
            DifyNotFoundError: For 404 status code
            DifyConflictError: For 409 status code
            DifyServerError: For 5xx status codes
            DifyAPIError: For other unexpected status codes
            DifyConnectionError: For connection-related errors
        """
        try:
            if response.status_code in (200, 201):
                if response.content:
                    try:
                        return response.json()
                    except ValueError as e:
                        raise DifyAPIError(f"Invalid JSON response: {str(e)}", response.status_code) from e
                else:
                    return {}
            elif response.status_code == 204:
                return {"status": "success"}
            elif response.status_code == 400:
                error_data = self._safe_parse_error_response(response)
                error_code = error_data.get("code", "unknown")
                default_msg = error_data.get("message") or "Bad request"
                message = ERROR_CODE_MAPPING.get(error_code) or default_msg
                raise DifyValidationError(message, response.status_code, error_code)
            elif response.status_code == 401:
                raise DifyAuthenticationError("Invalid API key", response.status_code)
            elif response.status_code == 403:
                error_data = self._safe_parse_error_response(response)
                error_code = error_data.get("code", "forbidden")
                message = ERROR_CODE_MAPPING.get(error_code) or "Forbidden"
                raise DifyValidationError(message, response.status_code, error_code)
            elif response.status_code == 404:
                raise DifyNotFoundError("Resource not found", response.status_code)
            elif response.status_code == 409:
                error_data = self._safe_parse_error_response(response)
                error_code = error_data.get("code", "conflict")
                message = ERROR_CODE_MAPPING.get(error_code) or "Conflict"
                raise DifyConflictError(message, response.status_code, error_code)
            elif response.status_code == 413:
                raise DifyValidationError("File too large", response.status_code, "file_too_large")
            elif response.status_code == 415:
                raise DifyValidationError(
                    "Unsupported file type",
                    response.status_code,
                    "unsupported_file_type",
                )
            elif response.status_code >= 500:
                raise DifyServerError("Server error", response.status_code)
            else:
                raise DifyAPIError(
                    f"Unexpected status code: {response.status_code}",
                    response.status_code,
                )
        except httpx.HTTPError as e:
            raise DifyConnectionError(f"Connection error: {str(e)}") from e

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make HTTP request."""
        url = f"{self.base_url}{path}"

        try:
            kwargs: Dict[str, Any] = {"method": method, "url": url, "params": params}

            if files:
                kwargs["files"] = files
                if data:
                    kwargs["data"] = data
                # Remove Content-Type header for multipart requests
                headers = self._get_headers()
                headers.pop("Content-Type", None)
                kwargs["headers"] = headers
            else:
                kwargs["json"] = json
                kwargs["headers"] = self._get_headers()

            response = self._client.request(**kwargs)
            return self._handle_response(response)

        except httpx.TimeoutException as e:
            raise DifyTimeoutError("Request timeout") from e
        except httpx.ConnectError as e:
            raise DifyConnectionError("Failed to connect to Dify API") from e
        except httpx.HTTPError as e:
            raise DifyConnectionError(f"HTTP error: {str(e)}") from e

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make GET request."""
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make POST request."""
        return self._request("POST", path, json=json, files=files, data=data)

    def patch(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """Make PATCH request."""
        return self._request("PATCH", path, json=json)

    def delete(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """Make DELETE request."""
        return self._request("DELETE", path, json=json)

    def close(self) -> None:
        """Close the HTTP client connection and cleanup resources."""
        self._client.close()

    def __enter__(self) -> "BaseClient":
        """Enter context manager.

        Returns:
            Self for method chaining
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and cleanup resources.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        self.close()
