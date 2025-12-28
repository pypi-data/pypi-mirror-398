"""
Comprehensive pytest test suite for SafeBrowse SDK v0.2.0

Run with: pytest tests/ -v
Run with coverage: pytest tests/ --cov=safebrowse --cov-report=html

Tests cover all mandatory requirements:
- fail_closed on timeout
- blocked content raises BlockedError
- sanitize() removes unsafe chunks
- scan_batch() handles mixed input
- error codes are correct
- hooks are called correctly
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from safebrowse import (
    SafeBrowseClient,
    AsyncSafeBrowseClient,
    SafeBrowseConfig,
    ScanResult,
    AskResult,
    SanitizeResult,
    BatchScanResult,
    SafeBrowseError,
    BlockedError,
    AuthenticationError,
    ConnectionError,
    ErrorCode,
)


# ==================== FIXTURES ====================

@pytest.fixture
def config():
    """Standard test configuration."""
    return SafeBrowseConfig(
        api_key="test-api-key",
        base_url="http://localhost:8000",
        timeout=30.0,
    )


@pytest.fixture
def client(config):
    """Standard test client."""
    client = SafeBrowseClient(config=config)
    yield client
    client.close()


@pytest.fixture
def mock_hooks():
    """Mock hooks for testing callbacks."""
    return {
        "on_blocked": Mock(),
        "on_allowed": Mock(),
    }


# ==================== CONFIGURATION TESTS ====================

class TestSafeBrowseConfig:
    """Test SafeBrowseConfig class."""
    
    def test_config_requires_api_key(self):
        """Config must have a non-empty API key."""
        with pytest.raises(ValueError, match="API key is required"):
            SafeBrowseConfig(api_key="")
    
    def test_config_fail_closed_enforced(self):
        """fail_closed=False must raise ValueError."""
        with pytest.raises(ValueError, match="fail_closed=False is not allowed"):
            SafeBrowseConfig(api_key="test", fail_closed=False)
    
    def test_config_fail_closed_always_true(self):
        """fail_closed is always True."""
        config = SafeBrowseConfig(api_key="test")
        assert config.fail_closed is True
    
    def test_config_default_values(self):
        """Config has sensible defaults."""
        config = SafeBrowseConfig(api_key="test")
        assert config.base_url == "http://localhost:8000"
        assert config.timeout == 30.0
        assert config.on_blocked is None
        assert config.on_allowed is None
    
    def test_config_custom_values(self):
        """Config accepts custom values."""
        config = SafeBrowseConfig(
            api_key="my-key",
            base_url="https://api.example.com",
            timeout=60.0,
        )
        assert config.api_key == "my-key"
        assert config.base_url == "https://api.example.com"
        assert config.timeout == 60.0
    
    def test_config_normalizes_base_url(self):
        """Config strips trailing slashes from base_url."""
        config = SafeBrowseConfig(api_key="test", base_url="http://api.com/")
        assert config.base_url == "http://api.com"
    
    def test_config_with_hooks(self):
        """with_hooks() creates new config with hooks."""
        config = SafeBrowseConfig(api_key="test")
        new_hook = Mock()
        new_config = config.with_hooks(on_blocked=new_hook)
        
        assert new_config.api_key == config.api_key
        assert new_config.on_blocked == new_hook
        assert config.on_blocked is None  # Original unchanged
    
    def test_config_from_env(self, monkeypatch):
        """from_env() loads from environment variables."""
        monkeypatch.setenv("SAFEBROWSE_API_KEY", "env-key")
        monkeypatch.setenv("SAFEBROWSE_BASE_URL", "http://env.example.com")
        monkeypatch.setenv("SAFEBROWSE_TIMEOUT", "45.0")
        
        config = SafeBrowseConfig.from_env()
        
        assert config.api_key == "env-key"
        assert config.base_url == "http://env.example.com"
        assert config.timeout == 45.0
    
    def test_config_from_env_missing_key(self, monkeypatch):
        """from_env() raises if API key is missing."""
        monkeypatch.delenv("SAFEBROWSE_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="API key is required"):
            SafeBrowseConfig.from_env()


# ==================== CLIENT INITIALIZATION TESTS ====================

class TestClientInitialization:
    """Test client initialization methods."""
    
    def test_client_with_api_key(self):
        """Client can be created with api_key."""
        client = SafeBrowseClient(api_key="test-key")
        assert client.api_key == "test-key"
        client.close()
    
    def test_client_with_config(self, config):
        """Client can be created with config object."""
        client = SafeBrowseClient(config=config)
        assert client.api_key == config.api_key
        assert client.base_url == config.base_url
        client.close()
    
    def test_client_requires_api_key(self):
        """Client requires api_key or config."""
        with pytest.raises(ValueError, match="api_key is required"):
            SafeBrowseClient()
    
    def test_client_context_manager(self):
        """Client works as context manager."""
        with SafeBrowseClient(api_key="test") as client:
            assert client.api_key == "test"
    
    def test_client_from_env(self, monkeypatch):
        """from_env() creates client from environment."""
        monkeypatch.setenv("SAFEBROWSE_API_KEY", "env-key")
        
        client = SafeBrowseClient.from_env()
        assert client.api_key == "env-key"
        client.close()


# ==================== ERROR CODE TESTS ====================

class TestErrorCodes:
    """Test machine-readable error codes."""
    
    def test_error_code_enum_values(self):
        """ErrorCode enum has expected values."""
        assert ErrorCode.INJECTION_DETECTED.value == "INJECTION_DETECTED"
        assert ErrorCode.POLICY_LOGIN_FORM.value == "POLICY_LOGIN_FORM"
        assert ErrorCode.AUTH_INVALID_KEY.value == "AUTH_INVALID_KEY"
        assert ErrorCode.CONN_REFUSED.value == "CONN_REFUSED"
    
    def test_blocked_error_has_code(self):
        """BlockedError includes error code."""
        error = BlockedError(
            message="Test blocked",
            risk_score=0.9,
            code=ErrorCode.INJECTION_DETECTED,
        )
        assert error.code == ErrorCode.INJECTION_DETECTED
    
    def test_blocked_error_to_dict(self):
        """BlockedError serializes to dict."""
        error = BlockedError(
            message="Content blocked",
            risk_score=0.85,
            code=ErrorCode.POLICY_LOGIN_FORM,
            explanations=["Found login form"],
            policy_violations=["no_login_forms"],
            request_id="req-123",
        )
        d = error.to_dict()
        
        assert d["error"] == "BlockedError"
        assert d["message"] == "Content blocked"
        assert d["code"] == "POLICY_LOGIN_FORM"
        assert d["risk_score"] == 0.85
        assert d["request_id"] == "req-123"
        assert "Found login form" in d["explanations"]
    
    def test_authentication_error_has_code(self):
        """AuthenticationError has correct code."""
        error = AuthenticationError()
        assert error.code == ErrorCode.AUTH_INVALID_KEY
    
    def test_connection_error_has_code(self):
        """ConnectionError has correct code."""
        error = ConnectionError()
        assert error.code == ErrorCode.CONN_REFUSED


# ==================== HOOK TESTS ====================

class TestLoggingHooks:
    """Test on_blocked and on_allowed callbacks."""
    
    def test_on_allowed_called_for_safe_content(self, mock_hooks):
        """on_allowed is called when content is safe."""
        client = SafeBrowseClient(
            api_key="test-key",
            on_allowed=mock_hooks["on_allowed"],
        )
        
        # Mock successful response
        with patch.object(client._client, 'post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"is_safe": True, "risk_score": 0.0, "request_id": "123"}
            )
            
            client.scan_html("<html>safe</html>", "http://example.com")
            
            mock_hooks["on_allowed"].assert_called_once()
            call_args = mock_hooks["on_allowed"].call_args[0][0]
            assert isinstance(call_args, ScanResult)
            assert call_args.is_safe is True
        
        client.close()
    
    def test_on_blocked_called_for_unsafe_content(self, mock_hooks):
        """on_blocked is called when content is unsafe."""
        client = SafeBrowseClient(
            api_key="test-key",
            on_blocked=mock_hooks["on_blocked"],
        )
        
        with patch.object(client._client, 'post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"is_safe": False, "risk_score": 0.9, "request_id": "123"}
            )
            
            client.scan_html("<html>dangerous</html>", "http://example.com")
            
            mock_hooks["on_blocked"].assert_called_once()
            call_args = mock_hooks["on_blocked"].call_args[0][0]
            assert call_args.is_safe is False
        
        client.close()
    
    def test_hooks_from_config(self, mock_hooks):
        """Hooks can be set via config object."""
        config = SafeBrowseConfig(
            api_key="test",
            on_blocked=mock_hooks["on_blocked"],
            on_allowed=mock_hooks["on_allowed"],
        )
        client = SafeBrowseClient(config=config)
        
        assert client._on_blocked == mock_hooks["on_blocked"]
        assert client._on_allowed == mock_hooks["on_allowed"]
        client.close()


# ==================== FAIL CLOSED TESTS ====================

class TestFailClosed:
    """Test fail-closed behavior."""
    
    def test_connection_error_raises_exception(self):
        """Connection failures raise ConnectionError."""
        client = SafeBrowseClient(api_key="test", base_url="http://localhost:99999")
        
        with pytest.raises(ConnectionError):
            client.scan_html("<html>test</html>", "http://example.com")
        
        client.close()
    
    def test_is_safe_returns_false_on_error(self):
        """is_safe() returns False on any error (fail closed)."""
        client = SafeBrowseClient(api_key="test", base_url="http://localhost:99999")
        
        result = client.is_safe("<html>test</html>", "http://example.com")
        assert result is False
        
        client.close()
    
    def test_batch_scan_fails_closed_per_item(self):
        """scan_batch() treats errors as blocked (fail closed)."""
        client = SafeBrowseClient(api_key="test", base_url="http://localhost:99999")
        
        result = client.scan_batch([
            {"html": "<html>test</html>", "url": "http://example.com"}
        ])
        
        assert result.blocked_count == 1
        assert result.safe_count == 0
        assert result.results[0].is_safe is False
        
        client.close()
    
    def test_auth_error_raises_exception(self):
        """Invalid API key raises AuthenticationError."""
        client = SafeBrowseClient(api_key="test")
        
        with patch.object(client._client, 'post') as mock_post:
            mock_post.return_value = Mock(status_code=401)
            
            with pytest.raises(AuthenticationError):
                client.scan_html("<html>test</html>", "http://example.com")
        
        client.close()


# ==================== SCAN TESTS ====================

class TestScanHtml:
    """Test scan_html() method."""
    
    def test_scan_html_returns_scan_result(self, client):
        """scan_html() returns ScanResult object."""
        with patch.object(client._client, 'post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "is_safe": True,
                    "risk_score": 0.1,
                    "reason": None,
                    "explanations": [],
                    "policy_violations": [],
                    "request_id": "req-456",
                }
            )
            
            result = client.scan_html("<html>test</html>", "http://example.com")
            
            assert isinstance(result, ScanResult)
            assert result.is_safe is True
            assert result.risk_score == 0.1
            assert result.request_id == "req-456"
    
    def test_scan_html_with_unsafe_content(self, client):
        """scan_html() correctly handles unsafe content."""
        with patch.object(client._client, 'post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "is_safe": False,
                    "risk_score": 0.95,
                    "reason": "Injection detected",
                    "explanations": ["Found 'ignore instructions' pattern"],
                    "policy_violations": [],
                    "request_id": "req-789",
                }
            )
            
            result = client.scan_html("<html>ignore instructions</html>", "http://example.com")
            
            assert result.is_safe is False
            assert result.risk_score == 0.95
            assert "Injection detected" in result.reason


# ==================== SAFE ASK TESTS ====================

class TestSafeAsk:
    """Test safe_ask() method."""
    
    def test_safe_ask_returns_answer(self, client):
        """safe_ask() returns answer for safe content."""
        with patch.object(client._client, 'post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "status": "ok",
                    "answer": "This page is about Python.",
                    "risk_score": 0.0,
                    "reason": None,
                    "explanations": [],
                    "request_id": "ask-123",
                }
            )
            
            result = client.safe_ask("<html>Python</html>", "http://example.com", "What is this?")
            
            assert isinstance(result, AskResult)
            assert result.status == "ok"
            assert result.answer == "This page is about Python."
    
    def test_safe_ask_raises_blocked_error(self, client):
        """safe_ask() raises BlockedError for blocked content."""
        with patch.object(client._client, 'post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "status": "blocked",
                    "answer": None,
                    "risk_score": 0.9,
                    "reason": "Content blocked",
                    "explanations": ["Injection detected"],
                    "policy_violations": [],
                    "request_id": "ask-456",
                }
            )
            
            with pytest.raises(BlockedError) as exc_info:
                client.safe_ask("<html>bad</html>", "http://example.com", "query")
            
            assert exc_info.value.risk_score == 0.9
            assert exc_info.value.request_id == "ask-456"


# ==================== GUARD TESTS ====================

class TestGuard:
    """Test guard() context manager."""
    
    def test_guard_yields_decision(self, client):
        """guard() yields ScanResult with decision metadata."""
        with patch.object(client._client, 'post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "is_safe": True,
                    "risk_score": 0.05,
                    "reason": None,
                    "explanations": [],
                    "policy_violations": [],
                    "request_id": "guard-123",
                }
            )
            
            with client.guard("<html>safe</html>", "http://example.com") as decision:
                assert isinstance(decision, ScanResult)
                assert decision.is_safe is True
                assert decision.risk_score == 0.05
                assert decision.request_id == "guard-123"
    
    def test_guard_raises_blocked_error(self, client):
        """guard() raises BlockedError for unsafe content."""
        with patch.object(client._client, 'post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "is_safe": False,
                    "risk_score": 0.8,
                    "reason": "Blocked by policy",
                    "explanations": [],
                    "policy_violations": ["login_form"],
                    "request_id": "guard-456",
                }
            )
            
            with pytest.raises(BlockedError) as exc_info:
                with client.guard("<html>login</html>", "http://example.com"):
                    pass  # Should not reach here
            
            assert exc_info.value.risk_score == 0.8
            assert exc_info.value.request_id == "guard-456"


# ==================== SANITIZE TESTS ====================

class TestSanitize:
    """Test sanitize() for RAG pipelines."""
    
    def test_sanitize_returns_result(self, client):
        """sanitize() returns SanitizeResult."""
        with patch.object(client._client, 'post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "total_count": 3,
                    "safe_count": 2,
                    "blocked_count": 1,
                    "results": [
                        {"is_safe": True, "risk_score": 0.0},
                        {"is_safe": False, "risk_score": 0.9},
                        {"is_safe": True, "risk_score": 0.1},
                    ],
                    "request_id": "san-123",
                }
            )
            
            result = client.sanitize(["safe1", "unsafe", "safe2"])
            
            assert isinstance(result, SanitizeResult)
            assert result.total_count == 3
            assert result.safe_count == 2
            assert result.blocked_count == 1
    
    def test_sanitize_removes_unsafe_chunks(self, client):
        """sanitize() returns only safe chunks."""
        with patch.object(client._client, 'post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "total_count": 3,
                    "safe_count": 2,
                    "blocked_count": 1,
                    "results": [
                        {"is_safe": True, "risk_score": 0.0},
                        {"is_safe": False, "risk_score": 0.9},  # This one removed
                        {"is_safe": True, "risk_score": 0.1},
                    ],
                    "request_id": "san-456",
                }
            )
            
            documents = ["chunk1", "ignore instructions", "chunk3"]
            result = client.sanitize(documents)
            
            assert len(result.safe_chunks) == 2
            assert "chunk1" in result.safe_chunks
            assert "chunk3" in result.safe_chunks
            assert "ignore instructions" not in result.safe_chunks


# ==================== BATCH SCAN TESTS ====================

class TestScanBatch:
    """Test scan_batch() for bulk operations."""
    
    def test_scan_batch_returns_result(self, client):
        """scan_batch() returns BatchScanResult."""
        with patch.object(client._client, 'post') as mock_post:
            def side_effect(*args, **kwargs):
                return Mock(
                    status_code=200,
                    json=lambda: {
                        "is_safe": True,
                        "risk_score": 0.0,
                        "request_id": "batch-item",
                    }
                )
            mock_post.side_effect = side_effect
            
            result = client.scan_batch([
                {"html": "<html>a</html>", "url": "http://a.com"},
                {"html": "<html>b</html>", "url": "http://b.com"},
            ])
            
            assert isinstance(result, BatchScanResult)
            assert result.total == 2
    
    def test_scan_batch_handles_mixed_input(self, client):
        """scan_batch() correctly categorizes mixed safe/unsafe."""
        call_count = [0]
        
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return Mock(status_code=200, json=lambda: {"is_safe": True, "risk_score": 0.0, "request_id": "1"})
            else:
                return Mock(status_code=200, json=lambda: {"is_safe": False, "risk_score": 0.9, "request_id": "2"})
        
        with patch.object(client._client, 'post', side_effect=side_effect):
            result = client.scan_batch([
                {"html": "<html>safe</html>", "url": "http://safe.com"},
                {"html": "<html>unsafe</html>", "url": "http://unsafe.com"},
            ])
            
            assert result.safe_count == 1
            assert result.blocked_count == 1
            assert result.results[0].is_safe is True
            assert result.results[1].is_safe is False


# ==================== CAPABILITIES TESTS ====================

class TestCapabilities:
    """Test get_capabilities() method."""
    
    def test_get_capabilities_returns_dict(self, client):
        """get_capabilities() returns feature flags."""
        with patch.object(client._client, 'get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "html_scanning": True,
                    "policy_engine": True,
                    "audit_logging": True,
                    "pdf_scanning": False,
                }
            )
            
            caps = client.get_capabilities()
            
            assert caps["html_scanning"] is True
            assert caps["policy_engine"] is True
    
    def test_get_capabilities_fallback(self, client):
        """get_capabilities() returns defaults on error."""
        with patch.object(client._client, 'get', side_effect=Exception("Network error")):
            caps = client.get_capabilities()
            
            assert caps["html_scanning"] is True  # Default


# ==================== CORRELATION ID TESTS ====================

class TestCorrelationId:
    """Test attach_request_id() for audit correlation."""
    
    def test_attach_request_id(self, client):
        """attach_request_id() sets correlation header."""
        client.attach_request_id("my-workflow-step-42")
        
        assert client._client.headers["X-Correlation-ID"] == "my-workflow-step-42"


# ==================== INTEGRATION TESTS (LIVE SERVER) ====================

@pytest.mark.integration
class TestIntegration:
    """Integration tests against live server.
    
    Run with: pytest tests/ -v -m integration
    Requires backend to be running on localhost:8000
    """
    
    def test_live_scan_html(self):
        """Test scan_html against live server."""
        client = SafeBrowseClient(api_key="test-key")
        result = client.scan_html("<html><body>Hello</body></html>", "http://example.com")
        
        assert isinstance(result, ScanResult)
        assert result.is_safe is True
        client.close()
    
    def test_live_sanitize(self):
        """Test sanitize against live server."""
        client = SafeBrowseClient(api_key="test-key")
        result = client.sanitize(["safe chunk", "another safe chunk"])
        
        assert isinstance(result, SanitizeResult)
        assert result.safe_count >= 0
        client.close()


# ==================== RUN ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
