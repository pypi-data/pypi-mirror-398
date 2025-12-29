"""Select the best prompt from candidates."""

from typing import List, Optional

import structlog

from tork.core.engine import GovernanceEngine
from tork.prompts.models import (
    PromptCandidate,
    PromptQuality,
    PromptSelectionCriteria,
    PromptSelectionResult,
)

logger = structlog.get_logger(__name__)

QUALITY_SCORES = {
    PromptQuality.EXCELLENT: 1.0,
    PromptQuality.GOOD: 0.8,
    PromptQuality.ACCEPTABLE: 0.6,
    PromptQuality.POOR: 0.3,
    PromptQuality.REJECTED: 0.0,
}


class PromptSelector:
    """Select the best prompt from candidates."""

    def __init__(self, governance_engine: Optional[GovernanceEngine] = None):
        """
        Initialize the prompt selector.

        Args:
            governance_engine: Optional GovernanceEngine for policy evaluation.
        """
        self._governance_engine = governance_engine or GovernanceEngine()
        logger.info("PromptSelector initialized")

    def select(
        self,
        candidates: List[PromptCandidate],
        criteria: Optional[PromptSelectionCriteria] = None,
    ) -> PromptSelectionResult:
        """
        Select the best prompt based on criteria.

        Args:
            candidates: List of prompt candidates.
            criteria: Selection criteria (uses defaults if None).

        Returns:
            PromptSelectionResult with selected prompt.
        """
        if not candidates:
            raise ValueError("No candidates provided")

        criteria = criteria or PromptSelectionCriteria()
        total_evaluated = len(candidates)

        filtered = self._filter_candidates(candidates, criteria)
        if not filtered:
            filtered = [c for c in candidates if c.quality != PromptQuality.REJECTED]
            if not filtered:
                filtered = candidates

        ranked = self.rank(filtered, criteria)
        selected = ranked[0]

        reasoning = self._generate_reasoning(selected, criteria, total_evaluated)
        confidence = self._calculate_confidence(selected, ranked, criteria)

        return PromptSelectionResult(
            selected=selected,
            candidates=candidates,
            selection_reasoning=reasoning,
            confidence=confidence,
            total_evaluated=total_evaluated,
        )

    def rank(
        self,
        candidates: List[PromptCandidate],
        criteria: Optional[PromptSelectionCriteria] = None,
    ) -> List[PromptCandidate]:
        """
        Rank all candidates by quality.

        Args:
            candidates: List of prompt candidates.
            criteria: Selection criteria for scoring.

        Returns:
            Candidates sorted by score (highest first).
        """
        criteria = criteria or PromptSelectionCriteria()

        scored = [
            (candidate, self._calculate_score(candidate, criteria))
            for candidate in candidates
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [c for c, _ in scored]

    def _filter_candidates(
        self,
        candidates: List[PromptCandidate],
        criteria: PromptSelectionCriteria,
    ) -> List[PromptCandidate]:
        """Filter candidates based on criteria thresholds."""
        filtered = []

        for candidate in candidates:
            if candidate.generator_agent in criteria.blocked_generators:
                continue

            if candidate.safety_score < criteria.min_safety:
                continue

            if candidate.clarity_score < criteria.min_clarity:
                continue

            if candidate.specificity_score < criteria.min_specificity:
                continue

            if candidate.token_count > criteria.max_tokens:
                continue

            filtered.append(candidate)

        return filtered

    def _calculate_score(
        self,
        candidate: PromptCandidate,
        criteria: PromptSelectionCriteria,
    ) -> float:
        """Calculate weighted score for a candidate."""
        base_score = (
            candidate.clarity_score * criteria.clarity_weight +
            candidate.specificity_score * criteria.specificity_weight +
            candidate.safety_score * criteria.safety_weight
        )

        quality_bonus = QUALITY_SCORES.get(candidate.quality, 0.5) * 0.2

        preference_bonus = 0.0
        if candidate.generator_agent in criteria.preferred_generators:
            preference_bonus = 0.1

        return base_score + quality_bonus + preference_bonus

    def _generate_reasoning(
        self,
        selected: PromptCandidate,
        criteria: PromptSelectionCriteria,
        total: int,
    ) -> str:
        """Generate reasoning for the selection."""
        reasons = []

        reasons.append(f"Evaluated {total} candidates")
        reasons.append(f"Selected prompt from {selected.generator_agent}")
        reasons.append(f"Quality: {selected.quality.value}")
        reasons.append(
            f"Scores - Clarity: {selected.clarity_score:.2f}, "
            f"Specificity: {selected.specificity_score:.2f}, "
            f"Safety: {selected.safety_score:.2f}"
        )

        if selected.generator_agent in criteria.preferred_generators:
            reasons.append("Generator is in preferred list")

        return "; ".join(reasons)

    def _calculate_confidence(
        self,
        selected: PromptCandidate,
        ranked: List[PromptCandidate],
        criteria: PromptSelectionCriteria,
    ) -> float:
        """Calculate confidence in the selection."""
        if len(ranked) == 1:
            return 0.8

        first_score = self._calculate_score(selected, criteria)
        second_score = self._calculate_score(ranked[1], criteria) if len(ranked) > 1 else 0

        margin = first_score - second_score
        confidence = min(1.0, 0.5 + margin)

        if selected.quality in [PromptQuality.EXCELLENT, PromptQuality.GOOD]:
            confidence = min(1.0, confidence + 0.1)

        return round(confidence, 2)
