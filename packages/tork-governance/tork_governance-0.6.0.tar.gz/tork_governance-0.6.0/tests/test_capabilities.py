"""Tests for the Agent Capability Labels system."""

import pytest

from tork.capabilities import (
    CapabilityLevel,
    PerformanceMetric,
    AgentCapability,
    AgentProfile,
    CapabilityRegistry,
    TaskMatcher,
    gpt4_profile,
    gpt4_turbo_profile,
    claude3_opus_profile,
    claude3_sonnet_profile,
    gemini_pro_profile,
    llama3_profile,
)
from tork.capabilities.registry import ProfileNotFoundError


class TestCapabilityLevelEnum:
    """Tests for CapabilityLevel enum."""

    def test_all_levels(self):
        assert CapabilityLevel.BASIC == "basic"
        assert CapabilityLevel.INTERMEDIATE == "intermediate"
        assert CapabilityLevel.ADVANCED == "advanced"
        assert CapabilityLevel.EXPERT == "expert"


class TestPerformanceMetricEnum:
    """Tests for PerformanceMetric enum."""

    def test_all_metrics(self):
        assert PerformanceMetric.SPEED == "speed"
        assert PerformanceMetric.ACCURACY == "accuracy"
        assert PerformanceMetric.CREATIVITY == "creativity"
        assert PerformanceMetric.SAFETY == "safety"
        assert PerformanceMetric.COST == "cost"
        assert PerformanceMetric.CONTEXT == "context"


class TestAgentCapabilityModel:
    """Tests for AgentCapability model."""

    def test_basic_capability(self):
        cap = AgentCapability(name="coding")
        assert cap.name == "coding"
        assert cap.level == CapabilityLevel.INTERMEDIATE
        assert cap.score == 0.5
        assert cap.verified is False

    def test_capability_with_all_fields(self):
        cap = AgentCapability(
            name="analysis",
            level=CapabilityLevel.EXPERT,
            score=0.95,
            verified=True,
            metadata={"benchmark": "test-v1"},
        )
        assert cap.level == CapabilityLevel.EXPERT
        assert cap.score == 0.95
        assert cap.verified is True


class TestAgentProfileModel:
    """Tests for AgentProfile model."""

    def test_basic_profile(self):
        profile = AgentProfile(
            agent_id="test-agent",
            name="Test Agent",
        )
        assert profile.agent_id == "test-agent"
        assert profile.capabilities == []
        assert profile.performance == {}

    def test_profile_with_capabilities(self):
        profile = AgentProfile(
            agent_id="full-agent",
            name="Full Agent",
            provider="test",
            model="test-v1",
            capabilities=[
                AgentCapability(name="coding", score=0.9),
                AgentCapability(name="analysis", score=0.85),
            ],
            performance={
                PerformanceMetric.SPEED: 0.8,
                PerformanceMetric.ACCURACY: 0.9,
            },
            strengths=["coding"],
            weaknesses=["creative"],
            best_for=["code review"],
            avoid_for=["poetry"],
        )
        assert len(profile.capabilities) == 2
        assert profile.get_capability_score("coding") == 0.9
        assert profile.get_capability_score("nonexistent") == 0.0


class TestCapabilityRegistry:
    """Tests for CapabilityRegistry."""

    def test_register_and_get(self):
        registry = CapabilityRegistry()
        profile = AgentProfile(agent_id="reg-test", name="Registry Test")
        registry.register(profile)

        retrieved = registry.get("reg-test")
        assert retrieved.name == "Registry Test"

    def test_get_not_found(self):
        registry = CapabilityRegistry()
        with pytest.raises(ProfileNotFoundError):
            registry.get("nonexistent")

    def test_list_all(self):
        registry = CapabilityRegistry()
        registry.register(AgentProfile(agent_id="a1", name="A1"))
        registry.register(AgentProfile(agent_id="a2", name="A2"))

        profiles = registry.list()
        assert len(profiles) == 2

    def test_list_filter_by_provider(self):
        registry = CapabilityRegistry()
        registry.register(AgentProfile(agent_id="a1", name="A1", provider="openai"))
        registry.register(AgentProfile(agent_id="a2", name="A2", provider="anthropic"))

        profiles = registry.list(provider="openai")
        assert len(profiles) == 1
        assert profiles[0].agent_id == "a1"

    def test_list_filter_by_capability(self):
        registry = CapabilityRegistry()
        registry.register(AgentProfile(
            agent_id="a1", name="A1",
            capabilities=[AgentCapability(name="coding", score=0.9)]
        ))
        registry.register(AgentProfile(
            agent_id="a2", name="A2",
            capabilities=[AgentCapability(name="writing", score=0.8)]
        ))

        profiles = registry.list(capability="coding")
        assert len(profiles) == 1
        assert profiles[0].agent_id == "a1"

    def test_list_filter_by_min_score(self):
        registry = CapabilityRegistry()
        registry.register(AgentProfile(
            agent_id="a1", name="A1",
            capabilities=[AgentCapability(name="coding", score=0.9)]
        ))
        registry.register(AgentProfile(
            agent_id="a2", name="A2",
            capabilities=[AgentCapability(name="coding", score=0.5)]
        ))

        profiles = registry.list(capability="coding", min_score=0.8)
        assert len(profiles) == 1
        assert profiles[0].agent_id == "a1"

    def test_find_best_for(self):
        registry = CapabilityRegistry()
        registry.register(AgentProfile(
            agent_id="a1", name="A1",
            best_for=["code review", "analysis"]
        ))
        registry.register(AgentProfile(
            agent_id="a2", name="A2",
            best_for=["creative writing"]
        ))

        results = registry.find_best_for("code review")
        assert len(results) == 1
        assert results[0].agent_id == "a1"

    def test_compare(self):
        registry = CapabilityRegistry()
        registry.register(AgentProfile(
            agent_id="a1", name="A1",
            capabilities=[AgentCapability(name="coding", score=0.9)]
        ))
        registry.register(AgentProfile(
            agent_id="a2", name="A2",
            capabilities=[AgentCapability(name="coding", score=0.7)]
        ))

        comparison = registry.compare(["a1", "a2"], capability="coding")
        assert comparison["winner"] == "a1"
        assert comparison["agents"]["a1"]["score"] == 0.9

    def test_update(self):
        registry = CapabilityRegistry()
        registry.register(AgentProfile(agent_id="update-test", name="Original"))

        updated = registry.update("update-test", {"name": "Updated"})
        assert updated.name == "Updated"

    def test_delete(self):
        registry = CapabilityRegistry()
        registry.register(AgentProfile(agent_id="delete-test", name="Delete"))

        assert registry.delete("delete-test")
        with pytest.raises(ProfileNotFoundError):
            registry.get("delete-test")


