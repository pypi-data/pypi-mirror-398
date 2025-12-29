"""Data models for the Agent Capability Labels system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class CapabilityLevel(str, Enum):
    """Proficiency level for a capability."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class PerformanceMetric(str, Enum):
    """Performance characteristics."""

    SPEED = "speed"
    ACCURACY = "accuracy"
    CREATIVITY = "creativity"
    SAFETY = "safety"
    COST = "cost"
    CONTEXT = "context"


class AgentCapability(BaseModel):
    """A single capability with proficiency level."""

    name: str = Field(..., description="Capability name")
    level: CapabilityLevel = Field(default=CapabilityLevel.INTERMEDIATE)
    score: float = Field(default=0.5, ge=0.0, le=1.0, description="Score from 0.0 to 1.0")
    verified: bool = Field(default=False, description="Has this been tested/verified?")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentProfile(BaseModel):
    """Complete capability profile for an agent."""

    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Display name")
    provider: str = Field(default="", description="Provider name")
    model: str = Field(default="", description="Model name")

    capabilities: List[AgentCapability] = Field(default_factory=list)
    performance: Dict[PerformanceMetric, float] = Field(default_factory=dict)

    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)

    best_for: List[str] = Field(default_factory=list)
    avoid_for: List[str] = Field(default_factory=list)

    description: str = Field(default="")
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_capability(self, name: str) -> AgentCapability | None:
        """Get a capability by name."""
        for cap in self.capabilities:
            if cap.name.lower() == name.lower():
                return cap
        return None

    def get_capability_score(self, name: str) -> float:
        """Get capability score by name, returns 0.0 if not found."""
        cap = self.get_capability(name)
        return cap.score if cap else 0.0
