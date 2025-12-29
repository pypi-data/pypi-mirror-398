"""Workflow execution engine with governance."""

import asyncio
import time
from typing import Any, Callable, Dict, Optional
import structlog

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest, PolicyDecision
from tork.compliance.receipts import ReceiptGenerator
from tork.workflows.models import (
    WorkflowDefinition,
    WorkflowStep,
    StepResult,
    WorkflowResult,
)

logger = structlog.get_logger(__name__)


class WorkflowExecutionError(Exception):
    """Error during workflow execution."""
    pass


class MaxCostExceededError(WorkflowExecutionError):
    """Workflow exceeded maximum cost limit."""
    pass


class HumanApprovalRequired(Exception):
    """Step requires human approval before continuing."""
    
    def __init__(self, step_id: str, workflow_id: str):
        self.step_id = step_id
        self.workflow_id = workflow_id
        super().__init__(f"Step '{step_id}' requires human approval")


class WorkflowEngine:
    """Execute governed workflows with chaining support."""

    def __init__(
        self,
        governance_engine: Optional[GovernanceEngine] = None,
        signing_key: str = "workflow-secret",
    ):
        """
        Initialize the workflow engine.

        Args:
            governance_engine: Optional GovernanceEngine for policy evaluation.
            signing_key: Key for signing compliance receipts.
        """
        self.governance_engine = governance_engine or GovernanceEngine()
        self.receipt_generator = ReceiptGenerator(signing_key=signing_key)
        self._executors: Dict[str, Callable] = {}
        self._paused_workflows: Dict[str, Dict[str, Any]] = {}
        logger.info("WorkflowEngine initialized")

    def register_executor(self, agent_type: str, executor: Callable) -> None:
        """
        Register a step executor for an agent type.

        Args:
            agent_type: Type identifier (e.g., 'langchain', 'custom').
            executor: Callable that executes the step. Signature: (step, inputs) -> output.
        """
        self._executors[agent_type] = executor
        logger.info("Executor registered", agent_type=agent_type)

    def execute(
        self,
        workflow: WorkflowDefinition,
        initial_input: Dict[str, Any],
    ) -> WorkflowResult:
        """
        Execute a workflow synchronously.

        Args:
            workflow: The workflow definition to execute.
            initial_input: Initial input data for the first step.

        Returns:
            WorkflowResult with all step results.
        """
        start_time = time.time()
        step_results: Dict[str, StepResult] = {}
        total_cost = 0.0
        total_tokens = 0
        final_output = None
        status = "completed"

        for step in workflow.steps:
            if step.id in workflow.require_human_approval:
                self._paused_workflows[workflow.id] = {
                    "workflow": workflow,
                    "initial_input": initial_input,
                    "step_results": dict(step_results),
                    "pending_step_id": step.id,
                    "total_cost": total_cost,
                    "total_tokens": total_tokens,
                    "start_time": start_time,
                }
                step_results[step.id] = StepResult(
                    step_id=step.id,
                    status="pending_approval",
                )
                status = "paused"
                break

            if workflow.max_total_cost is not None and total_cost >= workflow.max_total_cost:
                status = "failed"
                step_results[step.id] = StepResult(
                    step_id=step.id,
                    status="failed",
                    error=f"Max cost exceeded: {total_cost} >= {workflow.max_total_cost}",
                )
                break

            inputs = self._map_inputs(step, step_results, initial_input)
            result = self._execute_step_with_retries(step, inputs, {"workflow_id": workflow.id}, workflow)

            step_results[step.id] = result
            total_cost += result.cost
            total_tokens += result.tokens_used
            final_output = result.output

            if result.status == "failed":
                if step.on_failure == "stop":
                    status = "failed"
                    break
                elif step.on_failure == "skip":
                    continue

        total_time = int((time.time() - start_time) * 1000)

        return WorkflowResult(
            workflow_id=workflow.id,
            status=status,
            step_results=list(step_results.values()),
            total_execution_time_ms=total_time,
            total_tokens_used=total_tokens,
            total_cost=total_cost,
            final_output=final_output,
        )

    def _execute_step_with_retries(
        self,
        step: WorkflowStep,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
        workflow: WorkflowDefinition,
    ) -> StepResult:
        """Execute a step with retry and fallback handling."""
        result = self._execute_step(step, inputs, context)

        if result.status == "failed":
            if step.on_failure == "retry":
                for _ in range(step.retry_count):
                    result = self._execute_step(step, inputs, context)
                    if result.status == "success":
                        break

            if result.status == "failed" and step.on_failure == "fallback" and step.fallback_step_id:
                fallback_step = next(
                    (s for s in workflow.steps if s.id == step.fallback_step_id),
                    None,
                )
                if fallback_step:
                    fallback_result = self._execute_step(fallback_step, inputs, context)
                    fallback_result = StepResult(
                        step_id=step.id,
                        status=fallback_result.status,
                        output=fallback_result.output,
                        error=fallback_result.error,
                        execution_time_ms=result.execution_time_ms + fallback_result.execution_time_ms,
                        tokens_used=result.tokens_used + fallback_result.tokens_used,
                        cost=result.cost + fallback_result.cost,
                        receipt_id=fallback_result.receipt_id,
                    )
                    result = fallback_result

        return result

    async def execute_async(
        self,
        workflow: WorkflowDefinition,
        initial_input: Dict[str, Any],
    ) -> WorkflowResult:
        """
        Execute a workflow asynchronously.

        Args:
            workflow: The workflow definition to execute.
            initial_input: Initial input data for the first step.

        Returns:
            WorkflowResult with all step results.
        """
        return await asyncio.to_thread(self.execute, workflow, initial_input)

    def _execute_step(
        self,
        step: WorkflowStep,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> StepResult:
        """
        Execute a single step with governance.

        Args:
            step: The step to execute.
            inputs: Input data for the step.
            context: Execution context.

        Returns:
            StepResult with output and metadata.
        """
        start_time = time.time()
        receipt_id = None

        request = EvaluationRequest(
            payload={"step_id": step.id, "inputs": inputs},
            agent_id=f"workflow-{context.get('workflow_id', 'unknown')}",
            action="step_execute",
        )
        pre_result = self.governance_engine.evaluate(request)

        if pre_result.decision == PolicyDecision.DENY:
            return StepResult(
                step_id=step.id,
                status="failed",
                error=f"Step blocked by governance: {pre_result.violations}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        governed_inputs = pre_result.modified_payload.get("inputs", inputs) if pre_result.modified_payload else inputs

        executor = self._executors.get(step.agent_type)
        if not executor:
            return StepResult(
                step_id=step.id,
                status="failed",
                error=f"No executor registered for agent type: {step.agent_type}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        try:
            output = executor(step, governed_inputs)
        except Exception as e:
            return StepResult(
                step_id=step.id,
                status="failed",
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        post_request = EvaluationRequest(
            payload={"step_id": step.id, "output": output},
            agent_id=f"workflow-{context.get('workflow_id', 'unknown')}",
            action="step_output",
        )
        post_result = self.governance_engine.evaluate(post_request)

        receipt = self.receipt_generator.create_receipt(
            result=post_result,
            request=post_request,
        )
        receipt_id = receipt.receipt_id

        governed_output = post_result.modified_payload.get("output", output) if post_result.modified_payload else output

        return StepResult(
            step_id=step.id,
            status="success",
            output=governed_output,
            execution_time_ms=int((time.time() - start_time) * 1000),
            tokens_used=step.config.get("tokens_used", 0),
            cost=step.config.get("cost", 0.0),
            receipt_id=receipt_id,
        )

    def _map_inputs(
        self,
        step: WorkflowStep,
        previous_results: Dict[str, StepResult],
        initial_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Map outputs from previous steps to current step inputs.

        Args:
            step: The current step.
            previous_results: Results from previous steps.
            initial_input: Initial workflow input.

        Returns:
            Mapped inputs for the current step.
        """
        inputs = dict(initial_input)

        for target_key, source_path in step.input_mapping.items():
            parts = source_path.split(".")
            if len(parts) >= 2:
                step_id = parts[0]
                field = parts[1]
                if step_id in previous_results:
                    result = previous_results[step_id]
                    if field == "output":
                        inputs[target_key] = result.output
                    elif hasattr(result, field):
                        inputs[target_key] = getattr(result, field)

        return inputs

    def pause(self, workflow_id: str) -> bool:
        """
        Pause a running workflow.

        Args:
            workflow_id: The workflow to pause.

        Returns:
            True if paused successfully.
        """
        if workflow_id in self._paused_workflows:
            return True
        return False

    def resume(self, workflow_id: str, approval: bool = True) -> Optional[WorkflowResult]:
        """
        Resume a paused workflow after human approval.

        Args:
            workflow_id: The workflow to resume.
            approval: Whether the human approved continuation.

        Returns:
            WorkflowResult if resumed, None if not found.
        """
        if workflow_id not in self._paused_workflows:
            return None

        state = self._paused_workflows.pop(workflow_id)
        workflow = state["workflow"]
        pending_step_id = state["pending_step_id"]
        step_results = state["step_results"]
        initial_input = state["initial_input"]
        total_cost = state["total_cost"]
        total_tokens = state["total_tokens"]
        original_start_time = state["start_time"]

        if not approval:
            return WorkflowResult(
                workflow_id=workflow_id,
                status="cancelled",
                step_results=list(step_results.values()),
                total_cost=total_cost,
                total_tokens_used=total_tokens,
            )

        found_pending = False
        status = "completed"
        final_output = None

        for step in workflow.steps:
            if step.id == pending_step_id:
                found_pending = True

            if not found_pending:
                continue

            if workflow.max_total_cost is not None and total_cost >= workflow.max_total_cost:
                status = "failed"
                step_results[step.id] = StepResult(
                    step_id=step.id,
                    status="failed",
                    error=f"Max cost exceeded: {total_cost} >= {workflow.max_total_cost}",
                )
                break

            inputs = self._map_inputs(step, step_results, initial_input)
            result = self._execute_step_with_retries(step, inputs, {"workflow_id": workflow_id}, workflow)
            step_results[step.id] = result
            total_cost += result.cost
            total_tokens += result.tokens_used
            final_output = result.output

            if result.status == "failed":
                if step.on_failure == "stop":
                    status = "failed"
                    break
                elif step.on_failure == "skip":
                    continue

        total_time = int((time.time() - original_start_time) * 1000)

        return WorkflowResult(
            workflow_id=workflow_id,
            status=status,
            step_results=list(step_results.values()),
            total_execution_time_ms=total_time,
            total_tokens_used=total_tokens,
            total_cost=total_cost,
            final_output=final_output,
        )
