"""Core routing engine implementation."""

import logging
import time
from typing import Dict, Any, Optional

from .models import RoutingConfig, RoutingResult, RoutingRule
from .conditions import ConditionEvaluator
from .strategies import TargetSelector
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class RoutingEngine:
    """Engine for evaluating routing rules and selecting targets."""

    def __init__(self, config: RoutingConfig):
        """
        Initialize the routing engine with a configuration.

        Args:
            config: The routing configuration to use

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = config
        self._validate_config()

    def route_request(self, request_data: Dict[str, Any]) -> RoutingResult:
        """
        Route a request based on configuration rules.

        Args:
            request_data: The request data to route

        Returns:
            RoutingResult with matched rule, selected targets, and explanation

        Raises:
            RoutingError: If routing fails
        """
        start_time = time.time()

        try:
            # Sort rules by priority (higher priority first)
            sorted_rules = sorted(
                [rule for rule in self.config.rules if rule.is_enabled],
                key=lambda x: x.priority,
                reverse=True,
            )

            logger.debug(f"Evaluating {len(sorted_rules)} enabled rules for routing")

            # Evaluate rules in priority order
            for rule in sorted_rules:
                if self._evaluate_rule(rule, request_data):
                    targets = TargetSelector.select_targets(
                        rule.strategy, rule.targets, request_data
                    )

                    execution_time_ms = (time.time() - start_time) * 1000

                    return RoutingResult(
                        matched_rule=rule,
                        selected_targets=targets,
                        explanation=f"Matched rule '{rule.name}' (priority {rule.priority})",
                        execution_time_ms=execution_time_ms,
                        metadata={
                            "evaluated_rules": len(sorted_rules),
                            "strategy": rule.strategy,
                            "target_count": len(targets),
                        },
                    )

            # No rules matched
            execution_time_ms = (time.time() - start_time) * 1000
            return RoutingResult(
                matched_rule=None,
                selected_targets=[],
                explanation="No rules matched the request",
                execution_time_ms=execution_time_ms,
                metadata={"evaluated_rules": len(sorted_rules)},
            )

        except Exception as e:
            logger.error(f"Error in routing engine: {e}")
            execution_time_ms = (time.time() - start_time) * 1000

            return RoutingResult(
                matched_rule=None,
                selected_targets=[],
                explanation=f"Routing error: {str(e)}",
                execution_time_ms=execution_time_ms,
                metadata={"error": str(e)},
            )

    def test_request(
        self, request_data: Dict[str, Any], expected_rule: Optional[str] = None
    ) -> RoutingResult:
        """
        Test a request against the routing configuration.

        Args:
            request_data: The request data to test
            expected_rule: Optional expected rule name for validation

        Returns:
            RoutingResult with test results
        """
        result = self.route_request(request_data)

        # Add test-specific metadata
        result.metadata = result.metadata or {}
        result.metadata["is_test"] = True

        if expected_rule:
            matched_expected = (
                result.matched_rule is not None
                and result.matched_rule.name == expected_rule
            )
            result.metadata["expected_rule"] = expected_rule
            result.metadata["matched_expected"] = matched_expected

            if not matched_expected:
                if result.matched_rule:
                    result.explanation += f" (expected '{expected_rule}')"
                else:
                    result.explanation += (
                        f" (expected '{expected_rule}', no rule matched)"
                    )

        return result

    def get_rule_coverage(self, test_requests: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze rule coverage for a set of test requests.

        Args:
            test_requests: List of request data to test

        Returns:
            Coverage analysis results
        """
        rule_hits = {rule.name: 0 for rule in self.config.rules}
        total_requests = len(test_requests)
        unmatched_requests = 0

        for request_data in test_requests:
            result = self.route_request(request_data)
            if result.matched_rule:
                rule_hits[result.matched_rule.name] += 1
            else:
                unmatched_requests += 1

        # Calculate coverage statistics
        covered_rules = sum(1 for hits in rule_hits.values() if hits > 0)
        total_rules = len(self.config.rules)
        coverage_percentage = (
            (covered_rules / total_rules * 100) if total_rules > 0 else 0
        )

        return {
            "total_requests": total_requests,
            "total_rules": total_rules,
            "covered_rules": covered_rules,
            "coverage_percentage": coverage_percentage,
            "unmatched_requests": unmatched_requests,
            "rule_hits": rule_hits,
            "uncovered_rules": [name for name, hits in rule_hits.items() if hits == 0],
        }

    def _evaluate_rule(self, rule: RoutingRule, request_data: Dict[str, Any]) -> bool:
        """Evaluate if a rule matches the request data."""
        try:
            return ConditionEvaluator.evaluate_conditions(rule.conditions, request_data)
        except Exception as e:
            logger.error(f"Error evaluating rule '{rule.name}': {e}")
            return False

    def _validate_config(self) -> None:
        """Validate the routing configuration."""
        if not self.config.rules:
            raise ConfigurationError("At least one routing rule must be specified")

        # Check for duplicate rule names
        rule_names = [rule.name for rule in self.config.rules]
        if len(rule_names) != len(set(rule_names)):
            raise ConfigurationError("Rule names must be unique")

        # Validate each rule's strategy-specific requirements
        for rule in self.config.rules:
            try:
                # This will validate the rule through Pydantic validators
                rule.targets  # Accessing this triggers validation
            except ValueError as e:
                raise ConfigurationError(f"Invalid rule '{rule.name}': {e}")


class RoutingEngineFactory:
    """Factory for creating routing engines."""

    @staticmethod
    def from_json(config_json: Dict[str, Any]) -> RoutingEngine:
        """Create routing engine from JSON configuration."""
        config = RoutingConfig.from_json(config_json)
        return RoutingEngine(config)

    @staticmethod
    def from_file(config_path: str) -> RoutingEngine:
        """Create routing engine from JSON file."""
        import json

        with open(config_path, "r") as f:
            config_json = json.load(f)

        return RoutingEngineFactory.from_json(config_json)

    @staticmethod
    def create_simple(name: str, model_endpoint: str) -> RoutingEngine:
        """Create a simple single-target routing engine."""
        from .models import RoutingTarget, RoutingRule

        config = RoutingConfig(
            name=name,
            description=f"Simple routing to {model_endpoint}",
            rules=[
                RoutingRule(
                    name="default",
                    description="Route all requests to default target",
                    priority=1,
                    targets=[
                        RoutingTarget(
                            provider="custom",
                            model_name="default",
                            endpoint=model_endpoint,
                        )
                    ],
                )
            ],
        )

        return RoutingEngine(config)
