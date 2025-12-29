"""Data models for the debate and consensus system."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DebateParticipant(BaseModel):
    """A participant in a debate."""

    id: str = Field(..., description="Unique participant identifier")
    name: str = Field(..., description="Human-readable name")
    agent_type: str = Field(
        ...,
        description="Type of agent: langchain, crewai, autogen, openai_agents, custom",
    )
    role: str = Field(
        default="debater",
        description="Role in debate: debater, critic, synthesizer, judge",
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific configuration"
    )
    weight: float = Field(default=1.0, description="Voting weight")


class DebateRound(BaseModel):
    """A single round of debate."""

    round_number: int = Field(..., description="Round number (1-indexed)")
    participant_id: str = Field(..., description="ID of the participant")
    input_prompt: str = Field(..., description="Prompt given to the participant")
    response: str = Field(..., description="Participant's response")
    critique_of: Optional[str] = Field(
        default=None, description="ID of response being critiqued"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(), description="When the round occurred"
    )
    tokens_used: int = Field(default=0, description="Tokens consumed")
    cost: float = Field(default=0.0, description="Cost of this round")


class ConsensusConfig(BaseModel):
    """Configuration for consensus building."""

    method: str = Field(
        default="synthesis",
        description="Consensus method: synthesis, voting, judge, unanimous",
    )
    max_rounds: int = Field(default=3, description="Maximum debate rounds")
    min_agreement_threshold: float = Field(
        default=0.7, description="Minimum agreement for voting method"
    )
    cost_limit: float = Field(
        default=10.0, description="Maximum cost before forcing conclusion"
    )
    stop_on_consensus: bool = Field(
        default=True, description="Stop when consensus is reached"
    )
    require_all_participants: bool = Field(
        default=True, description="Require all participants to respond"
    )


class DebateResult(BaseModel):
    """Result of a debate session."""

    session_id: str = Field(..., description="Unique session identifier")
    status: str = Field(
        ...,
        description="Status: consensus_reached, max_rounds_reached, cost_limit_reached, no_consensus",
    )
    rounds: List[DebateRound] = Field(
        default_factory=list, description="All debate rounds"
    )
    final_consensus: Optional[str] = Field(
        default=None, description="Final consensus text"
    )
    agreement_score: float = Field(default=0.0, description="Agreement score (0-1)")
    total_tokens: int = Field(default=0, description="Total tokens consumed")
    total_cost: float = Field(default=0.0, description="Total cost")
    receipt_ids: List[str] = Field(
        default_factory=list, description="Compliance receipt IDs"
    )
