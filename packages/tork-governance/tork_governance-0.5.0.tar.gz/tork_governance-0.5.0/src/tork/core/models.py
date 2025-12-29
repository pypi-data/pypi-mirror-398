"""
Core data models for governance operations.

Provides Pydantic models for evaluation requests, results, and policy decisions.
"""

from enum import Enum
from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    pass


class PolicyDecision(str, Enum):
    """Policy decision outcome."""
    
    ALLOW = "allow"
    DENY = "deny"
    REDACT = "redact"


class EvaluationRequest(BaseModel):
    """Request for policy evaluation."""
    
    agent_id: str = Field(..., description="ID of the agent performing the action")
    action: str = Field(..., description="Action being performed")
    payload: dict[str, Any] = Field(default_factory=dict, description="Action payload")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Additional metadata")


class EvaluationResult(BaseModel):
    """Result of policy evaluation."""
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    decision: PolicyDecision = Field(..., description="Final policy decision")
    reason: str = Field(..., description="Explanation of the decision")
    original_payload: dict[str, Any] = Field(..., description="Original unmodified payload")
    modified_payload: Optional[dict[str, Any]] = Field(
        default=None, description="Modified payload (if redacted)"
    )
    violations: list[str] = Field(default_factory=list, description="List of policy violations")
    pii_matches: list[Any] = Field(default_factory=list, description="PII matches detected")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Evaluation timestamp")
