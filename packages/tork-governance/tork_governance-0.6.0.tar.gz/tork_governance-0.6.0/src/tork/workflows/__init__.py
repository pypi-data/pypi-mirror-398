"""Workflow system for Tork Governance SDK."""

from tork.workflows.models import (
    WorkflowStep,
    WorkflowDefinition,
    StepResult,
    WorkflowResult,
)
from tork.workflows.engine import WorkflowEngine
from tork.workflows.builder import WorkflowBuilder
from tork.workflows.templates import (
    research_critique_rewrite,
    multi_agent_consensus,
    review_and_approve,
)

__all__ = [
    "WorkflowStep",
    "WorkflowDefinition",
    "StepResult",
    "WorkflowResult",
    "WorkflowEngine",
    "WorkflowBuilder",
    "research_critique_rewrite",
    "multi_agent_consensus",
    "review_and_approve",
]
