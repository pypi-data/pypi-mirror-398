"""Middleware for integrating Tork governance with OpenAI Agents SDK."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tork.adapters.openai_agents.governed import GovernedOpenAIAgent, GovernedRunner

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest, PolicyDecision
from tork.compliance.receipts import ReceiptGenerator
from tork.adapters.openai_agents.exceptions import (
    InputBlockedError,
    OutputBlockedError,
    ToolCallBlockedError,
)

DANGEROUS_TOOLS = {
    "shell",
    "exec",
    "eval",
    "subprocess",
    "os.system",
    "run_command",
    "execute_code",
    "file_delete",
    "rm",
    "drop_table",
}


class TorkOpenAIAgentsMiddleware:
    """Middleware to integrate Tork governance with OpenAI Agents SDK."""

    def __init__(
        self,
        engine: Optional[GovernanceEngine] = None,
        agent_id: Optional[str] = None,
        signing_key: str = "default-secret",
    ):
        """
        Initialize the middleware.

        Args:
            engine: Optional GovernanceEngine. If not provided, creates default with PII redaction.
            agent_id: Identifier for the agent (for tracking and receipts).
            signing_key: Key for signing compliance receipts.
        """
        self.engine = engine or GovernanceEngine()
        self.agent_id = agent_id or "openai-agent"
        self.receipt_generator = ReceiptGenerator(signing_key=signing_key)

    def wrap_agent(self, agent: Any) -> "GovernedOpenAIAgent":
        """
        Wrap an OpenAI Agent with governance controls.

        Args:
            agent: The OpenAI Agent instance to wrap.

        Returns:
            A GovernedOpenAIAgent that intercepts agent runs.
        """
        from tork.adapters.openai_agents.governed import GovernedOpenAIAgent

        return GovernedOpenAIAgent(agent, self)

    def process_input(
        self, input_text: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process input through governance before sending to agent.

        Args:
            input_text: The user input text.
            context: Optional additional context for evaluation.

        Returns:
            Dict with 'text' (processed input) and 'result' (evaluation result).

        Raises:
            InputBlockedError: If the input is blocked by a policy.
        """
        payload = {"content": input_text}
        if context:
            payload["context"] = context

        request = EvaluationRequest(
            payload=payload,
            agent_id=self.agent_id,
            action="agent_input",
        )
        result = self.engine.evaluate(request)

        if result.decision == PolicyDecision.DENY:
            raise InputBlockedError(
                f"Input blocked by policy: {result.violations}"
            )

        processed_text = input_text
        if result.modified_payload and "content" in result.modified_payload:
            processed_text = result.modified_payload["content"]

        return {"text": processed_text, "result": result}

    def process_output(
        self, output: str, tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process agent output through governance.

        Args:
            output: The agent's output text.
            tool_calls: Optional list of tool calls made by the agent.

        Returns:
            Dict with 'text' (processed output), 'result', and 'receipt'.

        Raises:
            OutputBlockedError: If the output is blocked by a policy.
        """
        payload = {"content": output}
        if tool_calls:
            payload["tool_calls"] = tool_calls

        request = EvaluationRequest(
            payload=payload,
            agent_id=self.agent_id,
            action="agent_output",
        )
        result = self.engine.evaluate(request)

        if result.decision == PolicyDecision.DENY:
            raise OutputBlockedError(
                f"Output blocked by policy: {result.violations}"
            )

        processed_text = output
        if result.modified_payload and "content" in result.modified_payload:
            processed_text = result.modified_payload["content"]

        receipt = self.receipt_generator.create_receipt(
            result=result,
            request=request,
        )

        return {"text": processed_text, "result": result, "receipt": receipt}

    def check_tool_call(
        self, tool_name: str, tool_args: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate tool calls against security policies.

        Args:
            tool_name: The name of the tool being called.
            tool_args: The arguments being passed to the tool.

        Returns:
            Dict with 'allowed' (bool), 'reason' (str), and 'result'.

        Raises:
            ToolCallBlockedError: If the tool call is blocked.
        """
        tool_args = tool_args or {}

        if tool_name.lower() in DANGEROUS_TOOLS:
            raise ToolCallBlockedError(
                f"Tool '{tool_name}' is blocked by security policy"
            )

        for part in tool_name.lower().split("."):
            if part in DANGEROUS_TOOLS:
                raise ToolCallBlockedError(
                    f"Tool '{tool_name}' contains dangerous operation '{part}'"
                )

        payload = {"tool_name": tool_name, "tool_args": tool_args}

        request = EvaluationRequest(
            payload=payload,
            agent_id=self.agent_id,
            action="tool_call",
        )
        result = self.engine.evaluate(request)

        if result.decision == PolicyDecision.DENY:
            raise ToolCallBlockedError(
                f"Tool call blocked by policy: {result.violations}"
            )

        return {
            "allowed": True,
            "reason": "Tool call permitted",
            "result": result,
        }

    def create_governed_runner(self) -> "GovernedRunner":
        """
        Create a GovernedRunner for running any agent with governance.

        Returns:
            A GovernedRunner instance.
        """
        from tork.adapters.openai_agents.governed import GovernedRunner

        return GovernedRunner(self)
