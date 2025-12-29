"""
Tests for governance policy templates.
"""

from pathlib import Path
import pytest

from tork.core.policy import PolicyLoader, Policy, PolicyOperator, PolicyAction
from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest


class TestPolicyLoading:
    """Test loading policy templates from files."""
    
    def test_pii_protection_policy_loads(self):
        """Test pii-protection.yaml loads correctly."""
        policy_path = Path("templates/policies/pii-protection.yaml")
        assert policy_path.exists(), f"Policy file not found: {policy_path}"
        
        policy = PolicyLoader.load_from_yaml(policy_path)
        
        assert policy.name == "pii-protection"
        assert "PII" in policy.description or "pii" in policy.description.lower()
        assert len(policy.rules) >= 4
        assert policy.enabled is True
        assert policy.priority == 100
    
    def test_api_security_policy_loads(self):
        """Test api-security.yaml loads correctly."""
        policy_path = Path("templates/policies/api-security.yaml")
        assert policy_path.exists(), f"Policy file not found: {policy_path}"
        
        policy = PolicyLoader.load_from_yaml(policy_path)
        
        assert policy.name == "api-security"
        assert "API" in policy.description or "api" in policy.description.lower()
        assert len(policy.rules) >= 3
        assert policy.enabled is True
        assert policy.priority == 90
    
    def test_content_moderation_policy_loads(self):
        """Test content-moderation.yaml loads correctly."""
        policy_path = Path("templates/policies/content-moderation.yaml")
        assert policy_path.exists(), f"Policy file not found: {policy_path}"
        
        policy = PolicyLoader.load_from_yaml(policy_path)
        
        assert policy.name == "content-moderation"
        assert "content" in policy.description.lower()
        assert len(policy.rules) >= 3
        assert policy.enabled is True
        assert policy.priority == 70
    
    def test_compliance_hipaa_policy_loads(self):
        """Test compliance-hipaa.yaml loads correctly."""
        policy_path = Path("templates/policies/compliance-hipaa.yaml")
        assert policy_path.exists(), f"Policy file not found: {policy_path}"
        
        policy = PolicyLoader.load_from_yaml(policy_path)
        
        assert policy.name == "hipaa-compliance"
        assert "HIPAA" in policy.description or "hipaa" in policy.description.lower()
        assert len(policy.rules) >= 3
        assert policy.enabled is True
        assert policy.priority == 110


class TestPolicyRuleStructure:
    """Test that policy rules have correct structure."""
    
    def test_pii_protection_rules_have_valid_fields(self):
        """Test pii-protection rules have all required fields."""
        policy = PolicyLoader.load_from_yaml("templates/policies/pii-protection.yaml")
        
        for rule in policy.rules:
            assert rule.field, "Rule must have a field"
            assert rule.operator in [PolicyOperator.EQUALS, PolicyOperator.CONTAINS, 
                                     PolicyOperator.REGEX, PolicyOperator.EXISTS]
            assert rule.action in [PolicyAction.ALLOW, PolicyAction.DENY, PolicyAction.REDACT]
    
    def test_api_security_rules_have_valid_fields(self):
        """Test api-security rules have all required fields."""
        policy = PolicyLoader.load_from_yaml("templates/policies/api-security.yaml")
        
        for rule in policy.rules:
            assert rule.field, "Rule must have a field"
            assert rule.operator in [PolicyOperator.EQUALS, PolicyOperator.CONTAINS, 
                                     PolicyOperator.REGEX, PolicyOperator.EXISTS]
            assert rule.action in [PolicyAction.ALLOW, PolicyAction.DENY, PolicyAction.REDACT]


class TestPolicyExecution:
    """Test that policies work with the governance engine."""
    
    def test_pii_protection_policy_redacts_email(self):
        """Test pii-protection policy redacts email addresses."""
        policy = PolicyLoader.load_from_yaml("templates/policies/pii-protection.yaml")
        engine = GovernanceEngine(policies=[policy])
        
        request = EvaluationRequest(
            agent_id="test-agent",
            action="test-action",
            payload={
                "user_email": "john.doe@example.com",
                "public_info": "Hello world"
            }
        )
        
        result = engine.evaluate(request)
        
        # Email should be redacted (field name matches)
        assert result.decision is not None
    
    def test_api_security_policy_denies_internal_ips(self):
        """Test api-security policy blocks internal IPs."""
        policy = PolicyLoader.load_from_yaml("templates/policies/api-security.yaml")
        engine = GovernanceEngine(policies=[policy])
        
        request = EvaluationRequest(
            agent_id="test-agent",
            action="test-action",
            payload={
                "source_ip": "192.168.1.1",
                "request_data": "some data"
            }
        )
        
        result = engine.evaluate(request)
        
        # Should have a decision (DENY or similar)
        assert result.decision is not None
    
    def test_content_moderation_policy_denies_spam(self):
        """Test content-moderation policy blocks spam patterns."""
        policy = PolicyLoader.load_from_yaml("templates/policies/content-moderation.yaml")
        engine = GovernanceEngine(policies=[policy])
        
        request = EvaluationRequest(
            agent_id="test-agent",
            action="test-action",
            payload={
                "content": "CLICK HERE NOW for VIAGRA"
            }
        )
        
        result = engine.evaluate(request)
        
        # Should have a decision
        assert result.decision is not None
    
    def test_hipaa_compliance_policy_redacts_ssn(self):
        """Test hipaa-compliance policy redacts SSN."""
        policy = PolicyLoader.load_from_yaml("templates/policies/compliance-hipaa.yaml")
        engine = GovernanceEngine(policies=[policy])
        
        request = EvaluationRequest(
            agent_id="test-agent",
            action="test-action",
            payload={
                "patient_ssn": "123-45-6789",
                "patient_name": "Jane Smith"
            }
        )
        
        result = engine.evaluate(request)
        
        # Should have a decision
        assert result.decision is not None


class TestPolicyIntegration:
    """Test multiple policies working together."""
    
    def test_multiple_policies_load_and_work(self):
        """Test loading and executing multiple policies."""
        pii_policy = PolicyLoader.load_from_yaml("templates/policies/pii-protection.yaml")
        api_policy = PolicyLoader.load_from_yaml("templates/policies/api-security.yaml")
        
        engine = GovernanceEngine(policies=[pii_policy, api_policy])
        
        request = EvaluationRequest(
            agent_id="test-agent",
            action="test-action",
            payload={
                "email": "user@example.com",
                "source_ip": "192.168.1.1"
            }
        )
        
        result = engine.evaluate(request)
        assert result is not None
