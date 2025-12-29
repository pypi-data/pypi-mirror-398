"""Data models for the Custom Agents/Personas system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class PersonaCapability(str, Enum):
    """Capabilities a persona can have."""

    RESEARCH = "research"
    ANALYSIS = "analysis"
    WRITING = "writing"
    CODING = "coding"
    CRITIQUE = "critique"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    DATA_PROCESSING = "data_processing"
    CREATIVE = "creative"
    LEGAL = "legal"
    FINANCIAL = "financial"
    MEDICAL = "medical"


class PersonaConfig(BaseModel):
    """Configuration for a custom persona."""

    id: str = Field(..., description="Unique persona identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(default="", description="Persona description")
    system_prompt: str = Field(..., description="Core prompt defining behavior")
    capabilities: List[PersonaCapability] = Field(default_factory=list)
    preferred_models: List[str] = Field(default_factory=list)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)

    governance_policy: Optional[str] = Field(default=None, description="Custom policy")
    pii_redaction: bool = Field(default=True)
    allowed_actions: List[str] = Field(default_factory=list)
    blocked_actions: List[str] = Field(default_factory=list)
    max_cost_per_request: float = Field(default=1.0, ge=0.0)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(default="")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PersonaInstance(BaseModel):
    """A running instance of a persona."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    persona_id: str = Field(..., description="Parent persona ID")
    session_id: str = Field(..., description="Session identifier")
    state: Dict[str, Any] = Field(default_factory=dict, description="Instance state/memory")
    messages_count: int = Field(default=0)
    total_tokens: int = Field(default=0)
    total_cost: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
