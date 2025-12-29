"""Tests for OpenAI Agents SDK integration adapter."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone

from tork.adapters.openai_agents import (
    TorkOpenAIAgentsMiddleware,
    GovernedOpenAIAgent,
    GovernedRunner,
    OpenAIAgentGovernanceError,
    InputBlockedError,
    OutputBlockedError,
    ToolCallBlockedError,
)
from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationResult, PolicyDecision
from tork.compliance.receipts import PolicyReceipt


class MockAgent:
    """Mock OpenAI Agent for testing."""

    def __init__(self, name: str = "TestAgent", response: str = "I am an AI assistant."):
        self.name = name
        self._response = response

    def run(self, input_text: str, **kwargs) -> str:
        return self._response

    async def run_async(self, input_text: str, **kwargs) -> str:
        return self._response


class TestMiddlewareInitialization:
    """Tests for middleware initialization."""

    def test_default_initialization(self):
        """Test middleware initializes with defaults."""
        mw = TorkOpenAIAgentsMiddleware()
        assert mw.agent_id == "openai-agent"
        assert isinstance(mw.engine, GovernanceEngine)
        assert mw.receipt_generator is not None

    def test_custom_initialization(self):
        """Test middleware with custom parameters."""
        engine = GovernanceEngine()
        mw = TorkOpenAIAgentsMiddleware(
            engine=engine,
            agent_id="custom-agent",
            signing_key="custom-key",
        )
        assert mw.agent_id == "custom-agent"
        assert mw.engine is engine


class TestWrapAgent:
    """Tests for agent wrapping."""

    def test_wrap_agent_returns_governed_agent(self):
        """Test wrap_agent returns GovernedOpenAIAgent."""
        mw = TorkOpenAIAgentsMiddleware()
        agent = MockAgent()
        governed = mw.wrap_agent(agent)
        assert isinstance(governed, GovernedOpenAIAgent)

    def test_wrapped_agent_proxies_attributes(self):
        """Test wrapped agent proxies attributes to original."""
        mw = TorkOpenAIAgentsMiddleware()
        agent = MockAgent(name="ProxyTest")
        governed = mw.wrap_agent(agent)
        assert governed.name == "ProxyTest"


class TestProcessInput:
    """Tests for input processing."""

    def test_process_input_clean_content(self):
        """Test processing clean input passes through."""
        mw = TorkOpenAIAgentsMiddleware()
        result = mw.process_input("Hello, how are you?")
        assert result["text"] == "Hello, how are you?"
        assert result["result"] is not None

    def test_process_input_with_pii_redaction(self):
        """Test PII in input is detected."""
        mw = TorkOpenAIAgentsMiddleware()
        result = mw.process_input("My email is test@example.com")
        assert result["result"] is not None

    def test_process_input_blocked(self):
        """Test input blocked by policy raises exception."""
        engine = GovernanceEngine()
        mock_result = EvaluationResult(
            decision=PolicyDecision.DENY,
            reason="Content blocked",
            violations=["Blocked content detected"],
            original_payload={"content": "bad input"},
            modified_payload=None,
            pii_found=[],
            timestamp=datetime.now(timezone.utc),
        )
        engine.evaluate = MagicMock(return_value=mock_result)
        mw = TorkOpenAIAgentsMiddleware(engine=engine)

        with pytest.raises(InputBlockedError) as exc_info:
            mw.process_input("bad input")
        assert "Blocked content detected" in str(exc_info.value)

    def test_process_input_with_context(self):
        """Test processing input with additional context."""
        mw = TorkOpenAIAgentsMiddleware()
        result = mw.process_input(
            "Query about user",
            context={"user_id": "123", "session": "abc"},
        )
        assert result["text"] == "Query about user"


class TestProcessOutput:
    """Tests for output processing."""

    def test_process_output_clean(self):
        """Test processing clean output."""
        mw = TorkOpenAIAgentsMiddleware()
        result = mw.process_output("Here is your response.")
        assert result["text"] == "Here is your response."
        assert "receipt" in result
        assert isinstance(result["receipt"], PolicyReceipt)

    def test_process_output_with_tool_calls(self):
        """Test processing output with tool calls."""
        mw = TorkOpenAIAgentsMiddleware()
        tool_calls = [{"name": "search", "args": {"query": "weather"}}]
        result = mw.process_output("The weather is sunny.", tool_calls=tool_calls)
        assert result["text"] == "The weather is sunny."

    def test_process_output_blocked(self):
        """Test output blocked by policy raises exception."""
        engine = GovernanceEngine()
        mock_result = EvaluationResult(
            decision=PolicyDecision.DENY,
            reason="Output blocked",
            violations=["Sensitive data in output"],
            original_payload={"content": "secret data"},
            modified_payload=None,
            pii_found=[],
            timestamp=datetime.now(timezone.utc),
        )
        engine.evaluate = MagicMock(return_value=mock_result)
        mw = TorkOpenAIAgentsMiddleware(engine=engine)

        with pytest.raises(OutputBlockedError) as exc_info:
            mw.process_output("secret data")
        assert "Sensitive data in output" in str(exc_info.value)


class TestCheckToolCall:
    """Tests for tool call validation."""

    def test_check_safe_tool(self):
        """Test safe tool call is allowed."""
        mw = TorkOpenAIAgentsMiddleware()
        result = mw.check_tool_call("search", {"query": "weather"})
        assert result["allowed"] is True
        assert result["reason"] == "Tool call permitted"

    def test_check_dangerous_tool_blocked(self):
        """Test dangerous tools are blocked."""
        mw = TorkOpenAIAgentsMiddleware()

        dangerous_tools = ["shell", "exec", "eval", "subprocess", "rm"]
        for tool in dangerous_tools:
            with pytest.raises(ToolCallBlockedError) as exc_info:
                mw.check_tool_call(tool, {})
            assert tool in str(exc_info.value).lower()

    def test_check_nested_dangerous_tool(self):
        """Test nested dangerous tool patterns are blocked."""
        mw = TorkOpenAIAgentsMiddleware()
        with pytest.raises(ToolCallBlockedError):
            mw.check_tool_call("os.system", {"cmd": "ls"})


class TestGovernedOpenAIAgent:
    """Tests for GovernedOpenAIAgent wrapper."""

    def test_run_method(self):
        """Test governed agent run method."""
        mw = TorkOpenAIAgentsMiddleware()
        agent = MockAgent(response="Test response")
        governed = GovernedOpenAIAgent(agent, mw)

        result = governed.run("Hello")
        assert result["output"] == "Test response"
        assert "input_result" in result
        assert "output_result" in result
        assert "receipt" in result

    def test_proxies_attributes(self):
        """Test governed agent proxies attributes."""
        mw = TorkOpenAIAgentsMiddleware()
        agent = MockAgent(name="AttributeTest")
        governed = GovernedOpenAIAgent(agent, mw)
        assert governed.name == "AttributeTest"

    @pytest.mark.asyncio
    async def test_run_async_method(self):
        """Test governed agent async run method."""
        mw = TorkOpenAIAgentsMiddleware()
        agent = MockAgent(response="Async response")
        governed = GovernedOpenAIAgent(agent, mw)

        result = await governed.run_async("Hello async")
        assert result["output"] == "Async response"
        assert "receipt" in result


class TestGovernedRunner:
    """Tests for GovernedRunner."""

    def test_run_any_agent(self):
        """Test runner can run any agent with governance."""
        mw = TorkOpenAIAgentsMiddleware()
        runner = GovernedRunner(mw)
        agent = MockAgent(response="Runner response")

        result = runner.run(agent, "Hello from runner")
        assert result["output"] == "Runner response"
        assert "receipt" in result

    def test_create_governed_runner(self):
        """Test creating runner from middleware."""
        mw = TorkOpenAIAgentsMiddleware()
        runner = mw.create_governed_runner()
        assert isinstance(runner, GovernedRunner)


class TestComplianceReceipts:
    """Tests for compliance receipt generation."""

    def test_receipt_generated_on_output(self):
        """Test compliance receipt is generated for each output."""
        mw = TorkOpenAIAgentsMiddleware()
        result = mw.process_output("Response text")

        receipt = result["receipt"]
        assert isinstance(receipt, PolicyReceipt)
        assert receipt.agent_id == "openai-agent"
        assert receipt.action == "agent_output"
        assert receipt.signature is not None

    def test_receipt_contains_decision(self):
        """Test receipt contains the policy decision."""
        mw = TorkOpenAIAgentsMiddleware()
        result = mw.process_output("Clean output")

        receipt = result["receipt"]
        assert receipt.decision == PolicyDecision.ALLOW


class TestExceptions:
    """Tests for exception hierarchy."""

    def test_exception_inheritance(self):
        """Test exception inheritance is correct."""
        assert issubclass(InputBlockedError, OpenAIAgentGovernanceError)
        assert issubclass(OutputBlockedError, OpenAIAgentGovernanceError)
        assert issubclass(ToolCallBlockedError, OpenAIAgentGovernanceError)
        assert issubclass(OpenAIAgentGovernanceError, Exception)

    def test_exception_messages(self):
        """Test exceptions can carry messages."""
        err = InputBlockedError("Custom message")
        assert str(err) == "Custom message"
