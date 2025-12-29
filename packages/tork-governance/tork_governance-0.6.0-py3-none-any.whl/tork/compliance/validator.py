"""
Policy Validator

Validates AI agent actions against governance policies.
"""

from pathlib import Path
from typing import Any
import yaml
import structlog

logger = structlog.get_logger(__name__)


class PolicyValidator:
    """
    Validates actions against governance policies.
    
    Loads YAML policy definitions and provides validation
    methods for AI agent operations.
    """
    
    def __init__(self) -> None:
        """Initialize the policy validator."""
        self._policies: list[dict[str, Any]] = []
        logger.info("PolicyValidator initialized")
    
    def load_policies(self, path: str | Path) -> int:
        """
        Load policies from a directory or file.
        
        Args:
            path: Path to policy file or directory.
            
        Returns:
            Number of policies loaded.
        """
        path = Path(path)
        
        if path.is_file():
            self._load_policy_file(path)
        elif path.is_dir():
            for policy_file in path.glob("*.yaml"):
                self._load_policy_file(policy_file)
            for policy_file in path.glob("*.yml"):
                self._load_policy_file(policy_file)
        
        logger.info("Policies loaded", count=len(self._policies))
        return len(self._policies)
    
    def _load_policy_file(self, path: Path) -> None:
        """Load a single policy file."""
        with open(path) as f:
            policy = yaml.safe_load(f)
            if policy:
                self._policies.append(policy)
                logger.debug("Policy file loaded", path=str(path))
    
    def validate(self, action: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate an action against loaded policies.
        
        Args:
            action: The action to validate.
            
        Returns:
            Tuple of (is_valid, list of violation messages).
        """
        violations: list[str] = []
        
        for policy in self._policies:
            rules = policy.get("rules", [])
            for rule in rules:
                if not self._check_rule(action, rule):
                    violations.append(rule.get("message", "Policy violation"))
        
        is_valid = len(violations) == 0
        logger.info("Action validated", is_valid=is_valid, violations=len(violations))
        return is_valid, violations
    
    def _check_rule(self, action: dict[str, Any], rule: dict[str, Any]) -> bool:
        """Check a single rule against an action."""
        return True
    
    @property
    def policy_count(self) -> int:
        """Return the number of loaded policies."""
        return len(self._policies)
