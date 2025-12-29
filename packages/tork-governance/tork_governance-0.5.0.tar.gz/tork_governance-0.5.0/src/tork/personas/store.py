"""Store and manage persona configurations."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
import yaml

from tork.personas.models import PersonaCapability, PersonaConfig

logger = structlog.get_logger(__name__)


class PersonaNotFoundError(Exception):
    """Raised when a persona is not found."""
    pass


class PersonaStore:
    """Store and manage persona configurations."""

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the persona store.

        Args:
            storage_path: Optional path for file-based storage.
        """
        self._personas: Dict[str, PersonaConfig] = {}
        self._storage_path = Path(storage_path) if storage_path else None

        if self._storage_path and self._storage_path.exists():
            self._load_from_file()

        logger.info("PersonaStore initialized", storage_path=storage_path)

    def _load_from_file(self) -> None:
        """Load personas from storage file."""
        if not self._storage_path or not self._storage_path.exists():
            return

        try:
            with open(self._storage_path, "r") as f:
                data = json.load(f)
                for persona_data in data.get("personas", []):
                    persona = PersonaConfig(**persona_data)
                    self._personas[persona.id] = persona
            logger.info("Loaded personas from file", count=len(self._personas))
        except Exception as e:
            logger.error("Failed to load personas", error=str(e))

    def _save_to_file(self) -> None:
        """Save personas to storage file."""
        if not self._storage_path:
            return

        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"personas": [p.model_dump(mode="json") for p in self._personas.values()]}
            with open(self._storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save personas", error=str(e))

    def save(self, persona: PersonaConfig) -> str:
        """
        Save a persona configuration.

        Args:
            persona: The persona configuration to save.

        Returns:
            The persona ID.
        """
        persona.updated_at = datetime.utcnow()
        self._personas[persona.id] = persona
        self._save_to_file()
        logger.info("Persona saved", persona_id=persona.id)
        return persona.id

    def get(self, persona_id: str) -> PersonaConfig:
        """
        Get a persona by ID.

        Args:
            persona_id: The persona identifier.

        Returns:
            The PersonaConfig.

        Raises:
            PersonaNotFoundError: If persona not found.
        """
        if persona_id not in self._personas:
            raise PersonaNotFoundError(f"Persona '{persona_id}' not found")
        return self._personas[persona_id]

    def list(
        self,
        tags: Optional[List[str]] = None,
        capabilities: Optional[List[PersonaCapability]] = None,
    ) -> List[PersonaConfig]:
        """
        List personas with optional filtering.

        Args:
            tags: Filter by tags (any match).
            capabilities: Filter by capabilities (any match).

        Returns:
            List of matching personas.
        """
        result = list(self._personas.values())

        if tags:
            result = [p for p in result if any(t in p.tags for t in tags)]

        if capabilities:
            result = [p for p in result if any(c in p.capabilities for c in capabilities)]

        return result

    def delete(self, persona_id: str) -> bool:
        """
        Delete a persona.

        Args:
            persona_id: The persona to delete.

        Returns:
            True if deleted, False if not found.
        """
        if persona_id in self._personas:
            del self._personas[persona_id]
            self._save_to_file()
            logger.info("Persona deleted", persona_id=persona_id)
            return True
        return False

    def update(self, persona_id: str, updates: Dict[str, Any]) -> PersonaConfig:
        """
        Update a persona configuration.

        Args:
            persona_id: The persona to update.
            updates: Dictionary of fields to update.

        Returns:
            The updated PersonaConfig.

        Raises:
            PersonaNotFoundError: If persona not found.
        """
        if persona_id not in self._personas:
            raise PersonaNotFoundError(f"Persona '{persona_id}' not found")

        persona = self._personas[persona_id]
        persona_data = persona.model_dump()
        persona_data.update(updates)
        persona_data["updated_at"] = datetime.utcnow()

        updated_persona = PersonaConfig(**persona_data)
        self._personas[persona_id] = updated_persona
        self._save_to_file()

        return updated_persona

    def export(self, persona_id: str, format: str = "json") -> str:
        """
        Export persona as JSON or YAML.

        Args:
            persona_id: The persona to export.
            format: Export format ("json" or "yaml").

        Returns:
            Serialized persona string.

        Raises:
            PersonaNotFoundError: If persona not found.
        """
        persona = self.get(persona_id)
        data = persona.model_dump(mode="json")

        if format == "yaml":
            return yaml.dump(data, default_flow_style=False, sort_keys=False)
        return json.dumps(data, indent=2, default=str)

    def import_persona(self, data: str, format: str = "json") -> PersonaConfig:
        """
        Import persona from JSON or YAML.

        Args:
            data: Serialized persona data.
            format: Import format ("json" or "yaml").

        Returns:
            The imported PersonaConfig.
        """
        if format == "yaml":
            parsed = yaml.safe_load(data)
        else:
            parsed = json.loads(data)

        persona = PersonaConfig(**parsed)
        self.save(persona)
        return persona
