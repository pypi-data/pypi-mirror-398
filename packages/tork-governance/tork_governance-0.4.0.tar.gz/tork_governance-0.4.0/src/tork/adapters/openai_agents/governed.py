"""Governed wrappers for OpenAI Agents SDK."""

from typing import Any, Dict, TYPE_CHECKING
import asyncio

if TYPE_CHECKING:
    from tork.adapters.openai_agents.middleware import TorkOpenAIAgentsMiddleware


class GovernedOpenAIAgent:
    """An OpenAI Agent wrapped with Tork governance."""

    def __init__(self, agent: Any, middleware: "TorkOpenAIAgentsMiddleware"):
        """
        Initialize a governed agent wrapper.

        Args:
            agent: The OpenAI Agent instance to wrap.
            middleware: The TorkOpenAIAgentsMiddleware for governance.
        """
        self._agent = agent
        self._middleware = middleware

    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Run agent with governance checks.

        Args:
            input_text: The input text to process.
            **kwargs: Additional arguments passed to the agent.

        Returns:
            Dict with 'output' (governed result), 'input_result', 'output_result', and 'receipt'.
        """
        input_processed = self._middleware.process_input(input_text)
        processed_input = input_processed["text"]

        if hasattr(self._agent, "run"):
            agent_output = self._agent.run(processed_input, **kwargs)
        elif callable(self._agent):
            agent_output = self._agent(processed_input, **kwargs)
        else:
            raise TypeError("Agent must have a 'run' method or be callable")

        output_text = str(agent_output)
        output_processed = self._middleware.process_output(output_text)

        return {
            "output": output_processed["text"],
            "input_result": input_processed["result"],
            "output_result": output_processed["result"],
            "receipt": output_processed["receipt"],
        }

    async def run_async(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Async version of run with governance.

        Args:
            input_text: The input text to process.
            **kwargs: Additional arguments passed to the agent.

        Returns:
            Dict with 'output' (governed result), 'input_result', 'output_result', and 'receipt'.
        """
        input_processed = self._middleware.process_input(input_text)
        processed_input = input_processed["text"]

        if hasattr(self._agent, "run_async"):
            agent_output = await self._agent.run_async(processed_input, **kwargs)
        elif hasattr(self._agent, "arun"):
            agent_output = await self._agent.arun(processed_input, **kwargs)
        elif hasattr(self._agent, "run"):
            agent_output = await asyncio.to_thread(
                self._agent.run, processed_input, **kwargs
            )
        elif callable(self._agent):
            agent_output = await asyncio.to_thread(
                self._agent, processed_input, **kwargs
            )
        else:
            raise TypeError("Agent must have a 'run' or 'run_async' method or be callable")

        output_text = str(agent_output)
        output_processed = self._middleware.process_output(output_text)

        return {
            "output": output_processed["text"],
            "input_result": input_processed["result"],
            "output_result": output_processed["result"],
            "receipt": output_processed["receipt"],
        }

    def __getattr__(self, name: str) -> Any:
        """Proxy all other attributes to wrapped agent."""
        return getattr(self._agent, name)


class GovernedRunner:
    """A governed wrapper for running any OpenAI Agent with governance."""

    def __init__(self, middleware: "TorkOpenAIAgentsMiddleware"):
        """
        Initialize the governed runner.

        Args:
            middleware: The TorkOpenAIAgentsMiddleware for governance.
        """
        self._middleware = middleware

    def run(self, agent: Any, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Run any agent with governance applied.

        Args:
            agent: The agent to run.
            input_text: The input text to process.
            **kwargs: Additional arguments passed to the agent.

        Returns:
            Dict with governed results.
        """
        governed_agent = GovernedOpenAIAgent(agent, self._middleware)
        return governed_agent.run(input_text, **kwargs)

    async def run_async(self, agent: Any, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Async run any agent with governance applied.

        Args:
            agent: The agent to run.
            input_text: The input text to process.
            **kwargs: Additional arguments passed to the agent.

        Returns:
            Dict with governed results.
        """
        governed_agent = GovernedOpenAIAgent(agent, self._middleware)
        return await governed_agent.run_async(input_text, **kwargs)
