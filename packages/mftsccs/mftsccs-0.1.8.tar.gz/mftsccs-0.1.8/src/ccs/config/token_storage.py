"""
TokenStorage - Manages authentication tokens and session information.

Stores bearer tokens and session IDs used for API authentication.
"""

from typing import Optional


class TokenStorage:
    """
    Storage class for authentication tokens and session information.

    This class manages the bearer access token used for API authentication
    and session identifiers for tracking user sessions.

    All attributes are class-level (static) to match the JS implementation.

    Example:
        >>> from ccs import TokenStorage
        >>> TokenStorage.BearerAccessToken = "your-jwt-token"
        >>> TokenStorage.sessionId = 12345
    """

    # Bearer token for API authentication
    BearerAccessToken: str = ""

    # Session identifier
    sessionId: int = 0

    # User ID from session
    userId: int = 0

    @classmethod
    def setToken(cls, token: str) -> None:
        """
        Set the bearer access token.

        Args:
            token: The JWT bearer token for authentication.
        """
        cls.BearerAccessToken = token

    @classmethod
    def getToken(cls) -> str:
        """
        Get the current bearer access token.

        Returns:
            The current bearer token string.
        """
        return cls.BearerAccessToken

    @classmethod
    def clearToken(cls) -> None:
        """Clear the bearer access token."""
        cls.BearerAccessToken = ""

    @classmethod
    def setSession(cls, sessionId: int, userId: int = 0) -> None:
        """
        Set session information.

        Args:
            sessionId: The session identifier.
            userId: Optional user ID associated with the session.
        """
        cls.sessionId = sessionId
        if userId:
            cls.userId = userId

    @classmethod
    def clearSession(cls) -> None:
        """Clear session information."""
        cls.sessionId = 0
        cls.userId = 0

    @classmethod
    def isAuthenticated(cls) -> bool:
        """
        Check if a valid token is present.

        Returns:
            True if a bearer token is set, False otherwise.
        """
        return bool(cls.BearerAccessToken)

    @classmethod
    def getAuthHeader(cls) -> dict:
        """
        Get the authorization header for API requests.

        Returns:
            Dictionary with Authorization header if token exists.
        """
        if cls.BearerAccessToken:
            return {"Authorization": f"Bearer {cls.BearerAccessToken}"}
        return {}
