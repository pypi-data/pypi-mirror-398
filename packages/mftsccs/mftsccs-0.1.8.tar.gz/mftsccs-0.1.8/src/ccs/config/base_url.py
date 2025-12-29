"""
BaseUrl - Configuration class for API endpoints and application settings.

Stores all URL configurations and application flags used throughout the library.
"""

import random
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class CCSConfig:
    """
    Configuration dataclass for CCS initialization.

    This class holds all optional configuration parameters for the CCS library,
    keeping the init() function clean with only essential parameters.

    Attributes:
        aiUrl: URL for the AI service. Defaults to "https://ai.freeschema.com"
        accessToken: JWT bearer token for authentication. Can be set later.
        enableAi: Whether to enable AI features. Defaults to True.
        flags: Dictionary of feature flags (logApplication, logPackage, accessTracker, isTest)
        parameters: Dictionary of additional parameters (e.g., logserver URL)
        storagePath: Path for storing local data (ID counters, etc.)
        clientId: OAuth client ID for authentication
        clientSecret: OAuth client secret for authentication

    Example:
        >>> config = CCSConfig(
        ...     aiUrl="https://ai.example.com",
        ...     accessToken="jwt-token",
        ...     flags={"logApplication": True},
        ...     storagePath="./data/ccs/"
        ... )
        >>> await init(
        ...     url="https://api.example.com",
        ...     nodeUrl="http://localhost:5001",
        ...     applicationName="MyApp",
        ...     config=config
        ... )
    """
    aiUrl: str = "https://ai.freeschema.com"
    accessToken: str = ""
    enableAi: bool = True
    flags: Optional[Dict[str, bool]] = None
    parameters: Optional[Dict[str, str]] = None
    storagePath: Optional[str] = None
    clientId: Optional[str] = None
    clientSecret: Optional[str] = None

    def __post_init__(self):
        """Initialize default flags if not provided."""
        if self.flags is None:
            self.flags = {
                "logApplication": False,
                "logPackage": False,
                "accessTracker": False,
                "isTest": False
            }


