"""Tests for the Custom Agents/Personas system."""

import json
import pytest
import tempfile
from pathlib import Path

from tork.personas import (
    PersonaCapability,
    PersonaConfig,
    PersonaInstance,
    PersonaStore,
    PersonaRuntime,
    PersonaBuilder,
    legal_analyst,
    code_reviewer,
    research_assistant,
    content_writer,
    data_analyst,
    financial_advisor,
)
from tork.personas.store import PersonaNotFoundError
from tork.personas.runtime import (
    CostLimitExceededError,
    BlockedActionError,
    InstanceNotFoundError,
)
from tork.core.engine import GovernanceEngine


class TestPersonaCapabilityEnum:
    """Tests for PersonaCapability enum."""

    def test_all_capabilities(self):
        assert PersonaCapability.RESEARCH == "research"
        assert PersonaCapability.ANALYSIS == "analysis"
        assert PersonaCapability.WRITING == "writing"
        assert PersonaCapability.CODING == "coding"
        assert PersonaCapability.CRITIQUE == "critique"
        assert PersonaCapability.SUMMARIZATION == "summarization"
        assert PersonaCapability.TRANSLATION == "translation"
        assert PersonaCapability.DATA_PROCESSING == "data_processing"
        assert PersonaCapability.CREATIVE == "creative"
        assert PersonaCapability.LEGAL == "legal"
        assert PersonaCapability.FINANCIAL == "financial"
        assert PersonaCapability.MEDICAL == "medical"


class TestPersonaConfigModel:
    """Tests for PersonaConfig model."""

    def test_basic_config(self):
        config = PersonaConfig(
            id="test-persona",
            name="Test Persona",
            system_prompt="You are a test assistant.",
        )
        assert config.id == "test-persona"
        assert config.name == "Test Persona"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.pii_redaction is True

    def test_config_with_all_fields(self):
        config = PersonaConfig(
            id="full-persona",
            name="Full Persona",
            description="A fully configured persona",
            system_prompt="You are an expert.",
            capabilities=[PersonaCapability.CODING, PersonaCapability.ANALYSIS],
            preferred_models=["gpt-4"],
            temperature=0.5,
            max_tokens=8192,
            governance_policy="strict",
            pii_redaction=True,
            allowed_actions=["review"],
            blocked_actions=["delete"],
            max_cost_per_request=2.0,
            tags=["test", "demo"],
            metadata={"version": "1.0"},
        )
        assert len(config.capabilities) == 2
        assert config.max_cost_per_request == 2.0


class TestPersonaInstanceModel:
    """Tests for PersonaInstance model."""

    def test_basic_instance(self):
        instance = PersonaInstance(
            persona_id="test-persona",
            session_id="session-123",
        )
        assert instance.persona_id == "test-persona"
        assert instance.session_id == "session-123"
        assert instance.messages_count == 0
        assert instance.total_tokens == 0
        assert instance.total_cost == 0.0


class TestPersonaStore:
    """Tests for PersonaStore."""

    def test_save_and_get(self):
        store = PersonaStore()
        config = PersonaConfig(
            id="store-test",
            name="Store Test",
            system_prompt="Test prompt",
        )
        store.save(config)
        retrieved = store.get("store-test")
        assert retrieved.name == "Store Test"

    def test_get_not_found(self):
        store = PersonaStore()
        with pytest.raises(PersonaNotFoundError):
            store.get("nonexistent")

    def test_list_all(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="p1", name="P1", system_prompt="test"))
        store.save(PersonaConfig(id="p2", name="P2", system_prompt="test"))
        personas = store.list()
        assert len(personas) == 2

    def test_list_filter_by_tags(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="p1", name="P1", system_prompt="test", tags=["legal"]))
        store.save(PersonaConfig(id="p2", name="P2", system_prompt="test", tags=["code"]))
        personas = store.list(tags=["legal"])
        assert len(personas) == 1
        assert personas[0].id == "p1"

    def test_list_filter_by_capabilities(self):
        store = PersonaStore()
        store.save(PersonaConfig(
            id="p1", name="P1", system_prompt="test",
            capabilities=[PersonaCapability.CODING]
        ))
        store.save(PersonaConfig(
            id="p2", name="P2", system_prompt="test",
            capabilities=[PersonaCapability.WRITING]
        ))
        personas = store.list(capabilities=[PersonaCapability.CODING])
        assert len(personas) == 1
        assert personas[0].id == "p1"

    def test_delete(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="delete-me", name="Delete", system_prompt="test"))
        assert store.delete("delete-me")
        with pytest.raises(PersonaNotFoundError):
            store.get("delete-me")

    def test_update(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="update-me", name="Original", system_prompt="test"))
        updated = store.update("update-me", {"name": "Updated"})
        assert updated.name == "Updated"

    def test_export_json(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="export-test", name="Export", system_prompt="test"))
        exported = store.export("export-test", format="json")
        data = json.loads(exported)
        assert data["id"] == "export-test"

    def test_export_yaml(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="yaml-test", name="YAML", system_prompt="test"))
        exported = store.export("yaml-test", format="yaml")
        assert "id: yaml-test" in exported

    def test_import_json(self):
        store = PersonaStore()
        data = json.dumps({
            "id": "imported",
            "name": "Imported Persona",
            "system_prompt": "Test prompt",
        })
        persona = store.import_persona(data, format="json")
        assert persona.id == "imported"
        assert store.get("imported").name == "Imported Persona"


