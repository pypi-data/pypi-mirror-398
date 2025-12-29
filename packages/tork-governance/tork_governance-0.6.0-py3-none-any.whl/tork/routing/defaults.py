"""Pre-defined route configurations for common sectors."""

from typing import List

from tork.routing.models import Role, Sector, RouteConfig


def education_routes() -> List[RouteConfig]:
    """Education sector route configurations."""
    return [
        RouteConfig(
            route_id="edu-student",
            name="Student Route",
            description="Route for student users in education",
            sectors=[Sector.EDUCATION],
            roles=[Role.STUDENT],
            target_persona="research-assistant",
            governance_policy="education-safe",
            pii_redaction=True,
            blocked_actions=["grade_assignment", "modify_records"],
            priority=5,
        ),
        RouteConfig(
            route_id="edu-teacher",
            name="Teacher Route",
            description="Route for teacher users in education",
            sectors=[Sector.EDUCATION],
            roles=[Role.TEACHER],
            target_persona="content-writer",
            governance_policy="education-standard",
            pii_redaction=True,
            allowed_actions=["create_content", "grade_assignment", "view_analytics"],
            priority=6,
        ),
        RouteConfig(
            route_id="edu-researcher",
            name="Researcher Route",
            description="Route for researchers in education",
            sectors=[Sector.EDUCATION],
            roles=[Role.RESEARCHER],
            target_persona="research-assistant",
            governance_policy="research-standard",
            pii_redaction=True,
            max_tokens=8192,
            priority=7,
        ),
        RouteConfig(
            route_id="edu-admin",
            name="Education Administrator Route",
            description="Route for administrators in education",
            sectors=[Sector.EDUCATION],
            roles=[Role.ADMINISTRATOR],
            governance_policy="admin-elevated",
            pii_redaction=True,
            allowed_actions=["view_reports", "manage_users", "configure_settings"],
            priority=8,
        ),
    ]


def healthcare_routes() -> List[RouteConfig]:
    """Healthcare sector route configurations."""
    return [
        RouteConfig(
            route_id="health-patient",
            name="Patient Route",
            description="Route for patient users",
            sectors=[Sector.HEALTHCARE],
            roles=[Role.PATIENT],
            governance_policy="hipaa-strict",
            pii_redaction=True,
            blocked_actions=["view_other_records", "prescribe_medication"],
            priority=5,
        ),
        RouteConfig(
            route_id="health-doctor",
            name="Doctor Route",
            description="Route for doctors and physicians",
            sectors=[Sector.HEALTHCARE],
            roles=[Role.DOCTOR],
            governance_policy="hipaa-provider",
            pii_redaction=True,
            allowed_actions=["view_patient_records", "prescribe_medication", "order_tests"],
            max_tokens=8192,
            priority=8,
        ),
        RouteConfig(
            route_id="health-nurse",
            name="Nurse Route",
            description="Route for nursing staff",
            sectors=[Sector.HEALTHCARE],
            roles=[Role.NURSE],
            governance_policy="hipaa-provider",
            pii_redaction=True,
            allowed_actions=["view_patient_records", "update_vitals"],
            blocked_actions=["prescribe_medication"],
            priority=7,
        ),
    ]


def finance_routes() -> List[RouteConfig]:
    """Finance sector route configurations."""
    return [
        RouteConfig(
            route_id="fin-analyst",
            name="Financial Analyst Route",
            description="Route for financial analysts",
            sectors=[Sector.FINANCE],
            roles=[Role.ANALYST],
            target_persona="data-analyst",
            governance_policy="finance-standard",
            pii_redaction=True,
            allowed_actions=["analyze_data", "generate_reports", "view_portfolios"],
            max_tokens=8192,
            priority=6,
        ),
        RouteConfig(
            route_id="fin-advisor",
            name="Financial Advisor Route",
            description="Route for financial advisors",
            sectors=[Sector.FINANCE],
            roles=[Role.FINANCIAL_ADVISOR],
            target_persona="financial-advisor",
            governance_policy="finance-advisory",
            pii_redaction=True,
            blocked_actions=["execute_trades", "transfer_funds"],
            priority=7,
        ),
        RouteConfig(
            route_id="fin-trader",
            name="Trader Route",
            description="Route for traders",
            sectors=[Sector.FINANCE],
            roles=[Role.TRADER],
            governance_policy="finance-trading",
            pii_redaction=True,
            allowed_actions=["view_market_data", "analyze_positions"],
            blocked_actions=["execute_trades"],
            priority=8,
        ),
    ]


def legal_routes() -> List[RouteConfig]:
    """Legal sector route configurations."""
    return [
        RouteConfig(
            route_id="legal-lawyer",
            name="Lawyer Route",
            description="Route for attorneys",
            sectors=[Sector.LEGAL],
            roles=[Role.LAWYER],
            target_persona="legal-analyst",
            governance_policy="legal-privileged",
            pii_redaction=True,
            allowed_actions=["analyze_documents", "draft_contracts", "research_case_law"],
            max_tokens=8192,
            priority=8,
        ),
        RouteConfig(
            route_id="legal-paralegal",
            name="Paralegal Route",
            description="Route for paralegals",
            sectors=[Sector.LEGAL],
            roles=[Role.PARALEGAL],
            target_persona="legal-analyst",
            governance_policy="legal-standard",
            pii_redaction=True,
            allowed_actions=["research_case_law", "summarize_documents"],
            blocked_actions=["provide_legal_advice"],
            priority=6,
        ),
        RouteConfig(
            route_id="legal-compliance",
            name="Compliance Officer Route",
            description="Route for compliance officers",
            sectors=[Sector.LEGAL],
            roles=[Role.COMPLIANCE_OFFICER],
            governance_policy="compliance-audit",
            pii_redaction=True,
            allowed_actions=["audit_records", "generate_compliance_reports"],
            priority=7,
        ),
    ]


def technology_routes() -> List[RouteConfig]:
    """Technology sector route configurations."""
    return [
        RouteConfig(
            route_id="tech-developer",
            name="Developer Route",
            description="Route for software developers",
            sectors=[Sector.TECHNOLOGY],
            roles=[Role.DEVELOPER],
            target_persona="code-reviewer",
            governance_policy="tech-standard",
            pii_redaction=True,
            allowed_actions=["review_code", "generate_code", "debug"],
            max_tokens=8192,
            temperature=0.3,
            priority=6,
        ),
        RouteConfig(
            route_id="tech-analyst",
            name="Tech Analyst Route",
            description="Route for technical analysts",
            sectors=[Sector.TECHNOLOGY],
            roles=[Role.ANALYST],
            target_persona="data-analyst",
            governance_policy="tech-standard",
            pii_redaction=True,
            priority=5,
        ),
        RouteConfig(
            route_id="tech-manager",
            name="Tech Manager Route",
            description="Route for technology managers",
            sectors=[Sector.TECHNOLOGY],
            roles=[Role.MANAGER],
            governance_policy="tech-elevated",
            pii_redaction=True,
            allowed_actions=["view_metrics", "generate_reports", "manage_resources"],
            priority=7,
        ),
    ]
