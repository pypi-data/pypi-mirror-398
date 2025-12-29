"""Pre-defined capability profiles for popular models."""

from tork.capabilities.models import (
    AgentCapability,
    AgentProfile,
    CapabilityLevel,
    PerformanceMetric,
)


def gpt4_profile() -> AgentProfile:
    """GPT-4 capability profile."""
    return AgentProfile(
        agent_id="gpt-4",
        name="GPT-4",
        provider="openai",
        model="gpt-4",
        capabilities=[
            AgentCapability(name="coding", level=CapabilityLevel.EXPERT, score=0.95),
            AgentCapability(name="analysis", level=CapabilityLevel.EXPERT, score=0.92),
            AgentCapability(name="reasoning", level=CapabilityLevel.EXPERT, score=0.93),
            AgentCapability(name="writing", level=CapabilityLevel.ADVANCED, score=0.88),
            AgentCapability(name="math", level=CapabilityLevel.ADVANCED, score=0.85),
            AgentCapability(name="creative", level=CapabilityLevel.INTERMEDIATE, score=0.75),
        ],
        performance={
            PerformanceMetric.ACCURACY: 0.92,
            PerformanceMetric.SPEED: 0.60,
            PerformanceMetric.CREATIVITY: 0.75,
            PerformanceMetric.SAFETY: 0.88,
            PerformanceMetric.COST: 0.40,
            PerformanceMetric.CONTEXT: 0.70,
        },
        strengths=["coding", "analysis", "reasoning", "instruction following"],
        weaknesses=["speed", "cost efficiency"],
        best_for=["code review", "data analysis", "complex reasoning", "technical writing"],
        avoid_for=["simple tasks", "high-volume processing"],
        description="OpenAI's flagship model with strong reasoning and coding abilities.",
        tags=["openai", "flagship", "coding", "reasoning"],
    )


def gpt4_turbo_profile() -> AgentProfile:
    """GPT-4 Turbo capability profile."""
    return AgentProfile(
        agent_id="gpt-4-turbo",
        name="GPT-4 Turbo",
        provider="openai",
        model="gpt-4-turbo",
        capabilities=[
            AgentCapability(name="coding", level=CapabilityLevel.EXPERT, score=0.93),
            AgentCapability(name="analysis", level=CapabilityLevel.EXPERT, score=0.90),
            AgentCapability(name="reasoning", level=CapabilityLevel.ADVANCED, score=0.88),
            AgentCapability(name="writing", level=CapabilityLevel.ADVANCED, score=0.87),
            AgentCapability(name="math", level=CapabilityLevel.ADVANCED, score=0.83),
            AgentCapability(name="creative", level=CapabilityLevel.ADVANCED, score=0.80),
        ],
        performance={
            PerformanceMetric.ACCURACY: 0.88,
            PerformanceMetric.SPEED: 0.85,
            PerformanceMetric.CREATIVITY: 0.80,
            PerformanceMetric.SAFETY: 0.85,
            PerformanceMetric.COST: 0.65,
            PerformanceMetric.CONTEXT: 0.95,
        },
        strengths=["speed", "large context", "balanced performance"],
        weaknesses=["slightly lower accuracy than GPT-4"],
        best_for=["long documents", "fast responses", "general tasks"],
        avoid_for=["tasks requiring maximum accuracy"],
        description="Faster and more cost-effective version of GPT-4 with 128k context.",
        tags=["openai", "fast", "large-context"],
    )


def claude3_opus_profile() -> AgentProfile:
    """Claude 3 Opus capability profile."""
    return AgentProfile(
        agent_id="claude-3-opus",
        name="Claude 3 Opus",
        provider="anthropic",
        model="claude-3-opus-20240229",
        capabilities=[
            AgentCapability(name="coding", level=CapabilityLevel.EXPERT, score=0.94),
            AgentCapability(name="analysis", level=CapabilityLevel.EXPERT, score=0.95),
            AgentCapability(name="reasoning", level=CapabilityLevel.EXPERT, score=0.94),
            AgentCapability(name="writing", level=CapabilityLevel.EXPERT, score=0.93),
            AgentCapability(name="math", level=CapabilityLevel.ADVANCED, score=0.87),
            AgentCapability(name="creative", level=CapabilityLevel.ADVANCED, score=0.88),
        ],
        performance={
            PerformanceMetric.ACCURACY: 0.94,
            PerformanceMetric.SPEED: 0.55,
            PerformanceMetric.CREATIVITY: 0.88,
            PerformanceMetric.SAFETY: 0.95,
            PerformanceMetric.COST: 0.30,
            PerformanceMetric.CONTEXT: 0.90,
        },
        strengths=["nuanced writing", "safety", "analysis", "following complex instructions"],
        weaknesses=["speed", "cost"],
        best_for=["complex analysis", "nuanced writing", "safety-critical tasks"],
        avoid_for=["simple tasks", "high-volume", "budget-constrained"],
        description="Anthropic's most capable model with exceptional reasoning and safety.",
        tags=["anthropic", "flagship", "safe", "analysis"],
    )


