"""
Adapters module for Tork Governance SDK.

Provides integration adapters for various AI agent frameworks
and external systems.
"""

from tork.adapters.base import BaseAdapter
from tork.adapters.langchain import (
    GovernanceViolation,
    TorkCallbackHandler,
    GovernedChain,
    create_governed_chain,
)

from tork.adapters.crewai import (
    TorkCrewAIMiddleware,
    GovernedAgent,
    GovernedCrew,
    GovernanceBlockedError,
    PIIDetectedError,
)
from tork.adapters.autogen import (
    TorkAutoGenMiddleware,
    GovernedAutoGenAgent,
    GovernedGroupChat,
    AutoGenGovernanceError,
    MessageBlockedError,
    ResponseBlockedError,
)

__all__ = [
    "BaseAdapter",
    "GovernanceViolation",
    "TorkCallbackHandler",
    "GovernedChain",
    "create_governed_chain",
    "TorkCrewAIMiddleware",
    "GovernedAgent",
    "GovernedCrew",
    "GovernanceBlockedError",
    "PIIDetectedError",
    "TorkAutoGenMiddleware",
    "GovernedAutoGenAgent",
    "GovernedGroupChat",
    "AutoGenGovernanceError",
    "MessageBlockedError",
    "ResponseBlockedError",
]