class TestPersonaRuntime:
    """Tests for PersonaRuntime."""

    def test_initialization(self):
        runtime = PersonaRuntime()
        assert runtime.store is not None
        assert runtime.governance_engine is not None

    def test_instantiate_persona(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="runtime-test", name="Runtime", system_prompt="test"))
        runtime = PersonaRuntime(store=store)

        instance = runtime.instantiate("runtime-test", session_id="sess-1")
        assert instance.persona_id == "runtime-test"
        assert instance.session_id == "sess-1"

    def test_execute_basic(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="exec-test", name="Exec", system_prompt="test"))
        runtime = PersonaRuntime(store=store)
        instance = runtime.instantiate("exec-test")

        result = runtime.execute(instance.id, "Hello, world!")
        assert result["output"] is not None
        assert result["blocked"] is False
        assert "receipt" in result

    def test_execute_with_executor(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="executor-test", name="Executor", system_prompt="test"))
        runtime = PersonaRuntime(store=store)

        def mock_executor(system_prompt, input_text, context):
            return {"output": f"Processed: {input_text}", "tokens": 10, "cost": 0.001}

        runtime.set_executor(mock_executor)
        instance = runtime.instantiate("executor-test")

        result = runtime.execute(instance.id, "test input")
        assert result["output"] == "Processed: test input"
        assert result["tokens"] == 10
        assert result["cost"] == 0.001

    def test_cost_limit_exceeded(self):
        store = PersonaStore()
        store.save(PersonaConfig(
            id="cost-test", name="Cost", system_prompt="test",
            max_cost_per_request=0.5
        ))
        runtime = PersonaRuntime(store=store)
        instance = runtime.instantiate("cost-test")

        with pytest.raises(CostLimitExceededError):
            runtime.execute(instance.id, "test", estimated_cost=1.0)

    def test_blocked_action(self):
        store = PersonaStore()
        store.save(PersonaConfig(
            id="blocked-test", name="Blocked", system_prompt="test",
            blocked_actions=["delete"]
        ))
        runtime = PersonaRuntime(store=store)
        instance = runtime.instantiate("blocked-test")

        with pytest.raises(BlockedActionError):
            runtime.execute(instance.id, "test", context={"action": "delete"})

    def test_allowed_actions_enforcement(self):
        store = PersonaStore()
        store.save(PersonaConfig(
            id="allowed-test", name="Allowed", system_prompt="test",
            allowed_actions=["read", "write"]
        ))
        runtime = PersonaRuntime(store=store)
        instance = runtime.instantiate("allowed-test")

        with pytest.raises(BlockedActionError):
            runtime.execute(instance.id, "test", context={"action": "delete"})

    def test_terminate_instance(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="term-test", name="Term", system_prompt="test"))
        runtime = PersonaRuntime(store=store)
        instance = runtime.instantiate("term-test")

        assert runtime.terminate(instance.id)
        with pytest.raises(InstanceNotFoundError):
            runtime.get_instance(instance.id)

    def test_list_instances(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="list-test", name="List", system_prompt="test"))
        runtime = PersonaRuntime(store=store)

        runtime.instantiate("list-test")
        runtime.instantiate("list-test")

        instances = runtime.list_instances()
        assert len(instances) == 2

    def test_list_instances_by_persona(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="p1", name="P1", system_prompt="test"))
        store.save(PersonaConfig(id="p2", name="P2", system_prompt="test"))
        runtime = PersonaRuntime(store=store)

        runtime.instantiate("p1")
        runtime.instantiate("p1")
        runtime.instantiate("p2")

        instances = runtime.list_instances(persona_id="p1")
        assert len(instances) == 2


