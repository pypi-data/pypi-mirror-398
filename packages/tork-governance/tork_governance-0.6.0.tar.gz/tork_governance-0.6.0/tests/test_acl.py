"""Tests for the ACL message schema system."""

import pytest
from datetime import datetime

from tork.acl import (
    Performative,
    ACLMessage,
    Conversation,
    Protocol,
    FIPARequestProtocol,
    FIPAContractNetProtocol,
    FIPAQueryProtocol,
    ACLRouter,
    MessageBuilder,
)
from tork.acl.router import ProtocolViolationError, AgentNotFoundError
from tork.core.engine import GovernanceEngine


class TestPerformativeEnum:
    """Tests for Performative enum."""

    def test_all_performatives(self):
        assert Performative.REQUEST == "request"
        assert Performative.INFORM == "inform"
        assert Performative.PROPOSE == "propose"
        assert Performative.ACCEPT == "accept"
        assert Performative.REJECT == "reject"
        assert Performative.QUERY == "query"
        assert Performative.CONFIRM == "confirm"
        assert Performative.CANCEL == "cancel"
        assert Performative.FAILURE == "failure"
        assert Performative.AGREE == "agree"
        assert Performative.REFUSE == "refuse"
        assert Performative.CALL_FOR_PROPOSAL == "cfp"


class TestACLMessageModel:
    """Tests for ACLMessage model."""

    def test_basic_message(self):
        msg = ACLMessage(
            performative=Performative.REQUEST,
            sender="agent1",
            receiver="agent2",
            content={"action": "do_something"},
        )
        assert msg.performative == Performative.REQUEST
        assert msg.sender == "agent1"
        assert msg.receiver == "agent2"
        assert msg.protocol == "fipa-request"
        assert msg.language == "json"

    def test_message_with_all_fields(self):
        msg = ACLMessage(
            performative=Performative.INFORM,
            sender="agent1",
            receiver="agent2",
            content="Hello",
            reply_to="msg123",
            conversation_id="conv456",
            protocol="fipa-query",
            ontology="weather",
            metadata={"priority": "high"},
        )
        assert msg.reply_to == "msg123"
        assert msg.conversation_id == "conv456"
        assert msg.ontology == "weather"
        assert msg.metadata["priority"] == "high"


class TestConversationModel:
    """Tests for Conversation model."""

    def test_basic_conversation(self):
        conv = Conversation(
            id="conv1",
            protocol="fipa-request",
            participants=["agent1", "agent2"],
        )
        assert conv.id == "conv1"
        assert conv.status == "active"
        assert len(conv.participants) == 2

    def test_conversation_with_messages(self):
        msg = ACLMessage(
            performative=Performative.REQUEST,
            sender="agent1",
            receiver="agent2",
            content="Test",
        )
        conv = Conversation(
            id="conv1",
            protocol="fipa-request",
            participants=["agent1", "agent2"],
            messages=[msg],
        )
        assert len(conv.messages) == 1


class TestFIPARequestProtocol:
    """Tests for FIPA Request protocol."""

    def test_initial_performatives(self):
        protocol = FIPARequestProtocol()
        assert Performative.REQUEST in protocol.initial_performatives()

    def test_valid_transitions(self):
        protocol = FIPARequestProtocol()
        transitions = protocol.valid_transitions(Performative.REQUEST)
        assert Performative.AGREE in transitions
        assert Performative.REFUSE in transitions

    def test_terminal_states(self):
        protocol = FIPARequestProtocol()
        assert protocol.is_terminal(Performative.INFORM)
        assert protocol.is_terminal(Performative.REFUSE)
        assert not protocol.is_terminal(Performative.REQUEST)


class TestFIPAContractNetProtocol:
    """Tests for FIPA Contract Net protocol."""

    def test_initial_performatives(self):
        protocol = FIPAContractNetProtocol()
        assert Performative.CALL_FOR_PROPOSAL in protocol.initial_performatives()

    def test_valid_transitions(self):
        protocol = FIPAContractNetProtocol()
        transitions = protocol.valid_transitions(Performative.CALL_FOR_PROPOSAL)
        assert Performative.PROPOSE in transitions
        assert Performative.REFUSE in transitions

    def test_terminal_states(self):
        protocol = FIPAContractNetProtocol()
        assert protocol.is_terminal(Performative.INFORM)
        assert protocol.is_terminal(Performative.REJECT)


