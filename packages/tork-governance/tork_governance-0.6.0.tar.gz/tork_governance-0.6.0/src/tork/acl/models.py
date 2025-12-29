"""Data models for the ACL message schema system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class Performative(str, Enum):
    """Standard ACL performatives (speech acts)."""

    REQUEST = "request"
    INFORM = "inform"
    PROPOSE = "propose"
    ACCEPT = "accept"
    REJECT = "reject"
    QUERY = "query"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    FAILURE = "failure"
    AGREE = "agree"
    REFUSE = "refuse"
    CALL_FOR_PROPOSAL = "cfp"


class ACLMessage(BaseModel):
    """Standard Agent Communication Language message."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    performative: Performative = Field(..., description="Speech act type")
    sender: str = Field(..., description="Sender agent ID")
    receiver: str = Field(..., description="Receiver agent ID or 'all' for broadcast")
    content: Any = Field(..., description="Message payload")
    reply_to: Optional[str] = Field(default=None, description="ID of message being replied to")
    conversation_id: Optional[str] = Field(default=None, description="Thread ID")
    protocol: str = Field(default="fipa-request", description="Protocol being used")
    language: str = Field(default="json", description="Content language")
    ontology: Optional[str] = Field(default=None, description="Domain ontology")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires: Optional[datetime] = Field(default=None, description="Message expiration")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    """A conversation thread between agents."""

    id: str = Field(..., description="Conversation ID")
    protocol: str = Field(..., description="Protocol being used")
    participants: List[str] = Field(default_factory=list, description="Agent IDs")
    messages: List[ACLMessage] = Field(default_factory=list)
    status: str = Field(default="active", description="active, completed, failed, cancelled")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
