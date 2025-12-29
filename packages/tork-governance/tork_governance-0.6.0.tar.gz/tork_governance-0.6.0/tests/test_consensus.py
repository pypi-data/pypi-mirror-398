"""Tests for the debate and consensus system."""

import pytest
from datetime import datetime

from tork.consensus import (
    DebateParticipant,
    DebateRound,
    ConsensusConfig,
    DebateResult,
    DebateEngine,
    SynthesisStrategy,
    VotingStrategy,
    JudgeStrategy,
    UnanimousStrategy,
    two_agent_critique,
    three_way_debate,
    expert_panel,
)
from tork.core.engine import GovernanceEngine


class TestDebateParticipantModel:
    """Tests for DebateParticipant model."""

    def test_basic_participant(self):
        participant = DebateParticipant(
            id="agent1", name="Agent 1", agent_type="custom"
        )
        assert participant.id == "agent1"
        assert participant.name == "Agent 1"
        assert participant.agent_type == "custom"
        assert participant.role == "debater"
        assert participant.weight == 1.0

    def test_participant_with_config(self):
        participant = DebateParticipant(
            id="agent1",
            name="Expert Agent",
            agent_type="langchain",
            role="judge",
            config={"model": "gpt-4"},
            weight=2.0,
        )
        assert participant.role == "judge"
        assert participant.config["model"] == "gpt-4"
        assert participant.weight == 2.0


class TestDebateRoundModel:
    """Tests for DebateRound model."""

    def test_basic_round(self):
        rnd = DebateRound(
            round_number=1,
            participant_id="agent1",
            input_prompt="What is AI?",
            response="AI is artificial intelligence.",
        )
        assert rnd.round_number == 1
        assert rnd.participant_id == "agent1"
        assert rnd.response == "AI is artificial intelligence."
        assert rnd.critique_of is None

    def test_critique_round(self):
        rnd = DebateRound(
            round_number=2,
            participant_id="agent2",
            input_prompt="Critique agent1's response",
            response="The response lacks specificity.",
            critique_of="agent1",
            tokens_used=50,
            cost=0.01,
        )
        assert rnd.critique_of == "agent1"
        assert rnd.tokens_used == 50
        assert rnd.cost == 0.01


class TestConsensusConfigModel:
    """Tests for ConsensusConfig model."""

    def test_default_config(self):
        config = ConsensusConfig()
        assert config.method == "synthesis"
        assert config.max_rounds == 3
        assert config.min_agreement_threshold == 0.7
        assert config.cost_limit == 10.0
        assert config.stop_on_consensus is True

    def test_custom_config(self):
        config = ConsensusConfig(
            method="voting",
            max_rounds=5,
            min_agreement_threshold=0.8,
            cost_limit=50.0,
        )
        assert config.method == "voting"
        assert config.max_rounds == 5


class TestDebateResultModel:
    """Tests for DebateResult model."""

    def test_basic_result(self):
        result = DebateResult(
            session_id="abc123",
            status="consensus_reached",
            final_consensus="AI is transformative technology.",
            agreement_score=0.85,
        )
        assert result.session_id == "abc123"
        assert result.status == "consensus_reached"
        assert result.agreement_score == 0.85

    def test_result_with_rounds(self):
        result = DebateResult(
            session_id="abc123",
            status="max_rounds_reached",
            rounds=[
                DebateRound(
                    round_number=1,
                    participant_id="a1",
                    input_prompt="Topic",
                    response="Response 1",
                )
            ],
            total_tokens=100,
            total_cost=0.05,
            receipt_ids=["r1", "r2"],
        )
        assert len(result.rounds) == 1
        assert result.total_tokens == 100


class TestDebateEngineInitialization:
    """Tests for DebateEngine initialization."""

    def test_default_init(self):
        engine = DebateEngine()
        assert engine.governance_engine is not None
        assert engine.receipt_generator is not None
        assert "synthesis" in engine._strategies
        assert "voting" in engine._strategies

    def test_custom_governance_engine(self):
        gov_engine = GovernanceEngine()
        engine = DebateEngine(governance_engine=gov_engine)
        assert engine.governance_engine is gov_engine


class TestRegisterExecutor:
    """Tests for executor registration."""

    def test_register_executor(self):
        engine = DebateEngine()
        executor = lambda p, i: "response"
        engine.register_executor("custom", executor)
        assert "custom" in engine._executors


