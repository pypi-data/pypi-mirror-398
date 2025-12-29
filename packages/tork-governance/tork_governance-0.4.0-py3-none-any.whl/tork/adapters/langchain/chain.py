"""
Governed Chain wrapper for LangChain.

Provides a wrapper that applies governance controls to any LangChain chain.
"""

from typing import Any, Optional, Dict
import structlog

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest, PolicyDecision
from tork.adapters.langchain.exceptions import GovernanceViolation

logger = structlog.get_logger(__name__)


class GovernedChain:
    """
    Wrapper that applies governance controls to a LangChain chain.
    
    Evaluates inputs before chain execution and outputs after,
    enforcing DENY decisions and applying REDACT modifications.
    """
    
    def __init__(
        self,
        chain: Any,
        engine: GovernanceEngine,
        identity_manager: Optional[Any] = None,
        receipt_generator: Optional[Any] = None,
        agent_id: str = "governed-chain",
    ) -> None:
        """
        Initialize the governed chain wrapper.
        
        Args:
            chain: The LangChain chain to wrap.
            engine: GovernanceEngine for policy evaluation.
            identity_manager: Optional IdentityManager for authentication.
            receipt_generator: Optional ReceiptGenerator for audit trails.
            agent_id: Agent ID for governance requests.
        """
        self.chain = chain
        self.engine = engine
        self.identity_manager = identity_manager
        self.receipt_generator = receipt_generator
        self.agent_id = agent_id
        self._receipts: list[Any] = []
        
        logger.info(
            "GovernedChain initialized",
            agent_id=agent_id,
            chain_type=type(chain).__name__,
        )
    
    @property
    def receipts(self) -> list[Any]:
        """Return list of generated receipts."""
        return self._receipts
    
    def _evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
    ) -> Any:
        """
        Evaluate payload against governance policies.
        
        Args:
            action: The action type.
            payload: Data to evaluate.
            
        Returns:
            EvaluationResult from the engine.
            
        Raises:
            GovernanceViolation: If policy decision is DENY.
        """
        request = EvaluationRequest(
            agent_id=self.agent_id,
            action=action,
            payload=payload,
        )
        
        result = self.engine.evaluate(request)
        
        if self.receipt_generator:
            receipt = self.receipt_generator.generate(result, request)
            self._receipts.append(receipt)
        
        if result.decision == PolicyDecision.DENY:
            logger.warning(
                "Governance violation in chain",
                action=action,
                violations=result.violations,
            )
            raise GovernanceViolation(
                message=result.reason,
                decision=result.decision,
                violations=result.violations,
            )
        
        return result
    
    def invoke(
        self,
        input: Any,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Invoke the chain with governance controls.
        
        Evaluates input before execution and output after,
        applying any redactions from policy evaluation.
        
        Args:
            input: Input to the chain.
            config: Optional configuration for the chain.
            **kwargs: Additional keyword arguments.
            
        Returns:
            The chain output, possibly modified by redaction policies.
            
        Raises:
            GovernanceViolation: If input or output is denied.
        """
        if isinstance(input, dict):
            input_payload = input
        else:
            input_payload = {"input": input}
        
        input_result = self._evaluate("chain_invoke_input", input_payload)
        
        if input_result.decision == PolicyDecision.REDACT and input_result.modified_payload:
            if isinstance(input, dict):
                input = input_result.modified_payload
            elif "input" in input_result.modified_payload:
                input = input_result.modified_payload["input"]
        
        logger.debug("Invoking wrapped chain", input_type=type(input).__name__)
        
        if config:
            output = self.chain.invoke(input, config, **kwargs)
        else:
            output = self.chain.invoke(input, **kwargs)
        
        if isinstance(output, dict):
            output_payload = output
        else:
            output_payload = {"output": output}
        
        output_result = self._evaluate("chain_invoke_output", output_payload)
        
        if output_result.decision == PolicyDecision.REDACT and output_result.modified_payload:
            if isinstance(output, dict):
                return output_result.modified_payload
            elif "output" in output_result.modified_payload:
                return output_result.modified_payload["output"]
        
        return output
    
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Allow calling the governed chain directly."""
        return self.invoke(*args, **kwargs)


def create_governed_chain(
    chain: Any,
    engine: GovernanceEngine,
    identity_manager: Optional[Any] = None,
    receipt_generator: Optional[Any] = None,
    agent_id: str = "governed-chain",
) -> GovernedChain:
    """
    Create a governed chain wrapper.
    
    Convenience function for creating a GovernedChain instance.
    
    Args:
        chain: The LangChain chain to wrap.
        engine: GovernanceEngine for policy evaluation.
        identity_manager: Optional IdentityManager for authentication.
        receipt_generator: Optional ReceiptGenerator for audit trails.
        agent_id: Agent ID for governance requests.
        
    Returns:
        GovernedChain instance wrapping the provided chain.
    """
    return GovernedChain(
        chain=chain,
        engine=engine,
        identity_manager=identity_manager,
        receipt_generator=receipt_generator,
        agent_id=agent_id,
    )
