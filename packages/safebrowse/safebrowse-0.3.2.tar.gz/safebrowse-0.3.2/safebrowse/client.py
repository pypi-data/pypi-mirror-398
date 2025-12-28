"""
SafeBrowse Client - Python SDK for SafeBrowse API.

Enterprise-grade SDK for AI browser security with prompt injection detection.
"""
import httpx
from dataclasses import dataclass
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, Any, Callable, Union, IO
import os

from .config import SafeBrowseConfig
from .exceptions import (
    SafeBrowseError,
    BlockedError,
    AuthenticationError,
    ConnectionError,
    ErrorCode,
)


@dataclass
class ScanResult:
    """
    Result of a safety scan.
    
    Attributes:
        is_safe: Whether the content passed all safety checks
        risk_score: Risk score from 0.0 (safe) to 1.0 (dangerous)
        reason: Human-readable reason if blocked
        explanations: List of human-readable safety explanations
        policy_violations: List of violated policy rules
        request_id: Unique request ID for audit correlation
    """
    is_safe: bool
    risk_score: float
    reason: str | None
    explanations: list[str] | None
    policy_violations: list[str] | None
    request_id: str


@dataclass
class AskResult:
    """
    Result of a safe-ask request.
    
    Attributes:
        status: "ok" if successful, "blocked" if content was blocked
        answer: LLM response (None if blocked)
        risk_score: Risk score from 0.0 (safe) to 1.0 (dangerous)
        reason: Human-readable reason if blocked
        explanations: List of human-readable safety explanations
        request_id: Unique request ID for audit correlation
    """
    status: str
    answer: str | None
    risk_score: float
    reason: str | None
    explanations: list[str] | None
    request_id: str


@dataclass
class SanitizeResult:
    """
    Result of RAG chunk sanitization.
    
    Attributes:
        total_count: Total number of chunks processed
        safe_count: Number of safe chunks
        blocked_count: Number of blocked chunks
        safe_chunks: List of safe chunk contents
        results: Detailed results per chunk
        request_id: Unique request ID for audit correlation
    """
    total_count: int
    safe_count: int
    blocked_count: int
    safe_chunks: list[str]
    results: list[dict]
    request_id: str


@dataclass  
class BatchScanResult:
    """
    Result of batch scanning.
    
    Attributes:
        total: Total number of items scanned
        safe_count: Number of safe items
        blocked_count: Number of blocked items
        results: List of individual ScanResult objects
    """
    total: int
    safe_count: int
    blocked_count: int
    results: list[ScanResult]


@dataclass
class AuditLogEntry:
    """Single audit log entry."""
    request_id: str
    timestamp: str
    url: str
    status: str
    risk_score: float
    reasons: list[str]
    policy_violations: list[str]


@dataclass
class AuditLogsResult:
    """Result of audit logs retrieval."""
    logs: list[AuditLogEntry]
    total: int
    limit: int
    offset: int


@dataclass
class AuditStatsResult:
    """Result of audit statistics retrieval."""
    total_requests: int
    blocked_requests: int
    allowed_requests: int
    block_rate: float
    avg_risk_score: float
    top_blocked_domains: list[dict]
    requests_by_hour: list[dict]


@dataclass
class DocumentScanResult:
    """Result of a document (PDF/Image) scan."""
    is_safe: bool
    risk_score: float
    extracted_text: str
    reason: str | None
    explanations: list[str] | None
    policy_violations: list[str] | None
    page_count: int
    request_id: str


@dataclass
class RedTeamScenario:
    """Red team attack scenario description."""
    id: str
    name: str
    description: str
    category: str


@dataclass
class RedTeamTestResult:
    """Result of a red team test run."""
    scenario_id: str
    passed: bool
    risk_score: float
    reason: str | None


@dataclass
class RedTeamSummary:
    """Summary of red team testing."""
    total_tests: int
    passed_count: int
    failed_count: int
    detection_rate: float
    results: list[RedTeamTestResult]


@dataclass
class AgentSessionResult:
    """State of a guarded agent session."""
    session_id: str
    total_steps: int
    is_stopped: bool
    duration_seconds: float
    stop_reason: str | None = None
    read_actions: int = 0
    write_actions: int = 0
    execute_actions: int = 0
    failed_steps: int = 0


