"""Tests for the Role/Sector Routing system."""

import pytest

from tork.routing import (
    Sector,
    Role,
    RoutingContext,
    RouteConfig,
    RoutingResult,
    SectorRouter,
    RoutingRule,
    RuleEngine,
    education_routes,
    healthcare_routes,
    finance_routes,
    legal_routes,
    technology_routes,
)
from tork.core.engine import GovernanceEngine


class TestSectorEnum:
    """Tests for Sector enum."""

    def test_all_sectors(self):
        assert Sector.EDUCATION == "education"
        assert Sector.HEALTHCARE == "healthcare"
        assert Sector.FINANCE == "finance"
        assert Sector.LEGAL == "legal"
        assert Sector.TECHNOLOGY == "technology"
        assert Sector.MARKETING == "marketing"
        assert Sector.RETAIL == "retail"
        assert Sector.MANUFACTURING == "manufacturing"
        assert Sector.GOVERNMENT == "government"
        assert Sector.NONPROFIT == "nonprofit"
        assert Sector.GENERAL == "general"


class TestRoleEnum:
    """Tests for Role enum."""

    def test_education_roles(self):
        assert Role.STUDENT == "student"
        assert Role.TEACHER == "teacher"
        assert Role.RESEARCHER == "researcher"

    def test_healthcare_roles(self):
        assert Role.PATIENT == "patient"
        assert Role.DOCTOR == "doctor"
        assert Role.NURSE == "nurse"

    def test_business_roles(self):
        assert Role.EXECUTIVE == "executive"
        assert Role.MANAGER == "manager"
        assert Role.ANALYST == "analyst"
        assert Role.DEVELOPER == "developer"


class TestRoutingContextModel:
    """Tests for RoutingContext model."""

    def test_basic_context(self):
        context = RoutingContext(
            sector=Sector.EDUCATION,
            role=Role.STUDENT,
        )
        assert context.sector == Sector.EDUCATION
        assert context.role == Role.STUDENT
        assert context.request_type == "general"

    def test_context_with_all_fields(self):
        context = RoutingContext(
            sector=Sector.HEALTHCARE,
            role=Role.DOCTOR,
            user_id="user-123",
            organization_id="org-456",
            request_type="patient_query",
            content={"query": "test"},
            permissions=["view_records", "prescribe"],
            metadata={"department": "cardiology"},
        )
        assert context.user_id == "user-123"
        assert "view_records" in context.permissions


class TestRouteConfigModel:
    """Tests for RouteConfig model."""

    def test_basic_config(self):
        config = RouteConfig(
            route_id="test-route",
            name="Test Route",
        )
        assert config.route_id == "test-route"
        assert config.pii_redaction is True
        assert config.enabled is True

    def test_config_with_sectors_roles(self):
        config = RouteConfig(
            route_id="edu-route",
            name="Education Route",
            sectors=[Sector.EDUCATION],
            roles=[Role.STUDENT, Role.TEACHER],
            target_persona="research-assistant",
            priority=5,
        )
        assert Sector.EDUCATION in config.sectors
        assert len(config.roles) == 2


class TestRoutingRule:
    """Tests for RoutingRule."""

    def test_rule_matches_sector(self):
        rule = RoutingRule(
            rule_id="test-rule",
            name="Test",
            sectors=[Sector.EDUCATION],
        )
        context = RoutingContext(sector=Sector.EDUCATION, role=Role.STUDENT)
        assert rule.matches(context) is True

        context2 = RoutingContext(sector=Sector.HEALTHCARE, role=Role.DOCTOR)
        assert rule.matches(context2) is False

    def test_rule_matches_role(self):
        rule = RoutingRule(
            rule_id="test-rule",
            name="Test",
            roles=[Role.DEVELOPER],
        )
        context = RoutingContext(sector=Sector.TECHNOLOGY, role=Role.DEVELOPER)
        assert rule.matches(context) is True

        context2 = RoutingContext(sector=Sector.TECHNOLOGY, role=Role.MANAGER)
        assert rule.matches(context2) is False

    def test_rule_matches_permissions(self):
        rule = RoutingRule(
            rule_id="test-rule",
            name="Test",
            required_permissions=["admin"],
        )
        context = RoutingContext(
            sector=Sector.GENERAL,
            role=Role.GENERAL_USER,
            permissions=["admin", "read"],
        )
        assert rule.matches(context) is True

        context2 = RoutingContext(
            sector=Sector.GENERAL,
            role=Role.GENERAL_USER,
            permissions=["read"],
        )
        assert rule.matches(context2) is False

    def test_disabled_rule(self):
        rule = RoutingRule(
            rule_id="disabled-rule",
            name="Disabled",
            enabled=False,
        )
        context = RoutingContext(sector=Sector.GENERAL, role=Role.GENERAL_USER)
        assert rule.matches(context) is False