class BaseUrl:
    """
    Configuration class for API endpoints and application settings.

    This class stores all the URL configurations needed to communicate with
    the CCS backend, AI services, and other related services.

    All attributes are class-level (static) to match the JS implementation.

    Example:
        >>> from ccs import BaseUrl
        >>> BaseUrl.BASE_URL = "https://api.example.com"
        >>> url = BaseUrl.GetConceptUrl()
    """

    # Core URLs
    BASE_URL: str = "https://localhost:7053/"
    NODE_CACHE_URL: str = ""
    AI_URL: str = "https://ai.freeschema.com"
    MQTT_URL: str = "192.168.1.249"
    NODE_URL: str = "http://localhost:5001"
    LOG_SERVER: str = "https://logdev.freeschema.com"

    # Application settings
    BASE_APPLICATION: str = ""
    DOCUMENTATION_WIDGET: int = 0
    isNearestCache: bool = True

    # OAuth credentials
    CLIENT_ID: Optional[str] = None
    CLIENT_SECRET: Optional[str] = None

    # Feature flags
    FLAGS: Dict[str, Any] = {
        "logApplication": False,
        "logPackage": False,
        "accessTracker": False,
        "isTest": False
    }

    # Randomizer for IndexedDB separation
    BASE_RANDOMIZER: int = 999

    @classmethod
    def setRandomizer(cls, id: int) -> None:
        """Set the randomizer value for IndexedDB."""
        cls.BASE_RANDOMIZER = id

    @classmethod
    def getRandomizer(cls) -> int:
        """Get the current randomizer value."""
        return cls.BASE_RANDOMIZER

    # ============================================================
    # Concept URLs
    # ============================================================

    @classmethod
    def GetConceptUrl(cls) -> str:
        """Get URL for fetching a single concept."""
        if not cls.NODE_CACHE_URL or cls.NODE_CACHE_URL.strip() == "":
            return cls.BASE_URL + "/api/getConcept"
        return cls.NODE_CACHE_URL + "/api/getConcept"

    @classmethod
    def GetConnectionUrl(cls) -> str:
        """Get URL for fetching a connection by ID."""
        if not cls.NODE_CACHE_URL or cls.NODE_CACHE_URL.strip() == "":
            return cls.BASE_URL + "/api/get-connection-by-id"
        return cls.NODE_CACHE_URL + "/api/get-connection-by-id"

    @classmethod
    def GetConceptBulkUrl(cls) -> str:
        """Get URL for bulk concept fetching."""
        if not cls.NODE_CACHE_URL or cls.NODE_CACHE_URL.strip() == "":
            return cls.BASE_URL + "/api/get_concept_bulk"
        return cls.NODE_CACHE_URL + "/api/get_concept_bulk"

    @classmethod
    def GetConnectionBulkUrl(cls) -> str:
        """Get URL for bulk connection fetching."""
        if not cls.NODE_CACHE_URL or cls.NODE_CACHE_URL.strip() == "":
            return cls.BASE_URL + "/api/get_connection_bulk"
        return cls.NODE_CACHE_URL + "/api/get_connection_bulk"

    @classmethod
    def GetAllConceptsOfUserUrl(cls) -> str:
        """Get URL for fetching all concepts of a user."""
        return cls.BASE_URL + "/api/get_all_concepts_of_user"

    @classmethod
    def GetAllConnectionsOfUserUrl(cls) -> str:
        """Get URL for fetching all connections of a user."""
        return cls.BASE_URL + "/api/get_all_connections_of_user"

    @classmethod
    def GetAllConnectionsOfCompositionUrl(cls) -> str:
        """Get URL for fetching all connections of a composition."""
        return cls.BASE_URL + "/api/get_all_connections_of_composition"

    @classmethod
    def GetAllConnectionsOfCompositionBulkUrl(cls) -> str:
        """Get URL for bulk composition connections."""
        return cls.BASE_URL + "/api/get_all_connections_of_composition_bulk"

    @classmethod
    def GetConceptByCharacterValueUrl(cls) -> str:
        """Get URL for fetching concept by character value."""
        return cls.BASE_URL + "/api/get_concept_by_character_value"

    @classmethod
    def GetConceptByCharacterAndTypeUrl(cls) -> str:
        """Get URL for fetching concept by character and type."""
        return cls.BASE_URL + "/api/get_concept_by_character_and_type"

    @classmethod
    def GetConceptByCharacterAndCategoryUrl(cls) -> str:
        """Get URL for fetching concept by character and category."""
        return cls.BASE_URL + "/api/get_concept_by_character_and_category"

    # ============================================================
    # Authentication URLs
    # ============================================================

    @classmethod
    def LoginUrl(cls) -> str:
        """Get URL for login."""
        return cls.BASE_URL + "/api/auth/login"

    @classmethod
    def SignupUrl(cls) -> str:
        """Get URL for signup."""
        return cls.BASE_URL + "/api/auth/signup"

    @classmethod
    def OAuthTokenUrl(cls) -> str:
        """Get URL for OAuth token request."""
        return cls.BASE_URL + "/api/oauth/token"

    @classmethod
    def OAuthRefreshUrl(cls) -> str:
        """Get URL for OAuth token refresh."""
        return cls.BASE_URL + "/api/oauth/refresh"

    # ============================================================
    # Create URLs
    # ============================================================

    @classmethod
    def CreateTheConceptUrl(cls) -> str:
        """Get URL for creating a concept."""
        return cls.BASE_URL + "/api/create_the_concept"

    @classmethod
    def CreateTheConnectionUrl(cls) -> str:
        """Get URL for creating a connection."""
        return cls.BASE_URL + "/api/create_the_connection"

    @classmethod
    def MakeTheTypeConceptUrl(cls) -> str:
        """Get URL for making a type concept."""
        return cls.BASE_URL + "/api/make_the_type_concept"

    # ============================================================
    # Delete URLs
    # ============================================================

    @classmethod
    def DeleteConceptUrl(cls) -> str:
        """Get URL for deleting a concept."""
        return cls.BASE_URL + "/api/delete_concept"

    @classmethod
    def DeleteTheConnectionUrl(cls) -> str:
        """Get URL for deleting a connection."""
        return cls.BASE_URL + "/api/delete_connection"

    @classmethod
    def DeleteTheConnectionBulkUrl(cls) -> str:
        """Get URL for bulk deleting connections."""
        return cls.BASE_URL + "/api/delete_connection_bulk"

    # ============================================================
    # Search URLs
    # ============================================================

    @classmethod
    def RecursiveSearchUrl(cls) -> str:
        """Get URL for recursive search."""
        return cls.BASE_URL + "/api/recursivesearch-concept-connection"

    @classmethod
    def SearchLinkMultipleAllApiUrl(cls) -> str:
        """Get URL for search link multiple."""
        return cls.BASE_URL + "/api/Connection/search-link-multiple-all-ccs"

    @classmethod
    def FreeschemaQueryUrl(cls) -> str:
        """Get URL for freeschema query."""
        return cls.BASE_URL + "/api/freeschema-query"

    # ============================================================
    # Ghost/Local URLs (Node server)
    # ============================================================

    @classmethod
    def CreateGhostConceptApiUrl(cls, withAuth: bool = True) -> str:
        """Get URL for creating ghost concept."""
        if withAuth:
            return cls.NODE_URL + "/api/v1/local-concepts"
        return cls.NODE_URL + "/api/v1/local-concepts-without-auth"

    @classmethod
    def CreateGhostConnectionApiUrl(cls) -> str:
        """Get URL for creating ghost connection."""
        return cls.NODE_URL + "/api/v1/local-connections"

    @classmethod
    def GetRealConceptById(cls) -> str:
        """Get URL for translating local concept to real."""
        return cls.NODE_URL + "/api/v1/local-concepts-translate"

    # ============================================================
    # Reserved IDs URLs
    # ============================================================

    @classmethod
    def GetReservedIdUrl(cls) -> str:
        """Get URL for reserved concept IDs."""
        return cls.BASE_URL + "/api/get_reserved_ids"

    @classmethod
    def GetReservedConnectionIdUrl(cls) -> str:
        """Get URL for reserved connection IDs."""
        return cls.BASE_URL + "/api/get_reserved_connection_ids"

    # ============================================================
    # Logger URLs
    # ============================================================

    @classmethod
    def PostLogger(cls) -> str:
        """Get URL for posting logs."""
        return cls.LOG_SERVER + "/api/logger"

    @classmethod
    def LogHealth(cls) -> str:
        """Get URL for log health check."""
        return cls.LOG_SERVER + "/api/check"

    # ============================================================
    # Upload URLs
    # ============================================================

    @classmethod
    def uploadImageUrl(cls) -> str:
        """Get URL for image upload."""
        return cls.BASE_URL + "/api/Image/UploadImage"

    @classmethod
    def uploadFileUrl(cls) -> str:
        """Get URL for file upload."""
        return cls.BASE_URL + "/api/Image/UploadFile"
