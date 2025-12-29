"""Pre-built workflow templates."""

from tork.workflows.builder import WorkflowBuilder
from tork.workflows.models import WorkflowDefinition


def research_critique_rewrite() -> WorkflowDefinition:
    """
    Research → Critique → Rewrite workflow template.

    A three-step workflow where:
    1. Research agent gathers information
    2. Critic agent reviews and provides feedback
    3. Writer agent rewrites based on feedback

    Returns:
        WorkflowDefinition for the research-critique-rewrite pattern.
    """
    return (
        WorkflowBuilder("research-critique-rewrite", "Research, Critique, and Rewrite")
        .description("Gather research, critique it, then rewrite with improvements")
        .add_step(
            step_id="research",
            name="Research",
            agent_type="custom",
            config={"role": "researcher"},
        )
        .add_step(
            step_id="critique",
            name="Critique",
            agent_type="custom",
            config={"role": "critic"},
        )
        .with_input_mapping("critique", {"research_output": "research.output"})
        .add_step(
            step_id="rewrite",
            name="Rewrite",
            agent_type="custom",
            config={"role": "writer"},
        )
        .with_input_mapping(
            "rewrite",
            {"research": "research.output", "feedback": "critique.output"},
        )
        .build()
    )


def multi_agent_consensus() -> WorkflowDefinition:
    """
    Get responses from multiple agents, then synthesize.

    A four-step workflow where:
    1. Agent A provides its perspective
    2. Agent B provides its perspective
    3. Agent C provides its perspective
    4. Synthesizer combines all perspectives

    Returns:
        WorkflowDefinition for the multi-agent consensus pattern.
    """
    return (
        WorkflowBuilder("multi-agent-consensus", "Multi-Agent Consensus")
        .description("Gather perspectives from multiple agents and synthesize")
        .add_step(
            step_id="agent_a",
            name="Agent A Perspective",
            agent_type="custom",
            config={"perspective": "technical"},
        )
        .add_step(
            step_id="agent_b",
            name="Agent B Perspective",
            agent_type="custom",
            config={"perspective": "business"},
        )
        .add_step(
            step_id="agent_c",
            name="Agent C Perspective",
            agent_type="custom",
            config={"perspective": "user"},
        )
        .add_step(
            step_id="synthesize",
            name="Synthesize",
            agent_type="custom",
            config={"role": "synthesizer"},
        )
        .with_input_mapping(
            "synthesize",
            {
                "technical": "agent_a.output",
                "business": "agent_b.output",
                "user": "agent_c.output",
            },
        )
        .build()
    )


def review_and_approve() -> WorkflowDefinition:
    """
    Draft → Review → Human Approval → Finalize.

    A four-step workflow where:
    1. Drafter creates initial content
    2. Reviewer checks and suggests changes
    3. Human approves (workflow pauses here)
    4. Finalizer produces the final version

    Returns:
        WorkflowDefinition for the review-and-approve pattern.
    """
    return (
        WorkflowBuilder("review-and-approve", "Review and Approve")
        .description("Draft content, review it, get human approval, then finalize")
        .add_step(
            step_id="draft",
            name="Draft",
            agent_type="custom",
            config={"role": "drafter"},
        )
        .add_step(
            step_id="review",
            name="Review",
            agent_type="custom",
            config={"role": "reviewer"},
        )
        .with_input_mapping("review", {"draft": "draft.output"})
        .add_step(
            step_id="approve",
            name="Human Approval",
            agent_type="custom",
            config={"role": "approval_gate"},
        )
        .require_approval("approve")
        .with_input_mapping("approve", {"reviewed": "review.output"})
        .add_step(
            step_id="finalize",
            name="Finalize",
            agent_type="custom",
            config={"role": "finalizer"},
        )
        .with_input_mapping(
            "finalize", {"approved": "approve.output", "draft": "draft.output"}
        )
        .build()
    )
