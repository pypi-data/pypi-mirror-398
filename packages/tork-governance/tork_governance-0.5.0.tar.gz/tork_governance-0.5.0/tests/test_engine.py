"""
Tests for the governance engine.

Tests core engine functionality including policy evaluation,
decision making, and payload modification.
"""

import pytest
from tork.core import (
    GovernanceEngine,
    Policy,
    PolicyRule,
    PolicyAction,
    PolicyOperator,
    PolicyDecision,
    EvaluationRequest,
)


class TestGovernanceEngine:
    """Tests for GovernanceEngine."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = GovernanceEngine()
        assert not engine.is_running()
        assert engine._policies == {}
    
    def test_engine_start_stop(self):
        """Test starting and stopping the engine."""
        engine = GovernanceEngine()
        
        engine.start()
        assert engine.is_running()
        
        engine.stop()
        assert not engine.is_running()
    
    def test_add_policy(self):
        """Test adding a policy to the engine."""
        engine = GovernanceEngine()
        
        policy = Policy(
            name="test-policy",
            description="Test policy",
            rules=[],
        )
        
        engine.add_policy(policy)
        assert "test-policy" in engine._policies
        assert engine._policies["test-policy"] == policy
    
    def test_remove_policy(self):
        """Test removing a policy from the engine."""
        engine = GovernanceEngine()
        
        policy = Policy(name="test-policy", rules=[])
        engine.add_policy(policy)
        
        assert engine.remove_policy("test-policy")
        assert "test-policy" not in engine._policies
        
        assert not engine.remove_policy("nonexistent")
    
    def test_engine_with_initial_policies(self):
        """Test engine initialization with policies."""
        policy = Policy(name="test-policy", rules=[])
        engine = GovernanceEngine(policies=[policy])
        
        assert "test-policy" in engine._policies
    
    def test_allow_decision_no_matching_rules(self):
        """Test ALLOW decision when no rules match."""
        engine = GovernanceEngine()
        
        rule = PolicyRule(
            field="admin",
            operator=PolicyOperator.EQUALS,
            value=True,
            action=PolicyAction.DENY,
        )
        
        policy = Policy(name="admin-policy", rules=[rule])
        engine.add_policy(policy)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="read",
            payload={"admin": False, "user": "alice"},
        )
        
        result = engine.evaluate(request)
        
        assert result.decision == PolicyDecision.ALLOW
        assert result.reason == "No policy violations"
        assert result.violations == []
        assert result.original_payload == request.payload
        assert result.modified_payload is None
    
    def test_deny_decision_matching_rule(self):
        """Test DENY decision when a rule matches."""
        engine = GovernanceEngine()
        
        rule = PolicyRule(
            field="admin",
            operator=PolicyOperator.EQUALS,
            value=True,
            action=PolicyAction.DENY,
        )
        
        policy = Policy(name="admin-policy", rules=[rule])
        engine.add_policy(policy)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="delete",
            payload={"admin": True, "user": "alice"},
        )
        
        result = engine.evaluate(request)
        
        assert result.decision == PolicyDecision.DENY
        assert len(result.violations) > 0
        assert "admin" in result.reason or "admin" in result.violations[0]
    
    def test_redact_decision_matching_rule(self):
        """Test REDACT decision and payload modification."""
        engine = GovernanceEngine()
        
        rule = PolicyRule(
            field="email",
            operator=PolicyOperator.EXISTS,
            action=PolicyAction.REDACT,
        )
        
        policy = Policy(name="redact-policy", rules=[rule])
        engine.add_policy(policy)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="view",
            payload={"email": "user@example.com", "name": "Alice"},
        )
        
        result = engine.evaluate(request)
        
        assert result.decision == PolicyDecision.REDACT
        assert result.modified_payload is not None
        assert result.modified_payload["email"] == "[REDACTED]"
        assert result.modified_payload["name"] == "Alice"
        assert result.original_payload["email"] == "user@example.com"
        assert len(result.violations) > 0
    
    def test_multiple_policies_priority(self):
        """Test multiple policies evaluated with priority."""
        engine = GovernanceEngine()
        
        # Low priority allow rule
        allow_rule = PolicyRule(
            field="sensitive",
            operator=PolicyOperator.EQUALS,
            value=False,
            action=PolicyAction.ALLOW,
        )
        
        allow_policy = Policy(
            name="allow-policy",
            rules=[allow_rule],
            priority=0,
        )
        
        # High priority deny rule
        deny_rule = PolicyRule(
            field="admin",
            operator=PolicyOperator.EQUALS,
            value=True,
            action=PolicyAction.DENY,
        )
        
        deny_policy = Policy(
            name="deny-policy",
            rules=[deny_rule],
            priority=10,
        )
        
        engine.add_policy(allow_policy)
        engine.add_policy(deny_policy)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="execute",
            payload={"admin": True, "sensitive": False},
        )
        
        result = engine.evaluate(request)
        
        # High priority deny should win
        assert result.decision == PolicyDecision.DENY
    
    def test_contains_operator(self):
        """Test the CONTAINS operator."""
        engine = GovernanceEngine()
        
        rule = PolicyRule(
            field="tags",
            operator=PolicyOperator.CONTAINS,
            value="restricted",
            action=PolicyAction.DENY,
        )
        
        policy = Policy(name="tag-policy", rules=[rule])
        engine.add_policy(policy)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="access",
            payload={"tags": ["public", "restricted", "internal"]},
        )
        
        result = engine.evaluate(request)
        
        assert result.decision == PolicyDecision.DENY
    
    def test_regex_operator(self):
        """Test the REGEX operator."""
        engine = GovernanceEngine()
        
        rule = PolicyRule(
            field="email",
            operator=PolicyOperator.REGEX,
            value=r"^.*@admin\..*$",
            action=PolicyAction.DENY,
        )
        
        policy = Policy(name="admin-email-policy", rules=[rule])
        engine.add_policy(policy)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="access",
            payload={"email": "user@admin.example.com"},
        )
        
        result = engine.evaluate(request)
        
        assert result.decision == PolicyDecision.DENY
    
    def test_nested_payload_fields(self):
        """Test evaluation of nested fields in payload."""
        engine = GovernanceEngine()
        
        rule = PolicyRule(
            field="user.role",
            operator=PolicyOperator.EQUALS,
            value="admin",
            action=PolicyAction.DENY,
        )
        
        policy = Policy(name="admin-role-policy", rules=[rule])
        engine.add_policy(policy)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="delete",
            payload={"user": {"role": "admin", "name": "Alice"}},
        )
        
        result = engine.evaluate(request)
        
        assert result.decision == PolicyDecision.DENY
    
    def test_redact_nested_field(self):
        """Test redaction of nested fields."""
        engine = GovernanceEngine()
        
        rule = PolicyRule(
            field="user.email",
            operator=PolicyOperator.EXISTS,
            action=PolicyAction.REDACT,
        )
        
        policy = Policy(name="redact-email-policy", rules=[rule])
        engine.add_policy(policy)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="view",
            payload={"user": {"email": "alice@example.com", "name": "Alice"}},
        )
        
        result = engine.evaluate(request)
        
        assert result.decision == PolicyDecision.REDACT
        assert result.modified_payload["user"]["email"] == "[REDACTED]"
        assert result.modified_payload["user"]["name"] == "Alice"
    
    def test_disabled_policy_skipped(self):
        """Test that disabled policies are not evaluated."""
        engine = GovernanceEngine()
        
        rule = PolicyRule(
            field="admin",
            operator=PolicyOperator.EQUALS,
            value=True,
            action=PolicyAction.DENY,
        )
        
        policy = Policy(name="admin-policy", rules=[rule], enabled=False)
        engine.add_policy(policy)
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="delete",
            payload={"admin": True},
        )
        
        result = engine.evaluate(request)
        
        # Should ALLOW because policy is disabled
        assert result.decision == PolicyDecision.ALLOW
        assert result.reason == "No policy violations"
