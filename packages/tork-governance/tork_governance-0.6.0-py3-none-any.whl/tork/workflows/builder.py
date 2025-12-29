"""Fluent builder for creating workflows."""

from typing import Any, Dict, Optional
from tork.workflows.models import WorkflowDefinition, WorkflowStep


class WorkflowBuilder:
    """Fluent builder for creating workflows."""

    def __init__(self, workflow_id: str, name: str):
        """
        Initialize a new workflow builder.

        Args:
            workflow_id: Unique identifier for the workflow.
            name: Human-readable name for the workflow.
        """
        self._workflow = WorkflowDefinition(
            id=workflow_id,
            name=name,
            steps=[],
        )

    def description(self, description: str) -> "WorkflowBuilder":
        """
        Set the workflow description.

        Args:
            description: Workflow description.

        Returns:
            Self for chaining.
        """
        self._workflow.description = description
        return self

    def add_step(
        self,
        step_id: str,
        name: str,
        agent_type: str,
        config: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 300,
        retry_count: int = 3,
        on_failure: str = "stop",
        fallback_step_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a step to the workflow.

        Args:
            step_id: Unique step identifier.
            name: Human-readable step name.
            agent_type: Type of agent (langchain, crewai, autogen, openai_agents, custom).
            config: Agent-specific configuration.
            timeout_seconds: Step timeout.
            retry_count: Number of retries on failure.
            on_failure: Failure strategy.
            fallback_step_id: Step to run on fallback.

        Returns:
            Self for chaining.
        """
        step = WorkflowStep(
            id=step_id,
            name=name,
            agent_type=agent_type,
            config=config or {},
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
            on_failure=on_failure,
            fallback_step_id=fallback_step_id,
        )
        self._workflow.steps.append(step)
        return self

    def with_input_mapping(
        self, step_id: str, mappings: Dict[str, str]
    ) -> "WorkflowBuilder":
        """
        Set input mappings for a step.

        Args:
            step_id: Step to configure.
            mappings: Dict mapping target keys to source paths (e.g., {"input": "step1.output"}).

        Returns:
            Self for chaining.
        """
        for step in self._workflow.steps:
            if step.id == step_id:
                step.input_mapping = mappings
                break
        return self

    def require_approval(self, step_id: str) -> "WorkflowBuilder":
        """
        Mark a step as requiring human approval.

        Args:
            step_id: Step that requires approval before execution.

        Returns:
            Self for chaining.
        """
        if step_id not in self._workflow.require_human_approval:
            self._workflow.require_human_approval.append(step_id)
        return self

    def with_governance_policy(self, policy: str) -> "WorkflowBuilder":
        """
        Set the governance policy for the workflow.

        Args:
            policy: Policy name to apply at each step.

        Returns:
            Self for chaining.
        """
        self._workflow.governance_policy = policy
        return self

    def with_max_cost(self, max_cost: float) -> "WorkflowBuilder":
        """
        Set maximum total cost for the workflow.

        Args:
            max_cost: Maximum cost in dollars.

        Returns:
            Self for chaining.
        """
        self._workflow.max_total_cost = max_cost
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> "WorkflowBuilder":
        """
        Set metadata for the workflow.

        Args:
            metadata: Additional metadata.

        Returns:
            Self for chaining.
        """
        self._workflow.metadata = metadata
        return self

    def build(self) -> WorkflowDefinition:
        """
        Build and return the workflow definition.

        Returns:
            The completed WorkflowDefinition.
        """
        return self._workflow