def claude3_sonnet_profile() -> AgentProfile:
    """Claude 3 Sonnet capability profile."""
    return AgentProfile(
        agent_id="claude-3-sonnet",
        name="Claude 3 Sonnet",
        provider="anthropic",
        model="claude-3-sonnet-20240229",
        capabilities=[
            AgentCapability(name="coding", level=CapabilityLevel.ADVANCED, score=0.88),
            AgentCapability(name="analysis", level=CapabilityLevel.ADVANCED, score=0.86),
            AgentCapability(name="reasoning", level=CapabilityLevel.ADVANCED, score=0.85),
            AgentCapability(name="writing", level=CapabilityLevel.ADVANCED, score=0.87),
            AgentCapability(name="math", level=CapabilityLevel.INTERMEDIATE, score=0.78),
            AgentCapability(name="creative", level=CapabilityLevel.ADVANCED, score=0.82),
        ],
        performance={
            PerformanceMetric.ACCURACY: 0.85,
            PerformanceMetric.SPEED: 0.80,
            PerformanceMetric.CREATIVITY: 0.82,
            PerformanceMetric.SAFETY: 0.92,
            PerformanceMetric.COST: 0.70,
            PerformanceMetric.CONTEXT: 0.90,
        },
        strengths=["balanced performance", "safety", "speed/quality ratio"],
        weaknesses=["not as capable as Opus for complex tasks"],
        best_for=["general tasks", "content generation", "chat applications"],
        avoid_for=["tasks requiring maximum capability"],
        description="Balanced model offering good performance at reasonable cost.",
        tags=["anthropic", "balanced", "safe"],
    )


def gemini_pro_profile() -> AgentProfile:
    """Gemini Pro capability profile."""
    return AgentProfile(
        agent_id="gemini-pro",
        name="Gemini Pro",
        provider="google",
        model="gemini-pro",
        capabilities=[
            AgentCapability(name="coding", level=CapabilityLevel.ADVANCED, score=0.85),
            AgentCapability(name="analysis", level=CapabilityLevel.ADVANCED, score=0.84),
            AgentCapability(name="reasoning", level=CapabilityLevel.ADVANCED, score=0.83),
            AgentCapability(name="writing", level=CapabilityLevel.ADVANCED, score=0.82),
            AgentCapability(name="math", level=CapabilityLevel.ADVANCED, score=0.80),
            AgentCapability(name="creative", level=CapabilityLevel.INTERMEDIATE, score=0.75),
        ],
        performance={
            PerformanceMetric.ACCURACY: 0.83,
            PerformanceMetric.SPEED: 0.88,
            PerformanceMetric.CREATIVITY: 0.75,
            PerformanceMetric.SAFETY: 0.85,
            PerformanceMetric.COST: 0.85,
            PerformanceMetric.CONTEXT: 0.75,
        },
        strengths=["speed", "cost efficiency", "multimodal"],
        weaknesses=["creative tasks", "nuanced writing"],
        best_for=["fast processing", "cost-effective tasks", "multimodal"],
        avoid_for=["creative writing", "nuanced analysis"],
        description="Google's efficient model with good speed and cost characteristics.",
        tags=["google", "efficient", "multimodal"],
    )


def llama3_profile() -> AgentProfile:
    """Llama 3 capability profile."""
    return AgentProfile(
        agent_id="llama-3-70b",
        name="Llama 3 70B",
        provider="meta",
        model="llama-3-70b",
        capabilities=[
            AgentCapability(name="coding", level=CapabilityLevel.ADVANCED, score=0.82),
            AgentCapability(name="analysis", level=CapabilityLevel.ADVANCED, score=0.80),
            AgentCapability(name="reasoning", level=CapabilityLevel.INTERMEDIATE, score=0.78),
            AgentCapability(name="writing", level=CapabilityLevel.ADVANCED, score=0.80),
            AgentCapability(name="math", level=CapabilityLevel.INTERMEDIATE, score=0.72),
            AgentCapability(name="creative", level=CapabilityLevel.INTERMEDIATE, score=0.75),
        ],
        performance={
            PerformanceMetric.ACCURACY: 0.80,
            PerformanceMetric.SPEED: 0.75,
            PerformanceMetric.CREATIVITY: 0.75,
            PerformanceMetric.SAFETY: 0.78,
            PerformanceMetric.COST: 0.95,
            PerformanceMetric.CONTEXT: 0.60,
        },
        strengths=["open source", "cost efficiency", "self-hosting"],
        weaknesses=["smaller context", "reasoning depth"],
        best_for=["self-hosted deployments", "budget tasks", "privacy-sensitive"],
        avoid_for=["complex reasoning", "very long documents"],
        description="Meta's open-source model, great for self-hosting and privacy.",
        tags=["meta", "open-source", "self-hosted"],
    )
