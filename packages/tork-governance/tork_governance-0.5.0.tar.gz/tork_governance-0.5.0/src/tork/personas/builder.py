"""Fluent builder for creating personas."""

from typing import Any, Dict
from datetime import datetime

from tork.personas.models import PersonaCapability, PersonaConfig


class PersonaBuilder:
    """Fluent builder for creating personas."""

    def __init__(self, persona_id: str, name: str):
        """
        Initialize the builder.

        Args:
            persona_id: Unique persona identifier.
            name: Display name for the persona.
        """
        self._config = PersonaConfig(
            id=persona_id,
            name=name,
            system_prompt="You are a helpful assistant.",
        )

    def with_description(self, description: str) -> "PersonaBuilder":
        """Set the persona description."""
        self._config.description = description
        return self

    def with_system_prompt(self, prompt: str) -> "PersonaBuilder":
        """Set the system prompt."""
        self._config.system_prompt = prompt
        return self

    def with_capabilities(self, *caps: PersonaCapability) -> "PersonaBuilder":
        """Add capabilities to the persona."""
        self._config.capabilities = list(caps)
        return self

    def with_preferred_models(self, *models: str) -> "PersonaBuilder":
        """Set preferred models."""
        self._config.preferred_models = list(models)
        return self

    def with_temperature(self, temp: float) -> "PersonaBuilder":
        """Set the temperature."""
        self._config.temperature = temp
        return self

    def with_max_tokens(self, tokens: int) -> "PersonaBuilder":
        """Set max tokens."""
        self._config.max_tokens = tokens
        return self

    def with_governance_policy(self, policy: str) -> "PersonaBuilder":
        """Set a custom governance policy."""
        self._config.governance_policy = policy
        return self

    def with_pii_redaction(self, enabled: bool) -> "PersonaBuilder":
        """Enable or disable PII redaction."""
        self._config.pii_redaction = enabled
        return self

    def with_allowed_actions(self, *actions: str) -> "PersonaBuilder":
        """Set allowed actions."""
        self._config.allowed_actions = list(actions)
        return self

    def with_blocked_actions(self, *actions: str) -> "PersonaBuilder":
        """Set blocked actions."""
        self._config.blocked_actions = list(actions)
        return self

    def with_max_cost(self, cost: float) -> "PersonaBuilder":
        """Set max cost per request."""
        self._config.max_cost_per_request = cost
        return self

    def with_tags(self, *tags: str) -> "PersonaBuilder":
        """Set tags."""
        self._config.tags = list(tags)
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> "PersonaBuilder":
        """Set metadata."""
        self._config.metadata = metadata
        return self

    def created_by(self, creator: str) -> "PersonaBuilder":
        """Set the creator."""
        self._config.created_by = creator
        return self

    def build(self) -> PersonaConfig:
        """Build and return the PersonaConfig."""
        self._config.updated_at = datetime.utcnow()
        return self._config
