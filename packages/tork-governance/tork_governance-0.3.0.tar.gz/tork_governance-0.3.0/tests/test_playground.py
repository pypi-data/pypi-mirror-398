"""
Tests for Playground Service and API.
"""

import pytest
from fastapi.testclient import TestClient

from tork.api.playground import PlaygroundService
from tork.api.app import app
from tork.core.engine import GovernanceEngine
from tork.core.redactor import PIIRedactor
from tork.core.policy import Policy, PolicyRule, PolicyAction, PolicyOperator
from tork.scanner.scanner import MCPScanner


class TestPlaygroundService:
    """Tests for PlaygroundService class."""
    
    def test_init_default(self):
        """Test default initialization."""
        service = PlaygroundService()
        assert service.engine is not None
        assert service.scanner is not None
        assert service._redactor is not None
    
    def test_init_with_engine(self):
        """Test initialization with custom engine."""
        engine = GovernanceEngine()
        service = PlaygroundService(engine=engine)
        assert service.engine is engine
    
    def test_init_with_scanner(self):
        """Test initialization with custom scanner."""
        scanner = MCPScanner()
        service = PlaygroundService(scanner=scanner)
        assert service.scanner is scanner
    
    def test_evaluate_payload_basic(self):
        """Test basic payload evaluation."""
        service = PlaygroundService()
        result = service.evaluate_payload({"message": "hello"})
        
        assert "decision" in result
        assert "violations" in result
        assert "modified_payload" in result
        assert "pii_found" in result
        assert "processing_time_ms" in result
        assert result["decision"] in ["ALLOW", "DENY", "REDACT"]
    
    def test_evaluate_payload_with_pii(self):
        """Test evaluation with PII in payload."""
        service = PlaygroundService()
        result = service.evaluate_payload({
            "email": "user@example.com",
            "data": "test"
        })
        
        assert result["decision"] == "REDACT"
        assert len(result["pii_found"]) > 0
        assert result["modified_payload"]["email"] == "[REDACTED_EMAIL]"
    
    def test_evaluate_payload_with_agent_id(self):
        """Test evaluation with custom agent ID."""
        service = PlaygroundService()
        result = service.evaluate_payload(
            {"data": "test"},
            agent_id="test-agent"
        )
        
        assert result["decision"] == "ALLOW"
    
    def test_redact_text_basic(self):
        """Test basic text redaction."""
        service = PlaygroundService()
        result = service.redact_text("Contact user@example.com for help")
        
        assert "original" in result
        assert "redacted" in result
        assert "matches" in result
        assert "processing_time_ms" in result
        assert "[REDACTED_EMAIL]" in result["redacted"]
    
    def test_redact_text_multiple_pii(self):
        """Test redaction with multiple PII types."""
        service = PlaygroundService()
        result = service.redact_text(
            "Email: test@example.com, Phone: 555-123-4567"
        )
        
        assert len(result["matches"]) >= 2
        assert "[REDACTED_EMAIL]" in result["redacted"]
        assert "[REDACTED_PHONE]" in result["redacted"]
    
    def test_redact_text_filter_types(self):
        """Test redaction with PII type filter."""
        service = PlaygroundService()
        result = service.redact_text(
            "Email: test@example.com, Phone: 555-123-4567",
            pii_types=["email"]
        )
        
        assert all(m["type"] == "email" for m in result["matches"])
        assert "[REDACTED_EMAIL]" in result["redacted"]
        assert "555-123-4567" in result["redacted"]
    
    def test_scan_content_basic(self):
        """Test basic content scanning."""
        service = PlaygroundService()
        result = service.scan_content('{"debug": true}')
        
        assert "findings" in result
        assert "summary" in result
        assert "processing_time_ms" in result
        assert "total" in result["summary"]
    
    def test_scan_content_with_secrets(self):
        """Test scanning content with secrets."""
        service = PlaygroundService()
        result = service.scan_content(
            '{"api_key": "sk_test_fake_abcdefghijklmnopqrstuvwxyz123456", "password": "admin123"}'
        )
        
        assert result["summary"]["total"] > 0
    
    def test_scan_content_custom_filename(self):
        """Test scanning with custom filename."""
        service = PlaygroundService()
        result = service.scan_content(
            '{"setting": "value"}',
            filename="server.yaml"
        )
        
        assert "findings" in result
    
    def test_list_policies_empty(self):
        """Test listing policies when none exist."""
        service = PlaygroundService()
        policies = service.list_policies()
        
        assert isinstance(policies, list)
    
    def test_list_policies_with_policies(self):
        """Test listing policies when policies exist."""
        engine = GovernanceEngine(pii_redactor=PIIRedactor())
        engine.add_policy(Policy(
            name="test-policy",
            rules=[PolicyRule(
                field="test",
                operator=PolicyOperator.EXISTS,
                action=PolicyAction.ALLOW,
            )]
        ))
        
        service = PlaygroundService(engine=engine)
        policies = service.list_policies()
        
        assert len(policies) == 1
        assert policies[0]["name"] == "test-policy"
        assert "enabled" in policies[0]
        assert "priority" in policies[0]
        assert "rules_count" in policies[0]


class TestPlaygroundAPI:
    """Tests for Playground API endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
    
    def test_evaluate_endpoint(self, client):
        """Test evaluate endpoint."""
        response = client.post("/playground/evaluate", json={
            "payload": {"message": "hello"}
        })
        assert response.status_code == 200
        data = response.json()
        assert "decision" in data
        assert "violations" in data
        assert "modified_payload" in data
    
    def test_evaluate_endpoint_with_pii(self, client):
        """Test evaluate endpoint with PII."""
        response = client.post("/playground/evaluate", json={
            "payload": {"email": "test@example.com"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "REDACT"
        assert len(data["pii_found"]) > 0
    
    def test_evaluate_endpoint_with_agent_id(self, client):
        """Test evaluate endpoint with agent ID."""
        response = client.post("/playground/evaluate", json={
            "payload": {"data": "test"},
            "agent_id": "custom-agent"
        })
        assert response.status_code == 200
    
    def test_redact_endpoint(self, client):
        """Test redact endpoint."""
        response = client.post("/playground/redact", json={
            "text": "Email me at user@example.com"
        })
        assert response.status_code == 200
        data = response.json()
        assert "original" in data
        assert "redacted" in data
        assert "[REDACTED_EMAIL]" in data["redacted"]
    
    def test_redact_endpoint_with_types(self, client):
        """Test redact endpoint with PII type filter."""
        response = client.post("/playground/redact", json={
            "text": "Email: a@b.com, Phone: 555-1234567",
            "pii_types": ["email"]
        })
        assert response.status_code == 200
        data = response.json()
        assert all(m["type"] == "email" for m in data["matches"])
    
    def test_scan_endpoint(self, client):
        """Test scan endpoint."""
        response = client.post("/playground/scan", json={
            "content": '{"debug": true}'
        })
        assert response.status_code == 200
        data = response.json()
        assert "findings" in data
        assert "summary" in data
    
    def test_scan_endpoint_with_filename(self, client):
        """Test scan endpoint with custom filename."""
        response = client.post("/playground/scan", json={
            "content": '{"setting": "value"}',
            "filename": "config.yaml"
        })
        assert response.status_code == 200
    
    def test_policies_endpoint(self, client):
        """Test policies endpoint."""
        response = client.get("/playground/policies")
        assert response.status_code == 200
        data = response.json()
        assert "policies" in data
        assert isinstance(data["policies"], list)
    
    def test_root_serves_html(self, client):
        """Test root endpoint serves HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
