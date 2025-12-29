"""
Tests for LangChain middleware integration.

Uses mocked LangChain components to test governance integration
without requiring actual LangChain installation.
"""

import pytest
from unittest.mock import Mock, MagicMock

from tork.core.engine import GovernanceEngine
from tork.core.policy import Policy, PolicyRule, PolicyAction
from tork.core.models import PolicyDecision
from tork.compliance.receipts import ReceiptGenerator
from tork.adapters.langchain import (
    GovernanceViolation,
    TorkCallbackHandler,
    GovernedChain,
    create_governed_chain,
)


class TestGovernanceViolation:
    """Tests for GovernanceViolation exception."""
    
    def test_basic_violation(self):
        """Test creating a basic governance violation."""
        violation = GovernanceViolation(
            message="Access denied",
            decision=PolicyDecision.DENY,
        )
        
        assert violation.message == "Access denied"
        assert violation.decision == PolicyDecision.DENY
        assert violation.violations == []
        assert str(violation) == "Access denied"
    
    def test_violation_with_details(self):
        """Test violation with specific violations list."""
        violation = GovernanceViolation(
            message="Policy violation",
            decision=PolicyDecision.DENY,
            violations=["Unauthorized access", "Missing credentials"],
        )
        
        assert len(violation.violations) == 2
        assert "Unauthorized access" in str(violation)


class TestTorkCallbackHandler:
    """Tests for TorkCallbackHandler class."""
    
    def test_initialization(self):
        """Test callback handler initialization."""
        engine = GovernanceEngine()
        handler = TorkCallbackHandler(engine=engine, agent_id="test-agent")
        
        assert handler.engine == engine
        assert handler.agent_id == "test-agent"
        assert handler.identity_manager is None
        assert handler.receipt_generator is None
        assert handler.receipts == []
    
    def test_initialization_with_all_options(self):
        """Test initialization with all optional components."""
        engine = GovernanceEngine()
        identity_manager = Mock()
        receipt_generator = ReceiptGenerator(signing_key="test-key")
        
        handler = TorkCallbackHandler(
            engine=engine,
            identity_manager=identity_manager,
            receipt_generator=receipt_generator,
            agent_id="full-agent",
        )
        
        assert handler.identity_manager == identity_manager
        assert handler.receipt_generator == receipt_generator
    
    def test_on_llm_start_allow(self):
        """Test on_llm_start with ALLOW decision."""
        engine = GovernanceEngine()
        handler = TorkCallbackHandler(engine=engine)
        
        handler.on_llm_start(
            serialized={"name": "gpt-4"},
            prompts=["Hello, how are you?"],
        )
    
    def test_on_llm_start_deny(self):
        """Test on_llm_start raises GovernanceViolation on DENY."""
        from tork.core.policy import PolicyOperator
        deny_rule = PolicyRule(
            field="prompts",
            operator=PolicyOperator.EXISTS,
            action=PolicyAction.DENY,
        )
        policy = Policy(name="deny-all", rules=[deny_rule])
        engine = GovernanceEngine(policies=[policy])
        handler = TorkCallbackHandler(engine=engine)
        
        with pytest.raises(GovernanceViolation) as exc_info:
            handler.on_llm_start(
                serialized={"name": "gpt-4"},
                prompts=["Test prompt"],
            )
        
        assert exc_info.value.decision == PolicyDecision.DENY
    
    def test_on_chain_start(self):
        """Test on_chain_start evaluation."""
        engine = GovernanceEngine()
        handler = TorkCallbackHandler(engine=engine)
        
        handler.on_chain_start(
            serialized={"name": "test-chain"},
            inputs={"question": "What is AI?"},
        )
    
    def test_on_chain_end(self):
        """Test on_chain_end evaluation."""
        engine = GovernanceEngine()
        handler = TorkCallbackHandler(engine=engine)
        
        handler.on_chain_end(
            outputs={"answer": "AI is artificial intelligence."},
        )
    
    def test_on_tool_start(self):
        """Test on_tool_start evaluation."""
        engine = GovernanceEngine()
        handler = TorkCallbackHandler(engine=engine)
        
        handler.on_tool_start(
            serialized={"name": "calculator"},
            input_str="2 + 2",
        )
    
    def test_on_tool_end(self):
        """Test on_tool_end evaluation."""
        engine = GovernanceEngine()
        handler = TorkCallbackHandler(engine=engine)
        
        handler.on_tool_end(output="4")
    
    def test_receipt_generation(self):
        """Test that receipts are generated when configured."""
        engine = GovernanceEngine()
        receipt_generator = ReceiptGenerator(signing_key="test-key")
        handler = TorkCallbackHandler(
            engine=engine,
            receipt_generator=receipt_generator,
        )
        
        handler.on_chain_start(
            serialized={"name": "test"},
            inputs={"data": "test"},
        )
        
        assert len(handler.receipts) == 1
        assert handler.receipts[0].agent_id == "langchain-agent"


