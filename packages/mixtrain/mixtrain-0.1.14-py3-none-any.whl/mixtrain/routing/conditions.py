"""Condition evaluation logic for routing rules."""

import re
from typing import Dict, Any, Union, List

from .models import RoutingCondition, ConditionOperator
from .exceptions import ConditionEvaluationError


class ConditionEvaluator:
    """Evaluates routing conditions against request data."""

    @staticmethod
    def evaluate_condition(condition: RoutingCondition, request_data: Dict[str, Any]) -> bool:
        """
        Evaluate a single condition against request data.

        Args:
            condition: The condition to evaluate
            request_data: The request data to evaluate against

        Returns:
            True if the condition matches, False otherwise

        Raises:
            ConditionEvaluationError: If condition evaluation fails
        """
        try:
            field = condition.field
            operator = condition.operator
            expected_value = condition.value

            # Get actual value from request data using dot notation
            actual_value = ConditionEvaluator._get_nested_value(request_data, field)

            # Apply operator
            return ConditionEvaluator._apply_operator(operator, actual_value, expected_value)

        except Exception as e:
            raise ConditionEvaluationError(
                f"Failed to evaluate condition '{condition.field}' {condition.operator} '{condition.value}': {e}"
            )

    @staticmethod
    def evaluate_conditions(conditions: List[RoutingCondition], request_data: Dict[str, Any]) -> bool:
        """
        Evaluate multiple conditions with AND logic.

        Args:
            conditions: List of conditions to evaluate
            request_data: The request data to evaluate against

        Returns:
            True if all conditions match, False otherwise
        """
        if not conditions:
            return True  # No conditions means always match

        # All conditions must be true (AND logic)
        for condition in conditions:
            if not ConditionEvaluator.evaluate_condition(condition, request_data):
                return False

        return True

    @staticmethod
    def _get_nested_value(data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        try:
            keys = field_path.split('.')
            value = data

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None

            return value
        except Exception:
            return None

    @staticmethod
    def _apply_operator(operator: ConditionOperator, actual_value: Any, expected_value: Any) -> bool:
        """Apply comparison operator between actual and expected values."""
        if operator == ConditionOperator.EQUALS:
            return actual_value == expected_value

        elif operator == ConditionOperator.NOT_EQUALS:
            return actual_value != expected_value

        elif operator == ConditionOperator.CONTAINS:
            return expected_value in str(actual_value) if actual_value is not None else False

        elif operator == ConditionOperator.NOT_CONTAINS:
            return expected_value not in str(actual_value) if actual_value is not None else True

        elif operator == ConditionOperator.IN:
            if not isinstance(expected_value, list):
                return False
            return actual_value in expected_value

        elif operator == ConditionOperator.NOT_IN:
            if not isinstance(expected_value, list):
                return True
            return actual_value not in expected_value

        elif operator == ConditionOperator.EXISTS:
            return actual_value is not None

        elif operator == ConditionOperator.NOT_EXISTS:
            return actual_value is None

        elif operator == ConditionOperator.GREATER_THAN:
            try:
                return float(actual_value) > float(expected_value)
            except (TypeError, ValueError):
                return False

        elif operator == ConditionOperator.LESS_THAN:
            try:
                return float(actual_value) < float(expected_value)
            except (TypeError, ValueError):
                return False

        elif operator == ConditionOperator.REGEX:
            try:
                return bool(re.search(str(expected_value), str(actual_value))) if actual_value is not None else False
            except re.error:
                return False

        else:
            raise ConditionEvaluationError(f"Unknown operator: {operator}")


class ConditionBuilder:
    """Builder for creating routing conditions."""

    def __init__(self, field: str):
        self.field = field

    def equals(self, value: Union[str, int, float, bool]) -> RoutingCondition:
        """Create equals condition."""
        return RoutingCondition(field=self.field, operator=ConditionOperator.EQUALS, value=value)

    def not_equals(self, value: Union[str, int, float, bool]) -> RoutingCondition:
        """Create not equals condition."""
        return RoutingCondition(field=self.field, operator=ConditionOperator.NOT_EQUALS, value=value)

    def contains(self, value: str) -> RoutingCondition:
        """Create contains condition."""
        return RoutingCondition(field=self.field, operator=ConditionOperator.CONTAINS, value=value)

    def not_contains(self, value: str) -> RoutingCondition:
        """Create not contains condition."""
        return RoutingCondition(field=self.field, operator=ConditionOperator.NOT_CONTAINS, value=value)

    def is_in(self, values: List[Any]) -> RoutingCondition:
        """Create in condition."""
        return RoutingCondition(field=self.field, operator=ConditionOperator.IN, value=values)

    def not_in(self, values: List[Any]) -> RoutingCondition:
        """Create not in condition."""
        return RoutingCondition(field=self.field, operator=ConditionOperator.NOT_IN, value=values)

    def exists(self) -> RoutingCondition:
        """Create exists condition."""
        return RoutingCondition(field=self.field, operator=ConditionOperator.EXISTS)

    def not_exists(self) -> RoutingCondition:
        """Create not exists condition."""
        return RoutingCondition(field=self.field, operator=ConditionOperator.NOT_EXISTS)

    def greater_than(self, value: Union[int, float]) -> RoutingCondition:
        """Create greater than condition."""
        return RoutingCondition(field=self.field, operator=ConditionOperator.GREATER_THAN, value=value)

    def less_than(self, value: Union[int, float]) -> RoutingCondition:
        """Create less than condition."""
        return RoutingCondition(field=self.field, operator=ConditionOperator.LESS_THAN, value=value)

    def matches_regex(self, pattern: str) -> RoutingCondition:
        """Create regex match condition."""
        return RoutingCondition(field=self.field, operator=ConditionOperator.REGEX, value=pattern)


def condition(field: str) -> ConditionBuilder:
    """Create a condition builder for the given field."""
    return ConditionBuilder(field)