class TestDefaultProfiles:
    """Tests for default model profiles."""

    def test_gpt4_profile(self):
        profile = gpt4_profile()
        assert profile.agent_id == "gpt-4"
        assert profile.provider == "openai"
        assert profile.get_capability_score("coding") >= 0.9

    def test_gpt4_turbo_profile(self):
        profile = gpt4_turbo_profile()
        assert profile.agent_id == "gpt-4-turbo"
        assert PerformanceMetric.CONTEXT in profile.performance

    def test_claude3_opus_profile(self):
        profile = claude3_opus_profile()
        assert profile.agent_id == "claude-3-opus"
        assert profile.provider == "anthropic"

    def test_claude3_sonnet_profile(self):
        profile = claude3_sonnet_profile()
        assert profile.agent_id == "claude-3-sonnet"

    def test_gemini_pro_profile(self):
        profile = gemini_pro_profile()
        assert profile.agent_id == "gemini-pro"
        assert profile.provider == "google"

    def test_llama3_profile(self):
        profile = llama3_profile()
        assert profile.agent_id == "llama-3-70b"
        assert profile.provider == "meta"


class TestTaskMatcher:
    """Tests for TaskMatcher."""

    def test_match_by_task(self):
        registry = CapabilityRegistry()
        registry.register(AgentProfile(
            agent_id="a1", name="A1",
            best_for=["code review"]
        ))

        matcher = TaskMatcher(registry)
        matches = matcher.match("code review task")
        assert len(matches) == 1

    def test_match_by_capabilities(self):
        registry = CapabilityRegistry()
        registry.register(AgentProfile(
            agent_id="a1", name="A1",
            capabilities=[
                AgentCapability(name="coding"),
                AgentCapability(name="analysis"),
            ]
        ))
        registry.register(AgentProfile(
            agent_id="a2", name="A2",
            capabilities=[AgentCapability(name="writing")]
        ))

        matcher = TaskMatcher(registry)
        matches = matcher.match("need help", required_capabilities=["coding", "analysis"])
        assert len(matches) == 1
        assert matches[0].agent_id == "a1"

    def test_rank_by_criteria(self):
        registry = CapabilityRegistry()
        registry.register(AgentProfile(
            agent_id="a1", name="A1",
            performance={PerformanceMetric.SPEED: 0.9, PerformanceMetric.ACCURACY: 0.7}
        ))
        registry.register(AgentProfile(
            agent_id="a2", name="A2",
            performance={PerformanceMetric.SPEED: 0.6, PerformanceMetric.ACCURACY: 0.95}
        ))

        matcher = TaskMatcher(registry)
        profiles = registry.list()

        ranked = matcher.rank(profiles, {PerformanceMetric.ACCURACY: 1.0})
        assert ranked[0].agent_id == "a2"

        ranked = matcher.rank(profiles, {PerformanceMetric.SPEED: 1.0})
        assert ranked[0].agent_id == "a1"

    def test_recommend(self):
        registry = CapabilityRegistry()
        registry.register(gpt4_profile())
        registry.register(claude3_opus_profile())
        registry.register(gemini_pro_profile())

        matcher = TaskMatcher(registry)
        recommendations = matcher.recommend("code review", top_n=2)

        assert len(recommendations) == 2
        assert all(isinstance(r[1], float) for r in recommendations)
