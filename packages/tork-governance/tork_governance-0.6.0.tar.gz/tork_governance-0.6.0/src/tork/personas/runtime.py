"""Execute personas with governance."""

from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

import structlog

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest, PolicyDecision
from tork.compliance.receipts import ReceiptGenerator
from tork.personas.models import PersonaConfig, PersonaInstance
from tork.personas.store import PersonaStore

logger = structlog.get_logger(__name__)


class CostLimitExceededError(Exception):
    """Raised when max cost per request is exceeded."""
    pass


class BlockedActionError(Exception):
    """Raised when a blocked action is attempted."""
    pass


class InstanceNotFoundError(Exception):
    """Raised when an instance is not found."""
    pass


class PersonaRuntime:
    """Execute personas with governance."""

    def __init__(
        self,
        store: Optional[PersonaStore] = None,
        governance_engine: Optional[GovernanceEngine] = None,
        signing_key: str = "persona-secret",
    ):
        """
        Initialize the persona runtime.

        Args:
            store: PersonaStore for retrieving configs.
            governance_engine: GovernanceEngine for policy evaluation.
            signing_key: Key for signing compliance receipts.
        """
        self.store = store or PersonaStore()
        self.governance_engine = governance_engine or GovernanceEngine()
        self.receipt_generator = ReceiptGenerator(signing_key=signing_key)
        self._instances: Dict[str, PersonaInstance] = {}
        self._persona_cache: Dict[str, PersonaConfig] = {}
        self._executor: Optional[Callable] = None

        logger.info("PersonaRuntime initialized")

    def set_executor(self, executor: Callable[[str, str, Dict], Dict]) -> None:
        """
        Set the LLM executor function.

        Args:
            executor: Function(system_prompt, input_text, context) -> Dict with 'output', 'tokens', 'cost'
        """
        self._executor = executor

    def instantiate(
        self,
        persona_id: str,
        session_id: Optional[str] = None,
    ) -> PersonaInstance:
        """
        Create a running instance of a persona.

        Args:
            persona_id: The persona configuration ID.
            session_id: Optional session identifier.

        Returns:
            The created PersonaInstance.
        """
        persona = self.store.get(persona_id)
        self._persona_cache[persona_id] = persona

        instance = PersonaInstance(
            id=str(uuid4()),
            persona_id=persona_id,
            session_id=session_id or str(uuid4()),
        )
        self._instances[instance.id] = instance

        logger.info("Persona instantiated", instance_id=instance.id, persona_id=persona_id)
        return instance

    def execute(
        self,
        instance_id: str,
        input_text: str,
        context: Optional[Dict[str, Any]] = None,
        estimated_cost: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Execute a persona instance with input.

        Args:
            instance_id: The instance identifier.
            input_text: User input text.
            context: Optional additional context.
            estimated_cost: Estimated cost for this request.

        Returns:
            Dict with 'output', 'tokens', 'cost', 'receipt'.
        """
        if instance_id not in self._instances:
            raise InstanceNotFoundError(f"Instance '{instance_id}' not found")

        instance = self._instances[instance_id]
        persona = self._get_persona_config(instance.persona_id)

        if estimated_cost > persona.max_cost_per_request:
            raise CostLimitExceededError(
                f"Estimated cost {estimated_cost} exceeds max {persona.max_cost_per_request}"
            )

        if context:
            action = context.get("action", "")
            if action and action in persona.blocked_actions:
                raise BlockedActionError(f"Action '{action}' is blocked for this persona")
            if persona.allowed_actions and action not in persona.allowed_actions:
                raise BlockedActionError(f"Action '{action}' is not allowed for this persona")

        request = EvaluationRequest(
            payload={"input": input_text, "context": context or {}},
            agent_id=instance.persona_id,
            action="persona_input",
        )
        input_result = self.governance_engine.evaluate(request)

        if input_result.decision == PolicyDecision.DENY:
            return {
                "output": None,
                "tokens": 0,
                "cost": 0.0,
                "blocked": True,
                "reason": "Input blocked by governance",
            }

        processed_input = input_text
        if input_result.decision == PolicyDecision.REDACT and input_result.modified_payload:
            processed_input = input_result.modified_payload.get("input", input_text)

        output = ""
        tokens = 0
        cost = 0.0

        if self._executor:
            result = self._executor(persona.system_prompt, processed_input, context or {})
            output = result.get("output", "")
            tokens = result.get("tokens", 0)
            cost = result.get("cost", 0.0)
        else:
            output = f"[Persona: {persona.name}] Processed: {processed_input}"
            tokens = len(processed_input.split())
            cost = tokens * 0.00001

        output_request = EvaluationRequest(
            payload={"output": output},
            agent_id=instance.persona_id,
            action="persona_output",
        )
        output_result = self.governance_engine.evaluate(output_request)

        if output_result.decision == PolicyDecision.DENY:
            output = "[Output blocked by governance]"
        elif output_result.decision == PolicyDecision.REDACT and output_result.modified_payload:
            output = output_result.modified_payload.get("output", output)

        receipt = self.receipt_generator.create_receipt(output_result, output_request)

        instance.messages_count += 1
        instance.total_tokens += tokens
        instance.total_cost += cost

        return {
            "output": output,
            "tokens": tokens,
            "cost": cost,
            "blocked": False,
            "receipt": receipt,
        }

    def _get_persona_config(self, persona_id: str) -> PersonaConfig:
        """Get persona config from cache or store."""
        if persona_id in self._persona_cache:
            return self._persona_cache[persona_id]

        persona = self.store.get(persona_id)
        self._persona_cache[persona_id] = persona
        return persona

    def get_instance(self, instance_id: str) -> PersonaInstance:
        """
        Get an active instance.

        Args:
            instance_id: The instance identifier.

        Returns:
            The PersonaInstance.
        """
        if instance_id not in self._instances:
            raise InstanceNotFoundError(f"Instance '{instance_id}' not found")
        return self._instances[instance_id]

    def terminate(self, instance_id: str) -> bool:
        """
        Terminate a persona instance.

        Args:
            instance_id: The instance to terminate.

        Returns:
            True if terminated, False if not found.
        """
        if instance_id in self._instances:
            del self._instances[instance_id]
            logger.info("Persona instance terminated", instance_id=instance_id)
            return True
        return False

    def list_instances(self, persona_id: Optional[str] = None) -> List[PersonaInstance]:
        """
        List active instances.

        Args:
            persona_id: Optional filter by persona ID.

        Returns:
            List of active instances.
        """
        instances = list(self._instances.values())
        if persona_id:
            instances = [i for i in instances if i.persona_id == persona_id]
        return instances
