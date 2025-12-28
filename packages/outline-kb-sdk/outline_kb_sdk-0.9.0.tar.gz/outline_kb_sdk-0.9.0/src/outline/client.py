"""HTTP client for communicating with the Outline API."""

import time
from typing import Any, Dict, Optional

import httpx

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    NetworkError,
    NotFoundError,
    OutlineError,
    RateLimitError,
    ServerError,
    ValidationError,
)


class OutlineClient:
    """Client for making requests to the Outline API."""

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout: int = 30,
        verify_ssl: bool = True,
        rate_limit_delay: float = 0.1,
    ):
        """
        Initialize the Outline API client.

        Args:
            api_url: Base URL of the Outline instance (e.g., 'https://app.getoutline.com')
            api_key: API key for authentication
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Whether to verify SSL certificates (default: True)
            rate_limit_delay: Delay in seconds between requests to avoid rate limits (default: 0.1)
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.rate_limit_delay = rate_limit_delay
        self._session = httpx.Client(timeout=timeout, verify=verify_ssl)
        self._last_request_time: float = 0

    def request(
        self,
        method: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request to an Outline API endpoint.

        The Outline API uses RPC-style endpoints where all requests are POST
        to /api/:method with the method name in the URL.

        Args:
            method: API method name (e.g., 'collections.list')
            data: Request payload dictionary

        Returns:
            Response data dictionary

        Raises:
            AuthenticationError: When API key is invalid (401)
            AuthorizationError: When user lacks permission (403)
            NotFoundError: When resource doesn't exist (404)
            ValidationError: When request validation fails (400)
            RateLimitError: When rate limit is exceeded (429)
            ServerError: When server error occurs (5xx)
            NetworkError: When network-level error occurs
            OutlineError: For other API errors
        """
        # Rate limiting: wait if needed
        if self.rate_limit_delay > 0:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - time_since_last)
            self._last_request_time = time.time()
        
        url = f"{self.api_url}/api/{method}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = self._session.post(
                url,
                json=data or {},
                headers=headers,
            )
        except httpx.RequestError as e:
            raise NetworkError("Failed to connect to Outline API", original_error=e)
        except Exception as e:
            raise NetworkError("Unexpected error during API request", original_error=e)

        # Handle successful responses
        if response.status_code in (200, 201):
            try:
                return response.json()
            except Exception:
                raise OutlineError(
                    f"Failed to parse response: {response.text}", status_code=response.status_code
                )
        
        # Handle 302 redirects (special case for attachments.redirect)
        if response.status_code == 302:
            # For redirects, return the text which contains the redirect URL
            return {"redirect_text": response.text, "status_code": 302}

        # Handle error responses
        self._handle_error(response)

        # This should never be reached due to _handle_error raising
        raise OutlineError("Unknown error occurred")  # pragma: no cover

    def _handle_error(self, response: httpx.Response) -> None:
        """
        Convert HTTP error responses to appropriate exceptions.

        Args:
            response: HTTP response object

        Raises:
            Appropriate exception based on status code
        """
        # Try to parse error details from response
        try:
            error_data = response.json()
            message = error_data.get("error", error_data.get("message", "Unknown error"))
            data = error_data.get("data")
        except Exception:
            message = response.text or f"HTTP {response.status_code}"
            data = None

        status_code = response.status_code

        # Map status codes to exceptions
        if status_code == 400:
            raise ValidationError(message, data=data)
        elif status_code == 401:
            raise AuthenticationError(message, data=data)
        elif status_code == 403:
            raise AuthorizationError(message, data=data)
        elif status_code == 404:
            raise NotFoundError(message, data=data)
        elif status_code == 429:
            # Extract retry-after header (can be float or int)
            retry_after_str = response.headers.get("Retry-After", "60")
            try:
                retry_after = int(float(retry_after_str))
            except (ValueError, TypeError):
                retry_after = 60
            raise RateLimitError(retry_after, message, data=data)
        elif 500 <= status_code < 600:
            raise ServerError(message, status_code=status_code, data=data)
        else:
            raise OutlineError(message, status_code=status_code, data=data)

    def close(self) -> None:
        """Close the HTTP client session."""
        self._session.close()

    def __enter__(self) -> "OutlineClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit - closes the session."""
        self.close()

    def __del__(self) -> None:
        """Cleanup when object is destroyed."""
        try:
            self.close()
        except Exception:
            pass  # Ignore errors during cleanup
