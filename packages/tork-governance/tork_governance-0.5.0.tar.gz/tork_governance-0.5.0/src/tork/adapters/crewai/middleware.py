from __future__ import annotations
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tork.adapters.crewai.governed import GovernedAgent, GovernedCrew

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest
from tork.core.redactor import PIIRedactor
from tork.compliance.receipts import ReceiptGenerator
from tork.adapters.crewai.exceptions import GovernanceBlockedError, PIIDetectedError

class TorkCrewAIMiddleware:
    """Middleware to integrate Tork governance with CrewAI agents."""
    
    def __init__(self, engine: Optional[GovernanceEngine] = None, agent_id: Optional[str] = None):
        self.engine = engine or GovernanceEngine()
        self.agent_id = agent_id or "crewai-agent"
        self.redactor = PIIRedactor()
        self.receipt_generator = ReceiptGenerator(signing_key="default-secret")

    def wrap_agent(self, agent: Any) -> "GovernedAgent":
        """Wrap a CrewAI agent with governance controls."""
        from tork.adapters.crewai.governed import GovernedAgent
        return GovernedAgent(agent, self)

    def wrap_crew(self, crew: Any) -> "GovernedCrew":
        """Wrap an entire CrewAI crew with governance."""
        from tork.adapters.crewai.governed import GovernedCrew
        return GovernedCrew(crew, self)

    def before_task(self, task: Any, agent: Any) -> Dict[str, Any]:
        """Called before a task is executed."""
        # Handle CrewAI task object which usually has a 'description' or similar
        description = getattr(task, "description", str(task))
        
        request = EvaluationRequest(
            payload={"task_description": description},
            agent_id=self.agent_id,
            action="ALLOW"
        )
        result = self.engine.evaluate(request)
        
        if result.decision.value == "deny":
            raise GovernanceBlockedError(f"Task blocked by policy: {result.violations}")
        
        # If engine didn't catch it but we want strict PII check:
        if result.violations and any("pii_detect" in str(v) for v in result.violations):
             raise PIIDetectedError("PII detected in task input and blocked.")

        return result.modified_payload or request.payload

    def after_task(self, task: Any, result_text: str, agent: Any) -> Dict[str, Any]:
        """Called after task completion."""
        request = EvaluationRequest(
            payload={"output": result_text},
            agent_id=self.agent_id,
            action="ALLOW"
        )
        eval_result = self.engine.evaluate(request)
        
        if eval_result.decision.value == "deny":
             raise GovernanceBlockedError(f"Task output blocked by policy: {eval_result.violations}")

        receipt = self.receipt_generator.generate(
            result=eval_result,
            request=request
        )
        
        modified_output = eval_result.modified_payload.get("output", result_text) if eval_result.modified_payload else result_text
        
        return {
            "result": modified_output,
            "receipt": receipt.model_dump()
        }
