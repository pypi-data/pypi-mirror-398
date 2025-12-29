"""Target selection strategies for routing."""

import random
from typing import List, Dict, Any

from .models import RoutingTarget, RoutingStrategy
from .exceptions import TargetSelectionError


class TargetSelector:
    """Selects targets based on routing strategy."""

    @staticmethod
    def select_targets(
        strategy: RoutingStrategy,
        targets: List[RoutingTarget],
        request_data: Dict[str, Any]
    ) -> List[RoutingTarget]:
        """
        Select targets based on the specified strategy.

        Args:
            strategy: The routing strategy to use
            targets: Available targets to select from
            request_data: Request data for context

        Returns:
            List of selected targets

        Raises:
            TargetSelectionError: If target selection fails
        """
        if not targets:
            raise TargetSelectionError("No targets available for selection")

        try:
            if strategy == RoutingStrategy.SINGLE:
                return SingleStrategy.select(targets, request_data)
            elif strategy == RoutingStrategy.SPLIT:
                return SplitStrategy.select(targets, request_data)
            elif strategy == RoutingStrategy.SHADOW:
                return ShadowStrategy.select(targets, request_data)
            elif strategy == RoutingStrategy.FALLBACK:
                return FallbackStrategy.select(targets, request_data)
            else:
                raise TargetSelectionError(f"Unknown strategy: {strategy}")

        except Exception as e:
            raise TargetSelectionError(f"Target selection failed for strategy '{strategy}': {e}")


class SingleStrategy:
    """Single target selection strategy."""

    @staticmethod
    def select(targets: List[RoutingTarget], request_data: Dict[str, Any]) -> List[RoutingTarget]:
        """Select the first target (or highest weight)."""
        # For single strategy, return the first target
        # Could be enhanced to select highest weight target
        return [targets[0]]


class SplitStrategy:
    """Split traffic strategy for A/B testing."""

    @staticmethod
    def select(targets: List[RoutingTarget], request_data: Dict[str, Any]) -> List[RoutingTarget]:
        """Select target based on weighted random selection."""
        return SplitStrategy._weighted_random_selection(targets)

    @staticmethod
    def _weighted_random_selection(targets: List[RoutingTarget]) -> List[RoutingTarget]:
        """Select target based on weights."""
        if not targets:
            return []

        # Calculate cumulative weights
        cumulative_weights = []
        total_weight = 0

        for target in targets:
            weight = target.weight
            total_weight += weight
            cumulative_weights.append(total_weight)

        if total_weight <= 0:
            return [targets[0]]

        # Random selection
        random_value = random.random() * total_weight

        for i, cum_weight in enumerate(cumulative_weights):
            if random_value <= cum_weight:
                return [targets[i]]

        # Fallback to last target
        return [targets[-1]]

    @staticmethod
    def validate_weights(targets: List[RoutingTarget]) -> None:
        """Validate that weights sum to 1.0 for split strategy."""
        total_weight = sum(target.weight for target in targets)
        if abs(total_weight - 1.0) > 0.001:  # Allow small floating point errors
            raise TargetSelectionError(
                f"Split strategy requires target weights to sum to 1.0, got {total_weight}"
            )


class ShadowStrategy:
    """Shadow routing strategy."""

    @staticmethod
    def select(targets: List[RoutingTarget], request_data: Dict[str, Any]) -> List[RoutingTarget]:
        """Return primary target and mark shadow target."""
        if len(targets) != 2:
            raise TargetSelectionError("Shadow strategy requires exactly 2 targets")

        primary = targets[0].copy(deep=True)
        shadow = targets[1].copy(deep=True)
        shadow.is_shadow = True

        return [primary, shadow]


class FallbackStrategy:
    """Fallback routing strategy."""

    @staticmethod
    def select(targets: List[RoutingTarget], request_data: Dict[str, Any]) -> List[RoutingTarget]:
        """Return all targets in fallback order."""
        # Return all targets, they will be tried in order until one succeeds
        return targets.copy()


class AdvancedSelectors:
    """Advanced target selection methods."""

    @staticmethod
    def select_by_region(targets: List[RoutingTarget], request_data: Dict[str, Any]) -> List[RoutingTarget]:
        """Select target based on geographic region."""
        user_region = request_data.get("user", {}).get("region")
        if not user_region:
            return [targets[0]]  # Default to first target

        # Look for targets with matching region in metadata
        regional_targets = [
            target for target in targets
            if target.headers and target.headers.get("region") == user_region
        ]

        return regional_targets if regional_targets else [targets[0]]

    @staticmethod
    def select_by_load_balancing(targets: List[RoutingTarget], request_data: Dict[str, Any]) -> List[RoutingTarget]:
        """Select target based on load balancing (round-robin simulation)."""
        # This is a simplified round-robin selection
        # In a real implementation, you'd track request counts
        request_count = request_data.get("_internal", {}).get("request_count", 0)
        selected_index = request_count % len(targets)
        return [targets[selected_index]]

    @staticmethod
    def select_by_cost(targets: List[RoutingTarget], request_data: Dict[str, Any]) -> List[RoutingTarget]:
        """Select target based on cost optimization."""
        # Sort by cost (if available in metadata) and select cheapest
        def get_cost(target):
            return float(target.headers.get("cost_per_request", 1.0)) if target.headers else 1.0

        sorted_targets = sorted(targets, key=get_cost)
        return [sorted_targets[0]]