class SafeBrowseClient:
    """
    SafeBrowse API client for Python.
    
    Usage:
        # Simple initialization
        client = SafeBrowseClient(api_key="your-key")
        
        # With config object
        config = SafeBrowseConfig(api_key="your-key", timeout=60)
        client = SafeBrowseClient(config=config)
        
        # From environment variables
        client = SafeBrowseClient.from_env()
        
        # Scan HTML for safety
        result = client.scan_html(html="<html>...</html>", url="https://example.com")
        
        # Ask a question safely
        result = client.safe_ask(
            html="<html>...</html>",
            url="https://example.com",
            query="What is this page about?"
        )
        
        # Use context manager for agent protection
        with client.guard(html, url) as decision:
            print(f"Risk score: {decision.risk_score}")
            agent.run()
        
        # Sanitize RAG chunks
        result = client.sanitize(documents=["chunk1", "chunk2"])
        safe_docs = result.safe_chunks
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        config: SafeBrowseConfig | None = None,
        on_blocked: Callable[[ScanResult], None] | None = None,
        on_allowed: Callable[[ScanResult], None] | None = None,
    ):
        """
        Initialize SafeBrowse client.
        
        Args:
            api_key: Your SafeBrowse API key (or use config)
            base_url: Base URL of the SafeBrowse API
            timeout: Request timeout in seconds
            config: SafeBrowseConfig object (overrides other params)
            on_blocked: Callback invoked when content is blocked
            on_allowed: Callback invoked when content is allowed
        """
        if config:
            self.api_key = config.api_key
            self.base_url = config.base_url
            self.timeout = config.timeout
            self._on_blocked = config.on_blocked or on_blocked
            self._on_allowed = config.on_allowed or on_allowed
        else:
            if not api_key:
                raise ValueError("api_key is required")
            self.api_key = api_key
            self.base_url = base_url.rstrip("/")
            self.timeout = timeout
            self._on_blocked = on_blocked
            self._on_allowed = on_allowed
        
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"X-API-Key": self.api_key},
        )
    
    @classmethod
    def from_env(
        cls,
        on_blocked: Callable[[ScanResult], None] | None = None,
        on_allowed: Callable[[ScanResult], None] | None = None,
    ) -> "SafeBrowseClient":
        """
        Create client from environment variables.
        
        Environment Variables:
            SAFEBROWSE_API_KEY: API key (required)
            SAFEBROWSE_BASE_URL: Base API URL (optional)
            SAFEBROWSE_TIMEOUT: Request timeout in seconds (optional)
        
        Returns:
            SafeBrowseClient instance
        """
        config = SafeBrowseConfig.from_env(
            on_blocked=on_blocked,
            on_allowed=on_allowed,
        )
        return cls(config=config)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()
    
    def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response and raise appropriate errors."""
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key", ErrorCode.AUTH_INVALID_KEY)
        
        if response.status_code >= 400:
            raise SafeBrowseError(
                f"API error: {response.status_code}",
                ErrorCode.API_ERROR,
            )
        
        return response.json()
    
    def _invoke_hooks(self, result: ScanResult):
        """Invoke appropriate hooks based on scan result."""
        if result.is_safe and self._on_allowed:
            self._on_allowed(result)
        elif not result.is_safe and self._on_blocked:
            self._on_blocked(result)
    
    def _determine_error_code(self, data: dict) -> ErrorCode:
        """Determine error code from API response."""
        reason = data.get("reason", "").lower()
        policy_violations = data.get("policy_violations", [])
        
        # Check policy violations first
        for violation in policy_violations:
            violation_lower = violation.lower()
            if "login" in violation_lower or "password" in violation_lower:
                return ErrorCode.POLICY_LOGIN_FORM
            if "payment" in violation_lower:
                return ErrorCode.POLICY_PAYMENT_FORM
            if "blocked domain" in violation_lower:
                return ErrorCode.POLICY_BLOCKED_DOMAIN
        
        # Check reason for injection patterns
        if "ignore" in reason or "instruction" in reason:
            return ErrorCode.INJECTION_INSTRUCTION_OVERRIDE
        if "hidden" in reason:
            return ErrorCode.INJECTION_HIDDEN_HTML
        if "system" in reason and "prompt" in reason:
            return ErrorCode.INJECTION_SYSTEM_PROMPT_LEAK
        if "role" in reason:
            return ErrorCode.INJECTION_ROLE_MANIPULATION
        
        return ErrorCode.INJECTION_DETECTED
    
    def scan_html(self, html: str, url: str) -> ScanResult:
        """
        Scan HTML content for prompt injection and policy violations.
        
        Args:
            html: Raw HTML content
            url: URL of the page
            
        Returns:
            ScanResult with safety information
            
        Raises:
            ConnectionError: If unable to connect to API
            AuthenticationError: If API key is invalid
        """
        try:
            response = self._client.post(
                "/scan-html",
                json={"html": html, "url": url},
            )
        except httpx.ConnectError:
            raise ConnectionError("Unable to connect to SafeBrowse API")
        
        data = self._handle_response(response)
        
        result = ScanResult(
            is_safe=data.get("is_safe", False),
            risk_score=data.get("risk_score", 1.0),
            reason=data.get("reason"),
            explanations=data.get("explanations"),
            policy_violations=data.get("policy_violations"),
            request_id=data.get("request_id", ""),
        )
        
        self._invoke_hooks(result)
        return result
    
    def safe_ask(self, html: str, url: str, query: str) -> AskResult:
        """
        Safely ask a question about a webpage.
        
        Args:
            html: Raw HTML content
            url: URL of the page
            query: Question to ask about the page
            
        Returns:
            AskResult with answer or blocking info
            
        Raises:
            BlockedError: If content is blocked
            ConnectionError: If unable to connect to API
            AuthenticationError: If API key is invalid
        """
        try:
            response = self._client.post(
                "/safe-ask",
                json={"html": html, "url": url, "query": query},
            )
        except httpx.ConnectError:
            raise ConnectionError("Unable to connect to SafeBrowse API")
        
        data = self._handle_response(response)
        
        result = AskResult(
            status=data.get("status", "error"),
            answer=data.get("answer"),
            risk_score=data.get("risk_score", 1.0),
            reason=data.get("reason"),
            explanations=data.get("explanations"),
            request_id=data.get("request_id", ""),
        )
        
        if result.status == "blocked":
            error_code = self._determine_error_code(data)
            raise BlockedError(
                message=result.reason or "Content blocked",
                risk_score=result.risk_score,
                code=error_code,
                explanations=result.explanations,
                policy_violations=data.get("policy_violations"),
                request_id=result.request_id,
            )
        
        return result
    
    def is_safe(self, html: str, url: str) -> bool:
        """
        Quick check if content is safe.
        
        Args:
            html: Raw HTML content
            url: URL of the page
            
        Returns:
            True if safe, False otherwise
        """
        try:
            result = self.scan_html(html, url)
            return result.is_safe
        except (BlockedError, SafeBrowseError):
            return False
    
    @contextmanager
    def guard(self, html: str, url: str) -> Generator[ScanResult, None, None]:
        """
        Context manager for protecting agent operations.
        
        Provides explicit access to decision metadata (risk_score, explanations, etc.)
        
        Usage:
            with client.guard(html, url) as decision:
                print(f"Risk score: {decision.risk_score}")
                # Only executes if content is safe
                agent.run()
        
        Raises:
            BlockedError: If content is blocked
        """
        result = self.scan_html(html, url)
        
        if not result.is_safe:
            error_code = ErrorCode.INJECTION_DETECTED
            if result.policy_violations:
                error_code = ErrorCode.POLICY_LOGIN_FORM  # Default policy code
            
            raise BlockedError(
                message=result.reason or "Content blocked by safety policy",
                risk_score=result.risk_score,
                code=error_code,
                explanations=result.explanations,
                policy_violations=result.policy_violations,
                request_id=result.request_id,
            )
        
        yield result
    
    def sanitize(
        self,
        documents: list[str],
        url: str = "unknown",
        source: str = "web",
    ) -> SanitizeResult:
        """
        Sanitize RAG document chunks.
        
        Scans each chunk for prompt injection and returns only safe chunks.
        
        Args:
            documents: List of document chunks to sanitize
            url: Source URL for the documents
            source: Source type ("web", "file", "api")
        
        Returns:
            SanitizeResult with safe chunks and detailed results
        
        Example:
            result = client.sanitize(
                documents=["chunk 1", "chunk 2", "ignore previous instructions"],
                source="web"
            )
            safe_docs = result.safe_chunks  # Only safe chunks
            print(f"Blocked {result.blocked_count} dangerous chunks")
        """
        try:
            response = self._client.post(
                "/sanitize",
                json={"chunks": documents, "url": url},
            )
        except httpx.ConnectError:
            raise ConnectionError("Unable to connect to SafeBrowse API")
        
        data = self._handle_response(response)
        
        # Extract safe chunks
        safe_chunks = []
        results = data.get("results", [])
        for i, result in enumerate(results):
            if result.get("is_safe", False):
                if i < len(documents):
                    safe_chunks.append(documents[i])
        
        return SanitizeResult(
            total_count=data.get("total_count", len(documents)),
            safe_count=data.get("safe_count", len(safe_chunks)),
            blocked_count=data.get("blocked_count", len(documents) - len(safe_chunks)),
            safe_chunks=safe_chunks,
            results=results,
            request_id=data.get("request_id", ""),
        )
    
    def scan_batch(
        self,
        items: list[dict[str, str]],
    ) -> BatchScanResult:
        """
        Scan multiple HTML documents in batch.
        
        Each item is scanned independently - batch still fails closed per item.
        
        Args:
            items: List of {"html": "...", "url": "..."} dicts
        
        Returns:
            BatchScanResult with individual results
        
        Example:
            results = client.scan_batch([
                {"html": "<html>...</html>", "url": "https://example.com"},
                {"html": "<html>...</html>", "url": "https://other.com"},
            ])
            print(f"Safe: {results.safe_count}/{results.total}")
        """
        results = []
        safe_count = 0
        blocked_count = 0
        
        for item in items:
            try:
                result = self.scan_html(
                    html=item.get("html", ""),
                    url=item.get("url", "unknown"),
                )
                results.append(result)
                if result.is_safe:
                    safe_count += 1
                else:
                    blocked_count += 1
            except SafeBrowseError:
                # Fail closed - treat errors as blocked
                blocked_count += 1
                results.append(ScanResult(
                    is_safe=False,
                    risk_score=1.0,
                    reason="Scan failed - treated as blocked (fail closed)",
                    explanations=["Error during scan"],
                    policy_violations=None,
                    request_id="",
                ))
        
        return BatchScanResult(
            total=len(items),
            safe_count=safe_count,
            blocked_count=blocked_count,
            results=results,
        )
    
    def get_capabilities(self) -> dict:
        """
        Get available API capabilities and feature flags.
        
        Returns:
            Dict of feature flags for forward compatibility
        
        Example:
            caps = client.get_capabilities()
            if caps.get("supports_pdf"):
                # Use PDF scanning
        """
        try:
            response = self._client.get("/capabilities")
            return self._handle_response(response)
        except Exception:
            # Default capabilities if endpoint unavailable
            return {
                "html_scanning": True,
                "policy_engine": True,
                "audit_logging": True,
            }
    
    def attach_request_id(self, correlation_id: str):
        """
        Attach a custom correlation ID for the next request.
        
        Useful for correlating SDK actions with internal workflows.
        
        Args:
            correlation_id: Your internal request/step ID
        
        Note: This sets a header that will be included in audit logs.
        """
        self._client.headers["X-Correlation-ID"] = correlation_id

    # ============== Audit Methods ==============

    def get_audit_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        domain: str | None = None,
    ) -> AuditLogsResult:
        """Get paginated audit logs."""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if domain:
            params["domain"] = domain
        
        response = self._client.get("/audit/logs", params=params)
        data = self._handle_response(response)
        
        logs = [
            AuditLogEntry(
                request_id=log["request_id"],
                timestamp=log["timestamp"],
                url=log["url"],
                status=log["status"],
                risk_score=log["risk_score"],
                reasons=log["reasons"],
                policy_violations=log["policy_violations"],
            )
            for log in data.get("logs", [])
        ]
        
        return AuditLogsResult(
            logs=logs,
            total=data.get("total", 0),
            limit=data.get("limit", limit),
            offset=data.get("offset", offset),
        )

    def get_audit_stats(self, hours: int = 24) -> AuditStatsResult:
        """Get aggregated audit statistics."""
        response = self._client.get("/audit/stats", params={"hours": hours})
        data = self._handle_response(response)
        
        return AuditStatsResult(
            total_requests=data.get("total_requests", 0),
            blocked_requests=data.get("blocked_requests", 0),
            allowed_requests=data.get("allowed_requests", 0),
            block_rate=data.get("block_rate", 0.0),
            avg_risk_score=data.get("avg_risk_score", 0.0),
            top_blocked_domains=data.get("top_blocked_domains", []),
            requests_by_hour=data.get("requests_by_hour", []),
        )

    # ============== Document Scanning Methods ==============

    def _scan_file(self, endpoint: str, file: Union[str, bytes, IO]) -> DocumentScanResult:
        """Helper to scan image or PDF files."""
        files = None
        if isinstance(file, str):
            files = {"file": open(file, "rb")}
        elif isinstance(file, bytes):
            files = {"file": ("file", file)}
        else:
            files = {"file": file}
            
        try:
            response = self._client.post(endpoint, files=files)
            data = self._handle_response(response)
            
            return DocumentScanResult(
                is_safe=data.get("is_safe", False),
                risk_score=data.get("risk_score", 1.0),
                extracted_text=data.get("extracted_text", ""),
                reason=data.get("reason"),
                explanations=data.get("explanations"),
                policy_violations=data.get("policy_violations"),
                page_count=data.get("page_count", 1),
                request_id=data.get("request_id", ""),
            )
        finally:
            if isinstance(file, str) and files:
                files["file"].close()

    def scan_image(self, file: Union[str, bytes, IO]) -> DocumentScanResult:
        """Scan an image for prompt injection via OCR."""
        return self._scan_file("/scan-image", file)

    def scan_pdf(self, file: Union[str, bytes, IO]) -> DocumentScanResult:
        """Scan a PDF for prompt injection (includes OCR for images)."""
        return self._scan_file("/scan-pdf", file)

    # ============== Red Team Methods ==============

    def list_attack_scenarios(self) -> list[RedTeamScenario]:
        """List all available attack scenarios for red team testing."""
        response = self._client.get("/test/scenarios")
        data = self._handle_response(response)
        
        return [
            RedTeamScenario(
                id=s["id"],
                name=s["name"],
                description=s["description"],
                category=s["category"],
            )
            for s in data.get("scenarios", [])
        ]

    def run_red_team_test(self, scenario_ids: list[str] | None = None) -> RedTeamSummary:
        """Run red team attack scenarios against SafeBrowse."""
        payload = {"scenario_ids": scenario_ids} if scenario_ids else {}
        response = self._client.post("/test/red-team", json=payload)
        data = self._handle_response(response)
        
        results = [
            RedTeamTestResult(
                scenario_id=r["scenario_id"],
                passed=r.get("detected", False),
                risk_score=r["risk_score"],
                reason=r.get("explanations", [None])[0],
            )
            for r in data.get("results", [])
        ]
        
        stats = data.get("statistics", {})
        return RedTeamSummary(
            total_tests=stats.get("total", 0),
            passed_count=stats.get("detected", 0),
            failed_count=stats.get("missed", 0),
            detection_rate=stats.get("detection_rate", 0.0),
            results=results,
        )

    # ============== Agent Guard Session Methods ==============

    def start_agent_session(
        self,
        max_steps: int = 100,
        max_retries: int = 5,
        timeout_seconds: float = 300,
    ) -> str:
        """Start a new guarded agent session and return session_id."""
        response = self._client.post(
            "/agent/session/start",
            json={
                "max_steps": max_steps,
                "max_retries": max_retries,
                "timeout_seconds": timeout_seconds,
            },
        )
        data = self._handle_response(response)
        return data["session_id"]

    def record_agent_step(
        self,
        session_id: str,
        action_type: str,
        action_name: str,
        success: bool = True,
    ) -> AgentSessionResult:
        """Record an agent step in a guarded session."""
        params = {
            "action_type": action_type,
            "action_name": action_name,
            "success": str(success).lower(),
        }
        response = self._client.post(
            f"/agent/session/{session_id}/step",
            params=params,
        )
        data = self._handle_response(response)
        summary = data.get("session_summary", {})
        return AgentSessionResult(
            session_id=summary["session_id"],
            total_steps=summary["total_steps"],
            is_stopped=summary["is_stopped"],
            duration_seconds=summary["duration_seconds"],
            stop_reason=summary.get("stop_reason"),
            read_actions=summary.get("read_actions", 0),
            write_actions=summary.get("write_actions", 0),
            execute_actions=summary.get("execute_actions", 0),
            failed_steps=summary.get("failed_steps", 0),
        )

    def get_agent_session(self, session_id: str) -> AgentSessionResult:
        """Get the current state of an agent session."""
        response = self._client.get(f"/agent/session/{session_id}")
        summary = self._handle_response(response)
        return AgentSessionResult(
            session_id=summary["session_id"],
            total_steps=summary["total_steps"],
            is_stopped=summary["is_stopped"],
            duration_seconds=summary["duration_seconds"],
            stop_reason=summary.get("stop_reason"),
            read_actions=summary.get("read_actions", 0),
            write_actions=summary.get("write_actions", 0),
            execute_actions=summary.get("execute_actions", 0),
            failed_steps=summary.get("failed_steps", 0),
        )

    def end_agent_session(self, session_id: str):
        """End an agent session."""
        response = self._client.delete(f"/agent/session/{session_id}")
        self._handle_response(response)


