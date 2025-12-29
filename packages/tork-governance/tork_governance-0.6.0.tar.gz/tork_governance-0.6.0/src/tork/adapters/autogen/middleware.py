from __future__ import annotations
from typing import Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from tork.adapters.autogen.governed import GovernedAutoGenAgent, GovernedGroupChat

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest, PolicyDecision
from tork.compliance.receipts import ReceiptGenerator
from tork.adapters.autogen.exceptions import MessageBlockedError, ResponseBlockedError

class TorkAutoGenMiddleware:
    """Middleware to integrate Tork governance with Microsoft AutoGen agents."""
    
    def __init__(self, engine: Optional[GovernanceEngine] = None, agent_id: Optional[str] = None):
        self.engine = engine or GovernanceEngine()
        self.agent_id = agent_id or "autogen-agent"
        self.receipt_generator = ReceiptGenerator(signing_key="default-secret")
    
    def wrap_agent(self, agent: Any) -> "GovernedAutoGenAgent":
        """Wrap an AutoGen agent with governance controls."""
        from tork.adapters.autogen.governed import GovernedAutoGenAgent
        return GovernedAutoGenAgent(agent, self)
    
    def process_message(self, message: Any, sender: Optional[str] = None) -> Any:
        """Process incoming message through governance."""
        # AutoGen messages can be strings or dicts
        content = message if isinstance(message, str) else str(message.get("content", message))
        
        request = EvaluationRequest(
            payload={"content": content, "sender": sender},
            agent_id=self.agent_id,
            action="message_receive"
        )
        result = self.engine.evaluate(request)
        
        if result.decision == PolicyDecision.DENY:
            raise MessageBlockedError(f"Message blocked by policy: {result.violations}")
        
        modified_content = result.modified_payload.get("content", content) if result.modified_payload else content
        
        if isinstance(message, dict) and "content" in message:
            message["content"] = modified_content
            return message
        return modified_content
    
    def process_response(self, response: Any, agent_name: Optional[str] = None) -> Any:
        """Process outgoing response through governance."""
        content = response if isinstance(response, str) else str(response.get("content", response))
        
        request = EvaluationRequest(
            payload={"content": content, "agent_name": agent_name},
            agent_id=self.agent_id,
            action="message_send"
        )
        result = self.engine.evaluate(request)
        
        if result.decision == PolicyDecision.DENY:
            raise ResponseBlockedError(f"Response blocked by policy: {result.violations}")
        
        # Generate compliance receipt
        self.receipt_generator.create_receipt(
            result=result,
            request=request
        )
        
        modified_content = result.modified_payload.get("content", content) if result.modified_payload else content
        
        if isinstance(response, dict) and "content" in response:
            response["content"] = modified_content
            return response
        return modified_content
    
    def create_governed_group_chat(self, agents: List[Any], **kwargs) -> "GovernedGroupChat":
        """Create a group chat with governance on all messages."""
        from tork.adapters.autogen.governed import GovernedGroupChat
        return GovernedGroupChat(agents, self, **kwargs)
