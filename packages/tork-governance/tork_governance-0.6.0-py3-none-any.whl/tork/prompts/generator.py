"""Generate prompts using specified agents."""

import re
import time
from typing import Any, Callable, Dict, List, Optional

import structlog

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest, PolicyDecision
from tork.prompts.models import PromptCandidate, PromptQuality, PromptType

logger = structlog.get_logger(__name__)


class PromptGenerator:
    """Generate prompts using specified agents."""

    def __init__(self, governance_engine: Optional[GovernanceEngine] = None):
        """
        Initialize the prompt generator.

        Args:
            governance_engine: Optional GovernanceEngine for policy evaluation.
        """
        self._governance_engine = governance_engine or GovernanceEngine()
        self._executors: Dict[str, Callable] = {}

        logger.info("PromptGenerator initialized")

    def register_executor(
        self,
        agent_id: str,
        executor: Callable[[str], Dict[str, Any]],
    ) -> None:
        """
        Register an executor for an agent.

        Args:
            agent_id: The agent identifier.
            executor: Function that takes a meta-prompt and returns {'content': str, 'model': str}.
        """
        self._executors[agent_id] = executor
        logger.info("Executor registered", agent_id=agent_id)

    def generate(
        self,
        task: str,
        prompt_type: PromptType,
        agent_id: str,
        context: str = "",
    ) -> PromptCandidate:
        """
        Generate a prompt using specified agent.

        Args:
            task: The task description.
            prompt_type: Type of prompt to generate.
            agent_id: The agent to use.
            context: Optional additional context.

        Returns:
            Generated PromptCandidate.
        """
        meta_prompt = self._build_meta_prompt(task, prompt_type, context)

        start_time = time.time()

        if agent_id in self._executors:
            executor = self._executors[agent_id]
            result = executor(meta_prompt)
            content = result.get("content", "")
            model = result.get("model", "")
        else:
            content = f"[Generated {prompt_type.value} prompt for: {task}]"
            model = "default"

        generation_time_ms = int((time.time() - start_time) * 1000)

        request = EvaluationRequest(
            payload={"content": content, "prompt_type": prompt_type.value},
            agent_id=agent_id,
            action="generate_prompt",
        )
        result = self._governance_engine.evaluate(request)

        if result.decision == PolicyDecision.DENY:
            content = "[Prompt blocked by governance]"
        elif result.decision == PolicyDecision.REDACT and result.modified_payload:
            content = result.modified_payload.get("content", content)

        scores = self._score_prompt(content)
        quality = self._assess_quality(scores)

        return PromptCandidate(
            prompt_type=prompt_type,
            content=content,
            generator_agent=agent_id,
            generator_model=model,
            quality=quality,
            clarity_score=scores["clarity"],
            specificity_score=scores["specificity"],
            safety_score=scores["safety"],
            token_count=len(content.split()),
            generation_time_ms=generation_time_ms,
        )

    def generate_multiple(
        self,
        task: str,
        prompt_type: PromptType,
        agent_ids: List[str],
        context: str = "",
    ) -> List[PromptCandidate]:
        """
        Generate prompts from multiple agents.

        Args:
            task: The task description.
            prompt_type: Type of prompt to generate.
            agent_ids: List of agent IDs to use.
            context: Optional additional context.

        Returns:
            List of generated PromptCandidates.
        """
        candidates = []
        for agent_id in agent_ids:
            try:
                candidate = self.generate(task, prompt_type, agent_id, context)
                candidates.append(candidate)
            except Exception as e:
                logger.error("Failed to generate prompt", agent_id=agent_id, error=str(e))
        return candidates

    def _build_meta_prompt(
        self,
        task: str,
        prompt_type: PromptType,
        context: str = "",
    ) -> str:
        """Build a meta-prompt for the given task and type."""
        type_instructions = {
            PromptType.SYSTEM: "Generate a system prompt that defines the AI assistant's role and behavior.",
            PromptType.USER: "Generate a user prompt that clearly states what the user wants.",
            PromptType.ASSISTANT: "Generate an assistant response template.",
            PromptType.CRITIQUE: "Generate a critique prompt that analyzes and evaluates content.",
            PromptType.SYNTHESIS: "Generate a synthesis prompt that combines multiple perspectives.",
            PromptType.REFINEMENT: "Generate a refinement prompt that improves existing content.",
            PromptType.EXPANSION: "Generate an expansion prompt that adds more detail.",
            PromptType.COMPRESSION: "Generate a compression prompt that summarizes concisely.",
        }

        instruction = type_instructions.get(prompt_type, "Generate a prompt.")
        
        meta = f"""Task: {task}

{instruction}

Requirements:
- Be clear and specific
- Include any necessary constraints
- Ensure the prompt is actionable
"""
        if context:
            meta += f"\nContext: {context}"

        return meta

    def _score_prompt(self, content: str) -> Dict[str, float]:
        """
        Score a prompt for clarity, specificity, and safety.

        Args:
            content: The prompt content.

        Returns:
            Dictionary with clarity, specificity, safety scores.
        """
        if not content or content.startswith("["):
            return {"clarity": 0.0, "specificity": 0.0, "safety": 0.5}

        word_count = len(content.split())
        sentence_count = len(re.split(r'[.!?]', content))

        clarity = min(1.0, 0.3 + (sentence_count * 0.1) + (0.01 * min(word_count, 50)))
        
        specific_words = ["specific", "exactly", "must", "should", "require", "include"]
        specificity = min(1.0, 0.3 + sum(0.1 for w in specific_words if w in content.lower()))

        unsafe_patterns = ["hack", "exploit", "bypass", "illegal", "harm"]
        safety_penalty = sum(0.2 for p in unsafe_patterns if p in content.lower())
        safety = max(0.0, 1.0 - safety_penalty)

        return {
            "clarity": round(clarity, 2),
            "specificity": round(specificity, 2),
            "safety": round(safety, 2),
        }

    def _assess_quality(self, scores: Dict[str, float]) -> PromptQuality:
        """
        Assess overall quality from scores.

        Args:
            scores: Dictionary with clarity, specificity, safety scores.

        Returns:
            PromptQuality assessment.
        """
        avg = (scores["clarity"] + scores["specificity"] + scores["safety"]) / 3

        if scores["safety"] < 0.5:
            return PromptQuality.REJECTED
        if avg >= 0.85:
            return PromptQuality.EXCELLENT
        if avg >= 0.7:
            return PromptQuality.GOOD
        if avg >= 0.5:
            return PromptQuality.ACCEPTABLE
        return PromptQuality.POOR
