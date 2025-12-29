"""Routing rules engine."""

from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from tork.routing.models import Role, Sector, RoutingContext


class RoutingRule(BaseModel):
    """A single routing rule."""

    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(default="")

    sectors: List[Sector] = Field(default_factory=list, description="Match these sectors")
    roles: List[Role] = Field(default_factory=list, description="Match these roles")
    request_types: List[str] = Field(default_factory=list, description="Match request types")

    required_permissions: List[str] = Field(default_factory=list)
    blocked_permissions: List[str] = Field(default_factory=list)

    conditions: Dict[str, Any] = Field(default_factory=dict, description="Additional conditions")

    priority: int = Field(default=0)
    enabled: bool = Field(default=True)

    def matches(self, context: RoutingContext) -> bool:
        """
        Check if this rule matches the given context.

        Args:
            context: The routing context to check.

        Returns:
            True if the rule matches, False otherwise.
        """
        if not self.enabled:
            return False

        if self.sectors and context.sector not in self.sectors:
            return False

        if self.roles and context.role not in self.roles:
            return False

        if self.request_types and context.request_type not in self.request_types:
            return False

        if self.required_permissions:
            if not all(p in context.permissions for p in self.required_permissions):
                return False

        if self.blocked_permissions:
            if any(p in context.permissions for p in self.blocked_permissions):
                return False

        for key, value in self.conditions.items():
            if key not in context.metadata:
                return False
            if context.metadata[key] != value:
                return False

        return True


class RuleEngine:
    """Engine for evaluating routing rules."""

    def __init__(self):
        """Initialize the rule engine."""
        self._rules: Dict[str, RoutingRule] = {}
        self._custom_matchers: Dict[str, Callable[[RoutingContext], bool]] = {}

    def add_rule(self, rule: RoutingRule) -> str:
        """
        Add a routing rule.

        Args:
            rule: The rule to add.

        Returns:
            The rule ID.
        """
        self._rules[rule.rule_id] = rule
        return rule.rule_id

    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a rule by ID.

        Args:
            rule_id: The rule to remove.

        Returns:
            True if removed, False if not found.
        """
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def add_custom_matcher(
        self,
        name: str,
        matcher: Callable[[RoutingContext], bool],
    ) -> None:
        """
        Add a custom matcher function.

        Args:
            name: Matcher name.
            matcher: Function that takes context and returns bool.
        """
        self._custom_matchers[name] = matcher

    def evaluate(self, context: RoutingContext) -> List[RoutingRule]:
        """
        Evaluate all rules against a context.

        Args:
            context: The routing context.

        Returns:
            List of matching rules, sorted by priority (highest first).
        """
        matching = []

        for rule in self._rules.values():
            if rule.matches(context):
                matching.append(rule)

        matching.sort(key=lambda r: r.priority, reverse=True)
        return matching

    def get_best_match(self, context: RoutingContext) -> Optional[RoutingRule]:
        """
        Get the highest priority matching rule.

        Args:
            context: The routing context.

        Returns:
            The best matching rule, or None.
        """
        matches = self.evaluate(context)
        return matches[0] if matches else None

    def list_rules(self) -> List[RoutingRule]:
        """Return all registered rules."""
        return list(self._rules.values())

    def get_rule(self, rule_id: str) -> Optional[RoutingRule]:
        """Get a rule by ID."""
        return self._rules.get(rule_id)
