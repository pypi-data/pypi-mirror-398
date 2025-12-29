"""
Exceptions for LangChain governance integration.
"""

from typing import Optional
from tork.core.models import PolicyDecision


class GovernanceViolation(Exception):
    """
    Exception raised when a governance policy denies an action.
    
    Attributes:
        message: Human-readable description of the violation.
        decision: The policy decision that caused the violation.
        violations: List of specific policy violations.
    """
    
    def __init__(
        self,
        message: str,
        decision: PolicyDecision,
        violations: Optional[list[str]] = None,
    ) -> None:
        """
        Initialize a governance violation exception.
        
        Args:
            message: Human-readable description.
            decision: The policy decision (typically DENY).
            violations: List of specific violations that occurred.
        """
        super().__init__(message)
        self.message = message
        self.decision = decision
        self.violations = violations or []
    
    def __str__(self) -> str:
        """Return string representation of the violation."""
        if self.violations:
            return f"{self.message}: {', '.join(self.violations)}"
        return self.message
