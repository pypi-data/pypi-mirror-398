"""
Limitry Python SDK - Umbrella package
Re-exports core functionality from limitry.client
"""

from limitry.client import (
    APIError,
    AuthenticationError,
    Client,
    ClientConfig,
    LimitryError,
    NetworkError,
    PaginatedResponse,
    collect_all,
    paginate_all,
)

__version__ = "0.3.0"

__all__ = [
    "Client",
    "ClientConfig",
    "LimitryError",
    "APIError",
    "AuthenticationError",
    "NetworkError",
    "PaginatedResponse",
    "paginate_all",
    "collect_all",
    "__version__",
]
