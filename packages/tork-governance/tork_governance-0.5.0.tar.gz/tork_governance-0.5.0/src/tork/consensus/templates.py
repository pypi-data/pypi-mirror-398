"""Pre-built debate configurations."""

from typing import List, Tuple

from tork.consensus.models import ConsensusConfig, DebateParticipant


def two_agent_critique() -> Tuple[List[DebateParticipant], ConsensusConfig]:
    """
    Agent A proposes, Agent B critiques, synthesize.

    Returns:
        Tuple of (participants, config) for a two-agent critique debate.
    """
    participants = [
        DebateParticipant(
            id="agent_a",
            name="Proposer",
            agent_type="custom",
            role="debater",
            config={"perspective": "proposer"},
        ),
        DebateParticipant(
            id="agent_b",
            name="Critic",
            agent_type="custom",
            role="critic",
            config={"perspective": "critic"},
        ),
        DebateParticipant(
            id="synthesizer",
            name="Synthesizer",
            agent_type="custom",
            role="synthesizer",
            config={"perspective": "neutral"},
        ),
    ]

    config = ConsensusConfig(
        method="synthesis",
        max_rounds=2,
        min_agreement_threshold=0.6,
        stop_on_consensus=True,
    )

    return participants, config


def three_way_debate() -> Tuple[List[DebateParticipant], ConsensusConfig]:
    """
    Three agents debate, judge decides.

    Returns:
        Tuple of (participants, config) for a three-way debate with judge.
    """
    participants = [
        DebateParticipant(
            id="debater_1",
            name="Debater 1",
            agent_type="custom",
            role="debater",
            config={"perspective": "conservative"},
        ),
        DebateParticipant(
            id="debater_2",
            name="Debater 2",
            agent_type="custom",
            role="debater",
            config={"perspective": "progressive"},
        ),
        DebateParticipant(
            id="debater_3",
            name="Debater 3",
            agent_type="custom",
            role="debater",
            config={"perspective": "moderate"},
        ),
        DebateParticipant(
            id="judge",
            name="Judge",
            agent_type="custom",
            role="judge",
            config={"perspective": "impartial"},
        ),
    ]

    config = ConsensusConfig(
        method="judge",
        max_rounds=3,
        min_agreement_threshold=0.8,
        stop_on_consensus=False,
    )

    return participants, config


def expert_panel() -> Tuple[List[DebateParticipant], ConsensusConfig]:
    """
    Multiple experts, weighted voting.

    Returns:
        Tuple of (participants, config) for an expert panel with weighted voting.
    """
    participants = [
        DebateParticipant(
            id="expert_1",
            name="Domain Expert",
            agent_type="custom",
            role="debater",
            config={"expertise": "domain"},
            weight=2.0,
        ),
        DebateParticipant(
            id="expert_2",
            name="Technical Expert",
            agent_type="custom",
            role="debater",
            config={"expertise": "technical"},
            weight=1.5,
        ),
        DebateParticipant(
            id="expert_3",
            name="General Expert",
            agent_type="custom",
            role="debater",
            config={"expertise": "general"},
            weight=1.0,
        ),
        DebateParticipant(
            id="expert_4",
            name="Junior Expert",
            agent_type="custom",
            role="debater",
            config={"expertise": "junior"},
            weight=0.5,
        ),
    ]

    config = ConsensusConfig(
        method="voting",
        max_rounds=2,
        min_agreement_threshold=0.6,
        stop_on_consensus=True,
    )

    return participants, config
