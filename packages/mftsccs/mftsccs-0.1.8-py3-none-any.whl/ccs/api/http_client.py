"""
HTTP Client - Handles API requests with automatic token refresh on 401 errors.
"""

import aiohttp
from typing import Optional, Dict, Any, NamedTuple

from ccs.config.base_url import BaseUrl
from ccs.config.token_storage import TokenStorage


class TokenRefreshError(Exception):
    """Raised when token refresh fails."""
    pass


class HttpResponse(NamedTuple):
    """Container for HTTP response data."""
    status: int
    body: bytes
    headers: Dict[str, str]

    async def json(self) -> Any:
        """Parse response body as JSON."""
        import json
        return json.loads(self.body.decode('utf-8'))

    async def text(self) -> str:
        """Get response body as text."""
        return self.body.decode('utf-8')


async def _refresh_oauth_token() -> bool:
    """
    Attempt to refresh the OAuth token using stored credentials.

    Returns:
        True if token refresh was successful, False otherwise.
    """
    # Check if we have OAuth credentials stored
    if not BaseUrl.CLIENT_ID or not BaseUrl.CLIENT_SECRET:
        return False

    if not BaseUrl.BASE_APPLICATION:
        return False

    try:
        # Import here to avoid circular dependency
        from ccs.api.oauth import getOAuthToken

        oauth_response = await getOAuthToken(
            client_id=BaseUrl.CLIENT_ID,
            client_secret=BaseUrl.CLIENT_SECRET,
            application_name=BaseUrl.BASE_APPLICATION,
            auto_set_token=True
        )

        return oauth_response.success

    except Exception as e:
        print(f"Token refresh failed: {e}")
        return False


async def request_with_retry(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    json: Optional[Dict[str, Any]] = None,
    max_retries: int = 1
) -> HttpResponse:
    """
    Make an HTTP request with automatic retry on 401 Unauthorized.

    If a 401 error occurs and OAuth credentials are available, this function
    will automatically refresh the token and retry the request once.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        url: The URL to request
        headers: Optional headers dict
        data: Optional form data
        json: Optional JSON body
        max_retries: Maximum number of retries on 401 (default: 1)

    Returns:
        HttpResponse object with status, body, and headers

    Raises:
        TokenRefreshError: If token refresh fails
        aiohttp.ClientError: For other network errors

    Example:
        >>> headers = {"Content-Type": "application/json"}
        >>> response = await request_with_retry(
        ...     "POST",
        ...     url,
        ...     headers=headers,
        ...     json={"id": 123}
        ... )
        >>> if response.status == 200:
        ...     data = await response.json()
    """
    if headers is None:
        headers = {}

    # Add auth header if available
    headers.update(TokenStorage.getAuthHeader())

    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries + 1):
            # Make the request
            async with session.request(
                method,
                url,
                headers=headers,
                data=data,
                json=json
            ) as response:
                # Read the response body while connection is still open
                body = await response.read()
                response_headers = dict(response.headers)
                status = response.status

                # If successful or not a 401, return the response
                if status != 401:
                    return HttpResponse(
                        status=status,
                        body=body,
                        headers=response_headers
                    )

                # On 401, attempt token refresh (only on first retry)
                if attempt < max_retries:
                    print(f"Received 401 Unauthorized, attempting token refresh...")

                    refresh_success = await _refresh_oauth_token()

                    if refresh_success:
                        print("Token refreshed successfully, retrying request...")
                        # Update headers with new token
                        headers.update(TokenStorage.getAuthHeader())
                        # Loop will retry the request
                        continue
                    else:
                        raise TokenRefreshError(
                            "Token refresh failed. Please check OAuth credentials."
                        )
                else:
                    # Max retries reached
                    raise TokenRefreshError(
                        "Received 401 Unauthorized and token refresh failed or unavailable."
                    )


async def post_with_retry(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    json: Optional[Dict[str, Any]] = None
) -> HttpResponse:
    """
    Convenience method for POST requests with automatic retry on 401.

    Args:
        url: The URL to request
        headers: Optional headers dict
        data: Optional form data
        json: Optional JSON body

    Returns:
        HttpResponse object
    """
    return await request_with_retry("POST", url, headers, data, json)


async def get_with_retry(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None
) -> HttpResponse:
    """
    Convenience method for GET requests with automatic retry on 401.

    Args:
        url: The URL to request
        headers: Optional headers dict
        params: Optional query parameters

    Returns:
        HttpResponse object
    """
    if params:
        # Build query string
        from urllib.parse import urlencode
        url = f"{url}?{urlencode(params)}"

    return await request_with_retry("GET", url, headers)
