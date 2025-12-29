"""Registry of agent capability profiles."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from tork.capabilities.models import AgentProfile

logger = structlog.get_logger(__name__)


class ProfileNotFoundError(Exception):
    """Raised when a profile is not found."""
    pass


class CapabilityRegistry:
    """Registry of agent capability profiles."""

    def __init__(self):
        """Initialize the registry."""
        self._profiles: Dict[str, AgentProfile] = {}
        logger.info("CapabilityRegistry initialized")

    def register(self, profile: AgentProfile) -> str:
        """
        Register an agent profile.

        Args:
            profile: The AgentProfile to register.

        Returns:
            The agent ID.
        """
        profile.updated_at = datetime.utcnow()
        self._profiles[profile.agent_id] = profile
        logger.info("Profile registered", agent_id=profile.agent_id)
        return profile.agent_id

    def get(self, agent_id: str) -> AgentProfile:
        """
        Get a profile by agent ID.

        Args:
            agent_id: The agent identifier.

        Returns:
            The AgentProfile.

        Raises:
            ProfileNotFoundError: If profile not found.
        """
        if agent_id not in self._profiles:
            raise ProfileNotFoundError(f"Profile '{agent_id}' not found")
        return self._profiles[agent_id]

    def list(
        self,
        provider: Optional[str] = None,
        capability: Optional[str] = None,
        min_score: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ) -> List[AgentProfile]:
        """
        List profiles with filtering.

        Args:
            provider: Filter by provider name.
            capability: Filter by capability name.
            min_score: Minimum capability score.
            tags: Filter by tags (any match).

        Returns:
            List of matching profiles.
        """
        result = list(self._profiles.values())

        if provider:
            result = [p for p in result if p.provider.lower() == provider.lower()]

        if capability:
            if min_score is not None:
                result = [
                    p for p in result
                    if p.get_capability_score(capability) >= min_score
                ]
            else:
                result = [
                    p for p in result
                    if p.get_capability(capability) is not None
                ]

        if tags:
            result = [p for p in result if any(t in p.tags for t in tags)]

        return result

    def find_best_for(self, task: str) -> List[AgentProfile]:
        """
        Find agents best suited for a task.

        Args:
            task: Task description to match.

        Returns:
            List of profiles suited for the task.
        """
        task_lower = task.lower()
        result = []

        for profile in self._profiles.values():
            for best in profile.best_for:
                if best.lower() in task_lower or task_lower in best.lower():
                    result.append(profile)
                    break

        return result

    def compare(
        self,
        agent_ids: List[str],
        capability: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare capabilities across agents.

        Args:
            agent_ids: List of agent IDs to compare.
            capability: Optional specific capability to compare.

        Returns:
            Comparison dictionary with scores.
        """
        comparison: Dict[str, Any] = {"agents": {}, "winner": None}

        profiles = []
        for agent_id in agent_ids:
            if agent_id in self._profiles:
                profiles.append(self._profiles[agent_id])

        if not profiles:
            return comparison

        best_score = -1.0
        best_agent = None

        for profile in profiles:
            if capability:
                score = profile.get_capability_score(capability)
                comparison["agents"][profile.agent_id] = {
                    "name": profile.name,
                    "score": score,
                }
                if score > best_score:
                    best_score = score
                    best_agent = profile.agent_id
            else:
                caps = {c.name: c.score for c in profile.capabilities}
                avg_score = sum(caps.values()) / len(caps) if caps else 0.0
                comparison["agents"][profile.agent_id] = {
                    "name": profile.name,
                    "capabilities": caps,
                    "average_score": avg_score,
                }
                if avg_score > best_score:
                    best_score = avg_score
                    best_agent = profile.agent_id

        comparison["winner"] = best_agent
        return comparison

    def update(self, agent_id: str, updates: Dict[str, Any]) -> AgentProfile:
        """
        Update a profile.

        Args:
            agent_id: The agent to update.
            updates: Dictionary of fields to update.

        Returns:
            The updated AgentProfile.

        Raises:
            ProfileNotFoundError: If profile not found.
        """
        if agent_id not in self._profiles:
            raise ProfileNotFoundError(f"Profile '{agent_id}' not found")

        profile = self._profiles[agent_id]
        profile_data = profile.model_dump()
        profile_data.update(updates)
        profile_data["updated_at"] = datetime.utcnow()

        updated_profile = AgentProfile(**profile_data)
        self._profiles[agent_id] = updated_profile

        return updated_profile

    def delete(self, agent_id: str) -> bool:
        """
        Delete a profile.

        Args:
            agent_id: The agent to delete.

        Returns:
            True if deleted, False if not found.
        """
        if agent_id in self._profiles:
            del self._profiles[agent_id]
            logger.info("Profile deleted", agent_id=agent_id)
            return True
        return False

    def count(self) -> int:
        """Return number of registered profiles."""
        return len(self._profiles)
