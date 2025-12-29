"""Fluent builder for ACL messages."""

from typing import Any, Dict, Optional
from datetime import datetime

from tork.acl.models import ACLMessage, Performative


class MessageBuilder:
    """Fluent builder for ACL messages."""

    @staticmethod
    def request(sender: str, receiver: str, content: Any) -> ACLMessage:
        """
        Create a REQUEST message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Request content.

        Returns:
            ACLMessage with REQUEST performative.
        """
        return ACLMessage(
            performative=Performative.REQUEST,
            sender=sender,
            receiver=receiver,
            content=content,
            protocol="fipa-request",
        )

    @staticmethod
    def inform(sender: str, receiver: str, content: Any, reply_to: Optional[str] = None) -> ACLMessage:
        """
        Create an INFORM message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Information content.
            reply_to: Optional message ID being replied to.

        Returns:
            ACLMessage with INFORM performative.
        """
        return ACLMessage(
            performative=Performative.INFORM,
            sender=sender,
            receiver=receiver,
            content=content,
            reply_to=reply_to,
        )

    @staticmethod
    def propose(sender: str, receiver: str, content: Any, reply_to: Optional[str] = None) -> ACLMessage:
        """
        Create a PROPOSE message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Proposal content.
            reply_to: Optional message ID being replied to.

        Returns:
            ACLMessage with PROPOSE performative.
        """
        return ACLMessage(
            performative=Performative.PROPOSE,
            sender=sender,
            receiver=receiver,
            content=content,
            reply_to=reply_to,
            protocol="fipa-contract-net",
        )

    @staticmethod
    def accept(sender: str, receiver: str, content: Any, reply_to: Optional[str] = None) -> ACLMessage:
        """
        Create an ACCEPT message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Acceptance content.
            reply_to: Optional message ID being replied to.

        Returns:
            ACLMessage with ACCEPT performative.
        """
        return ACLMessage(
            performative=Performative.ACCEPT,
            sender=sender,
            receiver=receiver,
            content=content,
            reply_to=reply_to,
        )

    @staticmethod
    def reject(sender: str, receiver: str, content: Any, reply_to: Optional[str] = None) -> ACLMessage:
        """
        Create a REJECT message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Rejection reason.
            reply_to: Optional message ID being replied to.

        Returns:
            ACLMessage with REJECT performative.
        """
        return ACLMessage(
            performative=Performative.REJECT,
            sender=sender,
            receiver=receiver,
            content=content,
            reply_to=reply_to,
        )

    @staticmethod
    def query(sender: str, receiver: str, content: Any) -> ACLMessage:
        """
        Create a QUERY message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Query content.

        Returns:
            ACLMessage with QUERY performative.
        """
        return ACLMessage(
            performative=Performative.QUERY,
            sender=sender,
            receiver=receiver,
            content=content,
            protocol="fipa-query",
        )

    @staticmethod
    def confirm(sender: str, receiver: str, content: Any, reply_to: Optional[str] = None) -> ACLMessage:
        """
        Create a CONFIRM message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Confirmation content.
            reply_to: Optional message ID being replied to.

        Returns:
            ACLMessage with CONFIRM performative.
        """
        return ACLMessage(
            performative=Performative.CONFIRM,
            sender=sender,
            receiver=receiver,
            content=content,
            reply_to=reply_to,
        )

    @staticmethod
    def cancel(sender: str, receiver: str, content: Any, reply_to: Optional[str] = None) -> ACLMessage:
        """
        Create a CANCEL message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Cancellation content.
            reply_to: Optional message ID being replied to.

        Returns:
            ACLMessage with CANCEL performative.
        """
        return ACLMessage(
            performative=Performative.CANCEL,
            sender=sender,
            receiver=receiver,
            content=content,
            reply_to=reply_to,
        )

    @staticmethod
    def failure(sender: str, receiver: str, content: Any, reply_to: Optional[str] = None) -> ACLMessage:
        """
        Create a FAILURE message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Failure reason.
            reply_to: Optional message ID being replied to.

        Returns:
            ACLMessage with FAILURE performative.
        """
        return ACLMessage(
            performative=Performative.FAILURE,
            sender=sender,
            receiver=receiver,
            content=content,
            reply_to=reply_to,
        )

    @staticmethod
    def agree(sender: str, receiver: str, content: Any, reply_to: Optional[str] = None) -> ACLMessage:
        """
        Create an AGREE message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Agreement content.
            reply_to: Optional message ID being replied to.

        Returns:
            ACLMessage with AGREE performative.
        """
        return ACLMessage(
            performative=Performative.AGREE,
            sender=sender,
            receiver=receiver,
            content=content,
            reply_to=reply_to,
        )

    @staticmethod
    def refuse(sender: str, receiver: str, content: Any, reply_to: Optional[str] = None) -> ACLMessage:
        """
        Create a REFUSE message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Refusal reason.
            reply_to: Optional message ID being replied to.

        Returns:
            ACLMessage with REFUSE performative.
        """
        return ACLMessage(
            performative=Performative.REFUSE,
            sender=sender,
            receiver=receiver,
            content=content,
            reply_to=reply_to,
        )

    @staticmethod
    def call_for_proposal(sender: str, receiver: str, content: Any) -> ACLMessage:
        """
        Create a CALL_FOR_PROPOSAL (CFP) message.

        Args:
            sender: Sender agent ID.
            receiver: Receiver agent ID or "all" for broadcast.
            content: CFP content.

        Returns:
            ACLMessage with CALL_FOR_PROPOSAL performative.
        """
        return ACLMessage(
            performative=Performative.CALL_FOR_PROPOSAL,
            sender=sender,
            receiver=receiver,
            content=content,
            protocol="fipa-contract-net",
        )

    @staticmethod
    def custom(
        performative: Performative,
        sender: str,
        receiver: str,
        content: Any,
        protocol: str = "fipa-request",
        conversation_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        ontology: Optional[str] = None,
        expires: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ACLMessage:
        """
        Create a custom ACL message with all options.

        Args:
            performative: The message performative.
            sender: Sender agent ID.
            receiver: Receiver agent ID.
            content: Message content.
            protocol: Protocol name.
            conversation_id: Optional conversation ID.
            reply_to: Optional message ID being replied to.
            ontology: Optional domain ontology.
            expires: Optional expiration datetime.
            metadata: Optional additional metadata.

        Returns:
            ACLMessage with specified options.
        """
        return ACLMessage(
            performative=performative,
            sender=sender,
            receiver=receiver,
            content=content,
            protocol=protocol,
            conversation_id=conversation_id,
            reply_to=reply_to,
            ontology=ontology,
            expires=expires,
            metadata=metadata or {},
        )
