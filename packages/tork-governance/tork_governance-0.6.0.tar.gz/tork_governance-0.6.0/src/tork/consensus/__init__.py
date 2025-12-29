"""Debate and consensus system for Tork Governance SDK."""

from tork.consensus.models import (
    DebateParticipant,
    DebateRound,
    ConsensusConfig,
    DebateResult,
)
from tork.consensus.engine import DebateEngine
from tork.consensus.strategies import (
    ConsensusStrategy,
    SynthesisStrategy,
    VotingStrategy,
    JudgeStrategy,
    UnanimousStrategy,
)
from tork.consensus.templates import (
    two_agent_critique,
    three_way_debate,
    expert_panel,
)

__all__ = [
    "DebateParticipant",
    "DebateRound",
    "ConsensusConfig",
    "DebateResult",
    "DebateEngine",
    "ConsensusStrategy",
    "SynthesisStrategy",
    "VotingStrategy",
    "JudgeStrategy",
    "UnanimousStrategy",
    "two_agent_critique",
    "three_way_debate",
    "expert_panel",
]
