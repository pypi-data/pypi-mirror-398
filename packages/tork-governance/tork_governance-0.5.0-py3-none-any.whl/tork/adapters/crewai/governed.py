from typing import Any, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from tork.adapters.crewai.middleware import TorkCrewAIMiddleware

class GovernedAgent:
    """A CrewAI agent wrapped with Tork governance."""
    
    def __init__(self, agent: Any, middleware: "TorkCrewAIMiddleware"):
        self._agent = agent
        self._middleware = middleware
    
    def execute_task(self, task: Any, context: Any = None):
        """Execute task with governance checks."""
        # Pre-execution governance
        self._middleware.before_task(task, self._agent)
        
        # Execute original agent task
        result = self._agent.execute_task(task, context=context)
        
        # Post-execution governance
        governed_result = self._middleware.after_task(task, result, self._agent)
        
        return governed_result["result"]
    
    def __getattr__(self, name: str):
        """Proxy all other attributes to wrapped agent."""
        return getattr(self._agent, name)

class GovernedCrew:
    """A CrewAI crew with all agents governed."""
    
    def __init__(self, crew: Any, middleware: "TorkCrewAIMiddleware"):
        self._crew = crew
        self._middleware = middleware
        self._governed_agents = [
            GovernedAgent(agent, middleware) for agent in getattr(crew, "agents", [])
        ]
        # In actual CrewAI we might need to monkeypatch the crew's agents list
        if hasattr(self._crew, "agents"):
            self._crew.agents = self._governed_agents
    
    def kickoff(self, inputs: Optional[Dict[str, Any]] = None):
        """Run the crew with governance on all tasks."""
        results = self._crew.kickoff(inputs=inputs)
        return results

    def __getattr__(self, name: str):
        return getattr(self._crew, name)
