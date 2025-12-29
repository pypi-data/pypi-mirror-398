"""
Initialization function for the CCS library.

The init() function must be called before using any other CCS functionality.
It configures the backend URLs, authentication, and application settings.
"""

import random
from typing import Optional, Dict, Any

from ccs.config.base_url import BaseUrl, CCSConfig
from ccs.config.token_storage import TokenStorage
from ccs.data.local_id import LocalId
from ccs.api.oauth import getOAuthToken


# Module-level state
_initialized: bool = False


async def init(
    url: str = "",
    nodeUrl: str = "",
    applicationName: str = "",
    config: Optional[CCSConfig] = None,
) -> bool:
    """
    Initialize the CCS library with backend configuration.

    This function MUST be called before using any other CCS functionality.
    It sets up the backend URLs, authentication tokens, and application settings.

    Args:
        url: The base URL for the CCS backend API.
             Example: "https://api.freeschema.com"

        nodeUrl: URL for the Node.js server (used for local sync, ghost IDs, etc.)
                Example: "http://localhost:5001"

        applicationName: Name identifier for this application.
                        Used for logging and tracking.

        config: Optional CCSConfig instance with additional configuration:
               - aiUrl: AI service URL (default: "https://ai.freeschema.com")
               - accessToken: JWT bearer token
               - enableAi: Enable AI features (default: True)
               - flags: Feature flags dict (logApplication, logPackage, accessTracker, isTest)
               - parameters: Additional parameters (e.g., logserver URL)
               - storagePath: Path for local data storage
               - clientId: OAuth client ID
               - clientSecret: OAuth client secret

    Returns:
        True if initialization was successful.

    Example:
        >>> # Using OAuth client credentials (recommended - token fetched automatically)
        >>> import asyncio
        >>> from ccs import init, CCSConfig
        >>>
        >>> async def main():
        ...     config = CCSConfig(
        ...         clientId="your-client-id",
        ...         clientSecret="your-client-secret",
        ...         flags={"logApplication": True},
        ...         storagePath="./data/ccs/"
        ...     )
        ...     await init(
        ...         url="https://api.freeschema.com",
        ...         nodeUrl="http://localhost:5001",
        ...         applicationName="MyApp",
        ...         config=config
        ...     )
        ...     print("CCS initialized with OAuth!")
        >>>
        >>> asyncio.run(main())

    Example:
        >>> # Using manual access token
        >>> config = CCSConfig(
        ...     accessToken="your-jwt-token",
        ...     aiUrl="https://ai.freeschema.com"
        ... )
        >>> await init(
        ...     url="https://api.freeschema.com",
        ...     nodeUrl="http://localhost:5001",
        ...     applicationName="MyApp",
        ...     config=config
        ... )

    Example:
        >>> # Minimal initialization
        >>> await init(
        ...     url="https://api.example.com",
        ...     nodeUrl="http://localhost:5001",
        ...     applicationName="MyApp"
        ... )

    Example:
        >>> # Initialize without token, add later
        >>> await init(
        ...     url="https://api.example.com",
        ...     nodeUrl="http://localhost:5001",
        ...     applicationName="MyApp"
        ... )
        >>> # ... user logs in ...
        >>> updateAccessToken("user-jwt-token")
    """
    global _initialized

    try:
        # Create default config if not provided
        if config is None:
            config = CCSConfig()

        # Set base URLs
        BaseUrl.BASE_URL = url if url else BaseUrl.BASE_URL
        BaseUrl.AI_URL = config.aiUrl
        BaseUrl.NODE_URL = nodeUrl if nodeUrl else BaseUrl.NODE_URL
        BaseUrl.BASE_APPLICATION = applicationName

        # Set OAuth credentials
        BaseUrl.CLIENT_ID = config.clientId
        BaseUrl.CLIENT_SECRET = config.clientSecret

        # Set log server from parameters
        if config.parameters and config.parameters.get("logserver"):
            BaseUrl.LOG_SERVER = config.parameters["logserver"]

        # Set custom storage path for local data (ID counters, etc.)
        # This allows app-specific isolation
        if config.storagePath:
            from pathlib import Path
            storage_dir = Path(config.storagePath)
            storage_dir.mkdir(parents=True, exist_ok=True)
            LocalId.set_storage_path(str(storage_dir / "local_ids.json"))

        # Handle authentication
        # If OAuth credentials are provided, fetch token automatically
        if config.clientId and config.clientSecret:
            if not applicationName:
                raise ValueError("applicationName is required when using OAuth client credentials")

            oauth_response = await getOAuthToken(
                client_id=config.clientId,
                client_secret=config.clientSecret,
                application_name=applicationName,
                auto_set_token=True
            )

            if not oauth_response.success:
                raise Exception(f"OAuth token request failed: {oauth_response.error}")

            # Token is already set by auto_set_token=True
        elif config.accessToken:
            # Use manually provided access token
            updateAccessToken(config.accessToken)

        # Generate randomizer for this session
        randomizer = random.randint(1, 100_000_000)
        BaseUrl.setRandomizer(randomizer)

        # NOTE: We do NOT reset LocalId counters here!
        # IDs must persist across init() calls to prevent collisions.
        # Only reset for testing purposes via LocalId.reset()

        # Set flags (already has defaults from CCSConfig.__post_init__)
        if config.flags:
            BaseUrl.FLAGS = config.flags

        _initialized = True

        return True

    except Exception as error:
        print(f"Cannot initialize the CCS system: {error}")
        raise error


def updateAccessToken(accessToken: str) -> None:
    """
    Update the bearer access token for API authentication.

    Call this function after user login to set the JWT token,
    or when the token needs to be refreshed.

    Args:
        accessToken: The JWT bearer token for authentication.

    Example:
        >>> from ccs import updateAccessToken
        >>> updateAccessToken("new-jwt-token-after-login")
    """
    TokenStorage.setToken(accessToken)


def isInitialized() -> bool:
    """
    Check if the CCS library has been initialized.

    Returns:
        True if init() has been called successfully.
    """
    return _initialized


def getConfig() -> Dict[str, Any]:
    """
    Get the current configuration.

    Returns:
        Dictionary with current configuration values.
    """
    return {
        "baseUrl": BaseUrl.BASE_URL,
        "aiUrl": BaseUrl.AI_URL,
        "nodeUrl": BaseUrl.NODE_URL,
        "applicationName": BaseUrl.BASE_APPLICATION,
        "logServer": BaseUrl.LOG_SERVER,
        "flags": BaseUrl.FLAGS,
        "randomizer": BaseUrl.BASE_RANDOMIZER,
        "isAuthenticated": TokenStorage.isAuthenticated(),
        "clientId": BaseUrl.CLIENT_ID,
        "hasClientSecret": BaseUrl.CLIENT_SECRET is not None and BaseUrl.CLIENT_SECRET != "",
    }
