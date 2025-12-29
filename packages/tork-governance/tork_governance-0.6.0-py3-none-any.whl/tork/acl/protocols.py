"""Interaction protocols for ACL messaging."""

from abc import ABC, abstractmethod
from typing import List

from tork.acl.models import Performative


class Protocol(ABC):
    """Base class for interaction protocols."""

    name: str = "base"

    @abstractmethod
    def valid_transitions(self, current_performative: Performative) -> List[Performative]:
        """
        Return valid next performatives.

        Args:
            current_performative: The current performative in the conversation.

        Returns:
            List of valid next performatives.
        """
        pass

    @abstractmethod
    def is_terminal(self, performative: Performative) -> bool:
        """
        Check if performative ends the protocol.

        Args:
            performative: The performative to check.

        Returns:
            True if this performative ends the conversation.
        """
        pass

    def initial_performatives(self) -> List[Performative]:
        """Return valid initial performatives for this protocol."""
        return []


class FIPARequestProtocol(Protocol):
    """
    Standard FIPA Request protocol.

    Flow: request -> agree/refuse -> inform/failure
    """

    name = "fipa-request"

    def valid_transitions(self, current_performative: Performative) -> List[Performative]:
        transitions = {
            Performative.REQUEST: [Performative.AGREE, Performative.REFUSE],
            Performative.AGREE: [Performative.INFORM, Performative.FAILURE],
            Performative.REFUSE: [],
            Performative.INFORM: [],
            Performative.FAILURE: [],
        }
        return transitions.get(current_performative, [])

    def is_terminal(self, performative: Performative) -> bool:
        return performative in [
            Performative.REFUSE,
            Performative.INFORM,
            Performative.FAILURE,
        ]

    def initial_performatives(self) -> List[Performative]:
        return [Performative.REQUEST]


class FIPAContractNetProtocol(Protocol):
    """
    FIPA Contract Net protocol for task allocation.

    Flow: cfp -> propose/refuse -> accept/reject -> inform/failure
    """

    name = "fipa-contract-net"

    def valid_transitions(self, current_performative: Performative) -> List[Performative]:
        transitions = {
            Performative.CALL_FOR_PROPOSAL: [Performative.PROPOSE, Performative.REFUSE],
            Performative.PROPOSE: [Performative.ACCEPT, Performative.REJECT],
            Performative.REFUSE: [],
            Performative.ACCEPT: [Performative.INFORM, Performative.FAILURE],
            Performative.REJECT: [],
            Performative.INFORM: [],
            Performative.FAILURE: [],
        }
        return transitions.get(current_performative, [])

    def is_terminal(self, performative: Performative) -> bool:
        return performative in [
            Performative.REFUSE,
            Performative.REJECT,
            Performative.INFORM,
            Performative.FAILURE,
        ]

    def initial_performatives(self) -> List[Performative]:
        return [Performative.CALL_FOR_PROPOSAL]


class FIPAQueryProtocol(Protocol):
    """
    FIPA Query protocol for information retrieval.

    Flow: query -> inform/failure
    """

    name = "fipa-query"

    def valid_transitions(self, current_performative: Performative) -> List[Performative]:
        transitions = {
            Performative.QUERY: [Performative.INFORM, Performative.FAILURE],
            Performative.INFORM: [],
            Performative.FAILURE: [],
        }
        return transitions.get(current_performative, [])

    def is_terminal(self, performative: Performative) -> bool:
        return performative in [Performative.INFORM, Performative.FAILURE]

    def initial_performatives(self) -> List[Performative]:
        return [Performative.QUERY]
