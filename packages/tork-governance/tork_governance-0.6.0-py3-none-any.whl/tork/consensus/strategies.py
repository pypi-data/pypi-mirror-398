"""Consensus strategies for debate resolution."""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

from tork.consensus.models import DebateParticipant, DebateRound


class ConsensusStrategy(ABC):
    """Base class for consensus strategies."""

    @abstractmethod
    def evaluate(
        self,
        rounds: List[DebateRound],
        participants: List[DebateParticipant],
        executor: Optional[Callable] = None,
    ) -> Tuple[str, float]:
        """
        Evaluate and return (consensus_text, agreement_score).

        Args:
            rounds: All debate rounds.
            participants: List of participants.
            executor: Optional executor for generating synthesis/judgment.

        Returns:
            Tuple of (consensus_text, agreement_score between 0-1).
        """
        pass


class SynthesisStrategy(ConsensusStrategy):
    """Combine all viewpoints into a unified response."""

    def evaluate(
        self,
        rounds: List[DebateRound],
        participants: List[DebateParticipant],
        executor: Optional[Callable] = None,
    ) -> Tuple[str, float]:
        """Synthesize all responses into a unified consensus."""
        if not rounds:
            return "", 0.0

        synthesizer = next(
            (p for p in participants if p.role == "synthesizer"), None
        )

        if synthesizer and executor:
            all_responses = "\n\n".join(
                f"[{r.participant_id}]: {r.response}" for r in rounds
            )
            prompt = f"Synthesize these viewpoints into a unified response:\n\n{all_responses}"
            consensus = executor(synthesizer, {"prompt": prompt})
            return consensus, 0.85
        else:
            latest_round = max(r.round_number for r in rounds)
            latest_responses = [r for r in rounds if r.round_number == latest_round]
            if latest_responses:
                combined = " | ".join(r.response for r in latest_responses)
                return f"Combined viewpoints: {combined}", 0.7
            return "", 0.0


class VotingStrategy(ConsensusStrategy):
    """Weighted voting on responses."""

    def evaluate(
        self,
        rounds: List[DebateRound],
        participants: List[DebateParticipant],
        executor: Optional[Callable] = None,
    ) -> Tuple[str, float]:
        """Use weighted voting to determine consensus."""
        if not rounds:
            return "", 0.0

        participant_weights = {p.id: p.weight for p in participants}
        response_scores: dict = {}

        latest_round = max(r.round_number for r in rounds)
        latest_responses = [r for r in rounds if r.round_number == latest_round]

        for response in latest_responses:
            weight = participant_weights.get(response.participant_id, 1.0)
            response_scores[response.response] = response_scores.get(response.response, 0) + weight

        if not response_scores:
            return "", 0.0

        total_weight = sum(participant_weights.get(r.participant_id, 1.0) for r in latest_responses)
        best_response = max(response_scores.items(), key=lambda x: x[1])
        agreement_score = best_response[1] / total_weight if total_weight > 0 else 0.0

        return best_response[0], agreement_score


class JudgeStrategy(ConsensusStrategy):
    """Single judge picks the best response."""

    def evaluate(
        self,
        rounds: List[DebateRound],
        participants: List[DebateParticipant],
        executor: Optional[Callable] = None,
    ) -> Tuple[str, float]:
        """Use a judge to determine the best response."""
        if not rounds:
            return "", 0.0

        judge = next((p for p in participants if p.role == "judge"), None)

        if judge and executor:
            all_responses = "\n\n".join(
                f"[{r.participant_id}]: {r.response}" for r in rounds
            )
            prompt = f"As a judge, select the best response and explain why:\n\n{all_responses}"
            judgment = executor(judge, {"prompt": prompt})
            return judgment, 0.9
        else:
            latest_round = max(r.round_number for r in rounds)
            latest_responses = [r for r in rounds if r.round_number == latest_round]
            if latest_responses:
                return latest_responses[0].response, 0.8
            return "", 0.0


class UnanimousStrategy(ConsensusStrategy):
    """Require all participants to agree."""

    def evaluate(
        self,
        rounds: List[DebateRound],
        participants: List[DebateParticipant],
        executor: Optional[Callable] = None,
    ) -> Tuple[str, float]:
        """Check if all participants agree."""
        if not rounds:
            return "", 0.0

        latest_round = max(r.round_number for r in rounds)
        latest_responses = [r for r in rounds if r.round_number == latest_round]

        unique_responses = set(r.response.strip().lower() for r in latest_responses)

        if len(unique_responses) == 1:
            return latest_responses[0].response, 1.0
        else:
            agreement = 1.0 / len(unique_responses) if unique_responses else 0.0
            most_common = latest_responses[0].response if latest_responses else ""
            return most_common, agreement