class AsyncSafeBrowseClient:
    """
    Async version of SafeBrowse client.
    
    Usage:
        async with AsyncSafeBrowseClient(api_key="your-key") as client:
            result = await client.scan_html(html="...", url="...")
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        config: SafeBrowseConfig | None = None,
        on_blocked: Callable[[ScanResult], None] | None = None,
        on_allowed: Callable[[ScanResult], None] | None = None,
    ):
        if config:
            self.api_key = config.api_key
            self.base_url = config.base_url
            self.timeout = config.timeout
            self._on_blocked = config.on_blocked or on_blocked
            self._on_allowed = config.on_allowed or on_allowed
        else:
            if not api_key:
                raise ValueError("api_key is required")
            self.api_key = api_key
            self.base_url = base_url.rstrip("/")
            self.timeout = timeout
            self._on_blocked = on_blocked
            self._on_allowed = on_allowed
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"X-API-Key": self.api_key},
        )
    
    @classmethod
    def from_env(
        cls,
        on_blocked: Callable[[ScanResult], None] | None = None,
        on_allowed: Callable[[ScanResult], None] | None = None,
    ) -> "AsyncSafeBrowseClient":
        """Create async client from environment variables."""
        config = SafeBrowseConfig.from_env(
            on_blocked=on_blocked,
            on_allowed=on_allowed,
        )
        return cls(config=config)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response and raise appropriate errors."""
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key", ErrorCode.AUTH_INVALID_KEY)
        
        if response.status_code >= 400:
            raise SafeBrowseError(
                f"API error: {response.status_code}",
                ErrorCode.API_ERROR,
            )
        
        return response.json()
    
    def _invoke_hooks(self, result: ScanResult):
        """Invoke appropriate hooks based on scan result."""
        if result.is_safe and self._on_allowed:
            self._on_allowed(result)
        elif not result.is_safe and self._on_blocked:
            self._on_blocked(result)
    
    async def scan_html(self, html: str, url: str) -> ScanResult:
        """Async version of scan_html."""
        try:
            response = await self._client.post(
                "/scan-html",
                json={"html": html, "url": url},
            )
        except httpx.ConnectError:
            raise ConnectionError("Unable to connect to SafeBrowse API")
        
        data = await self._handle_response(response)
        
        result = ScanResult(
            is_safe=data.get("is_safe", False),
            risk_score=data.get("risk_score", 1.0),
            reason=data.get("reason"),
            explanations=data.get("explanations"),
            policy_violations=data.get("policy_violations"),
            request_id=data.get("request_id", ""),
        )
        
        self._invoke_hooks(result)
        return result
    
    async def safe_ask(self, html: str, url: str, query: str) -> AskResult:
        """Async version of safe_ask."""
        try:
            response = await self._client.post(
                "/safe-ask",
                json={"html": html, "url": url, "query": query},
            )
        except httpx.ConnectError:
            raise ConnectionError("Unable to connect to SafeBrowse API")
        
        data = await self._handle_response(response)
        
        result = AskResult(
            status=data.get("status", "error"),
            answer=data.get("answer"),
            risk_score=data.get("risk_score", 1.0),
            reason=data.get("reason"),
            explanations=data.get("explanations"),
            request_id=data.get("request_id", ""),
        )
        
        if result.status == "blocked":
            raise BlockedError(
                message=result.reason or "Content blocked",
                risk_score=result.risk_score,
                code=ErrorCode.INJECTION_DETECTED,
                explanations=result.explanations,
                request_id=result.request_id,
            )
        
        return result
    
    async def is_safe(self, html: str, url: str) -> bool:
        """Async version of is_safe."""
        try:
            result = await self.scan_html(html, url)
            return result.is_safe
        except (BlockedError, SafeBrowseError):
            return False
    
    async def sanitize(
        self,
        documents: list[str],
        url: str = "unknown",
        source: str = "web",
    ) -> SanitizeResult:
        """Async version of sanitize."""
        try:
            response = await self._client.post(
                "/sanitize",
                json={"chunks": documents, "url": url},
            )
        except httpx.ConnectError:
            raise ConnectionError("Unable to connect to SafeBrowse API")
        
        data = await self._handle_response(response)
        
        safe_chunks = []
        results = data.get("results", [])
        for i, result in enumerate(results):
            if result.get("is_safe", False):
                if i < len(documents):
                    safe_chunks.append(documents[i])
        
        return SanitizeResult(
            total_count=data.get("total_count", len(documents)),
            safe_count=data.get("safe_count", len(safe_chunks)),
            blocked_count=data.get("blocked_count", len(documents) - len(safe_chunks)),
            safe_chunks=safe_chunks,
            results=results,
            request_id=data.get("request_id", ""),
        )

    async def get_capabilities(self) -> dict:
        """Async version of get_capabilities."""
        try:
            response = await self._client.get("/capabilities")
            return await self._handle_response(response)
        except Exception:
            return {
                "html_scanning": True,
                "policy_engine": True,
                "audit_logging": True,
            }

    async def get_audit_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        domain: str | None = None,
    ) -> AuditLogsResult:
        """Async version of get_audit_logs."""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if domain:
            params["domain"] = domain
        
        response = await self._client.get("/audit/logs", params=params)
        data = await self._handle_response(response)
        
        logs = [
            AuditLogEntry(
                request_id=log["request_id"],
                timestamp=log["timestamp"],
                url=log["url"],
                status=log["status"],
                risk_score=log["risk_score"],
                reasons=log["reasons"],
                policy_violations=log["policy_violations"],
            )
            for log in data.get("logs", [])
        ]
        
        return AuditLogsResult(
            logs=logs,
            total=data.get("total", 0),
            limit=data.get("limit", limit),
            offset=data.get("offset", offset),
        )

    async def get_audit_stats(self, hours: int = 24) -> AuditStatsResult:
        """Async version of get_audit_stats."""
        response = await self._client.get("/audit/stats", params={"hours": hours})
        data = await self._handle_response(response)
        
        return AuditStatsResult(
            total_requests=data.get("total_requests", 0),
            blocked_requests=data.get("blocked_requests", 0),
            allowed_requests=data.get("allowed_requests", 0),
            block_rate=data.get("block_rate", 0.0),
            avg_risk_score=data.get("avg_risk_score", 0.0),
            top_blocked_domains=data.get("top_blocked_domains", []),
            requests_by_hour=data.get("requests_by_hour", []),
        )

    async def _scan_file(self, endpoint: str, file: Union[str, bytes, IO]) -> DocumentScanResult:
        """Helper to scan image or PDF files asynchronously."""
        files = None
        should_close = False
        if isinstance(file, str):
            files = {"file": open(file, "rb")}
            should_close = True
        elif isinstance(file, bytes):
            files = {"file": ("file", file)}
        else:
            files = {"file": file}
            
        try:
            response = await self._client.post(endpoint, files=files)
            data = await self._handle_response(response)
            
            return DocumentScanResult(
                is_safe=data.get("is_safe", False),
                risk_score=data.get("risk_score", 1.0),
                extracted_text=data.get("extracted_text", ""),
                reason=data.get("reason"),
                explanations=data.get("explanations"),
                policy_violations=data.get("policy_violations"),
                page_count=data.get("page_count", 1),
                request_id=data.get("request_id", ""),
            )
        finally:
            if should_close and files:
                files["file"].close()

    async def scan_image(self, file: Union[str, bytes, IO]) -> DocumentScanResult:
        """Async version of scan_image."""
        return await self._scan_file("/scan-image", file)

    async def scan_pdf(self, file: Union[str, bytes, IO]) -> DocumentScanResult:
        """Async version of scan_pdf."""
        return await self._scan_file("/scan-pdf", file)

    async def list_attack_scenarios(self) -> list[RedTeamScenario]:
        """Async version of list_attack_scenarios."""
        response = await self._client.get("/test/scenarios")
        data = await self._handle_response(response)
        
        return [
            RedTeamScenario(
                id=s["id"],
                name=s["name"],
                description=s["description"],
                category=s["category"],
            )
            for s in data.get("scenarios", [])
        ]

    async def run_red_team_test(self, scenario_ids: list[str] | None = None) -> RedTeamSummary:
        """Async version of run_red_team_test."""
        payload = {"scenario_ids": scenario_ids} if scenario_ids else {}
        response = await self._client.post("/test/red-team", json=payload)
        data = await self._handle_response(response)
        
        results = [
            RedTeamTestResult(
                scenario_id=r["scenario_id"],
                passed=r.get("detected", False),
                risk_score=r["risk_score"],
                reason=r.get("explanations", [None])[0],
            )
            for r in data.get("results", [])
        ]
        
        stats = data.get("statistics", {})
        return RedTeamSummary(
            total_tests=stats.get("total", 0),
            passed_count=stats.get("detected", 0),
            failed_count=stats.get("missed", 0),
            detection_rate=stats.get("detection_rate", 0.0),
            results=results,
        )

    async def start_agent_session(
        self,
        max_steps: int = 100,
        max_retries: int = 5,
        timeout_seconds: float = 300,
    ) -> str:
        """Async version of start_agent_session."""
        response = await self._client.post(
            "/agent/session/start",
            json={
                "max_steps": max_steps,
                "max_retries": max_retries,
                "timeout_seconds": timeout_seconds,
            },
        )
        data = await self._handle_response(response)
        return data["session_id"]

    async def record_agent_step(
        self,
        session_id: str,
        action_type: str,
        action_name: str,
        success: bool = True,
    ) -> AgentSessionResult:
        """Async version of record_agent_step."""
        params = {
            "action_type": action_type,
            "action_name": action_name,
            "success": str(success).lower(),
        }
        response = await self._client.post(
            f"/agent/session/{session_id}/step",
            params=params,
        )
        data = await self._handle_response(response)
        summary = data.get("session_summary", {})
        return AgentSessionResult(
            session_id=summary["session_id"],
            total_steps=summary["total_steps"],
            is_stopped=summary["is_stopped"],
            duration_seconds=summary["duration_seconds"],
            stop_reason=summary.get("stop_reason"),
            read_actions=summary.get("read_actions", 0),
            write_actions=summary.get("write_actions", 0),
            execute_actions=summary.get("execute_actions", 0),
            failed_steps=summary.get("failed_steps", 0),
        )

    async def get_agent_session(self, session_id: str) -> AgentSessionResult:
        """Async version of get_agent_session."""
        response = await self._client.get(f"/agent/session/{session_id}")
        summary = await self._handle_response(response)
        return AgentSessionResult(
            session_id=summary["session_id"],
            total_steps=summary["total_steps"],
            is_stopped=summary["is_stopped"],
            duration_seconds=summary["duration_seconds"],
            stop_reason=summary.get("stop_reason"),
            read_actions=summary.get("read_actions", 0),
            write_actions=summary.get("write_actions", 0),
            execute_actions=summary.get("execute_actions", 0),
            failed_steps=summary.get("failed_steps", 0),
        )

    async def end_agent_session(self, session_id: str):
        """Async version of end_agent_session."""
        response = await self._client.delete(f"/agent/session/{session_id}")
        await self._handle_response(response)
