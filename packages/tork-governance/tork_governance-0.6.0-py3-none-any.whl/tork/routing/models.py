"""Data models for the Role/Sector Routing system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Sector(str, Enum):
    """Industry sectors."""

    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    LEGAL = "legal"
    TECHNOLOGY = "technology"
    MARKETING = "marketing"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    GENERAL = "general"


class Role(str, Enum):
    """User roles within sectors."""

    STUDENT = "student"
    TEACHER = "teacher"
    ADMINISTRATOR = "administrator"
    RESEARCHER = "researcher"

    PATIENT = "patient"
    DOCTOR = "doctor"
    NURSE = "nurse"
    PHARMACIST = "pharmacist"

    EXECUTIVE = "executive"
    MANAGER = "manager"
    ANALYST = "analyst"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    SUPPORT = "support"

    LAWYER = "lawyer"
    PARALEGAL = "paralegal"
    COMPLIANCE_OFFICER = "compliance_officer"

    ACCOUNTANT = "accountant"
    TRADER = "trader"
    FINANCIAL_ADVISOR = "financial_advisor"

    CUSTOMER = "customer"
    VENDOR = "vendor"
    PARTNER = "partner"

    GENERAL_USER = "general_user"


class RoutingContext(BaseModel):
    """Context for routing decisions."""

    sector: Sector = Field(..., description="Industry sector")
    role: Role = Field(..., description="User role")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    organization_id: Optional[str] = Field(default=None, description="Organization ID")
    request_type: str = Field(default="general", description="Type of request")
    content: Any = Field(default=None, description="Request content")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RouteConfig(BaseModel):
    """Configuration for a route."""

    route_id: str = Field(..., description="Unique route identifier")
    name: str = Field(..., description="Route name")
    description: str = Field(default="")

    sectors: List[Sector] = Field(default_factory=list, description="Applicable sectors")
    roles: List[Role] = Field(default_factory=list, description="Applicable roles")

    target_agent: Optional[str] = Field(default=None, description="Target agent ID")
    target_persona: Optional[str] = Field(default=None, description="Target persona ID")

    governance_policy: Optional[str] = Field(default=None, description="Policy to apply")
    pii_redaction: bool = Field(default=True)
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.7)

    allowed_actions: List[str] = Field(default_factory=list)
    blocked_actions: List[str] = Field(default_factory=list)

    priority: int = Field(default=0, description="Route priority (higher = more important)")
    enabled: bool = Field(default=True)

    metadata: Dict[str, Any] = Field(default_factory=dict)


class RoutingResult(BaseModel):
    """Result of a routing decision."""

    matched: bool = Field(..., description="Whether a route was matched")
    route: Optional[RouteConfig] = Field(default=None, description="Matched route")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    fallback_used: bool = Field(default=False)
    matched_rules: List[str] = Field(default_factory=list, description="Rules that matched")
    context: Optional[RoutingContext] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
