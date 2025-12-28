"""
SafeBrowse Python SDK
AI-powered browser security with prompt injection detection.

Enterprise-grade security for AI agents and RAG pipelines.
"""
from .config import SafeBrowseConfig
from .client import (
    SafeBrowseClient,
    AsyncSafeBrowseClient,
    ScanResult,
    AskResult,
    SanitizeResult,
    BatchScanResult,
)
from .exceptions import (
    SafeBrowseError,
    BlockedError,
    AuthenticationError,
    ConnectionError,
    ConfigurationError,
    ErrorCode,
)

__version__ = "0.2.0"
__all__ = [
    # Config
    "SafeBrowseConfig",
    # Clients
    "SafeBrowseClient",
    "AsyncSafeBrowseClient",
    # Results
    "ScanResult",
    "AskResult",
    "SanitizeResult",
    "BatchScanResult",
    # Exceptions
    "SafeBrowseError",
    "BlockedError",
    "AuthenticationError",
    "ConnectionError",
    "ConfigurationError",
    # Enums
    "ErrorCode",
]
