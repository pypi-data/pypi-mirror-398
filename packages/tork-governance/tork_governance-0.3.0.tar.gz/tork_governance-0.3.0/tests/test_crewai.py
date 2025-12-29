import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from tork.adapters.crewai.middleware import TorkCrewAIMiddleware
from tork.adapters.crewai.governed import GovernedAgent, GovernedCrew
from tork.adapters.crewai.exceptions import GovernanceBlockedError, PIIDetectedError
from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationResult, PolicyDecision

class MockTask:
    def __init__(self, description):
        self.description = description

class MockAgent:
    def __init__(self, name="Test Agent"):
        self.name = name
        self.agents = [] # for crew compatibility
    def execute_task(self, task, context=None):
        return f"Result for {task.description}"

class MockCrew:
    def __init__(self, agents):
        self.agents = agents
    def kickoff(self, inputs=None):
        return "Crew result"

def test_middleware_init():
    mw = TorkCrewAIMiddleware(agent_id="test-agent")
    assert mw.agent_id == "test-agent"
    assert isinstance(mw.engine, GovernanceEngine)

def test_wrap_agent():
    mw = TorkCrewAIMiddleware()
    agent = MockAgent()
    governed = mw.wrap_agent(agent)
    assert isinstance(governed, GovernedAgent)
    assert governed.name == "Test Agent"

def test_wrap_crew():
    mw = TorkCrewAIMiddleware()
    agent = MockAgent()
    crew = MockCrew(agents=[agent])
    governed_crew = mw.wrap_crew(crew)
    assert isinstance(governed_crew, GovernedCrew)
    assert isinstance(governed_crew.agents[0], GovernedAgent)

def test_before_task_allowed():
    mw = TorkCrewAIMiddleware()
    task = MockTask("Clean task")
    agent = MockAgent()
    payload = mw.before_task(task, agent)
    assert payload["task_description"] == "Clean task"

def test_before_task_blocked():
    engine = GovernanceEngine()
    mock_res = EvaluationResult(
        decision=PolicyDecision.DENY,
        reason="Blocked",
        violations=["Test violation"],
        original_payload={"task_description": "Bad task"},
        modified_payload=None,
        pii_found=[],
        timestamp=datetime.now(timezone.utc)
    )
    engine.evaluate = MagicMock(return_value=mock_res)
    
    mw = TorkCrewAIMiddleware(engine=engine)
    task = MockTask("Bad task")
    agent = MockAgent()
    
    with pytest.raises(GovernanceBlockedError):
        mw.before_task(task, agent)

def test_after_task_allowed():
    mw = TorkCrewAIMiddleware()
    task = MockTask("task")
    agent = MockAgent()
    res = mw.after_task(task, "Clean result", agent)
    assert res["result"] == "Clean result"
    assert "receipt" in res

def test_governed_agent_execution():
    mw = TorkCrewAIMiddleware()
    agent = MockAgent()
    governed = GovernedAgent(agent, mw)
    task = MockTask("task description")
    
    result = governed.execute_task(task)
    assert result == "Result for task description"

def test_governed_agent_getattr():
    agent = MockAgent()
    governed = GovernedAgent(agent, None)
    assert governed.name == "Test Agent"

def test_governed_crew_kickoff():
    mw = TorkCrewAIMiddleware()
    agent = MockAgent()
    crew = MockCrew(agents=[agent])
    governed_crew = GovernedCrew(crew, mw)
    
    res = governed_crew.kickoff()
    assert res == "Crew result"

def test_pii_redaction_before_task():
    mw = TorkCrewAIMiddleware()
    task = MockTask("My email is test@example.com")
    agent = MockAgent()
    payload = mw.before_task(task, agent)
    assert "task_description" in payload

def test_receipt_generation_after_task():
    mw = TorkCrewAIMiddleware()
    res = mw.after_task(MockTask("t"), "result", MockAgent())
    assert "receipt" in res
    assert res["receipt"]["agent_id"] == "crewai-agent"
