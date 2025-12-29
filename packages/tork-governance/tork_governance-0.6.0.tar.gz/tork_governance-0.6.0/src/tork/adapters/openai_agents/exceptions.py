"""Exceptions for OpenAI Agents SDK governance integration."""


class OpenAIAgentGovernanceError(Exception):
    """Base exception for OpenAI Agent governance errors."""
    pass


class InputBlockedError(OpenAIAgentGovernanceError):
    """Raised when input is blocked by a governance policy."""
    pass


class OutputBlockedError(OpenAIAgentGovernanceError):
    """Raised when agent output is blocked by a governance policy."""
    pass


class ToolCallBlockedError(OpenAIAgentGovernanceError):
    """Raised when a tool call is blocked by security policies."""
    pass
