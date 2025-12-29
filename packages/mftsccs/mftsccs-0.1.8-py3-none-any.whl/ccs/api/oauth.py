"""
OAuth API - Handles OAuth token requests for authentication.
"""

import aiohttp
from typing import Optional
from dataclasses import dataclass

from ccs.config.base_url import BaseUrl
from ccs.config.token_storage import TokenStorage


@dataclass
class OAuthResponse:
    """Response from OAuth token request."""
    success: bool
    access_token: str = ""
    token_type: str = ""
    expires_in: int = 0
    error: str = ""


async def getOAuthToken(
    client_id: str,
    client_secret: str,
    application_name: str,
    auto_set_token: bool = True
) -> OAuthResponse:
    """
    Request an OAuth access token from the server.

    This function authenticates with the OAuth endpoint using client credentials
    and returns an access token that can be used for API requests.

    Args:
        client_id: The OAuth client ID.
        client_secret: The OAuth client secret.
        application_name: The name of the application requesting the token.
        auto_set_token: If True, automatically sets the token in TokenStorage
                       for subsequent API calls. Default: True.

    Returns:
        OAuthResponse with the access token if successful, or error details if failed.

    Example:
        >>> from ccs.api import getOAuthToken
        >>>
        >>> response = await getOAuthToken(
        ...     client_id="101084838",
        ...     client_secret="your-client-secret",
        ...     application_name="myapp"
        ... )
        >>> if response.success:
        ...     print(f"Token: {response.access_token}")
        ... else:
        ...     print(f"Error: {response.error}")

    Example:
        >>> # Get token without auto-setting
        >>> response = await getOAuthToken(
        ...     client_id="101084838",
        ...     client_secret="secret",
        ...     application_name="myapp",
        ...     auto_set_token=False
        ... )
        >>> # Manually set token later
        >>> if response.success:
        ...     updateAccessToken(response.access_token)
    """
    try:
        url = BaseUrl.OAuthTokenUrl()

        # Create form data like the JS version
        form_data = aiohttp.FormData()
        form_data.add_field("client_id", client_id)
        form_data.add_field("client_secret", client_secret)
        form_data.add_field("application_name", application_name)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data) as response:
                if response.status == 200:
                    # Try to parse as JSON first
                    try:
                        json_data = await response.json()
                        access_token = json_data.get("access_token", "")
                        token_type = json_data.get("token_type", "Bearer")
                        expires_in = json_data.get("expires_in", 0)
                    except:
                        # If not JSON, treat response as the token itself
                        access_token = await response.text()
                        token_type = "Bearer"
                        expires_in = 0

                    if access_token:
                        # Auto-set token if requested
                        if auto_set_token:
                            TokenStorage.setToken(access_token)

                        return OAuthResponse(
                            success=True,
                            access_token=access_token,
                            token_type=token_type,
                            expires_in=expires_in
                        )
                    else:
                        return OAuthResponse(
                            success=False,
                            error="No access token in response"
                        )
                else:
                    error_text = await response.text()
                    return OAuthResponse(
                        success=False,
                        error=f"HTTP {response.status}: {error_text}"
                    )

    except aiohttp.ClientError as e:
        return OAuthResponse(
            success=False,
            error=f"Network error: {str(e)}"
        )
    except Exception as e:
        return OAuthResponse(
            success=False,
            error=f"Unexpected error: {str(e)}"
        )


async def refreshOAuthToken(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    auto_set_token: bool = True
) -> OAuthResponse:
    """
    Refresh an OAuth access token using a refresh token.

    Args:
        client_id: The OAuth client ID.
        client_secret: The OAuth client secret.
        refresh_token: The refresh token from a previous authentication.
        auto_set_token: If True, automatically sets the new token in TokenStorage.

    Returns:
        OAuthResponse with the new access token if successful.
    """
    try:
        url = BaseUrl.OAuthRefreshUrl()

        form_data = aiohttp.FormData()
        form_data.add_field("client_id", client_id)
        form_data.add_field("client_secret", client_secret)
        form_data.add_field("refresh_token", refresh_token)
        form_data.add_field("grant_type", "refresh_token")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data) as response:
                if response.status == 200:
                    try:
                        json_data = await response.json()
                        access_token = json_data.get("access_token", "")
                        token_type = json_data.get("token_type", "Bearer")
                        expires_in = json_data.get("expires_in", 0)
                    except:
                        access_token = await response.text()
                        token_type = "Bearer"
                        expires_in = 0

                    if access_token:
                        if auto_set_token:
                            TokenStorage.setToken(access_token)

                        return OAuthResponse(
                            success=True,
                            access_token=access_token,
                            token_type=token_type,
                            expires_in=expires_in
                        )
                    else:
                        return OAuthResponse(
                            success=False,
                            error="No access token in response"
                        )
                else:
                    error_text = await response.text()
                    return OAuthResponse(
                        success=False,
                        error=f"HTTP {response.status}: {error_text}"
                    )

    except aiohttp.ClientError as e:
        return OAuthResponse(
            success=False,
            error=f"Network error: {str(e)}"
        )
    except Exception as e:
        return OAuthResponse(
            success=False,
            error=f"Unexpected error: {str(e)}"
        )