class TestFIPAQueryProtocol:
    """Tests for FIPA Query protocol."""

    def test_initial_performatives(self):
        protocol = FIPAQueryProtocol()
        assert Performative.QUERY in protocol.initial_performatives()

    def test_valid_transitions(self):
        protocol = FIPAQueryProtocol()
        transitions = protocol.valid_transitions(Performative.QUERY)
        assert Performative.INFORM in transitions
        assert Performative.FAILURE in transitions


class TestACLRouterInitialization:
    """Tests for ACLRouter initialization."""

    def test_default_init(self):
        router = ACLRouter()
        assert router.governance_engine is not None
        assert router.receipt_generator is not None

    def test_custom_governance_engine(self):
        gov_engine = GovernanceEngine()
        router = ACLRouter(governance_engine=gov_engine)
        assert router.governance_engine is gov_engine


class TestRegisterAgent:
    """Tests for agent registration."""

    def test_register_agent(self):
        router = ACLRouter()
        router.register_agent("agent1", lambda msg: None)
        assert "agent1" in router.list_agents()

    def test_unregister_agent(self):
        router = ACLRouter()
        router.register_agent("agent1", lambda msg: None)
        assert router.unregister_agent("agent1")
        assert "agent1" not in router.list_agents()


class TestSendMessage:
    """Tests for sending messages."""

    def test_send_simple_message(self):
        router = ACLRouter()

        def handler(msg):
            return ACLMessage(
                performative=Performative.INFORM,
                sender=msg.receiver,
                receiver=msg.sender,
                content="Response",
            )

        router.register_agent("agent2", handler)

        msg = MessageBuilder.request("agent1", "agent2", "Hello")
        response = router.send(msg)

        assert response is not None
        assert response.performative == Performative.INFORM
        assert response.content == "Response"

    def test_send_to_unregistered_agent(self):
        router = ACLRouter()
        msg = MessageBuilder.request("agent1", "unknown", "Hello")

        with pytest.raises(AgentNotFoundError):
            router.send(msg)


class TestBroadcast:
    """Tests for broadcasting messages."""

    def test_broadcast_message(self):
        router = ACLRouter()

        def handler1(msg):
            return ACLMessage(
                performative=Performative.INFORM,
                sender="agent1",
                receiver=msg.sender,
                content="Response 1",
            )

        def handler2(msg):
            return ACLMessage(
                performative=Performative.INFORM,
                sender="agent2",
                receiver=msg.sender,
                content="Response 2",
            )

        router.register_agent("agent1", handler1)
        router.register_agent("agent2", handler2)

        msg = MessageBuilder.call_for_proposal("sender", "all", "Task")
        responses = router.broadcast(msg)

        assert len(responses) == 2


class TestConversationManagement:
    """Tests for conversation management."""

    def test_start_conversation(self):
        router = ACLRouter()
        conv = router.start_conversation("fipa-request", ["agent1", "agent2"])

        assert conv.protocol == "fipa-request"
        assert len(conv.participants) == 2
        assert conv.status == "active"

    def test_get_conversation(self):
        router = ACLRouter()
        conv = router.start_conversation("fipa-request", ["agent1", "agent2"])
        retrieved = router.get_conversation(conv.id)

        assert retrieved is not None
        assert retrieved.id == conv.id


