from typing import Any, Optional, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from tork.adapters.autogen.middleware import TorkAutoGenMiddleware

class GovernedAutoGenAgent:
    """An AutoGen agent wrapped with Tork governance."""
    
    def __init__(self, agent: Any, middleware: "TorkAutoGenMiddleware"):
        self._agent = agent
        self._middleware = middleware
    
    def receive(self, message: Any, sender: Any, request_reply: Optional[bool] = None):
        """Receive message with governance checks."""
        governed_message = self._middleware.process_message(message, sender=getattr(sender, "name", str(sender)))
        return self._agent.receive(governed_message, sender, request_reply)
    
    def generate_reply(self, messages: Optional[List[Dict[str, Any]]] = None, sender: Optional[Any] = None, **kwargs):
        """Generate reply with governance."""
        # Process input messages
        if messages:
            messages = [self._middleware.process_message(m) for m in messages]
        
        # Generate reply via original agent
        reply = self._agent.generate_reply(messages=messages, sender=sender, **kwargs)
        
        # Process output through governance
        return self._middleware.process_response(reply, agent_name=getattr(self._agent, "name", "agent"))
    
    def __getattr__(self, name: str):
        """Proxy all other attributes to wrapped agent."""
        return getattr(self._agent, name)

class GovernedGroupChat:
    """An AutoGen GroupChat with governance on all agent communications."""
    
    def __init__(self, agents: List[Any], middleware: "TorkAutoGenMiddleware", **kwargs):
        self._middleware = middleware
        self._agents = [middleware.wrap_agent(a) for a in agents]
        self._kwargs = kwargs
    
    @property
    def agents(self):
        return self._agents

    def __getattr__(self, name: str):
        # We don't have a real GroupChat object to wrap in this mock, so we just proxy to self
        return getattr(self, name)
