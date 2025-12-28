"""
Custom exceptions for SafeBrowse SDK.

All exceptions include machine-readable error codes for automation.
"""
from enum import Enum


class ErrorCode(str, Enum):
    """Machine-readable error codes for SafeBrowse exceptions."""
    
    # Authentication errors
    AUTH_INVALID_KEY = "AUTH_INVALID_KEY"
    AUTH_EXPIRED_KEY = "AUTH_EXPIRED_KEY"
    AUTH_MISSING_KEY = "AUTH_MISSING_KEY"
    
    # Connection errors
    CONN_REFUSED = "CONN_REFUSED"
    CONN_TIMEOUT = "CONN_TIMEOUT"
    CONN_DNS_FAILURE = "CONN_DNS_FAILURE"
    
    # Injection detection
    INJECTION_DETECTED = "INJECTION_DETECTED"
    INJECTION_HIDDEN_HTML = "INJECTION_HIDDEN_HTML"
    INJECTION_INSTRUCTION_OVERRIDE = "INJECTION_INSTRUCTION_OVERRIDE"
    INJECTION_SYSTEM_PROMPT_LEAK = "INJECTION_SYSTEM_PROMPT_LEAK"
    INJECTION_ROLE_MANIPULATION = "INJECTION_ROLE_MANIPULATION"
    
    # Policy violations
    POLICY_LOGIN_FORM = "POLICY_LOGIN_FORM"
    POLICY_PAYMENT_FORM = "POLICY_PAYMENT_FORM"
    POLICY_BLOCKED_DOMAIN = "POLICY_BLOCKED_DOMAIN"
    POLICY_SUSPICIOUS_URL = "POLICY_SUSPICIOUS_URL"
    POLICY_SENSITIVE_DATA = "POLICY_SENSITIVE_DATA"
    
    # Content issues
    CONTENT_TOO_LARGE = "CONTENT_TOO_LARGE"
    CONTENT_MALFORMED = "CONTENT_MALFORMED"
    
    # Generic
    UNKNOWN = "UNKNOWN"
    API_ERROR = "API_ERROR"


class SafeBrowseError(Exception):
    """
    Base exception for SafeBrowse SDK.
    
    Attributes:
        message: Human-readable error message
        code: Machine-readable error code for automation
        request_id: Unique request ID for audit correlation
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN,
        request_id: str | None = None,
    ):
        self.message = message
        self.code = code
        self.request_id = request_id
        super().__init__(message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code.value if isinstance(self.code, ErrorCode) else self.code,
            "request_id": self.request_id,
        }


class BlockedError(SafeBrowseError):
    """
    Raised when content is blocked by SafeBrowse.
    
    Attributes:
        message: Human-readable reason for blocking
        code: Machine-readable error code
        risk_score: Risk score (0.0-1.0)
        explanations: List of human-readable explanations
        policy_violations: List of violated policy rules
        request_id: Unique request ID for audit correlation
    
    Example:
        try:
            result = client.safe_ask(html, url, query)
        except BlockedError as e:
            print(f"Blocked: {e.message}")
            print(f"Code: {e.code}")  # e.g., ErrorCode.INJECTION_DETECTED
            print(f"Risk: {e.risk_score}")
            print(f"Request ID: {e.request_id}")
    """
    
    def __init__(
        self,
        message: str,
        risk_score: float,
        code: ErrorCode = ErrorCode.INJECTION_DETECTED,
        explanations: list[str] | None = None,
        policy_violations: list[str] | None = None,
        request_id: str | None = None,
    ):
        super().__init__(message, code, request_id)
        self.risk_score = risk_score
        self.explanations = explanations or []
        self.policy_violations = policy_violations or []
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for logging/serialization."""
        result = super().to_dict()
        result.update({
            "risk_score": self.risk_score,
            "explanations": self.explanations,
            "policy_violations": self.policy_violations,
        })
        return result


class AuthenticationError(SafeBrowseError):
    """Raised when API key is invalid or missing."""
    
    def __init__(
        self,
        message: str = "Invalid API key",
        code: ErrorCode = ErrorCode.AUTH_INVALID_KEY,
        request_id: str | None = None,
    ):
        super().__init__(message, code, request_id)


class ConnectionError(SafeBrowseError):
    """Raised when unable to connect to SafeBrowse API."""
    
    def __init__(
        self,
        message: str = "Unable to connect to SafeBrowse API",
        code: ErrorCode = ErrorCode.CONN_REFUSED,
        request_id: str | None = None,
    ):
        super().__init__(message, code, request_id)


class ConfigurationError(SafeBrowseError):
    """Raised when SDK configuration is invalid."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN,
    ):
        super().__init__(message, code, None)