class TestProtocolValidation:
    """Tests for protocol validation."""

    def test_valid_protocol_sequence(self):
        router = ACLRouter()

        def responder(msg):
            if msg.performative == Performative.REQUEST:
                return ACLMessage(
                    performative=Performative.AGREE,
                    sender=msg.receiver,
                    receiver=msg.sender,
                    content="Agreed",
                )
            return None

        router.register_agent("agent2", responder)
        conv = router.start_conversation("fipa-request", ["agent1", "agent2"])

        msg = ACLMessage(
            performative=Performative.REQUEST,
            sender="agent1",
            receiver="agent2",
            content="Do something",
            conversation_id=conv.id,
        )
        response = router.send(msg)
        assert response.performative == Performative.AGREE

    def test_invalid_protocol_sequence(self):
        router = ACLRouter()
        router.register_agent("agent2", lambda msg: None)
        conv = router.start_conversation("fipa-request", ["agent1", "agent2"])

        msg1 = ACLMessage(
            performative=Performative.REQUEST,
            sender="agent1",
            receiver="agent2",
            content="Request",
            conversation_id=conv.id,
        )
        router.send(msg1)

        msg2 = ACLMessage(
            performative=Performative.REQUEST,
            sender="agent1",
            receiver="agent2",
            content="Another request",
            conversation_id=conv.id,
        )

        with pytest.raises(ProtocolViolationError):
            router.send(msg2)


class TestMessageBuilder:
    """Tests for MessageBuilder."""

    def test_build_request(self):
        msg = MessageBuilder.request("a1", "a2", "content")
        assert msg.performative == Performative.REQUEST
        assert msg.protocol == "fipa-request"

    def test_build_inform(self):
        msg = MessageBuilder.inform("a1", "a2", "info", reply_to="msg123")
        assert msg.performative == Performative.INFORM
        assert msg.reply_to == "msg123"

    def test_build_propose(self):
        msg = MessageBuilder.propose("a1", "a2", {"offer": 100})
        assert msg.performative == Performative.PROPOSE
        assert msg.protocol == "fipa-contract-net"

    def test_build_query(self):
        msg = MessageBuilder.query("a1", "a2", "What is X?")
        assert msg.performative == Performative.QUERY
        assert msg.protocol == "fipa-query"

    def test_build_cfp(self):
        msg = MessageBuilder.call_for_proposal("a1", "all", "Task")
        assert msg.performative == Performative.CALL_FOR_PROPOSAL

    def test_build_all_types(self):
        assert MessageBuilder.accept("a", "b", "ok").performative == Performative.ACCEPT
        assert MessageBuilder.reject("a", "b", "no").performative == Performative.REJECT
        assert MessageBuilder.confirm("a", "b", "yes").performative == Performative.CONFIRM
        assert MessageBuilder.cancel("a", "b", "stop").performative == Performative.CANCEL
        assert MessageBuilder.failure("a", "b", "error").performative == Performative.FAILURE
        assert MessageBuilder.agree("a", "b", "ok").performative == Performative.AGREE
        assert MessageBuilder.refuse("a", "b", "no").performative == Performative.REFUSE

    def test_build_custom(self):
        msg = MessageBuilder.custom(
            performative=Performative.INFORM,
            sender="a1",
            receiver="a2",
            content="custom",
            ontology="domain",
            metadata={"key": "value"},
        )
        assert msg.ontology == "domain"
        assert msg.metadata["key"] == "value"


class TestGovernanceIntegration:
    """Tests for governance integration."""

    def test_governance_applied_to_messages(self):
        router = ACLRouter()
        router.register_agent("agent2", lambda msg: ACLMessage(
            performative=Performative.INFORM,
            sender="agent2",
            receiver="agent1",
            content="Response",
        ))

        msg = MessageBuilder.request("agent1", "agent2", "test@example.com")
        response = router.send(msg)

        assert response is not None


class TestConversationLifecycle:
    """Tests for conversation lifecycle."""

    def test_conversation_completes(self):
        router = ACLRouter()

        def responder(msg):
            return ACLMessage(
                performative=Performative.INFORM,
                sender=msg.receiver,
                receiver=msg.sender,
                content="Done",
            )

        router.register_agent("agent2", responder)
        conv = router.start_conversation("fipa-query", ["agent1", "agent2"])

        msg = ACLMessage(
            performative=Performative.QUERY,
            sender="agent1",
            receiver="agent2",
            content="Query",
            conversation_id=conv.id,
        )
        router.send(msg)

        updated_conv = router.get_conversation(conv.id)
        assert updated_conv.status == "completed"
        assert updated_conv.ended_at is not None
