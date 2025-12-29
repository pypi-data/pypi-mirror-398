"""Data models for workflow system."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    """A single step in a workflow."""

    id: str = Field(..., description="Unique step identifier")
    name: str = Field(..., description="Human-readable step name")
    agent_type: str = Field(
        ...,
        description="Type of agent: langchain, crewai, autogen, openai_agents, custom",
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific configuration"
    )
    input_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Map previous step outputs to this step's inputs",
    )
    timeout_seconds: int = Field(default=300, description="Step timeout in seconds")
    retry_count: int = Field(default=3, description="Number of retries on failure")
    on_failure: str = Field(
        default="stop",
        description="Failure strategy: stop, skip, retry, fallback",
    )
    fallback_step_id: Optional[str] = Field(
        default=None, description="Step ID to execute on fallback"
    )


class WorkflowDefinition(BaseModel):
    """Definition of a complete workflow."""

    id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Human-readable workflow name")
    description: str = Field(default="", description="Workflow description")
    steps: List[WorkflowStep] = Field(
        default_factory=list, description="List of workflow steps"
    )
    governance_policy: Optional[str] = Field(
        default=None, description="Policy name to apply at each step"
    )
    require_human_approval: List[str] = Field(
        default_factory=list, description="Step IDs requiring human approval"
    )
    max_total_cost: Optional[float] = Field(
        default=None, description="Maximum total cost for the workflow"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class StepResult(BaseModel):
    """Result of executing a single step."""

    step_id: str = Field(..., description="Step identifier")
    status: str = Field(
        ..., description="Status: success, failed, skipped, pending_approval"
    )
    output: Any = Field(default=None, description="Step output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_ms: int = Field(default=0, description="Execution time in ms")
    tokens_used: int = Field(default=0, description="Tokens consumed")
    cost: float = Field(default=0.0, description="Cost of this step")
    receipt_id: Optional[str] = Field(
        default=None, description="Compliance receipt ID"
    )


class WorkflowResult(BaseModel):
    """Result of executing a complete workflow."""

    workflow_id: str = Field(..., description="Workflow identifier")
    status: str = Field(
        ..., description="Status: completed, failed, paused, cancelled"
    )
    step_results: List[StepResult] = Field(
        default_factory=list, description="Results for each step"
    )
    total_execution_time_ms: int = Field(default=0, description="Total execution time")
    total_tokens_used: int = Field(default=0, description="Total tokens consumed")
    total_cost: float = Field(default=0.0, description="Total cost")
    final_output: Any = Field(default=None, description="Final workflow output")