class TestSimpleTwoAgentDebate:
    """Tests for simple two-agent debate."""

    def test_two_agent_debate(self):
        engine = DebateEngine()
        engine.register_executor(
            "custom", lambda p, i: f"Response from {p.name}"
        )

        participants = [
            DebateParticipant(id="a1", name="Agent 1", agent_type="custom"),
            DebateParticipant(id="a2", name="Agent 2", agent_type="custom"),
        ]

        result = engine.debate(
            topic="What is the best programming language?",
            participants=participants,
            config=ConsensusConfig(max_rounds=1),
        )

        assert result.status in ["consensus_reached", "max_rounds_reached"]
        assert len(result.rounds) == 2


class TestDebateWithCritiqueRounds:
    """Tests for debate with critique rounds."""

    def test_critique_rounds(self):
        engine = DebateEngine()
        engine.register_executor(
            "custom", lambda p, i: f"Response from {p.name}"
        )

        participants = [
            DebateParticipant(id="a1", name="Agent 1", agent_type="custom", role="debater"),
            DebateParticipant(id="a2", name="Agent 2", agent_type="custom", role="debater"),
        ]

        result = engine.debate(
            topic="Debate topic",
            participants=participants,
            config=ConsensusConfig(max_rounds=2, stop_on_consensus=False),
        )

        assert len(result.rounds) >= 2
        critique_rounds = [r for r in result.rounds if r.critique_of is not None]
        assert len(critique_rounds) >= 1


class TestSynthesisConsensusMethod:
    """Tests for synthesis consensus method."""

    def test_synthesis_strategy(self):
        strategy = SynthesisStrategy()
        rounds = [
            DebateRound(
                round_number=1,
                participant_id="a1",
                input_prompt="Topic",
                response="View A",
            ),
            DebateRound(
                round_number=1,
                participant_id="a2",
                input_prompt="Topic",
                response="View B",
            ),
        ]
        participants = [
            DebateParticipant(id="a1", name="A1", agent_type="custom"),
            DebateParticipant(id="a2", name="A2", agent_type="custom"),
        ]

        consensus, score = strategy.evaluate(rounds, participants)
        assert "View A" in consensus or "View B" in consensus
        assert score > 0


class TestVotingConsensusMethod:
    """Tests for voting consensus method."""

    def test_voting_strategy(self):
        strategy = VotingStrategy()
        rounds = [
            DebateRound(
                round_number=1,
                participant_id="a1",
                input_prompt="Topic",
                response="Same response",
            ),
            DebateRound(
                round_number=1,
                participant_id="a2",
                input_prompt="Topic",
                response="Same response",
            ),
        ]
        participants = [
            DebateParticipant(id="a1", name="A1", agent_type="custom", weight=1.0),
            DebateParticipant(id="a2", name="A2", agent_type="custom", weight=1.0),
        ]

        consensus, score = strategy.evaluate(rounds, participants)
        assert consensus == "Same response"
        assert score == 1.0


class TestJudgeConsensusMethod:
    """Tests for judge consensus method."""

    def test_judge_strategy(self):
        strategy = JudgeStrategy()
        rounds = [
            DebateRound(
                round_number=1,
                participant_id="a1",
                input_prompt="Topic",
                response="Response A",
            ),
        ]
        participants = [
            DebateParticipant(id="a1", name="A1", agent_type="custom"),
            DebateParticipant(id="judge", name="Judge", agent_type="custom", role="judge"),
        ]

        consensus, score = strategy.evaluate(rounds, participants)
        assert consensus == "Response A"
        assert score > 0


class TestMaxRoundsLimit:
    """Tests for max rounds limit."""

    def test_max_rounds_enforced(self):
        engine = DebateEngine()
        engine.register_executor("custom", lambda p, i: "Response")

        participants = [
            DebateParticipant(id="a1", name="Agent 1", agent_type="custom"),
        ]

        result = engine.debate(
            topic="Topic",
            participants=participants,
            config=ConsensusConfig(max_rounds=2, stop_on_consensus=False),
        )

        max_round = max(r.round_number for r in result.rounds)
        assert max_round <= 2


