"""Tests for the Agent-Selectable Prompts system."""

import pytest

from tork.prompts import (
    PromptType,
    PromptQuality,
    PromptCandidate,
    PromptSelectionCriteria,
    PromptSelectionResult,
    PromptGenerator,
    PromptSelector,
    PromptOrchestrator,
    critique_meta_prompt,
    synthesis_meta_prompt,
    refinement_meta_prompt,
    expansion_meta_prompt,
    compression_meta_prompt,
)
from tork.core.engine import GovernanceEngine


class TestPromptTypeEnum:
    """Tests for PromptType enum."""

    def test_all_types(self):
        assert PromptType.SYSTEM == "system"
        assert PromptType.USER == "user"
        assert PromptType.ASSISTANT == "assistant"
        assert PromptType.CRITIQUE == "critique"
        assert PromptType.SYNTHESIS == "synthesis"
        assert PromptType.REFINEMENT == "refinement"
        assert PromptType.EXPANSION == "expansion"
        assert PromptType.COMPRESSION == "compression"


class TestPromptQualityEnum:
    """Tests for PromptQuality enum."""

    def test_all_qualities(self):
        assert PromptQuality.EXCELLENT == "excellent"
        assert PromptQuality.GOOD == "good"
        assert PromptQuality.ACCEPTABLE == "acceptable"
        assert PromptQuality.POOR == "poor"
        assert PromptQuality.REJECTED == "rejected"


class TestPromptCandidateModel:
    """Tests for PromptCandidate model."""

    def test_basic_candidate(self):
        candidate = PromptCandidate(
            prompt_type=PromptType.SYSTEM,
            content="You are a helpful assistant.",
            generator_agent="gpt-4",
        )
        assert candidate.prompt_type == PromptType.SYSTEM
        assert candidate.quality == PromptQuality.ACCEPTABLE
        assert candidate.safety_score == 1.0

    def test_candidate_with_all_fields(self):
        candidate = PromptCandidate(
            prompt_type=PromptType.CRITIQUE,
            content="Analyze the following...",
            generator_agent="claude-3",
            generator_model="claude-3-opus",
            quality=PromptQuality.EXCELLENT,
            clarity_score=0.9,
            specificity_score=0.85,
            safety_score=0.95,
            token_count=100,
            generation_time_ms=500,
        )
        assert candidate.generator_model == "claude-3-opus"
        assert candidate.clarity_score == 0.9


class TestPromptSelectionCriteriaModel:
    """Tests for PromptSelectionCriteria model."""

    def test_default_criteria(self):
        criteria = PromptSelectionCriteria()
        assert criteria.min_safety == 0.8
        assert criteria.max_tokens == 4096
        assert criteria.prefer_quality == PromptQuality.GOOD

    def test_custom_criteria(self):
        criteria = PromptSelectionCriteria(
            min_clarity=0.7,
            min_safety=0.9,
            preferred_generators=["gpt-4", "claude-3"],
            blocked_generators=["low-quality-model"],
        )
        assert criteria.min_clarity == 0.7
        assert "gpt-4" in criteria.preferred_generators


class TestPromptSelectionResultModel:
    """Tests for PromptSelectionResult model."""

    def test_result(self):
        candidate = PromptCandidate(
            prompt_type=PromptType.SYSTEM,
            content="Test",
            generator_agent="test-agent",
        )
        result = PromptSelectionResult(
            selected=candidate,
            candidates=[candidate],
            selection_reasoning="Best match",
            confidence=0.9,
        )
        assert result.confidence == 0.9


class TestPromptGenerator:
    """Tests for PromptGenerator."""

    def test_initialization(self):
        generator = PromptGenerator()
        assert generator._governance_engine is not None

    def test_register_executor(self):
        generator = PromptGenerator()
        generator.register_executor("test-agent", lambda x: {"content": "test", "model": "test"})
        assert "test-agent" in generator._executors

    def test_generate_basic(self):
        generator = PromptGenerator()
        candidate = generator.generate(
            task="Write a greeting",
            prompt_type=PromptType.SYSTEM,
            agent_id="default-agent",
        )
        assert candidate.generator_agent == "default-agent"
        assert candidate.prompt_type == PromptType.SYSTEM

    def test_generate_with_executor(self):
        generator = PromptGenerator()

        def mock_executor(meta_prompt):
            return {"content": "Custom generated prompt", "model": "mock-v1"}

        generator.register_executor("mock-agent", mock_executor)
        candidate = generator.generate(
            task="Test task",
            prompt_type=PromptType.USER,
            agent_id="mock-agent",
        )
        assert candidate.content == "Custom generated prompt"
        assert candidate.generator_model == "mock-v1"

    def test_generate_multiple(self):
        generator = PromptGenerator()
        candidates = generator.generate_multiple(
            task="Write a story",
            prompt_type=PromptType.SYSTEM,
            agent_ids=["agent-1", "agent-2", "agent-3"],
        )
        assert len(candidates) == 3

    def test_prompt_scoring(self):
        generator = PromptGenerator()
        scores = generator._score_prompt("This is a clear and specific prompt that must include details.")
        assert "clarity" in scores
        assert "specificity" in scores
        assert "safety" in scores
        assert scores["specificity"] > 0.3

    def test_quality_assessment(self):
        generator = PromptGenerator()
        
        high_scores = {"clarity": 0.9, "specificity": 0.9, "safety": 0.95}
        assert generator._assess_quality(high_scores) == PromptQuality.EXCELLENT

        low_safety = {"clarity": 0.9, "specificity": 0.9, "safety": 0.3}
        assert generator._assess_quality(low_safety) == PromptQuality.REJECTED


