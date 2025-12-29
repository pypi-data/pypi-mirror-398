"""Match tasks to best-suited agents."""

from typing import Dict, List, Optional, Tuple

import structlog

from tork.capabilities.models import AgentProfile, PerformanceMetric
from tork.capabilities.registry import CapabilityRegistry

logger = structlog.get_logger(__name__)


class TaskMatcher:
    """Match tasks to best-suited agents."""

    def __init__(self, registry: CapabilityRegistry):
        """
        Initialize the task matcher.

        Args:
            registry: The CapabilityRegistry to use for lookups.
        """
        self._registry = registry

    def match(
        self,
        task_description: str,
        required_capabilities: Optional[List[str]] = None,
    ) -> List[AgentProfile]:
        """
        Find agents matching task requirements.

        Args:
            task_description: Description of the task.
            required_capabilities: List of required capability names.

        Returns:
            List of matching AgentProfiles.
        """
        task_lower = task_description.lower()

        profiles = self._registry.list()
        if not required_capabilities:
            results = []
            for profile in profiles:
                for best in profile.best_for:
                    if best.lower() in task_lower or task_lower in best.lower():
                        results.append(profile)
                        break
                else:
                    for cap in profile.capabilities:
                        if cap.name.lower() in task_lower:
                            results.append(profile)
                            break
            return results

        matching = []
        for profile in profiles:
            has_all = True
            for req in required_capabilities:
                if profile.get_capability(req) is None:
                    has_all = False
                    break
            if has_all:
                matching.append(profile)

        return matching

    def rank(
        self,
        profiles: List[AgentProfile],
        criteria: Dict[PerformanceMetric, float],
    ) -> List[AgentProfile]:
        """
        Rank agents by weighted criteria.

        Args:
            profiles: List of profiles to rank.
            criteria: Dictionary mapping PerformanceMetric to weight (0-1).

        Returns:
            Profiles sorted by weighted score (highest first).
        """
        def calculate_score(profile: AgentProfile) -> float:
            total = 0.0
            weight_sum = 0.0
            for metric, weight in criteria.items():
                if metric in profile.performance:
                    total += profile.performance[metric] * weight
                    weight_sum += weight
            return total / weight_sum if weight_sum > 0 else 0.0

        scored = [(profile, calculate_score(profile)) for profile in profiles]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [p for p, _ in scored]

    def recommend(
        self,
        task: str,
        top_n: int = 3,
    ) -> List[Tuple[AgentProfile, float]]:
        """
        Recommend top N agents with confidence scores.

        Args:
            task: Task description.
            top_n: Number of recommendations.

        Returns:
            List of (AgentProfile, confidence_score) tuples.
        """
        task_lower = task.lower()
        all_profiles = self._registry.list()

        scored_profiles: List[Tuple[AgentProfile, float]] = []

        for profile in all_profiles:
            score = 0.0

            for best in profile.best_for:
                if best.lower() in task_lower or task_lower in best.lower():
                    score += 0.4
                    break

            for strength in profile.strengths:
                if strength.lower() in task_lower:
                    score += 0.15

            for avoid in profile.avoid_for:
                if avoid.lower() in task_lower or task_lower in avoid.lower():
                    score -= 0.3
                    break

            for weakness in profile.weaknesses:
                if weakness.lower() in task_lower:
                    score -= 0.1

            for cap in profile.capabilities:
                if cap.name.lower() in task_lower:
                    score += cap.score * 0.3
                    break

            if profile.performance:
                avg_perf = sum(profile.performance.values()) / len(profile.performance)
                score += avg_perf * 0.2

            score = max(0.0, min(1.0, score))
            scored_profiles.append((profile, score))

        scored_profiles.sort(key=lambda x: x[1], reverse=True)

        return scored_profiles[:top_n]