class TestPersonaBuilder:
    """Tests for PersonaBuilder."""

    def test_basic_build(self):
        persona = PersonaBuilder("builder-test", "Builder Test").build()
        assert persona.id == "builder-test"
        assert persona.name == "Builder Test"

    def test_fluent_api(self):
        persona = (
            PersonaBuilder("fluent", "Fluent Test")
            .with_description("A fluently built persona")
            .with_system_prompt("You are a custom assistant.")
            .with_capabilities(PersonaCapability.CODING, PersonaCapability.ANALYSIS)
            .with_preferred_models("gpt-4", "claude-3")
            .with_temperature(0.5)
            .with_max_tokens(8000)
            .with_governance_policy("custom-policy")
            .with_pii_redaction(False)
            .with_allowed_actions("read", "write")
            .with_blocked_actions("delete")
            .with_max_cost(5.0)
            .with_tags("test", "demo")
            .with_metadata({"version": "2.0"})
            .created_by("test-user")
            .build()
        )

        assert persona.description == "A fluently built persona"
        assert len(persona.capabilities) == 2
        assert persona.temperature == 0.5
        assert persona.pii_redaction is False
        assert "read" in persona.allowed_actions
        assert persona.max_cost_per_request == 5.0
        assert persona.created_by == "test-user"


class TestPersonaTemplates:
    """Tests for persona templates."""

    def test_legal_analyst_template(self):
        persona = legal_analyst()
        assert persona.id == "legal-analyst"
        assert PersonaCapability.LEGAL in persona.capabilities
        assert "provide_legal_advice" in persona.blocked_actions

    def test_code_reviewer_template(self):
        persona = code_reviewer()
        assert persona.id == "code-reviewer"
        assert PersonaCapability.CODING in persona.capabilities
        assert "review_code" in persona.allowed_actions

    def test_research_assistant_template(self):
        persona = research_assistant()
        assert persona.id == "research-assistant"
        assert PersonaCapability.RESEARCH in persona.capabilities

    def test_content_writer_template(self):
        persona = content_writer()
        assert persona.id == "content-writer"
        assert PersonaCapability.WRITING in persona.capabilities

    def test_data_analyst_template(self):
        persona = data_analyst()
        assert persona.id == "data-analyst"
        assert PersonaCapability.DATA_PROCESSING in persona.capabilities

    def test_financial_advisor_template(self):
        persona = financial_advisor()
        assert persona.id == "financial-advisor"
        assert PersonaCapability.FINANCIAL in persona.capabilities
        assert "provide_investment_advice" in persona.blocked_actions


class TestGovernanceIntegration:
    """Tests for governance integration with personas."""

    def test_governance_applied_to_execution(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="gov-test", name="Gov", system_prompt="test"))
        gov_engine = GovernanceEngine()
        runtime = PersonaRuntime(store=store, governance_engine=gov_engine)
        instance = runtime.instantiate("gov-test")

        result = runtime.execute(instance.id, "test@example.com")
        assert result["blocked"] is False
        assert "receipt" in result


class TestCostTracking:
    """Tests for cost tracking."""

    def test_cost_accumulates_per_instance(self):
        store = PersonaStore()
        store.save(PersonaConfig(id="cost-track", name="Cost", system_prompt="test"))
        runtime = PersonaRuntime(store=store)

        def mock_executor(system_prompt, input_text, context):
            return {"output": "response", "tokens": 100, "cost": 0.01}

        runtime.set_executor(mock_executor)
        instance = runtime.instantiate("cost-track")

        runtime.execute(instance.id, "test1")
        runtime.execute(instance.id, "test2")
        runtime.execute(instance.id, "test3")

        updated_instance = runtime.get_instance(instance.id)
        assert updated_instance.messages_count == 3
        assert updated_instance.total_tokens == 300
        assert abs(updated_instance.total_cost - 0.03) < 0.0001