class TestCostLimitEnforcement:
    """Tests for cost limit enforcement."""

    def test_cost_limit(self):
        engine = DebateEngine()
        engine.register_executor("custom", lambda p, i: "Response")

        participants = [
            DebateParticipant(
                id="a1",
                name="Agent 1",
                agent_type="custom",
                config={"cost": 5.0},
            ),
            DebateParticipant(
                id="a2",
                name="Agent 2",
                agent_type="custom",
                config={"cost": 5.0},
            ),
        ]

        result = engine.debate(
            topic="Topic",
            participants=participants,
            config=ConsensusConfig(cost_limit=8.0, max_rounds=5),
        )

        assert result.status == "cost_limit_reached"
        assert result.total_cost >= 8.0


class TestStopOnConsensus:
    """Tests for stop on consensus."""

    def test_stop_on_consensus(self):
        engine = DebateEngine()
        engine.register_executor("custom", lambda p, i: "Agreed response")

        participants = [
            DebateParticipant(id="a1", name="A1", agent_type="custom"),
            DebateParticipant(id="a2", name="A2", agent_type="custom"),
        ]

        result = engine.debate(
            topic="Topic",
            participants=participants,
            config=ConsensusConfig(
                method="unanimous",
                max_rounds=5,
                min_agreement_threshold=1.0,
                stop_on_consensus=True,
            ),
        )

        assert result.status == "consensus_reached"


class TestGovernanceApplied:
    """Tests for governance applied to responses."""

    def test_governance_on_responses(self):
        engine = DebateEngine()
        engine.register_executor("custom", lambda p, i: "Response with test@example.com")

        participants = [
            DebateParticipant(id="a1", name="A1", agent_type="custom"),
        ]

        result = engine.debate(
            topic="Topic",
            participants=participants,
            config=ConsensusConfig(max_rounds=1),
        )

        assert len(result.receipt_ids) >= 1


class TestComplianceReceiptsGenerated:
    """Tests for compliance receipt generation."""

    def test_receipts_per_response(self):
        engine = DebateEngine()
        engine.register_executor("custom", lambda p, i: "Response")

        participants = [
            DebateParticipant(id="a1", name="A1", agent_type="custom"),
            DebateParticipant(id="a2", name="A2", agent_type="custom"),
        ]

        result = engine.debate(
            topic="Topic",
            participants=participants,
            config=ConsensusConfig(max_rounds=1),
        )

        assert len(result.receipt_ids) == len(result.rounds)


class TestDebateTemplates:
    """Tests for pre-built debate templates."""

    def test_two_agent_critique_template(self):
        participants, config = two_agent_critique()
        assert len(participants) == 3
        assert any(p.role == "synthesizer" for p in participants)
        assert config.method == "synthesis"

    def test_three_way_debate_template(self):
        participants, config = three_way_debate()
        assert len(participants) == 4
        assert any(p.role == "judge" for p in participants)
        assert config.method == "judge"

    def test_expert_panel_template(self):
        participants, config = expert_panel()
        assert len(participants) == 4
        assert config.method == "voting"
        weights = [p.weight for p in participants]
        assert max(weights) == 2.0
        assert min(weights) == 0.5


class TestAgreementScoreCalculation:
    """Tests for agreement score calculation."""

    def test_unanimous_agreement(self):
        strategy = UnanimousStrategy()
        rounds = [
            DebateRound(
                round_number=1,
                participant_id="a1",
                input_prompt="Topic",
                response="Same",
            ),
            DebateRound(
                round_number=1,
                participant_id="a2",
                input_prompt="Topic",
                response="Same",
            ),
        ]
        participants = [
            DebateParticipant(id="a1", name="A1", agent_type="custom"),
            DebateParticipant(id="a2", name="A2", agent_type="custom"),
        ]

        _, score = strategy.evaluate(rounds, participants)
        assert score == 1.0

    def test_no_agreement(self):
        strategy = UnanimousStrategy()
        rounds = [
            DebateRound(
                round_number=1,
                participant_id="a1",
                input_prompt="Topic",
                response="View A",
            ),
            DebateRound(
                round_number=1,
                participant_id="a2",
                input_prompt="Topic",
                response="View B",
            ),
        ]
        participants = [
            DebateParticipant(id="a1", name="A1", agent_type="custom"),
            DebateParticipant(id="a2", name="A2", agent_type="custom"),
        ]

        _, score = strategy.evaluate(rounds, participants)
        assert score < 1.0
