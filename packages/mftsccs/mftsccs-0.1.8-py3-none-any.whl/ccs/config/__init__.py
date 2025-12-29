"""
Configuration classes for the CCS library.
"""

from ccs.config.base_url import BaseUrl, CCSConfig
from ccs.config.token_storage import TokenStorage

__all__ = [
    "BaseUrl",
    "TokenStorage",
    "CCSConfig",
]
