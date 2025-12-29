"""
Tests for PIIRedactor integration with GovernanceEngine.
"""

import pytest
from tork.core import (
    GovernanceEngine,
    PIIRedactor,
    PIIType,
    Policy,
    PolicyRule,
    PolicyAction,
    PolicyOperator,
    EvaluationRequest,
    PolicyDecision,
)


class TestEngineRedactorIntegration:
    """Tests for GovernanceEngine with PIIRedactor."""
    
    def test_engine_initialization_with_redactor(self):
        """Test engine initialization with PIIRedactor."""
        redactor = PIIRedactor()
        engine = GovernanceEngine(pii_redactor=redactor, enable_auto_redaction=True)
        
        assert engine.pii_redactor is redactor
        assert engine.enable_auto_redaction is True
    
    def test_engine_auto_redaction_disabled(self):
        """Test engine with auto-redaction disabled."""
        redactor = PIIRedactor()
        engine = GovernanceEngine(pii_redactor=redactor, enable_auto_redaction=False)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="access",
            payload={"email": "user@example.com", "name": "John"},
        )
        
        result = engine.evaluate(request)
        
        # Should allow without redaction
        assert result.decision == PolicyDecision.ALLOW
        assert result.modified_payload is None
    
    def test_auto_redaction_pii_detection(self):
        """Test auto-redaction with PII detection."""
        redactor = PIIRedactor()
        engine = GovernanceEngine(pii_redactor=redactor, enable_auto_redaction=True)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="access",
            payload={"email": "user@example.com", "name": "John", "ssn": "123-45-6789"},
        )
        
        result = engine.evaluate(request)
        
        # Should detect PII and redact
        assert result.decision == PolicyDecision.REDACT
        assert len(result.pii_matches) == 2  # email + ssn
        assert result.modified_payload is not None
        assert "[REDACTED_EMAIL]" in result.modified_payload["email"]
        assert "[REDACTED_SSN]" in result.modified_payload["ssn"]
        assert result.modified_payload["name"] == "John"
    
    def test_pii_matches_in_result(self):
        """Test that PII matches are included in result."""
        redactor = PIIRedactor()
        engine = GovernanceEngine(pii_redactor=redactor, enable_auto_redaction=True)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="access",
            payload={"email": "alice@example.com", "phone": "555-123-4567"},
        )
        
        result = engine.evaluate(request)
        
        assert len(result.pii_matches) == 2
        assert any(m.pii_type == PIIType.EMAIL for m in result.pii_matches)
        assert any(m.pii_type == PIIType.PHONE for m in result.pii_matches)
    
    def test_explicit_redact_rule_with_pii_redactor(self):
        """Test explicit REDACT rule combined with PII redactor."""
        redactor = PIIRedactor()
        engine = GovernanceEngine(pii_redactor=redactor, enable_auto_redaction=True)
        
        # Add explicit redact rule
        rule = PolicyRule(
            field="sensitive",
            operator=PolicyOperator.EQUALS,
            value=True,
            action=PolicyAction.REDACT,
        )
        policy = Policy(name="redact-policy", rules=[rule])
        engine.add_policy(policy)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="access",
            payload={"email": "user@example.com", "sensitive": True},
        )
        
        result = engine.evaluate(request)
        
        # Should redact due to both explicit rule and PII detection
        assert result.decision == PolicyDecision.REDACT
        assert len(result.pii_matches) >= 1
    
    def test_evaluate_with_redaction_method(self):
        """Test the evaluate_with_redaction convenience method."""
        redactor = PIIRedactor()
        # Start with auto-redaction disabled
        engine = GovernanceEngine(
            pii_redactor=redactor,
            enable_auto_redaction=False
        )
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="access",
            payload={"email": "user@example.com"},
        )
        
        # evaluate() should not redact since auto-redaction is disabled
        result1 = engine.evaluate(request)
        assert result1.decision == PolicyDecision.ALLOW
        
        # evaluate_with_redaction() should redact
        result2 = engine.evaluate_with_redaction(request)
        assert result2.decision == PolicyDecision.REDACT
        assert len(result2.pii_matches) == 1
        
        # Original setting should be restored
        assert engine.enable_auto_redaction is False
    
    def test_no_pii_with_redactor_enabled(self):
        """Test that ALLOW is returned when no PII is found."""
        redactor = PIIRedactor()
        engine = GovernanceEngine(pii_redactor=redactor, enable_auto_redaction=True)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="access",
            payload={"name": "John", "age": 30, "verified": True},
        )
        
        result = engine.evaluate(request)
        
        # No PII found, should allow
        assert result.decision == PolicyDecision.ALLOW
        assert len(result.pii_matches) == 0
        assert result.modified_payload is None
    
    def test_create_default_engine(self):
        """Test the create_default_engine() factory function."""
        engine = create_default_engine()
        
        assert engine.pii_redactor is not None
        assert engine.enable_auto_redaction is True
        assert "pii-protection" in engine._policies
    
    def test_default_engine_pii_protection_policy(self):
        """Test that default engine has working PII protection."""
        engine = create_default_engine()
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="access",
            payload={"email": "user@example.com", "name": "John"},
        )
        
        result = engine.evaluate(request)
        
        # Should redact sensitive data (via policy rule)
        assert result.decision == PolicyDecision.REDACT
        # The modified payload should have redacted email
        assert "[REDACTED]" in result.modified_payload["email"]
        assert result.modified_payload["name"] == "John"


def create_default_engine() -> GovernanceEngine:
    """
    Create a default governance engine with PII protection.
    
    Returns:
        GovernanceEngine preconfigured with PIIRedactor and default policies.
    """
    from tork.core import PIIRedactor, Policy, PolicyRule, PolicyAction, PolicyOperator
    
    # Create and configure redactor
    redactor = PIIRedactor()
    
    # Create default PII protection policy
    pii_rules = [
        PolicyRule(
            field="email",
            operator=PolicyOperator.EXISTS,
            action=PolicyAction.REDACT,
        ),
        PolicyRule(
            field="phone",
            operator=PolicyOperator.EXISTS,
            action=PolicyAction.REDACT,
        ),
        PolicyRule(
            field="ssn",
            operator=PolicyOperator.EXISTS,
            action=PolicyAction.REDACT,
        ),
        PolicyRule(
            field="credit_card",
            operator=PolicyOperator.EXISTS,
            action=PolicyAction.REDACT,
        ),
    ]
    
    pii_policy = Policy(
        name="pii-protection",
        description="Default PII protection policy",
        rules=pii_rules,
        enabled=True,
        priority=100,  # High priority
    )
    
    # Create and return engine
    return GovernanceEngine(
        policies=[pii_policy],
        pii_redactor=redactor,
        enable_auto_redaction=True,
    )
