"""Sector-based routing with governance integration."""

from typing import Any, Dict, List, Optional

import structlog

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest, PolicyDecision
from tork.compliance.receipts import ReceiptGenerator
from tork.routing.models import (
    Role,
    Sector,
    RouteConfig,
    RoutingContext,
    RoutingResult,
)
from tork.routing.rules import RoutingRule, RuleEngine

logger = structlog.get_logger(__name__)


class SectorRouter:
    """Route requests based on sector and role with governance."""

    def __init__(
        self,
        governance_engine: Optional[GovernanceEngine] = None,
        signing_key: str = "routing-secret",
    ):
        """
        Initialize the sector router.

        Args:
            governance_engine: Optional GovernanceEngine for policy evaluation.
            signing_key: Key for signing compliance receipts.
        """
        self.governance_engine = governance_engine or GovernanceEngine()
        self.receipt_generator = ReceiptGenerator(signing_key=signing_key)
        self._routes: Dict[str, RouteConfig] = {}
        self._rule_engine = RuleEngine()
        self._fallback_route: Optional[RouteConfig] = None

        logger.info("SectorRouter initialized")

    def add_route(self, route: RouteConfig) -> str:
        """
        Add a route configuration.

        Args:
            route: The route configuration.

        Returns:
            The route ID.
        """
        self._routes[route.route_id] = route

        rule = RoutingRule(
            rule_id=f"route-{route.route_id}",
            name=route.name,
            sectors=route.sectors,
            roles=route.roles,
            priority=route.priority,
            enabled=route.enabled,
        )
        self._rule_engine.add_rule(rule)

        logger.info("Route added", route_id=route.route_id)
        return route.route_id

    def remove_route(self, route_id: str) -> bool:
        """
        Remove a route.

        Args:
            route_id: The route to remove.

        Returns:
            True if removed, False if not found.
        """
        if route_id in self._routes:
            del self._routes[route_id]
            self._rule_engine.remove_rule(f"route-{route_id}")
            return True
        return False

    def set_fallback(self, route: RouteConfig) -> None:
        """
        Set the fallback route for unmatched requests.

        Args:
            route: The fallback route configuration.
        """
        self._fallback_route = route

    def route(self, context: RoutingContext) -> RoutingResult:
        """
        Route a request based on context.

        Args:
            context: The routing context.

        Returns:
            RoutingResult with matched route and details.
        """
        request = EvaluationRequest(
            payload={
                "sector": context.sector.value,
                "role": context.role.value,
                "request_type": context.request_type,
                "content": context.content,
            },
            agent_id=context.user_id or "anonymous",
            action="route_request",
        )
        result = self.governance_engine.evaluate(request)

        if result.decision == PolicyDecision.DENY:
            logger.warning("Routing blocked by governance", context=context.model_dump())
            return RoutingResult(
                matched=False,
                confidence=0.0,
                context=context,
            )

        matching_rules = self._rule_engine.evaluate(context)
        matched_rule_ids = [r.rule_id for r in matching_rules]

        matched_route = None
        fallback_used = False
        confidence = 0.0

        if matching_rules:
            best_rule = matching_rules[0]
            route_id = best_rule.rule_id.replace("route-", "")
            if route_id in self._routes:
                matched_route = self._routes[route_id]
                confidence = min(1.0, 0.5 + (best_rule.priority * 0.1))
        elif self._fallback_route:
            matched_route = self._fallback_route
            fallback_used = True
            confidence = 0.3

        self.receipt_generator.create_receipt(result, request)

        return RoutingResult(
            matched=matched_route is not None,
            route=matched_route,
            confidence=confidence,
            fallback_used=fallback_used,
            matched_rules=matched_rule_ids,
            context=context,
        )

    def route_by_sector_role(
        self,
        sector: Sector,
        role: Role,
        content: Any = None,
        user_id: Optional[str] = None,
    ) -> RoutingResult:
        """
        Convenience method to route by sector and role.

        Args:
            sector: The industry sector.
            role: The user role.
            content: Optional request content.
            user_id: Optional user identifier.

        Returns:
            RoutingResult with matched route.
        """
        context = RoutingContext(
            sector=sector,
            role=role,
            content=content,
            user_id=user_id,
        )
        return self.route(context)

    def get_routes_for_sector(self, sector: Sector) -> List[RouteConfig]:
        """
        Get all routes applicable to a sector.

        Args:
            sector: The sector to filter by.

        Returns:
            List of applicable routes.
        """
        return [
            r for r in self._routes.values()
            if sector in r.sectors or not r.sectors
        ]

    def get_routes_for_role(self, role: Role) -> List[RouteConfig]:
        """
        Get all routes applicable to a role.

        Args:
            role: The role to filter by.

        Returns:
            List of applicable routes.
        """
        return [
            r for r in self._routes.values()
            if role in r.roles or not r.roles
        ]

    def list_routes(self) -> List[RouteConfig]:
        """Return all registered routes."""
        return list(self._routes.values())

    def get_route(self, route_id: str) -> Optional[RouteConfig]:
        """Get a route by ID."""
        return self._routes.get(route_id)
