"""Debate engine for multi-agent consensus building."""

import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import structlog

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest, PolicyDecision
from tork.compliance.receipts import ReceiptGenerator
from tork.consensus.models import (
    DebateParticipant,
    DebateRound,
    ConsensusConfig,
    DebateResult,
)
from tork.consensus.strategies import (
    ConsensusStrategy,
    SynthesisStrategy,
    VotingStrategy,
    JudgeStrategy,
    UnanimousStrategy,
)

logger = structlog.get_logger(__name__)


class DebateEngine:
    """Orchestrate multi-agent debates with consensus building."""

    def __init__(
        self,
        governance_engine: Optional[GovernanceEngine] = None,
        signing_key: str = "debate-secret",
    ):
        """
        Initialize the debate engine.

        Args:
            governance_engine: Optional GovernanceEngine for policy evaluation.
            signing_key: Key for signing compliance receipts.
        """
        self.governance_engine = governance_engine or GovernanceEngine()
        self.receipt_generator = ReceiptGenerator(signing_key=signing_key)
        self._executors: Dict[str, Callable] = {}
        self._strategies: Dict[str, ConsensusStrategy] = {
            "synthesis": SynthesisStrategy(),
            "voting": VotingStrategy(),
            "judge": JudgeStrategy(),
            "unanimous": UnanimousStrategy(),
        }
        logger.info("DebateEngine initialized")

    def register_executor(self, agent_type: str, executor: Callable) -> None:
        """
        Register an executor for an agent type.

        Args:
            agent_type: Type identifier (e.g., 'langchain', 'custom').
            executor: Callable that executes the agent. Signature: (participant, inputs) -> response.
        """
        self._executors[agent_type] = executor
        logger.info("Executor registered", agent_type=agent_type)

    def debate(
        self,
        topic: str,
        participants: List[DebateParticipant],
        config: Optional[ConsensusConfig] = None,
        initial_context: str = "",
    ) -> DebateResult:
        """
        Run a debate session.

        Args:
            topic: The debate topic or question.
            participants: List of debate participants.
            config: Consensus configuration.
            initial_context: Additional context for the debate.

        Returns:
            DebateResult with all rounds and final consensus.
        """
        config = config or ConsensusConfig()
        session_id = str(uuid.uuid4())[:8]
        all_rounds: List[DebateRound] = []
        receipt_ids: List[str] = []
        total_tokens = 0
        total_cost = 0.0

        debaters = [p for p in participants if p.role == "debater"]
        critics = [p for p in participants if p.role == "critic"]

        for round_num in range(1, config.max_rounds + 1):
            if total_cost >= config.cost_limit:
                return DebateResult(
                    session_id=session_id,
                    status="cost_limit_reached",
                    rounds=all_rounds,
                    total_tokens=total_tokens,
                    total_cost=total_cost,
                    receipt_ids=receipt_ids,
                )

            if round_num == 1:
                context = f"Topic: {topic}\n\n{initial_context}".strip()
                round_rounds, round_receipts, round_tokens, round_cost = self._run_governed_round(
                    round_num, debaters, context, session_id
                )
            else:
                previous_responses = "\n\n".join(
                    f"[{r.participant_id}]: {r.response}"
                    for r in all_rounds
                    if r.round_number == round_num - 1
                )
                context = f"Topic: {topic}\n\nPrevious responses:\n{previous_responses}"

                critique_participants = critics if critics else debaters
                round_rounds, round_receipts, round_tokens, round_cost = self._run_governed_critique_round(
                    round_num, critique_participants, context, all_rounds, session_id
                )

            all_rounds.extend(round_rounds)
            receipt_ids.extend(round_receipts)
            total_tokens += round_tokens
            total_cost += round_cost

            if total_cost >= config.cost_limit:
                return DebateResult(
                    session_id=session_id,
                    status="cost_limit_reached",
                    rounds=all_rounds,
                    total_tokens=total_tokens,
                    total_cost=total_cost,
                    receipt_ids=receipt_ids,
                )

            consensus_reached, agreement_score = self._check_consensus(
                all_rounds, config, participants
            )

            if consensus_reached and config.stop_on_consensus:
                final_consensus, consensus_receipts, consensus_tokens, consensus_cost = self._build_governed_consensus(
                    all_rounds, participants, config, session_id
                )
                receipt_ids.extend(consensus_receipts)
                total_tokens += consensus_tokens
                total_cost += consensus_cost
                
                return DebateResult(
                    session_id=session_id,
                    status="consensus_reached",
                    rounds=all_rounds,
                    final_consensus=final_consensus,
                    agreement_score=agreement_score,
                    total_tokens=total_tokens,
                    total_cost=total_cost,
                    receipt_ids=receipt_ids,
                )

        final_consensus, consensus_receipts, consensus_tokens, consensus_cost = self._build_governed_consensus(
            all_rounds, participants, config, session_id
        )
        receipt_ids.extend(consensus_receipts)
        total_tokens += consensus_tokens
        total_cost += consensus_cost
        _, agreement_score = self._check_consensus(all_rounds, config, participants)

        return DebateResult(
            session_id=session_id,
            status="max_rounds_reached",
            rounds=all_rounds,
            final_consensus=final_consensus,
            agreement_score=agreement_score,
            total_tokens=total_tokens,
            total_cost=total_cost,
            receipt_ids=receipt_ids,
        )

    def _apply_governance(
        self,
        response: str,
        participant_id: str,
        session_id: str,
    ) -> Tuple[str, str, bool]:
        """
        Apply governance to a response and return governed output.

        Returns:
            Tuple of (governed_response, receipt_id, is_denied)
        """
        request = EvaluationRequest(
            payload={"response": response, "participant": participant_id},
            agent_id=f"debate-{session_id}",
            action="debate_response",
        )
        result = self.governance_engine.evaluate(request)
        receipt = self.receipt_generator.create_receipt(result, request)

        if result.decision == PolicyDecision.DENY:
            return "[Response blocked by governance policy]", receipt.receipt_id, True
        elif result.decision == PolicyDecision.REDACT and result.modified_payload:
            governed_response = result.modified_payload.get("response", response)
            return governed_response, receipt.receipt_id, False
        else:
            return response, receipt.receipt_id, False

    def _run_governed_round(
        self,
        round_num: int,
        participants: List[DebateParticipant],
        context: str,
        session_id: str,
    ) -> Tuple[List[DebateRound], List[str], int, float]:
        """Run a governed debate round."""
        rounds = []
        receipt_ids = []
        total_tokens = 0
        total_cost = 0.0

        for participant in participants:
            executor = self._executors.get(participant.agent_type)
            if not executor:
                response = f"[No executor for {participant.agent_type}]"
                tokens = 0
                cost = 0.0
            else:
                try:
                    response = executor(participant, {"prompt": context})
                    tokens = participant.config.get("tokens_used", 0)
                    cost = participant.config.get("cost", 0.0)
                except Exception as e:
                    response = f"[Error: {str(e)}]"
                    tokens = 0
                    cost = 0.0

            governed_response, receipt_id, _ = self._apply_governance(
                response, participant.id, session_id
            )
            receipt_ids.append(receipt_id)
            total_tokens += tokens
            total_cost += cost

            rounds.append(
                DebateRound(
                    round_number=round_num,
                    participant_id=participant.id,
                    input_prompt=context,
                    response=governed_response,
                    timestamp=datetime.now(),
                    tokens_used=tokens,
                    cost=cost,
                )
            )

        return rounds, receipt_ids, total_tokens, total_cost

    def _run_governed_critique_round(
        self,
        round_num: int,
        participants: List[DebateParticipant],
        context: str,
        previous_rounds: List[DebateRound],
        session_id: str,
    ) -> Tuple[List[DebateRound], List[str], int, float]:
        """Run a governed critique round."""
        rounds = []
        receipt_ids = []
        total_tokens = 0
        total_cost = 0.0
        
        previous_round_responses = [
            r for r in previous_rounds if r.round_number == round_num - 1
        ]

        for participant in participants:
            for prev_response in previous_round_responses:
                if prev_response.participant_id == participant.id:
                    continue

                critique_prompt = (
                    f"{context}\n\n"
                    f"Critique the response from {prev_response.participant_id}:\n"
                    f'"{prev_response.response}"'
                )

                executor = self._executors.get(participant.agent_type)
                if not executor:
                    response = f"[No executor for {participant.agent_type}]"
                    tokens = 0
                    cost = 0.0
                else:
                    try:
                        response = executor(participant, {"prompt": critique_prompt})
                        tokens = participant.config.get("tokens_used", 0)
                        cost = participant.config.get("cost", 0.0)
                    except Exception as e:
                        response = f"[Error: {str(e)}]"
                        tokens = 0
                        cost = 0.0

                governed_response, receipt_id, _ = self._apply_governance(
                    response, participant.id, session_id
                )
                receipt_ids.append(receipt_id)
                total_tokens += tokens
                total_cost += cost

                rounds.append(
                    DebateRound(
                        round_number=round_num,
                        participant_id=participant.id,
                        input_prompt=critique_prompt,
                        response=governed_response,
                        critique_of=prev_response.participant_id,
                        timestamp=datetime.now(),
                        tokens_used=tokens,
                        cost=cost,
                    )
                )

        return rounds, receipt_ids, total_tokens, total_cost

    def _check_consensus(
        self,
        rounds: List[DebateRound],
        config: ConsensusConfig,
        participants: List[DebateParticipant],
    ) -> Tuple[bool, float]:
        """Check if consensus has been reached."""
        if not rounds:
            return False, 0.0

        strategy = self._strategies.get(config.method, SynthesisStrategy())
        _, agreement_score = strategy.evaluate(rounds, participants, None)

        return agreement_score >= config.min_agreement_threshold, agreement_score

    def _build_governed_consensus(
        self,
        rounds: List[DebateRound],
        participants: List[DebateParticipant],
        config: ConsensusConfig,
        session_id: str,
    ) -> Tuple[str, List[str], int, float]:
        """Build final consensus with governance applied."""
        if not rounds:
            return "", [], 0, 0.0

        strategy = self._strategies.get(config.method, SynthesisStrategy())
        receipt_ids = []
        total_tokens = 0
        total_cost = 0.0

        def governed_executor(participant: DebateParticipant, inputs: Dict[str, Any]) -> str:
            nonlocal total_tokens, total_cost, receipt_ids
            executor = self._executors.get(participant.agent_type)
            if not executor:
                return ""
            
            response = executor(participant, inputs)
            tokens = participant.config.get("tokens_used", 0)
            cost = participant.config.get("cost", 0.0)
            total_tokens += tokens
            total_cost += cost

            governed_response, receipt_id, _ = self._apply_governance(
                response, participant.id, session_id
            )
            receipt_ids.append(receipt_id)
            return governed_response

        consensus, _ = strategy.evaluate(rounds, participants, governed_executor)
        return consensus, receipt_ids, total_tokens, total_cost
