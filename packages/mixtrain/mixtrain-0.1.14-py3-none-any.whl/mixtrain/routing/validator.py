"""Configuration validation for routing engine."""

from typing import List, Dict, Any
from .models import RoutingConfig, RoutingRule, RoutingCondition, RoutingTarget, RoutingStrategy, ConditionOperator
from .exceptions import RoutingConfigValidationError


class RoutingValidator:
    """Validates routing configurations."""

    @staticmethod
    def validate_config(config: RoutingConfig) -> List[str]:
        """
        Validate routing configuration and return list of errors.

        Args:
            config: The routing configuration to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Check required fields
        if not config.name or not config.name.strip():
            errors.append("Configuration name is required and cannot be empty")

        # Validate rules
        if not config.rules:
            errors.append("At least one routing rule must be specified")
        else:
            rule_names = []
            for i, rule in enumerate(config.rules):
                rule_errors = RoutingValidator._validate_rule(rule, f"rule[{i}]")
                errors.extend(rule_errors)

                # Check for duplicate rule names
                if rule.name in rule_names:
                    errors.append(f"Duplicate rule name '{rule.name}' found")
                rule_names.append(rule.name)

        return errors

    @staticmethod
    def validate_config_dict(config_data: Dict[str, Any]) -> List[str]:
        """
        Validate routing configuration from dictionary.

        Args:
            config_data: Dictionary containing configuration data

        Returns:
            List of validation error messages
        """
        try:
            config = RoutingConfig.from_json(config_data)
            return RoutingValidator.validate_config(config)
        except Exception as e:
            return [f"Failed to parse configuration: {str(e)}"]

    @staticmethod
    def validate_and_raise(config: RoutingConfig) -> None:
        """
        Validate configuration and raise ValidationError if invalid.

        Args:
            config: The routing configuration to validate

        Raises:
            ValidationError: If configuration is invalid
        """
        errors = RoutingValidator.validate_config(config)
        if errors:
            raise RoutingConfigValidationError("Configuration validation failed", errors)

    @staticmethod
    def _validate_rule(rule: RoutingRule, context: str) -> List[str]:
        """Validate a single routing rule."""
        errors = []

        if not rule.name or not rule.name.strip():
            errors.append(f"{context}: Rule name is required and cannot be empty")

        # Validate priority
        if rule.priority < 0:
            errors.append(f"{context}: Rule priority cannot be negative")

        # Validate conditions
        for j, condition in enumerate(rule.conditions):
            condition_errors = RoutingValidator._validate_condition(condition, f"{context}.conditions[{j}]")
            errors.extend(condition_errors)

        # Validate targets
        if not rule.targets:
            errors.append(f"{context}: At least one target is required")
        else:
            for k, target in enumerate(rule.targets):
                target_errors = RoutingValidator._validate_target(target, f"{context}.targets[{k}]")
                errors.extend(target_errors)

        # Strategy-specific validation
        strategy_errors = RoutingValidator._validate_strategy(rule, context)
        errors.extend(strategy_errors)

        return errors

    @staticmethod
    def _validate_condition(condition: RoutingCondition, context: str) -> List[str]:
        """Validate a routing condition."""
        errors = []

        if not condition.field or not condition.field.strip():
            errors.append(f"{context}: Condition field is required and cannot be empty")

        # Validate field path (basic check)
        if condition.field and '..' in condition.field:
            errors.append(f"{context}: Invalid field path '{condition.field}' (contains '..')")

        # Some operators require values
        value_required_operators = [
            ConditionOperator.EQUALS,
            ConditionOperator.NOT_EQUALS,
            ConditionOperator.CONTAINS,
            ConditionOperator.NOT_CONTAINS,
            ConditionOperator.IN,
            ConditionOperator.NOT_IN,
            ConditionOperator.GREATER_THAN,
            ConditionOperator.LESS_THAN,
            ConditionOperator.REGEX
        ]

        if condition.operator in value_required_operators and condition.value is None:
            errors.append(f"{context}: Operator '{condition.operator}' requires a value")

        # Validate operator-specific value types
        if condition.operator in [ConditionOperator.IN, ConditionOperator.NOT_IN]:
            if condition.value is not None and not isinstance(condition.value, list):
                errors.append(f"{context}: Operator '{condition.operator}' requires a list value")

        if condition.operator in [ConditionOperator.GREATER_THAN, ConditionOperator.LESS_THAN]:
            if condition.value is not None:
                try:
                    float(condition.value)
                except (TypeError, ValueError):
                    errors.append(f"{context}: Operator '{condition.operator}' requires a numeric value")

        # Validate regex pattern
        if condition.operator == ConditionOperator.REGEX and condition.value is not None:
            try:
                import re
                re.compile(str(condition.value))
            except re.error as e:
                errors.append(f"{context}: Invalid regex pattern '{condition.value}': {e}")

        return errors

    @staticmethod
    def _validate_target(target: RoutingTarget, context: str) -> List[str]:
        """Validate a routing target."""
        errors = []

        # Required fields
        required_fields = {
            'provider': target.provider,
            'model_name': target.model_name,
            'endpoint': target.endpoint
        }

        for field_name, field_value in required_fields.items():
            if not field_value or not str(field_value).strip():
                errors.append(f"{context}: Field '{field_name}' is required and cannot be empty")

        # Validate weight
        if not (0.0 <= target.weight <= 1.0):
            errors.append(f"{context}: Weight must be between 0.0 and 1.0, got {target.weight}")

        # Validate timeout
        if target.timeout_ms is not None and target.timeout_ms < 100:
            errors.append(f"{context}: Timeout must be at least 100ms, got {target.timeout_ms}")

        # Validate retry count
        if target.retry_count is not None and (target.retry_count < 0 or target.retry_count > 5):
            errors.append(f"{context}: Retry count must be between 0 and 5, got {target.retry_count}")

        # Validate endpoint URL (basic check)
        if target.endpoint:
            if not (target.endpoint.startswith('http://') or target.endpoint.startswith('https://')):
                errors.append(f"{context}: Endpoint must be a valid HTTP/HTTPS URL")

        return errors

    @staticmethod
    def _validate_strategy(rule: RoutingRule, context: str) -> List[str]:
        """Validate strategy-specific requirements."""
        errors = []

        if rule.strategy == RoutingStrategy.SPLIT:
            # Check weights sum to 1.0
            total_weight = sum(target.weight for target in rule.targets)
            if abs(total_weight - 1.0) > 0.001:  # Allow small floating point errors
                errors.append(
                    f"{context}: Split strategy requires target weights to sum to 1.0, got {total_weight:.3f}"
                )

            # All targets should have weights specified
            for i, target in enumerate(rule.targets):
                if target.weight == 1.0 and len(rule.targets) > 1:
                    errors.append(
                        f"{context}.targets[{i}]: Split strategy requires explicit weights for all targets"
                    )

        elif rule.strategy == RoutingStrategy.SHADOW:
            if len(rule.targets) != 2:
                errors.append(
                    f"{context}: Shadow strategy requires exactly 2 targets (primary and shadow), got {len(rule.targets)}"
                )

        elif rule.strategy == RoutingStrategy.FALLBACK:
            # Fallback targets should ideally have different providers for redundancy
            providers = [target.provider for target in rule.targets]
            if len(set(providers)) == 1 and len(providers) > 1:
                # This is a warning rather than an error
                pass  # Could add warnings system later

        return errors


class ConfigurationLinter:
    """Advanced linting for routing configurations."""

    @staticmethod
    def lint_config(config: RoutingConfig) -> Dict[str, List[str]]:
        """
        Perform comprehensive linting of configuration.

        Returns:
            Dictionary with 'errors', 'warnings', and 'suggestions' keys
        """
        errors = RoutingValidator.validate_config(config)
        warnings = ConfigurationLinter._get_warnings(config)
        suggestions = ConfigurationLinter._get_suggestions(config)

        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }

    @staticmethod
    def _get_warnings(config: RoutingConfig) -> List[str]:
        """Get configuration warnings."""
        warnings = []

        # Check for overlapping priorities
        priorities = [rule.priority for rule in config.rules if rule.is_enabled]
        if len(priorities) != len(set(priorities)):
            warnings.append("Multiple rules have the same priority - evaluation order may be unpredictable")

        # Check for rules without conditions (catch-all rules)
        catch_all_rules = [rule for rule in config.rules if not rule.conditions and rule.is_enabled]
        if len(catch_all_rules) > 1:
            warnings.append("Multiple catch-all rules (no conditions) found - only the highest priority will match")

        # Check for disabled rules
        disabled_rules = [rule for rule in config.rules if not rule.is_enabled]
        if disabled_rules:
            warnings.append(f"{len(disabled_rules)} rules are disabled and will not be evaluated")

        return warnings

    @staticmethod
    def _get_suggestions(config: RoutingConfig) -> List[str]:
        """Get configuration improvement suggestions."""
        suggestions = []

        # Suggest adding descriptions for rules without them
        rules_without_desc = [rule for rule in config.rules if not rule.description]
        if rules_without_desc:
            suggestions.append(f"Consider adding descriptions to {len(rules_without_desc)} rules for better maintainability")

        # Suggest using fallback strategy for production resilience
        has_fallback = any(rule.strategy == RoutingStrategy.FALLBACK for rule in config.rules)
        if not has_fallback:
            suggestions.append("Consider adding fallback rules for better resilience in production")

        # Suggest adding catch-all rule
        has_catch_all = any(not rule.conditions for rule in config.rules if rule.is_enabled)
        if not has_catch_all:
            suggestions.append("Consider adding a catch-all rule (no conditions) as the lowest priority fallback")

        return suggestions