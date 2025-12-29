"""
Policy management and evaluation.

Provides policy models and loading mechanisms.
"""

from typing import Any, Optional
from enum import Enum
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, ConfigDict
import structlog

logger = structlog.get_logger(__name__)


class PolicyOperator(str, Enum):
    """Operators for policy rule evaluation."""
    
    EQUALS = "equals"
    CONTAINS = "contains"
    REGEX = "regex"
    EXISTS = "exists"


class PolicyAction(str, Enum):
    """Actions that a policy rule can trigger."""
    
    ALLOW = "allow"
    DENY = "deny"
    REDACT = "redact"


class PolicyRule(BaseModel):
    """A single policy rule."""
    
    model_config = ConfigDict(use_enum_values=False)
    
    field: str = Field(..., description="Field path in the payload (dot notation)")
    operator: PolicyOperator = Field(..., description="Comparison operator")
    value: Optional[Any] = Field(default=None, description="Value to compare against")
    action: PolicyAction = Field(..., description="Action to take if rule matches")


class Policy(BaseModel):
    """A governance policy containing multiple rules."""
    
    model_config = ConfigDict(use_enum_values=False)
    
    name: str = Field(..., description="Unique policy name")
    description: str = Field(default="", description="Policy description")
    rules: list[PolicyRule] = Field(default_factory=list, description="Policy rules")
    enabled: bool = Field(default=True, description="Whether policy is enabled")
    priority: int = Field(default=0, description="Policy priority (higher = evaluated first)")


class PolicyLoader:
    """Loads policies from YAML files and dictionaries."""
    
    @staticmethod
    def load_from_yaml(path: str | Path) -> Policy:
        """
        Load a single policy from a YAML file.
        
        Args:
            path: Path to the YAML policy file.
            
        Returns:
            Loaded Policy object.
        """
        path = Path(path)
        with open(path) as f:
            data = yaml.safe_load(f)
        
        logger.info("Policy loaded from YAML", path=str(path), name=data.get("name"))
        return PolicyLoader.load_from_dict(data)
    
    @staticmethod
    def load_from_dict(data: dict[str, Any]) -> Policy:
        """
        Load a policy from a dictionary.
        
        Args:
            data: Dictionary containing policy configuration.
            
        Returns:
            Loaded Policy object.
        """
        # Convert rule dicts to PolicyRule objects
        rules = []
        for rule_data in data.get("rules", []):
            rule_data["operator"] = PolicyOperator(rule_data.get("operator", "equals"))
            rule_data["action"] = PolicyAction(rule_data.get("action", "allow"))
            rules.append(PolicyRule(**rule_data))
        
        data["rules"] = rules
        return Policy(**data)
