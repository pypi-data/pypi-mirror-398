"""Tests for the workflow system."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from tork.workflows import (
    WorkflowStep,
    WorkflowDefinition,
    StepResult,
    WorkflowResult,
    WorkflowEngine,
    WorkflowBuilder,
    research_critique_rewrite,
    multi_agent_consensus,
    review_and_approve,
)
from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationResult, PolicyDecision


class TestWorkflowStepModel:
    """Tests for WorkflowStep model."""

    def test_basic_step(self):
        step = WorkflowStep(id="step1", name="Test Step", agent_type="custom")
        assert step.id == "step1"
        assert step.name == "Test Step"
        assert step.agent_type == "custom"
        assert step.timeout_seconds == 300
        assert step.retry_count == 3
        assert step.on_failure == "stop"

    def test_step_with_config(self):
        step = WorkflowStep(
            id="step1",
            name="Configured Step",
            agent_type="langchain",
            config={"model": "gpt-4"},
            input_mapping={"query": "previous.output"},
        )
        assert step.config["model"] == "gpt-4"
        assert step.input_mapping["query"] == "previous.output"


class TestWorkflowDefinitionModel:
    """Tests for WorkflowDefinition model."""

    def test_basic_workflow(self):
        workflow = WorkflowDefinition(
            id="wf1",
            name="Test Workflow",
            steps=[
                WorkflowStep(id="s1", name="Step 1", agent_type="custom"),
            ],
        )
        assert workflow.id == "wf1"
        assert len(workflow.steps) == 1

    def test_workflow_with_governance(self):
        workflow = WorkflowDefinition(
            id="wf1",
            name="Governed Workflow",
            steps=[],
            governance_policy="pii-protection",
            require_human_approval=["review_step"],
            max_total_cost=10.0,
        )
        assert workflow.governance_policy == "pii-protection"
        assert "review_step" in workflow.require_human_approval
        assert workflow.max_total_cost == 10.0


class TestStepResultModel:
    """Tests for StepResult model."""

    def test_success_result(self):
        result = StepResult(
            step_id="s1",
            status="success",
            output="Hello World",
            execution_time_ms=100,
            tokens_used=50,
            cost=0.01,
        )
        assert result.status == "success"
        assert result.output == "Hello World"
        assert result.cost == 0.01

    def test_failed_result(self):
        result = StepResult(
            step_id="s1",
            status="failed",
            error="Timeout exceeded",
        )
        assert result.status == "failed"
        assert result.error == "Timeout exceeded"


class TestWorkflowResultModel:
    """Tests for WorkflowResult model."""

    def test_completed_workflow(self):
        result = WorkflowResult(
            workflow_id="wf1",
            status="completed",
            step_results=[
                StepResult(step_id="s1", status="success", output="result1"),
                StepResult(step_id="s2", status="success", output="result2"),
            ],
            final_output="result2",
        )
        assert result.status == "completed"
        assert len(result.step_results) == 2
        assert result.final_output == "result2"


class TestWorkflowEngineInitialization:
    """Tests for WorkflowEngine initialization."""

    def test_default_init(self):
        engine = WorkflowEngine()
        assert engine.governance_engine is not None
        assert engine.receipt_generator is not None

    def test_custom_governance_engine(self):
        gov_engine = GovernanceEngine()
        engine = WorkflowEngine(governance_engine=gov_engine)
        assert engine.governance_engine is gov_engine


class TestRegisterExecutor:
    """Tests for executor registration."""

    def test_register_executor(self):
        engine = WorkflowEngine()
        executor = MagicMock(return_value="executed")
        engine.register_executor("custom", executor)
        assert "custom" in engine._executors


class TestExecuteSimpleWorkflow:
    """Tests for simple workflow execution."""

    def test_two_step_workflow(self):
        engine = WorkflowEngine()
        engine.register_executor("custom", lambda step, inputs: f"Output from {step.name}")

        workflow = WorkflowDefinition(
            id="wf1",
            name="Simple Workflow",
            steps=[
                WorkflowStep(id="s1", name="Step 1", agent_type="custom"),
                WorkflowStep(id="s2", name="Step 2", agent_type="custom"),
            ],
        )

        result = engine.execute(workflow, {"input": "test"})
        assert result.status == "completed"
        assert len(result.step_results) == 2
        assert result.final_output == "Output from Step 2"


class TestExecuteWithInputMapping:
    """Tests for workflow with input mapping."""

    def test_input_mapping(self):
        engine = WorkflowEngine()

        def executor(step, inputs):
            if step.id == "s1":
                return "First output"
            elif step.id == "s2":
                return f"Received: {inputs.get('mapped_input', 'nothing')}"
            return "unknown"

        engine.register_executor("custom", executor)

        workflow = (
            WorkflowBuilder("wf1", "Mapped Workflow")
            .add_step("s1", "Step 1", "custom")
            .add_step("s2", "Step 2", "custom")
            .with_input_mapping("s2", {"mapped_input": "s1.output"})
            .build()
        )

        result = engine.execute(workflow, {})
        assert result.status == "completed"
        assert "First output" in result.step_results[1].output


class TestExecuteWithGovernance:
    """Tests for governance during execution."""

    def test_governance_applied(self):
        engine = WorkflowEngine()
        engine.register_executor("custom", lambda step, inputs: "Output")

        workflow = WorkflowDefinition(
            id="wf1",
            name="Governed Workflow",
            steps=[WorkflowStep(id="s1", name="Step 1", agent_type="custom")],
        )

        result = engine.execute(workflow, {"data": "test@example.com"})
        assert result.status == "completed"
        assert result.step_results[0].receipt_id is not None


class TestExecuteWithStepFailure:
    """Tests for step failure handling."""

    def test_failure_stop(self):
        engine = WorkflowEngine()

        def failing_executor(step, inputs):
            if step.id == "s1":
                raise ValueError("Step failed")
            return "success"

        engine.register_executor("custom", failing_executor)

        workflow = WorkflowDefinition(
            id="wf1",
            name="Failing Workflow",
            steps=[
                WorkflowStep(id="s1", name="Step 1", agent_type="custom", on_failure="stop"),
                WorkflowStep(id="s2", name="Step 2", agent_type="custom"),
            ],
        )

        result = engine.execute(workflow, {})
        assert result.status == "failed"
        assert len(result.step_results) == 1

    def test_failure_skip(self):
        engine = WorkflowEngine()

        def failing_executor(step, inputs):
            if step.id == "s1":
                raise ValueError("Step failed")
            return "success"

        engine.register_executor("custom", failing_executor)

        workflow = WorkflowDefinition(
            id="wf1",
            name="Skip Workflow",
            steps=[
                WorkflowStep(id="s1", name="Step 1", agent_type="custom", on_failure="skip"),
                WorkflowStep(id="s2", name="Step 2", agent_type="custom"),
            ],
        )

        result = engine.execute(workflow, {})
        assert result.status == "completed"
        assert result.step_results[0].status == "failed"
        assert result.step_results[1].status == "success"

    def test_failure_retry(self):
        engine = WorkflowEngine()
        call_count = {"count": 0}

        def retry_executor(step, inputs):
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise ValueError("Retry needed")
            return "success after retry"

        engine.register_executor("custom", retry_executor)

        workflow = WorkflowDefinition(
            id="wf1",
            name="Retry Workflow",
            steps=[
                WorkflowStep(id="s1", name="Step 1", agent_type="custom", on_failure="retry", retry_count=3),
            ],
        )

        result = engine.execute(workflow, {})
        assert result.step_results[0].status == "success"


class TestExecuteWithMaxCost:
    """Tests for max cost limit."""

    def test_max_cost_exceeded(self):
        engine = WorkflowEngine()
        engine.register_executor("custom", lambda step, inputs: "output")

        workflow = WorkflowDefinition(
            id="wf1",
            name="Cost Limited",
            steps=[
                WorkflowStep(id="s1", name="Step 1", agent_type="custom", config={"cost": 5.0}),
                WorkflowStep(id="s2", name="Step 2", agent_type="custom", config={"cost": 5.0}),
                WorkflowStep(id="s3", name="Step 3", agent_type="custom", config={"cost": 5.0}),
            ],
            max_total_cost=10.0,
        )

        result = engine.execute(workflow, {})
        assert result.status == "failed"
        assert "Max cost" in result.step_results[-1].error


class TestWorkflowBuilder:
    """Tests for WorkflowBuilder fluent API."""

    def test_builder_basic(self):
        workflow = (
            WorkflowBuilder("wf1", "Test Workflow")
            .description("A test workflow")
            .add_step("s1", "Step 1", "custom")
            .add_step("s2", "Step 2", "langchain")
            .build()
        )
        assert workflow.id == "wf1"
        assert workflow.description == "A test workflow"
        assert len(workflow.steps) == 2

    def test_builder_with_all_options(self):
        workflow = (
            WorkflowBuilder("wf1", "Full Workflow")
            .add_step("s1", "Step 1", "custom")
            .add_step("s2", "Step 2", "custom")
            .with_input_mapping("s2", {"input": "s1.output"})
            .require_approval("s2")
            .with_governance_policy("pii-protection")
            .with_max_cost(50.0)
            .with_metadata({"team": "engineering"})
            .build()
        )
        assert workflow.governance_policy == "pii-protection"
        assert workflow.max_total_cost == 50.0
        assert "s2" in workflow.require_human_approval
        assert workflow.metadata["team"] == "engineering"


class TestWorkflowTemplates:
    """Tests for pre-built workflow templates."""

    def test_research_critique_rewrite(self):
        workflow = research_critique_rewrite()
        assert workflow.id == "research-critique-rewrite"
        assert len(workflow.steps) == 3
        assert workflow.steps[0].id == "research"
        assert workflow.steps[1].id == "critique"
        assert workflow.steps[2].id == "rewrite"

    def test_multi_agent_consensus(self):
        workflow = multi_agent_consensus()
        assert workflow.id == "multi-agent-consensus"
        assert len(workflow.steps) == 4
        assert workflow.steps[3].id == "synthesize"

    def test_review_and_approve(self):
        workflow = review_and_approve()
        assert workflow.id == "review-and-approve"
        assert "approve" in workflow.require_human_approval


class TestPauseAndResume:
    """Tests for pause and resume functionality."""

    def test_pause_at_approval(self):
        engine = WorkflowEngine()
        engine.register_executor("custom", lambda step, inputs: "output")

        workflow = (
            WorkflowBuilder("wf1", "Approval Workflow")
            .add_step("s1", "Step 1", "custom")
            .add_step("s2", "Approval", "custom")
            .require_approval("s2")
            .add_step("s3", "Step 3", "custom")
            .build()
        )

        result = engine.execute(workflow, {})
        assert result.status == "paused"
        assert result.step_results[-1].status == "pending_approval"

    def test_resume_workflow(self):
        engine = WorkflowEngine()
        engine.register_executor("custom", lambda step, inputs: f"output-{step.id}")

        workflow = (
            WorkflowBuilder("wf1", "Approval Workflow")
            .add_step("s1", "Step 1", "custom")
            .add_step("s2", "Approval", "custom")
            .require_approval("s2")
            .add_step("s3", "Step 3", "custom")
            .build()
        )

        engine.execute(workflow, {})
        resumed = engine.resume("wf1", approval=True)
        assert resumed is not None
        assert resumed.status == "completed"


class TestComplianceReceiptGeneration:
    """Tests for compliance receipt generation."""

    def test_receipt_per_step(self):
        engine = WorkflowEngine()
        engine.register_executor("custom", lambda step, inputs: "output")

        workflow = WorkflowDefinition(
            id="wf1",
            name="Receipt Workflow",
            steps=[
                WorkflowStep(id="s1", name="Step 1", agent_type="custom"),
                WorkflowStep(id="s2", name="Step 2", agent_type="custom"),
            ],
        )

        result = engine.execute(workflow, {})
        assert all(r.receipt_id is not None for r in result.step_results)


class TestAsyncExecution:
    """Tests for async workflow execution."""

    @pytest.mark.asyncio
    async def test_async_execute(self):
        engine = WorkflowEngine()
        engine.register_executor("custom", lambda step, inputs: "async output")

        workflow = WorkflowDefinition(
            id="wf1",
            name="Async Workflow",
            steps=[WorkflowStep(id="s1", name="Step 1", agent_type="custom")],
        )

        result = await engine.execute_async(workflow, {})
        assert result.status == "completed"
        assert result.final_output == "async output"


class TestNoExecutorRegistered:
    """Tests for missing executor handling."""

    def test_missing_executor(self):
        engine = WorkflowEngine()

        workflow = WorkflowDefinition(
            id="wf1",
            name="No Executor",
            steps=[WorkflowStep(id="s1", name="Step 1", agent_type="unknown")],
        )

        result = engine.execute(workflow, {})
        assert result.step_results[0].status == "failed"
        assert "No executor" in result.step_results[0].error
