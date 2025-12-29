"""
Governance Engine

The central orchestrator for AI agent governance operations.
"""

from typing import Any, Optional
from datetime import datetime
import re
import structlog

from tork.core.models import EvaluationRequest, EvaluationResult, PolicyDecision
from tork.core.policy import Policy, PolicyRule, PolicyAction

logger = structlog.get_logger(__name__)


class GovernanceEngine:
    """
    Main governance engine for AI agent oversight.
    
    Coordinates policy enforcement, identity verification,
    and compliance checking across agent operations.
    """
    
    def __init__(
        self,
        policies: Optional[list[Policy]] = None,
        pii_redactor: Optional[Any] = None,
        enable_auto_redaction: bool = True,
    ) -> None:
        """
        Initialize the governance engine.
        
        Args:
            policies: Optional list of Policy objects to load.
            pii_redactor: Optional PIIRedactor instance for PII detection and redaction.
            enable_auto_redaction: Whether to auto-redact PII even without explicit REDACT rules.
        """
        self._policies: dict[str, Policy] = {}
        self._initialized = False
        self.pii_redactor = pii_redactor
        self.enable_auto_redaction = enable_auto_redaction
        
        if policies:
            for policy in policies:
                self.add_policy(policy)
        
        logger.info(
            "GovernanceEngine initialized",
            policy_count=len(self._policies),
            pii_redactor_enabled=pii_redactor is not None,
            auto_redaction_enabled=enable_auto_redaction,
        )
    
    def start(self) -> None:
        """Start the governance engine."""
        self._initialized = True
        logger.info("GovernanceEngine started", policies=list(self._policies.keys()))
    
    def stop(self) -> None:
        """Stop the governance engine."""
        self._initialized = False
        logger.info("GovernanceEngine stopped")
    
    def is_running(self) -> bool:
        """Check if the engine is running."""
        return self._initialized
    
    def add_policy(self, policy: Policy) -> None:
        """
        Add a policy to the engine.
        
        Args:
            policy: Policy object to add.
        """
        self._policies[policy.name] = policy
        logger.info("Policy added", name=policy.name, priority=policy.priority)
    
    def remove_policy(self, name: str) -> bool:
        """
        Remove a policy from the engine.
        
        Args:
            name: Name of the policy to remove.
            
        Returns:
            True if removed, False if not found.
        """
        if name in self._policies:
            del self._policies[name]
            logger.info("Policy removed", name=name)
            return True
        return False
    
    def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        """
        Evaluate a request against loaded policies.
        
        Args:
            request: The evaluation request.
            
        Returns:
            The evaluation result with decision and violations.
        """
        violations: list[str] = []
        pii_matches: list[Any] = []
        modified_payload = request.payload.copy()
        final_decision = PolicyDecision.ALLOW
        reason = "No policy violations"
        
        # Sort policies by priority (higher first)
        sorted_policies = sorted(
            self._policies.values(),
            key=lambda p: p.priority,
            reverse=True
        )
        
        # Evaluate each enabled policy
        for policy in sorted_policies:
            if not policy.enabled:
                continue
            
            for rule in policy.rules:
                if self._check_rule(rule, request.payload):
                    decision, new_payload = self._apply_action(rule, modified_payload)
                    modified_payload = new_payload
                    
                    # DENY takes precedence over all other decisions
                    if decision == PolicyDecision.DENY:
                        final_decision = PolicyDecision.DENY
                        reason = f"Denied by policy '{policy.name}' rule"
                        violations.append(
                            f"Policy '{policy.name}' denied action: {rule.field} {rule.operator.value}"
                        )
                    # REDACT takes precedence over ALLOW
                    elif decision == PolicyDecision.REDACT and final_decision == PolicyDecision.ALLOW:
                        final_decision = PolicyDecision.REDACT
                        reason = f"Redacted by policy '{policy.name}'"
                        violations.append(
                            f"Policy '{policy.name}' redacted field: {rule.field}"
                        )
        
        # Auto-redact PII if enabled
        if self.pii_redactor and self.enable_auto_redaction:
            redacted_payload, pii_matches = self.pii_redactor.redact_dict(modified_payload)
            if pii_matches:
                modified_payload = redacted_payload
                if final_decision == PolicyDecision.ALLOW:
                    final_decision = PolicyDecision.REDACT
                    reason = f"PII auto-redaction enabled - {len(pii_matches)} PII items detected"
                violations.extend([f"Auto-redacted PII: {m.pii_type.value}" for m in pii_matches])
        
        logger.info(
            "Request evaluated",
            agent_id=request.agent_id,
            action=request.action,
            decision=final_decision,
            violations=len(violations),
            pii_matches=len(pii_matches),
        )
        
        return EvaluationResult(
            decision=final_decision,
            reason=reason,
            original_payload=request.payload,
            modified_payload=modified_payload if final_decision == PolicyDecision.REDACT else None,
            violations=violations,
            pii_matches=pii_matches,
            timestamp=datetime.utcnow(),
        )
    
    def evaluate_with_redaction(self, request: EvaluationRequest) -> EvaluationResult:
        """
        Evaluate a request and always redact PII from the modified payload.
        
        This is a convenience method that forces auto-redaction regardless of settings.
        
        Args:
            request: The evaluation request.
            
        Returns:
            The evaluation result with PII redacted from modified_payload.
        """
        # Temporarily enable auto-redaction
        original_auto_redaction = self.enable_auto_redaction
        self.enable_auto_redaction = True
        
        try:
            return self.evaluate(request)
        finally:
            # Restore original setting
            self.enable_auto_redaction = original_auto_redaction
    
    def _check_rule(self, rule: PolicyRule, payload: dict[str, Any]) -> bool:
        """
        Check if a rule matches the given payload.
        
        Args:
            rule: The policy rule to check.
            payload: The payload to check against.
            
        Returns:
            True if the rule matches, False otherwise.
        """
        value = self._get_nested_value(payload, rule.field)
        
        if rule.operator == "exists":
            return value is not None
        
        if value is None:
            return False
        
        if rule.operator == "equals":
            return value == rule.value
        
        if rule.operator == "contains":
            if isinstance(value, (list, str)):
                return rule.value in value
            return False
        
        if rule.operator == "regex":
            if isinstance(value, str) and isinstance(rule.value, str):
                return bool(re.search(rule.value, value))
            return False
        
        return False
    
    def _apply_action(
        self, rule: PolicyRule, payload: dict[str, Any]
    ) -> tuple[PolicyDecision, dict[str, Any]]:
        """
        Apply a rule's action to the payload.
        
        Args:
            rule: The policy rule.
            payload: The payload to modify.
            
        Returns:
            Tuple of (decision, modified_payload).
        """
        modified = payload.copy()
        
        if rule.action == PolicyAction.DENY:
            return PolicyDecision.DENY, modified
        
        if rule.action == PolicyAction.REDACT:
            self._redact_nested_value(modified, rule.field)
            return PolicyDecision.REDACT, modified
        
        # ALLOW or default
        return PolicyDecision.ALLOW, modified
    
    def _get_nested_value(self, data: dict[str, Any], path: str) -> Any:
        """
        Get a nested value from a dict using dot notation.
        
        Args:
            data: The dictionary to search.
            path: Dot-separated path (e.g., "user.email").
            
        Returns:
            The value at the path, or None if not found.
        """
        keys = path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        
        return current
    
    def _redact_nested_value(self, data: dict[str, Any], path: str) -> None:
        """
        Redact a nested value in a dict using dot notation.
        
        Args:
            data: The dictionary to modify (modified in-place).
            path: Dot-separated path (e.g., "user.email").
        """
        keys = path.split(".")
        current = data
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                return
            if not isinstance(current[key], dict):
                return
            current = current[key]
        
        # Redact the final key
        if keys and keys[-1] in current:
            current[keys[-1]] = "[REDACTED]"