class TestPromptSelector:
    """Tests for PromptSelector."""

    def test_initialization(self):
        selector = PromptSelector()
        assert selector._governance_engine is not None

    def test_select_basic(self):
        selector = PromptSelector()
        candidates = [
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="Prompt 1",
                generator_agent="agent-1",
                clarity_score=0.7,
                safety_score=0.9,
            ),
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="Prompt 2",
                generator_agent="agent-2",
                clarity_score=0.9,
                safety_score=0.9,
            ),
        ]
        result = selector.select(candidates)
        assert result.selected.generator_agent == "agent-2"

    def test_select_with_criteria(self):
        selector = PromptSelector()
        candidates = [
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="Prompt 1",
                generator_agent="preferred-agent",
                clarity_score=0.7,
                safety_score=0.9,
            ),
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="Prompt 2",
                generator_agent="other-agent",
                clarity_score=0.8,
                safety_score=0.9,
            ),
        ]
        criteria = PromptSelectionCriteria(preferred_generators=["preferred-agent"])
        result = selector.select(candidates, criteria)
        assert result.selected.generator_agent == "preferred-agent"

    def test_blocked_generators(self):
        selector = PromptSelector()
        candidates = [
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="Prompt 1",
                generator_agent="blocked-agent",
                clarity_score=0.95,
                safety_score=0.9,
            ),
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="Prompt 2",
                generator_agent="allowed-agent",
                clarity_score=0.7,
                safety_score=0.9,
            ),
        ]
        criteria = PromptSelectionCriteria(blocked_generators=["blocked-agent"])
        result = selector.select(candidates, criteria)
        assert result.selected.generator_agent == "allowed-agent"

    def test_safety_threshold(self):
        selector = PromptSelector()
        candidates = [
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="Unsafe prompt",
                generator_agent="agent-1",
                safety_score=0.3,
            ),
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="Safe prompt",
                generator_agent="agent-2",
                safety_score=0.95,
            ),
        ]
        criteria = PromptSelectionCriteria(min_safety=0.8)
        result = selector.select(candidates, criteria)
        assert result.selected.generator_agent == "agent-2"

    def test_rank(self):
        selector = PromptSelector()
        candidates = [
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="Low",
                generator_agent="agent-1",
                clarity_score=0.3,
            ),
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="High",
                generator_agent="agent-2",
                clarity_score=0.9,
            ),
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="Medium",
                generator_agent="agent-3",
                clarity_score=0.6,
            ),
        ]
        ranked = selector.rank(candidates)
        assert ranked[0].generator_agent == "agent-2"
        assert ranked[2].generator_agent == "agent-1"


class TestPromptOrchestrator:
    """Tests for PromptOrchestrator."""

    def test_initialization(self):
        orchestrator = PromptOrchestrator()
        assert orchestrator._generator is not None
        assert orchestrator._selector is not None

    def test_orchestrate(self):
        orchestrator = PromptOrchestrator()
        result = orchestrator.orchestrate(
            task="Write a poem",
            prompt_type=PromptType.SYSTEM,
            agent_ids=["agent-1", "agent-2"],
        )
        assert result.selected is not None
        assert result.total_evaluated == 2

    def test_refine(self):
        orchestrator = PromptOrchestrator()
        original = PromptCandidate(
            prompt_type=PromptType.SYSTEM,
            content="Original prompt",
            generator_agent="original-agent",
            quality=PromptQuality.ACCEPTABLE,
        )
        refined = orchestrator.refine(original, "refiner-agent", "Make it clearer")
        assert refined.prompt_type == PromptType.REFINEMENT
        assert refined.metadata.get("original_id") == original.id

    def test_iterate(self):
        orchestrator = PromptOrchestrator()
        result = orchestrator.iterate(
            task="Complex task",
            agent_ids=["agent-1", "agent-2"],
            max_iterations=2,
        )
        assert result.selected is not None


class TestMetaPromptTemplates:
    """Tests for meta-prompt templates."""

    def test_critique_meta_prompt(self):
        prompt = critique_meta_prompt("Review this code", "Python code")
        assert "critique" in prompt.lower()
        assert "Review this code" in prompt

    def test_synthesis_meta_prompt(self):
        prompt = synthesis_meta_prompt("Combine these ideas")
        assert "synthesis" in prompt.lower()
        assert "perspectives" in prompt.lower()

    def test_refinement_meta_prompt(self):
        prompt = refinement_meta_prompt("Original text", "Add more detail")
        assert "refine" in prompt.lower()
        assert "Original text" in prompt
        assert "Add more detail" in prompt

    def test_expansion_meta_prompt(self):
        prompt = expansion_meta_prompt("Brief task")
        assert "expand" in prompt.lower()
        assert "Brief task" in prompt

    def test_compression_meta_prompt(self):
        prompt = compression_meta_prompt("Very long and verbose task description")
        assert "compress" in prompt.lower()


class TestGovernanceIntegration:
    """Tests for governance integration."""

    def test_generator_with_governance(self):
        gov_engine = GovernanceEngine()
        generator = PromptGenerator(governance_engine=gov_engine)
        candidate = generator.generate(
            task="test@example.com",
            prompt_type=PromptType.SYSTEM,
            agent_id="test-agent",
        )
        assert candidate is not None

    def test_selector_with_governance(self):
        gov_engine = GovernanceEngine()
        selector = PromptSelector(governance_engine=gov_engine)
        candidates = [
            PromptCandidate(
                prompt_type=PromptType.SYSTEM,
                content="Test",
                generator_agent="agent",
            )
        ]
        result = selector.select(candidates)
        assert result.selected is not None
