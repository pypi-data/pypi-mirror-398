"""
Tests for HTTP proxy adapter.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pydantic import ValidationError

from tork.core.engine import GovernanceEngine
from tork.core.policy import Policy, PolicyRule, PolicyAction, PolicyOperator
from tork.core.models import PolicyDecision
from tork.core.redactor import PIIRedactor
from tork.compliance.receipts import ReceiptGenerator
from tork.adapters.http import (
    ProxyConfig,
    ProxyResponse,
    GovernedProxy,
    create_proxy_app,
)


class TestProxyConfig:
    """Tests for ProxyConfig model."""
    
    def test_basic_config(self):
        """Test creating a basic proxy config."""
        config = ProxyConfig(target_base_url="https://api.example.com")
        
        assert config.target_base_url == "https://api.example.com"
        assert config.timeout == 30.0
        assert config.headers == {}
        assert config.verify_ssl is True
    
    def test_full_config(self):
        """Test creating a fully configured proxy."""
        config = ProxyConfig(
            target_base_url="https://api.example.com",
            timeout=60.0,
            headers={"Authorization": "Bearer token"},
            verify_ssl=False,
        )
        
        assert config.timeout == 60.0
        assert config.headers["Authorization"] == "Bearer token"
        assert config.verify_ssl is False
    
    def test_config_requires_target_url(self):
        """Test that target_base_url is required."""
        with pytest.raises(ValidationError):
            ProxyConfig()


class TestProxyResponse:
    """Tests for ProxyResponse model."""
    
    def test_basic_response(self):
        """Test creating a basic response."""
        response = ProxyResponse(
            status_code=200,
            body={"data": "test"},
            headers={"Content-Type": "application/json"},
            request_decision=PolicyDecision.ALLOW,
            response_decision=PolicyDecision.ALLOW,
        )
        
        assert response.status_code == 200
        assert response.body == {"data": "test"}
        assert response.receipts == []
    
    def test_response_with_receipts(self):
        """Test response with receipt IDs."""
        response = ProxyResponse(
            status_code=200,
            body=None,
            headers={},
            request_decision=PolicyDecision.ALLOW,
            response_decision=PolicyDecision.REDACT,
            receipts=["receipt-1", "receipt-2"],
        )
        
        assert len(response.receipts) == 2


class TestGovernedProxy:
    """Tests for GovernedProxy class."""
    
    def test_initialization(self):
        """Test proxy initialization."""
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine()
        
        proxy = GovernedProxy(config=config, engine=engine)
        
        assert proxy.config == config
        assert proxy.engine == engine
        assert proxy.identity_manager is None
        assert proxy.receipt_generator is None
    
    def test_initialization_with_all_options(self):
        """Test initialization with all optional components."""
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine()
        identity_manager = Mock()
        receipt_generator = ReceiptGenerator(signing_key="test-key")
        
        proxy = GovernedProxy(
            config=config,
            engine=engine,
            identity_manager=identity_manager,
            receipt_generator=receipt_generator,
        )
        
        assert proxy.identity_manager == identity_manager
        assert proxy.receipt_generator == receipt_generator
    
    def test_evaluate_request(self):
        """Test request evaluation."""
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine()
        proxy = GovernedProxy(config=config, engine=engine)
        
        result = proxy._evaluate_request(
            method="POST",
            path="/api/data",
            body={"key": "value"},
            agent_id="test-agent",
        )
        
        assert result.decision == PolicyDecision.ALLOW
    
    def test_evaluate_request_deny(self):
        """Test request evaluation with DENY policy."""
        deny_rule = PolicyRule(
            field="path",
            operator=PolicyOperator.CONTAINS,
            value="admin",
            action=PolicyAction.DENY,
        )
        policy = Policy(name="block-admin", rules=[deny_rule])
        
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine(policies=[policy])
        proxy = GovernedProxy(config=config, engine=engine)
        
        result = proxy._evaluate_request(
            method="GET",
            path="/admin/users",
            body=None,
            agent_id="test-agent",
        )
        
        assert result.decision == PolicyDecision.DENY
    
    def test_evaluate_response(self):
        """Test response evaluation."""
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine()
        proxy = GovernedProxy(config=config, engine=engine)
        
        result = proxy._evaluate_response(
            response_body={"data": "test"},
            agent_id="test-agent",
        )
        
        assert result.decision == PolicyDecision.ALLOW
    
    def test_evaluate_response_redact(self):
        """Test response evaluation with PII redaction."""
        redactor = PIIRedactor()
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine(pii_redactor=redactor, enable_auto_redaction=True)
        proxy = GovernedProxy(config=config, engine=engine)
        
        result = proxy._evaluate_response(
            response_body={"email": "user@example.com"},
            agent_id="test-agent",
        )
        
        assert result.decision == PolicyDecision.REDACT
        assert "[REDACTED_EMAIL]" in result.modified_payload.get("email", "")
    
    @pytest.mark.asyncio
    async def test_request_allow(self):
        """Test making a request that is allowed."""
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine()
        proxy = GovernedProxy(config=config, engine=engine)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.headers = {"Content-Type": "application/json"}
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            result = await proxy.request(
                method="GET",
                path="/api/data",
                agent_id="test-agent",
            )
        
        assert result.status_code == 200
        assert result.body == {"result": "success"}
        assert result.request_decision == PolicyDecision.ALLOW
    
    @pytest.mark.asyncio
    async def test_request_deny(self):
        """Test making a request that is denied."""
        deny_rule = PolicyRule(
            field="path",
            operator=PolicyOperator.CONTAINS,
            value="secret",
            action=PolicyAction.DENY,
        )
        policy = Policy(name="block-secret", rules=[deny_rule])
        
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine(policies=[policy])
        proxy = GovernedProxy(config=config, engine=engine)
        
        result = await proxy.request(
            method="GET",
            path="/api/secret",
            agent_id="test-agent",
        )
        
        assert result.status_code == 403
        assert result.request_decision == PolicyDecision.DENY
        assert "error" in result.body
    
    @pytest.mark.asyncio
    async def test_request_with_receipts(self):
        """Test that receipts are generated when configured."""
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine()
        receipt_generator = ReceiptGenerator(signing_key="test-key")
        proxy = GovernedProxy(
            config=config,
            engine=engine,
            receipt_generator=receipt_generator,
        )
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {}
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            result = await proxy.request(
                method="GET",
                path="/api/data",
            )
        
        assert len(result.receipts) == 2


class TestProxyApp:
    """Tests for create_proxy_app function."""
    
    def test_create_app(self):
        """Test creating the proxy FastAPI app."""
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine()
        
        app = create_proxy_app(config=config, engine=engine)
        
        assert app is not None
        assert app.title == "Tork Governed Proxy"
    
    def test_create_app_with_custom_title(self):
        """Test creating app with custom title."""
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine()
        
        app = create_proxy_app(
            config=config,
            engine=engine,
            title="Custom Proxy",
            description="Custom description",
        )
        
        assert app.title == "Custom Proxy"
    
    def test_app_has_routes(self):
        """Test that app has the expected routes."""
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine()
        
        app = create_proxy_app(config=config, engine=engine)
        
        route_methods = set()
        for route in app.routes:
            if hasattr(route, 'methods'):
                route_methods.update(route.methods)
        
        assert "GET" in route_methods
        assert "POST" in route_methods
        assert "PUT" in route_methods
        assert "DELETE" in route_methods
        assert "PATCH" in route_methods
    
    def test_app_with_all_options(self):
        """Test creating app with all options."""
        config = ProxyConfig(target_base_url="https://api.example.com")
        engine = GovernanceEngine()
        identity_manager = Mock()
        receipt_generator = ReceiptGenerator(signing_key="test-key")
        
        app = create_proxy_app(
            config=config,
            engine=engine,
            identity_manager=identity_manager,
            receipt_generator=receipt_generator,
        )
        
        assert app is not None
