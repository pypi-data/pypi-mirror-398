"""Sunbay Nexus Python SDK public exports."""

try:
    from importlib.metadata import version

    __version__ = version("sunbay-nexus-sdk")
except ImportError:
    # Fallback for Python < 3.8
    import pkg_resources

    __version__ = pkg_resources.get_distribution("sunbay-nexus-sdk").version
except Exception:
    # Fallback if package is not installed (e.g., during development)
    __version__ = "1.0.4"

from .client import NexusClient
from .exceptions import SunbayBusinessError, SunbayNetworkError
from .enums import (
    AuthenticationMethod,
    CardNetworkType,
    EntryMode,
    PaymentCategory,
    TransactionStatus,
    TransactionType,
)

__all__ = (
    "NexusClient",
    "SunbayBusinessError",
    "SunbayNetworkError",
    "TransactionStatus",
    "TransactionType",
    "CardNetworkType",
    "EntryMode",
    "PaymentCategory",
    "AuthenticationMethod",
)



