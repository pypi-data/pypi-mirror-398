"""ACL message router with governance integration."""

from datetime import datetime
from typing import Callable, Dict, List, Optional
from uuid import uuid4
import structlog

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest, PolicyDecision
from tork.compliance.receipts import ReceiptGenerator
from tork.acl.models import ACLMessage, Conversation
from tork.acl.protocols import (
    Protocol,
    FIPARequestProtocol,
    FIPAContractNetProtocol,
    FIPAQueryProtocol,
)

logger = structlog.get_logger(__name__)


class ProtocolViolationError(Exception):
    """Raised when a message violates protocol rules."""
    pass


class AgentNotFoundError(Exception):
    """Raised when the receiver agent is not registered."""
    pass


class ACLRouter:
    """Route ACL messages between agents with governance."""

    def __init__(
        self,
        governance_engine: Optional[GovernanceEngine] = None,
        signing_key: str = "acl-secret",
    ):
        """
        Initialize the ACL router.

        Args:
            governance_engine: Optional GovernanceEngine for policy evaluation.
            signing_key: Key for signing compliance receipts.
        """
        self.governance_engine = governance_engine or GovernanceEngine()
        self.receipt_generator = ReceiptGenerator(signing_key=signing_key)
        self._agents: Dict[str, Callable[[ACLMessage], ACLMessage]] = {}
        self._conversations: Dict[str, Conversation] = {}
        self._protocols: Dict[str, Protocol] = {
            "fipa-request": FIPARequestProtocol(),
            "fipa-contract-net": FIPAContractNetProtocol(),
            "fipa-query": FIPAQueryProtocol(),
        }
        logger.info("ACLRouter initialized")

    def register_agent(
        self, agent_id: str, handler: Callable[[ACLMessage], ACLMessage]
    ) -> None:
        """
        Register an agent message handler.

        Args:
            agent_id: Unique agent identifier.
            handler: Callable that receives a message and returns a response.
        """
        self._agents[agent_id] = handler
        logger.info("Agent registered", agent_id=agent_id)

    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent.

        Args:
            agent_id: Agent to unregister.

        Returns:
            True if agent was unregistered, False if not found.
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def send(self, message: ACLMessage) -> Optional[ACLMessage]:
        """
        Send a message with governance checks.

        Args:
            message: The ACL message to send.

        Returns:
            Response message from the receiver, or None if blocked.

        Raises:
            AgentNotFoundError: If receiver is not registered.
            ProtocolViolationError: If message violates protocol rules.
        """
        if message.conversation_id:
            conversation = self._conversations.get(message.conversation_id)
            if conversation:
                if not self._validate_protocol(message, conversation):
                    raise ProtocolViolationError(
                        f"Invalid performative {message.performative} in protocol {conversation.protocol}"
                    )

        request = EvaluationRequest(
            payload={
                "performative": message.performative.value,
                "sender": message.sender,
                "receiver": message.receiver,
                "content": message.content,
            },
            agent_id=message.sender,
            action="acl_send",
        )
        result = self.governance_engine.evaluate(request)
        self.receipt_generator.create_receipt(result, request)

        if result.decision == PolicyDecision.DENY:
            logger.warning("Message blocked by governance", message_id=message.id)
            return None

        if result.decision == PolicyDecision.REDACT and result.modified_payload:
            message.content = result.modified_payload.get("content", message.content)

        if message.conversation_id and message.conversation_id in self._conversations:
            self._conversations[message.conversation_id].messages.append(message)

        if message.receiver == "all":
            return None

        if message.receiver not in self._agents:
            raise AgentNotFoundError(f"Agent {message.receiver} not registered")

        handler = self._agents[message.receiver]
        response = handler(message)

        if response and message.conversation_id:
            response.conversation_id = message.conversation_id
            response.reply_to = message.id
            if message.conversation_id in self._conversations:
                self._conversations[message.conversation_id].messages.append(response)

                protocol = self._protocols.get(
                    self._conversations[message.conversation_id].protocol
                )
                if protocol and protocol.is_terminal(response.performative):
                    self._conversations[message.conversation_id].status = "completed"
                    self._conversations[message.conversation_id].ended_at = datetime.utcnow()

        return response

    def broadcast(self, message: ACLMessage) -> List[ACLMessage]:
        """
        Broadcast message to all agents.

        Args:
            message: The ACL message to broadcast.

        Returns:
            List of response messages from all agents.
        """
        message.receiver = "all"
        responses = []

        request = EvaluationRequest(
            payload={
                "performative": message.performative.value,
                "sender": message.sender,
                "content": message.content,
            },
            agent_id=message.sender,
            action="acl_broadcast",
        )
        result = self.governance_engine.evaluate(request)
        self.receipt_generator.create_receipt(result, request)

        if result.decision == PolicyDecision.DENY:
            return []

        if result.decision == PolicyDecision.REDACT and result.modified_payload:
            message.content = result.modified_payload.get("content", message.content)

        for agent_id, handler in self._agents.items():
            if agent_id == message.sender:
                continue

            individual_message = ACLMessage(
                performative=message.performative,
                sender=message.sender,
                receiver=agent_id,
                content=message.content,
                conversation_id=message.conversation_id,
                protocol=message.protocol,
                language=message.language,
                ontology=message.ontology,
                metadata=message.metadata,
            )

            try:
                response = handler(individual_message)
                if response:
                    responses.append(response)
            except Exception as e:
                logger.error("Broadcast handler error", agent_id=agent_id, error=str(e))

        return responses

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: The conversation ID.

        Returns:
            The Conversation if found, None otherwise.
        """
        return self._conversations.get(conversation_id)

    def start_conversation(
        self, protocol: str, participants: List[str]
    ) -> Conversation:
        """
        Start a new conversation.

        Args:
            protocol: The protocol to use for this conversation.
            participants: List of participant agent IDs.

        Returns:
            The newly created Conversation.
        """
        conversation_id = str(uuid4())[:8]
        conversation = Conversation(
            id=conversation_id,
            protocol=protocol,
            participants=participants,
        )
        self._conversations[conversation_id] = conversation
        logger.info("Conversation started", conversation_id=conversation_id, protocol=protocol)
        return conversation

    def _validate_protocol(self, message: ACLMessage, conversation: Conversation) -> bool:
        """
        Validate message follows protocol rules.

        Args:
            message: The message to validate.
            conversation: The conversation context.

        Returns:
            True if valid, False otherwise.
        """
        protocol = self._protocols.get(conversation.protocol)
        if not protocol:
            return True

        if not conversation.messages:
            return message.performative in protocol.initial_performatives()

        last_message = conversation.messages[-1]
        valid_next = protocol.valid_transitions(last_message.performative)
        return message.performative in valid_next

    def list_agents(self) -> List[str]:
        """Return list of registered agent IDs."""
        return list(self._agents.keys())

    def list_conversations(self) -> List[Conversation]:
        """Return list of all conversations."""
        return list(self._conversations.values())
