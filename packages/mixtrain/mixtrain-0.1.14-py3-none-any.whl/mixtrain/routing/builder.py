"""Builder pattern for creating routing configurations."""

from typing import List, Optional, Union, Dict, Any

from .models import (
    RoutingConfig,
    RoutingRule,
    RoutingCondition,
    RoutingTarget,
    RoutingStrategy,
    ConditionOperator
)
from .conditions import condition


class ConfigBuilder:
    """Builder for creating routing configurations."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.rules: List[RoutingRule] = []
        self.metadata: Dict[str, Any] = {}

    def add_rule(self, name: str, priority: int = 0, description: str = "") -> "RuleBuilder":
        """
        Add a new rule to the configuration.

        Args:
            name: Name of the rule
            priority: Priority of the rule (higher = evaluated first)
            description: Description of the rule

        Returns:
            RuleBuilder for fluent configuration
        """
        rule_builder = RuleBuilder(self, name, priority, description)
        return rule_builder

    def add_metadata(self, key: str, value: Any) -> "ConfigBuilder":
        """Add metadata to the configuration."""
        self.metadata[key] = value
        return self

    def build(self) -> RoutingConfig:
        """Build the routing configuration."""
        return RoutingConfig(
            name=self.name,
            description=self.description,
            rules=self.rules,
            metadata=self.metadata
        )

    def _add_rule(self, rule: RoutingRule) -> None:
        """Internal method to add a completed rule."""
        self.rules.append(rule)


class RuleBuilder:
    """Builder for creating routing rules."""

    def __init__(self, config_builder: ConfigBuilder, name: str, priority: int = 0, description: str = ""):
        self.config_builder = config_builder
        self.name = name
        self.priority = priority
        self.description = description
        self.is_enabled = True
        self.conditions: List[RoutingCondition] = []
        self.strategy = RoutingStrategy.SINGLE
        self.targets: List[RoutingTarget] = []

    # Condition methods
    def when(self, field: str) -> "ConditionBuilder":
        """Start a condition for this rule."""
        return ConditionBuilder(self, field)

    def with_condition(
        self,
        field: str,
        operator: Union[str, ConditionOperator],
        value: Any = None,
        description: str = ""
    ) -> "RuleBuilder":
        """
        Add a condition to this rule.

        Args:
            field: Field path to evaluate
            operator: Comparison operator
            value: Expected value
            description: Condition description

        Returns:
            RuleBuilder for chaining
        """
        if isinstance(operator, str):
            operator = ConditionOperator(operator)

        condition = RoutingCondition(
            field=field,
            operator=operator,
            value=value,
            description=description
        )
        self.conditions.append(condition)
        return self

    # Strategy methods
    def use_single_strategy(self) -> "RuleBuilder":
        """Use single target strategy."""
        self.strategy = RoutingStrategy.SINGLE
        return self

    def use_split_strategy(self) -> "RuleBuilder":
        """Use split (A/B testing) strategy."""
        self.strategy = RoutingStrategy.SPLIT
        return self

    def use_shadow_strategy(self) -> "RuleBuilder":
        """Use shadow routing strategy."""
        self.strategy = RoutingStrategy.SHADOW
        return self

    def use_fallback_strategy(self) -> "RuleBuilder":
        """Use fallback strategy."""
        self.strategy = RoutingStrategy.FALLBACK
        return self

    # Target methods
    def add_target(
        self,
        provider: str,
        model_name: str,
        endpoint: str,
        weight: float = 1.0,
        **kwargs
    ) -> "TargetBuilder":
        """
        Add a target to this rule.

        Args:
            provider: Model provider
            model_name: Name of the model
            endpoint: Model endpoint URL
            weight: Routing weight
            **kwargs: Additional target properties

        Returns:
            TargetBuilder for fluent configuration
        """
        target_builder = TargetBuilder(self, provider, model_name, endpoint, weight, **kwargs)
        return target_builder

    def add_modal_target(
        self,
        model_name: str,
        app_name: str,
        function_name: str,
        request_class: str,
        weight: float = 1.0
    ) -> "TargetBuilder":
        """Add a Modal provider target."""
        endpoint = f"https://{app_name}.modal.run"
        return self.add_target(
            provider="modal",
            model_name=model_name,
            endpoint=endpoint,
            weight=weight,
            function_name=function_name,
            request_class=request_class
        )

    def add_fal_target(
        self,
        model_name: str,
        endpoint_id: str,
        weight: float = 1.0
    ) -> "TargetBuilder":
        """Add a Fal provider target."""
        endpoint = f"https://fal.run/{endpoint_id}"
        return self.add_target(
            provider="fal",
            model_name=model_name,
            endpoint=endpoint,
            weight=weight
        )

    # Control methods
    def enable(self) -> "RuleBuilder":
        """Enable this rule."""
        self.is_enabled = True
        return self

    def disable(self) -> "RuleBuilder":
        """Disable this rule."""
        self.is_enabled = False
        return self

    def set_priority(self, priority: int) -> "RuleBuilder":
        """Set rule priority."""
        self.priority = priority
        return self

    # Build methods
    def and_rule(self, name: str, priority: int = 0, description: str = "") -> "RuleBuilder":
        """Finish this rule and start a new one."""
        self._finish_rule()
        return self.config_builder.add_rule(name, priority, description)

    def build(self) -> RoutingConfig:
        """Finish this rule and build the configuration."""
        self._finish_rule()
        return self.config_builder.build()

    def _add_target(self, target: RoutingTarget) -> None:
        """Internal method to add a target."""
        self.targets.append(target)

    def _finish_rule(self) -> None:
        """Internal method to finish and add the rule."""
        rule = RoutingRule(
            name=self.name,
            description=self.description,
            priority=self.priority,
            is_enabled=self.is_enabled,
            conditions=self.conditions,
            strategy=self.strategy,
            targets=self.targets
        )
        self.config_builder._add_rule(rule)


class ConditionBuilder:
    """Builder for creating conditions."""

    def __init__(self, rule_builder: RuleBuilder, field: str):
        self.rule_builder = rule_builder
        self.field = field

    def equals(self, value: Any, description: str = "") -> RuleBuilder:
        """Add equals condition."""
        return self.rule_builder.with_condition(self.field, ConditionOperator.EQUALS, value, description)

    def not_equals(self, value: Any, description: str = "") -> RuleBuilder:
        """Add not equals condition."""
        return self.rule_builder.with_condition(self.field, ConditionOperator.NOT_EQUALS, value, description)

    def contains(self, value: str, description: str = "") -> RuleBuilder:
        """Add contains condition."""
        return self.rule_builder.with_condition(self.field, ConditionOperator.CONTAINS, value, description)

    def not_contains(self, value: str, description: str = "") -> RuleBuilder:
        """Add not contains condition."""
        return self.rule_builder.with_condition(self.field, ConditionOperator.NOT_CONTAINS, value, description)

    def is_in(self, values: List[Any], description: str = "") -> RuleBuilder:
        """Add in condition."""
        return self.rule_builder.with_condition(self.field, ConditionOperator.IN, values, description)

    def not_in(self, values: List[Any], description: str = "") -> RuleBuilder:
        """Add not in condition."""
        return self.rule_builder.with_condition(self.field, ConditionOperator.NOT_IN, values, description)

    def exists(self, description: str = "") -> RuleBuilder:
        """Add exists condition."""
        return self.rule_builder.with_condition(self.field, ConditionOperator.EXISTS, None, description)

    def not_exists(self, description: str = "") -> RuleBuilder:
        """Add not exists condition."""
        return self.rule_builder.with_condition(self.field, ConditionOperator.NOT_EXISTS, None, description)

    def greater_than(self, value: Union[int, float], description: str = "") -> RuleBuilder:
        """Add greater than condition."""
        return self.rule_builder.with_condition(self.field, ConditionOperator.GREATER_THAN, value, description)

    def less_than(self, value: Union[int, float], description: str = "") -> RuleBuilder:
        """Add less than condition."""
        return self.rule_builder.with_condition(self.field, ConditionOperator.LESS_THAN, value, description)

    def matches_regex(self, pattern: str, description: str = "") -> RuleBuilder:
        """Add regex match condition."""
        return self.rule_builder.with_condition(self.field, ConditionOperator.REGEX, pattern, description)


class TargetBuilder:
    """Builder for creating targets."""

    def __init__(
        self,
        rule_builder: RuleBuilder,
        provider: str,
        model_name: str,
        endpoint: str,
        weight: float = 1.0,
        **kwargs
    ):
        self.rule_builder = rule_builder
        self.target = RoutingTarget(
            provider=provider,
            model_name=model_name,
            endpoint=endpoint,
            weight=weight,
            **kwargs
        )

    def with_label(self, label: str) -> "TargetBuilder":
        """Set target label."""
        self.target.label = label
        return self

    def with_timeout(self, timeout_ms: int) -> "TargetBuilder":
        """Set target timeout."""
        self.target.timeout_ms = timeout_ms
        return self

    def with_retries(self, retry_count: int) -> "TargetBuilder":
        """Set retry count."""
        self.target.retry_count = retry_count
        return self

    def with_weight(self, weight: float) -> "TargetBuilder":
        """Set target weight."""
        self.target.weight = weight
        return self

    def with_headers(self, headers: Dict[str, str]) -> "TargetBuilder":
        """Set custom headers."""
        self.target.headers = headers
        return self

    def with_header(self, name: str, value: str) -> "TargetBuilder":
        """Add a single header."""
        if self.target.headers is None:
            self.target.headers = {}
        self.target.headers[name] = value
        return self

    # Termination methods
    def add_target(self, provider: str, model_name: str, endpoint: str, weight: float = 1.0, **kwargs) -> "TargetBuilder":
        """Finish this target and add another."""
        self._finish_target()
        return self.rule_builder.add_target(provider, model_name, endpoint, weight, **kwargs)

    def and_rule(self, name: str, priority: int = 0, description: str = "") -> RuleBuilder:
        """Finish this target and start a new rule."""
        self._finish_target()
        return self.rule_builder.and_rule(name, priority, description)

    def build(self) -> RoutingConfig:
        """Finish this target and build the configuration."""
        self._finish_target()
        return self.rule_builder.build()

    def _finish_target(self) -> None:
        """Internal method to finish and add the target."""
        self.rule_builder._add_target(self.target)


# Convenience functions for common patterns
def create_simple_config(name: str, endpoint: str) -> RoutingConfig:
    """Create a simple single-endpoint configuration."""
    return (ConfigBuilder(name, f"Simple routing to {endpoint}")
            .add_rule("default", description="Route all requests to single endpoint")
            .add_target("custom", "default", endpoint)
            .build())


def create_ab_test_config(
    name: str,
    control_endpoint: str,
    variant_endpoint: str,
    variant_percentage: float = 0.1
) -> RoutingConfig:
    """Create an A/B testing configuration."""
    control_weight = 1.0 - variant_percentage
    variant_weight = variant_percentage

    return (ConfigBuilder(name, f"A/B test: {variant_percentage*100}% to variant")
            .add_rule("ab_test", priority=100, description="Split traffic for A/B testing")
            .use_split_strategy()
            .add_target("control", "control", control_endpoint, control_weight)
            .with_label("control")
            .add_target("variant", "variant", variant_endpoint, variant_weight)
            .with_label("variant")
            .build())


def create_premium_routing_config(
    name: str,
    premium_endpoint: str,
    standard_endpoint: str
) -> RoutingConfig:
    """Create a configuration that routes premium users to better models."""
    return (ConfigBuilder(name, "Premium user routing")
            .add_rule("premium_users", priority=100, description="Route premium users to premium model")
            .when("user.tier").equals("premium")
            .add_target("premium", "premium-model", premium_endpoint)
            .and_rule("standard_users", priority=50, description="Route standard users to standard model")
            .add_target("standard", "standard-model", standard_endpoint)
            .build())