class TestGovernedChain:
    """Tests for GovernedChain wrapper."""
    
    def test_initialization(self):
        """Test governed chain initialization."""
        mock_chain = Mock()
        engine = GovernanceEngine()
        
        governed = GovernedChain(chain=mock_chain, engine=engine)
        
        assert governed.chain == mock_chain
        assert governed.engine == engine
        assert governed.receipts == []
    
    def test_invoke_allow(self):
        """Test invoke passes through on ALLOW."""
        mock_chain = Mock()
        mock_chain.invoke.return_value = {"result": "success"}
        engine = GovernanceEngine()
        
        governed = GovernedChain(chain=mock_chain, engine=engine)
        result = governed.invoke({"query": "test"})
        
        assert result == {"result": "success"}
        mock_chain.invoke.assert_called_once()
    
    def test_invoke_deny_input(self):
        """Test invoke raises GovernanceViolation on DENY for input."""
        from tork.core.policy import PolicyOperator
        deny_rule = PolicyRule(
            field="query",
            operator=PolicyOperator.CONTAINS,
            value="secret",
            action=PolicyAction.DENY,
        )
        policy = Policy(name="security", rules=[deny_rule])
        
        mock_chain = Mock()
        engine = GovernanceEngine(policies=[policy])
        governed = GovernedChain(chain=mock_chain, engine=engine)
        
        with pytest.raises(GovernanceViolation):
            governed.invoke({"query": "tell me the secret"})
        
        mock_chain.invoke.assert_not_called()
    
    def test_invoke_with_redaction(self):
        """Test that REDACT modifies output."""
        from tork.core.redactor import PIIRedactor
        
        redactor = PIIRedactor()
        engine = GovernanceEngine(pii_redactor=redactor, enable_auto_redaction=True)
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = {"response": "Contact us at user@example.com"}
        
        governed = GovernedChain(chain=mock_chain, engine=engine)
        result = governed.invoke({"query": "How to contact?"})
        
        assert "response" in result
        assert "[REDACTED_EMAIL]" in result["response"]
    
    def test_invoke_with_config(self):
        """Test invoke with config parameter."""
        mock_chain = Mock()
        mock_chain.invoke.return_value = "output"
        engine = GovernanceEngine()
        
        governed = GovernedChain(chain=mock_chain, engine=engine)
        config = {"temperature": 0.5}
        result = governed.invoke("input", config=config)
        
        mock_chain.invoke.assert_called_once()
        call_args = mock_chain.invoke.call_args
        assert call_args[0][1] == config
    
    def test_callable(self):
        """Test that governed chain is callable."""
        mock_chain = Mock()
        mock_chain.invoke.return_value = {"answer": "42"}
        engine = GovernanceEngine()
        
        governed = GovernedChain(chain=mock_chain, engine=engine)
        result = governed({"question": "What is the answer?"})
        
        assert result == {"answer": "42"}
    
    def test_receipt_generation(self):
        """Test receipt generation during invoke."""
        mock_chain = Mock()
        mock_chain.invoke.return_value = {"output": "result"}
        engine = GovernanceEngine()
        receipt_generator = ReceiptGenerator(signing_key="test-key")
        
        governed = GovernedChain(
            chain=mock_chain,
            engine=engine,
            receipt_generator=receipt_generator,
        )
        
        governed.invoke({"input": "test"})
        
        assert len(governed.receipts) == 2


class TestCreateGovernedChain:
    """Tests for create_governed_chain convenience function."""
    
    def test_create_basic(self):
        """Test creating a basic governed chain."""
        mock_chain = Mock()
        engine = GovernanceEngine()
        
        governed = create_governed_chain(chain=mock_chain, engine=engine)
        
        assert isinstance(governed, GovernedChain)
        assert governed.chain == mock_chain
        assert governed.engine == engine
    
    def test_create_with_all_options(self):
        """Test creating governed chain with all options."""
        mock_chain = Mock()
        engine = GovernanceEngine()
        identity_manager = Mock()
        receipt_generator = ReceiptGenerator(signing_key="key")
        
        governed = create_governed_chain(
            chain=mock_chain,
            engine=engine,
            identity_manager=identity_manager,
            receipt_generator=receipt_generator,
            agent_id="custom-agent",
        )
        
        assert governed.identity_manager == identity_manager
        assert governed.receipt_generator == receipt_generator
        assert governed.agent_id == "custom-agent"
