"""
SafeBrowse SDK Configuration.

Provides centralized configuration with environment variable support.
"""
import os
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class SafeBrowseConfig:
    """
    Configuration for SafeBrowse client.
    
    Can be created explicitly or loaded from environment variables.
    
    Usage:
        # Explicit config
        config = SafeBrowseConfig(api_key="your-key")
        
        # From environment
        config = SafeBrowseConfig.from_env()
        
        # Mixed (env fallback)
        config = SafeBrowseConfig(api_key=os.getenv("MY_KEY"))
    
    Environment Variables:
        SAFEBROWSE_API_KEY: API key (required)
        SAFEBROWSE_BASE_URL: Base API URL (optional)
        SAFEBROWSE_TIMEOUT: Request timeout in seconds (optional)
    """
    
    # Required
    api_key: str
    
    # Optional with defaults
    base_url: str = "http://localhost:8000"
    timeout: float = 30.0
    
    # Logging hooks (optional callbacks)
    on_blocked: Callable[[Any], None] | None = None
    on_allowed: Callable[[Any], None] | None = None
    
    # Security settings (enforced, not configurable by design)
    fail_closed: bool = field(default=True, repr=False)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            raise ValueError(
                "API key is required. Set SAFEBROWSE_API_KEY environment variable "
                "or pass api_key explicitly."
            )
        
        # Ensure fail_closed cannot be disabled (security guarantee)
        if not self.fail_closed:
            raise ValueError(
                "fail_closed=False is not allowed. SafeBrowse always fails closed "
                "for security. This setting cannot be disabled."
            )
        
        # Normalize base URL
        self.base_url = self.base_url.rstrip("/")
    
    @classmethod
    def from_env(
        cls,
        prefix: str = "SAFEBROWSE_",
        on_blocked: Callable[[Any], None] | None = None,
        on_allowed: Callable[[Any], None] | None = None,
    ) -> "SafeBrowseConfig":
        """
        Create configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix (default: SAFEBROWSE_)
            on_blocked: Callback when content is blocked
            on_allowed: Callback when content is allowed
        
        Returns:
            SafeBrowseConfig instance
        
        Raises:
            ValueError: If required variables are missing
        
        Environment Variables:
            {prefix}API_KEY: API key (required)
            {prefix}BASE_URL: Base API URL (optional)
            {prefix}TIMEOUT: Request timeout in seconds (optional)
        """
        api_key = os.getenv(f"{prefix}API_KEY", "")
        base_url = os.getenv(f"{prefix}BASE_URL", "http://localhost:8000")
        timeout_str = os.getenv(f"{prefix}TIMEOUT", "30.0")
        
        try:
            timeout = float(timeout_str)
        except ValueError:
            timeout = 30.0
        
        return cls(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            on_blocked=on_blocked,
            on_allowed=on_allowed,
        )
    
    def with_hooks(
        self,
        on_blocked: Callable[[Any], None] | None = None,
        on_allowed: Callable[[Any], None] | None = None,
    ) -> "SafeBrowseConfig":
        """
        Create a new config with updated hooks.
        
        Args:
            on_blocked: Callback when content is blocked
            on_allowed: Callback when content is allowed
        
        Returns:
            New SafeBrowseConfig with updated hooks
        """
        return SafeBrowseConfig(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            on_blocked=on_blocked or self.on_blocked,
            on_allowed=on_allowed or self.on_allowed,
        )