class TestRuleEngine:
    """Tests for RuleEngine."""

    def test_add_and_evaluate(self):
        engine = RuleEngine()
        engine.add_rule(RoutingRule(
            rule_id="edu-rule",
            name="Education",
            sectors=[Sector.EDUCATION],
            priority=5,
        ))
        engine.add_rule(RoutingRule(
            rule_id="health-rule",
            name="Healthcare",
            sectors=[Sector.HEALTHCARE],
            priority=10,
        ))

        context = RoutingContext(sector=Sector.EDUCATION, role=Role.STUDENT)
        matches = engine.evaluate(context)
        assert len(matches) == 1
        assert matches[0].rule_id == "edu-rule"

    def test_priority_ordering(self):
        engine = RuleEngine()
        engine.add_rule(RoutingRule(
            rule_id="low-priority",
            name="Low",
            sectors=[Sector.TECHNOLOGY],
            priority=1,
        ))
        engine.add_rule(RoutingRule(
            rule_id="high-priority",
            name="High",
            sectors=[Sector.TECHNOLOGY],
            priority=10,
        ))

        context = RoutingContext(sector=Sector.TECHNOLOGY, role=Role.DEVELOPER)
        matches = engine.evaluate(context)
        assert len(matches) == 2
        assert matches[0].rule_id == "high-priority"

    def test_get_best_match(self):
        engine = RuleEngine()
        engine.add_rule(RoutingRule(
            rule_id="rule-1",
            name="Rule 1",
            sectors=[Sector.FINANCE],
            priority=5,
        ))
        engine.add_rule(RoutingRule(
            rule_id="rule-2",
            name="Rule 2",
            sectors=[Sector.FINANCE],
            priority=10,
        ))

        context = RoutingContext(sector=Sector.FINANCE, role=Role.ANALYST)
        best = engine.get_best_match(context)
        assert best is not None
        assert best.rule_id == "rule-2"


class TestSectorRouter:
    """Tests for SectorRouter."""

    def test_initialization(self):
        router = SectorRouter()
        assert router.governance_engine is not None

    def test_add_route(self):
        router = SectorRouter()
        route = RouteConfig(
            route_id="test-route",
            name="Test",
            sectors=[Sector.EDUCATION],
            roles=[Role.STUDENT],
        )
        router.add_route(route)
        assert router.get_route("test-route") is not None

    def test_route_matching(self):
        router = SectorRouter()
        router.add_route(RouteConfig(
            route_id="edu-student",
            name="Education Student",
            sectors=[Sector.EDUCATION],
            roles=[Role.STUDENT],
            priority=5,
        ))

        context = RoutingContext(sector=Sector.EDUCATION, role=Role.STUDENT)
        result = router.route(context)
        assert result.matched is True
        assert result.route.route_id == "edu-student"

    def test_no_match(self):
        router = SectorRouter()
        router.add_route(RouteConfig(
            route_id="edu-route",
            name="Education",
            sectors=[Sector.EDUCATION],
            roles=[Role.STUDENT],
        ))

        context = RoutingContext(sector=Sector.HEALTHCARE, role=Role.DOCTOR)
        result = router.route(context)
        assert result.matched is False

    def test_fallback_route(self):
        router = SectorRouter()
        router.set_fallback(RouteConfig(
            route_id="fallback",
            name="Fallback Route",
        ))

        context = RoutingContext(sector=Sector.GENERAL, role=Role.GENERAL_USER)
        result = router.route(context)
        assert result.matched is True
        assert result.fallback_used is True

    def test_route_by_sector_role(self):
        router = SectorRouter()
        router.add_route(RouteConfig(
            route_id="tech-dev",
            name="Tech Developer",
            sectors=[Sector.TECHNOLOGY],
            roles=[Role.DEVELOPER],
        ))

        result = router.route_by_sector_role(
            Sector.TECHNOLOGY,
            Role.DEVELOPER,
            content="test request",
        )
        assert result.matched is True

    def test_get_routes_for_sector(self):
        router = SectorRouter()
        router.add_route(RouteConfig(
            route_id="edu-1",
            name="Edu 1",
            sectors=[Sector.EDUCATION],
        ))
        router.add_route(RouteConfig(
            route_id="health-1",
            name="Health 1",
            sectors=[Sector.HEALTHCARE],
        ))

        edu_routes = router.get_routes_for_sector(Sector.EDUCATION)
        assert len(edu_routes) == 1
        assert edu_routes[0].route_id == "edu-1"


class TestDefaultRoutes:
    """Tests for default route configurations."""

    def test_education_routes(self):
        routes = education_routes()
        assert len(routes) >= 3
        route_ids = [r.route_id for r in routes]
        assert "edu-student" in route_ids
        assert "edu-teacher" in route_ids

    def test_healthcare_routes(self):
        routes = healthcare_routes()
        assert len(routes) >= 2
        doctor_route = next(r for r in routes if r.route_id == "health-doctor")
        assert "prescribe_medication" in doctor_route.allowed_actions

    def test_finance_routes(self):
        routes = finance_routes()
        assert len(routes) >= 2
        analyst_route = next(r for r in routes if r.route_id == "fin-analyst")
        assert Sector.FINANCE in analyst_route.sectors

    def test_legal_routes(self):
        routes = legal_routes()
        assert len(routes) >= 2
        lawyer_route = next(r for r in routes if r.route_id == "legal-lawyer")
        assert Role.LAWYER in lawyer_route.roles

    def test_technology_routes(self):
        routes = technology_routes()
        assert len(routes) >= 2
        dev_route = next(r for r in routes if r.route_id == "tech-developer")
        assert "review_code" in dev_route.allowed_actions


class TestGovernanceIntegration:
    """Tests for governance integration with routing."""

    def test_governance_applied_to_routing(self):
        gov_engine = GovernanceEngine()
        router = SectorRouter(governance_engine=gov_engine)

        router.add_route(RouteConfig(
            route_id="test-route",
            name="Test",
            sectors=[Sector.TECHNOLOGY],
            roles=[Role.DEVELOPER],
        ))

        context = RoutingContext(
            sector=Sector.TECHNOLOGY,
            role=Role.DEVELOPER,
            content="test@example.com",
        )
        result = router.route(context)
        assert result.matched is True
