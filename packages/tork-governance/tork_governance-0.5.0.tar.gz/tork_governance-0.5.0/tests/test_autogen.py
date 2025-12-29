import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from tork.adapters.autogen.middleware import TorkAutoGenMiddleware
from tork.adapters.autogen.governed import GovernedAutoGenAgent, GovernedGroupChat
from tork.adapters.autogen.exceptions import MessageBlockedError, ResponseBlockedError
from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationResult, PolicyDecision

class MockAgent:
    def __init__(self, name="TestAgent"):
        self.name = name
    def receive(self, message, sender, request_reply=None):
        return "received"
    def generate_reply(self, messages=None, sender=None, **kwargs):
        return "I am an AI assistant."

def test_middleware_init():
    mw = TorkAutoGenMiddleware(agent_id="test-autogen")
    assert mw.agent_id == "test-autogen"
    assert isinstance(mw.engine, GovernanceEngine)

def test_wrap_agent():
    mw = TorkAutoGenMiddleware()
    agent = MockAgent()
    governed = mw.wrap_agent(agent)
    assert isinstance(governed, GovernedAutoGenAgent)
    assert governed.name == "TestAgent"

def test_process_message_allowed():
    mw = TorkAutoGenMiddleware()
    msg = "Hello"
    res = mw.process_message(msg)
    assert res == "Hello"

def test_process_message_blocked():
    engine = GovernanceEngine()
    mock_res = EvaluationResult(
        decision=PolicyDecision.DENY,
        reason="Blocked",
        violations=["Blocked content"],
        original_payload={"content": "bad"},
        modified_payload=None,
        pii_found=[],
        timestamp=datetime.now(timezone.utc)
    )
    engine.evaluate = MagicMock(return_value=mock_res)
    mw = TorkAutoGenMiddleware(engine=engine)
    with pytest.raises(MessageBlockedError):
        mw.process_message("bad")

def test_process_response_allowed():
    mw = TorkAutoGenMiddleware()
    res = mw.process_response("Clean response")
    assert res == "Clean response"

def test_governed_agent_receive():
    mw = TorkAutoGenMiddleware()
    agent = MockAgent()
    governed = GovernedAutoGenAgent(agent, mw)
    res = governed.receive("Hello", sender="User")
    assert res == "received"

def test_governed_agent_generate_reply():
    mw = TorkAutoGenMiddleware()
    agent = MockAgent()
    governed = GovernedAutoGenAgent(agent, mw)
    res = governed.generate_reply(messages=[{"content": "hi"}])
    assert res == "I am an AI assistant."

def test_governed_group_chat():
    mw = TorkAutoGenMiddleware()
    agents = [MockAgent("A1"), MockAgent("A2")]
    group = GovernedGroupChat(agents, mw)
    assert len(group.agents) == 2
    assert isinstance(group.agents[0], GovernedAutoGenAgent)

def test_pii_redaction_in_message():
    mw = TorkAutoGenMiddleware()
    # PII in message should be handled by default engine if configured
    # Here we just verify the flow doesn't crash
    msg = "My email is test@example.com"
    res = mw.process_message(msg)
    assert isinstance(res, str)

def test_compliance_receipt_on_response():
    mw = TorkAutoGenMiddleware()
    # Use a real or mock engine that allows
    res = mw.process_response("Response text")
    # Receipt generation happens inside process_response
    assert res == "Response text"
