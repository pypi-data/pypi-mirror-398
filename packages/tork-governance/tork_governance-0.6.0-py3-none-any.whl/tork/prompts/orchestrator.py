"""Orchestrate multi-agent prompt generation and selection."""

from typing import List, Optional

import structlog

from tork.prompts.models import (
    PromptCandidate,
    PromptQuality,
    PromptSelectionCriteria,
    PromptSelectionResult,
    PromptType,
)
from tork.prompts.generator import PromptGenerator
from tork.prompts.selector import PromptSelector

logger = structlog.get_logger(__name__)


class PromptOrchestrator:
    """Orchestrate multi-agent prompt generation and selection."""

    def __init__(
        self,
        generator: Optional[PromptGenerator] = None,
        selector: Optional[PromptSelector] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            generator: PromptGenerator instance.
            selector: PromptSelector instance.
        """
        self._generator = generator or PromptGenerator()
        self._selector = selector or PromptSelector()
        logger.info("PromptOrchestrator initialized")

    @property
    def generator(self) -> PromptGenerator:
        """Get the prompt generator."""
        return self._generator

    @property
    def selector(self) -> PromptSelector:
        """Get the prompt selector."""
        return self._selector

    def orchestrate(
        self,
        task: str,
        prompt_type: PromptType,
        agent_ids: List[str],
        criteria: Optional[PromptSelectionCriteria] = None,
        context: str = "",
    ) -> PromptSelectionResult:
        """
        Generate prompts from multiple agents and select the best.

        Args:
            task: The task description.
            prompt_type: Type of prompt to generate.
            agent_ids: List of agent IDs to use.
            criteria: Selection criteria.
            context: Optional additional context.

        Returns:
            PromptSelectionResult with best prompt.
        """
        logger.info(
            "Orchestrating prompt generation",
            task=task,
            prompt_type=prompt_type.value,
            agent_count=len(agent_ids),
        )

        candidates = self._generator.generate_multiple(
            task=task,
            prompt_type=prompt_type,
            agent_ids=agent_ids,
            context=context,
        )

        if not candidates:
            fallback = PromptCandidate(
                prompt_type=prompt_type,
                content=f"[Fallback prompt for: {task}]",
                generator_agent="fallback",
                quality=PromptQuality.POOR,
            )
            return PromptSelectionResult(
                selected=fallback,
                candidates=[fallback],
                selection_reasoning="No candidates generated, using fallback",
                confidence=0.1,
                total_evaluated=0,
            )

        return self._selector.select(candidates, criteria)

    def refine(
        self,
        prompt: PromptCandidate,
        refiner_agent: str,
        feedback: str = "",
    ) -> PromptCandidate:
        """
        Refine a prompt using another agent.

        Args:
            prompt: The prompt to refine.
            refiner_agent: Agent ID to use for refinement.
            feedback: Optional feedback for refinement.

        Returns:
            Refined PromptCandidate.
        """
        refinement_task = f"Refine the following prompt:\n\n{prompt.content}"
        if feedback:
            refinement_task += f"\n\nFeedback: {feedback}"

        refined = self._generator.generate(
            task=refinement_task,
            prompt_type=PromptType.REFINEMENT,
            agent_id=refiner_agent,
            context=f"Original quality: {prompt.quality.value}",
        )

        refined.metadata["original_id"] = prompt.id
        refined.metadata["original_generator"] = prompt.generator_agent

        return refined

    def iterate(
        self,
        task: str,
        agent_ids: List[str],
        max_iterations: int = 3,
        criteria: Optional[PromptSelectionCriteria] = None,
    ) -> PromptSelectionResult:
        """
        Iteratively generate and refine until quality threshold met.

        Args:
            task: The task description.
            agent_ids: List of agent IDs.
            max_iterations: Maximum refinement iterations.
            criteria: Selection criteria with quality threshold.

        Returns:
            PromptSelectionResult with best prompt.
        """
        criteria = criteria or PromptSelectionCriteria()
        target_quality = criteria.prefer_quality

        result = self.orchestrate(
            task=task,
            prompt_type=PromptType.SYSTEM,
            agent_ids=agent_ids,
            criteria=criteria,
        )

        quality_order = [
            PromptQuality.EXCELLENT,
            PromptQuality.GOOD,
            PromptQuality.ACCEPTABLE,
            PromptQuality.POOR,
            PromptQuality.REJECTED,
        ]
        target_index = quality_order.index(target_quality)
        current_index = quality_order.index(result.selected.quality)

        iteration = 0
        while current_index > target_index and iteration < max_iterations:
            if not agent_ids:
                break

            refiner = agent_ids[iteration % len(agent_ids)]
            refined = self.refine(
                result.selected,
                refiner,
                feedback=f"Please improve to {target_quality.value} quality",
            )

            if quality_order.index(refined.quality) < current_index:
                result = PromptSelectionResult(
                    selected=refined,
                    candidates=result.candidates + [refined],
                    selection_reasoning=f"Refined in iteration {iteration + 1}",
                    confidence=min(1.0, result.confidence + 0.1),
                    total_evaluated=result.total_evaluated + 1,
                )
                current_index = quality_order.index(refined.quality)

            iteration += 1

        return result
