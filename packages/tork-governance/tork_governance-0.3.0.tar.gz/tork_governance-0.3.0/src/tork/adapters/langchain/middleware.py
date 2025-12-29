"""
LangChain Callback Handler for Tork Governance.

Integrates governance controls into LangChain's callback system
for monitoring and controlling LLM, chain, and tool operations.
"""

from typing import Any, Optional, Dict, List
import structlog

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest, PolicyDecision
from tork.adapters.langchain.exceptions import GovernanceViolation

try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import LLMResult
    LANGCHAIN_AVAILABLE = True
except ImportError:
    BaseCallbackHandler = object
    LLMResult = Any
    LANGCHAIN_AVAILABLE = False

logger = structlog.get_logger(__name__)


class TorkCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler for governance enforcement.
    
    Integrates with LangChain's callback system to evaluate
    LLM calls, chain executions, and tool invocations against
    governance policies.
    """
    
    def __init__(
        self,
        engine: GovernanceEngine,
        identity_manager: Optional[Any] = None,
        receipt_generator: Optional[Any] = None,
        agent_id: str = "langchain-agent",
    ) -> None:
        """
        Initialize the Tork callback handler.
        
        Args:
            engine: GovernanceEngine instance for policy evaluation.
            identity_manager: Optional IdentityManager for agent authentication.
            receipt_generator: Optional ReceiptGenerator for audit trails.
            agent_id: Default agent ID for governance requests.
        """
        self.engine = engine
        self.identity_manager = identity_manager
        self.receipt_generator = receipt_generator
        self.agent_id = agent_id
        self._receipts: list[Any] = []
        
        logger.info(
            "TorkCallbackHandler initialized",
            agent_id=agent_id,
            has_identity_manager=identity_manager is not None,
            has_receipt_generator=receipt_generator is not None,
        )
    
    @property
    def receipts(self) -> list[Any]:
        """Return list of generated receipts."""
        return self._receipts
    
    def _evaluate_and_enforce(
        self,
        action: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Evaluate payload against governance policies and enforce decisions.
        
        Args:
            action: The action type (llm_start, chain_end, etc.)
            payload: The data to evaluate.
            metadata: Optional additional context.
            
        Returns:
            The EvaluationResult.
            
        Raises:
            GovernanceViolation: If policy decision is DENY.
        """
        request = EvaluationRequest(
            agent_id=self.agent_id,
            action=action,
            payload=payload,
            metadata=metadata,
        )
        
        result = self.engine.evaluate(request)
        
        if self.receipt_generator:
            receipt = self.receipt_generator.generate(result, request)
            self._receipts.append(receipt)
        
        if result.decision == PolicyDecision.DENY:
            logger.warning(
                "Governance violation",
                action=action,
                violations=result.violations,
            )
            raise GovernanceViolation(
                message=result.reason,
                decision=result.decision,
                violations=result.violations,
            )
        
        logger.debug(
            "Governance check passed",
            action=action,
            decision=result.decision.value,
        )
        
        return result
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """
        Called when LLM starts processing.
        
        Args:
            serialized: Serialized LLM information.
            prompts: List of prompts being sent to the LLM.
            **kwargs: Additional keyword arguments.
        """
        payload = {
            "prompts": prompts,
            "llm_info": serialized,
        }
        self._evaluate_and_enforce("llm_start", payload, kwargs)
    
    def on_llm_end(
        self,
        response: Any,
        **kwargs: Any,
    ) -> None:
        """
        Called when LLM finishes processing.
        
        Args:
            response: The LLM response.
            **kwargs: Additional keyword arguments.
        """
        if hasattr(response, 'generations'):
            generations = []
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, 'text'):
                        generations.append(gen.text)
            payload = {"generations": generations}
        else:
            payload = {"response": str(response)}
        
        self._evaluate_and_enforce("llm_end", payload, kwargs)
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """
        Called when a chain starts execution.
        
        Args:
            serialized: Serialized chain information.
            inputs: Input data to the chain.
            **kwargs: Additional keyword arguments.
        """
        payload = {
            "inputs": inputs,
            "chain_info": serialized,
        }
        self._evaluate_and_enforce("chain_start", payload, kwargs)
    
    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """
        Called when a chain finishes execution.
        
        Args:
            outputs: Output data from the chain.
            **kwargs: Additional keyword arguments.
        """
        payload = {"outputs": outputs}
        self._evaluate_and_enforce("chain_end", payload, kwargs)
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """
        Called when a tool starts execution.
        
        Args:
            serialized: Serialized tool information.
            input_str: Input string to the tool.
            **kwargs: Additional keyword arguments.
        """
        payload = {
            "input": input_str,
            "tool_info": serialized,
        }
        self._evaluate_and_enforce("tool_start", payload, kwargs)
    
    def on_tool_end(
        self,
        output: str,
        **kwargs: Any,
    ) -> None:
        """
        Called when a tool finishes execution.
        
        Args:
            output: Output from the tool.
            **kwargs: Additional keyword arguments.
        """
        payload = {"output": output}
        self._evaluate_and_enforce("tool_end", payload, kwargs)
