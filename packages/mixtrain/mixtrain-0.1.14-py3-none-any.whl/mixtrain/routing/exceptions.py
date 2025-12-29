"""Routing engine exceptions."""


class RoutingError(Exception):
    """Base exception for routing engine errors."""
    pass


class ConfigurationError(RoutingError):
    """Raised when routing configuration is invalid."""
    pass


class RoutingConfigValidationError(RoutingError):
    """Raised when configuration validation fails."""

    def __init__(self, message: str, errors: list = None):
        super().__init__(message)
        self.errors = errors or []


class TargetSelectionError(RoutingError):
    """Raised when target selection fails."""
    pass


class ConditionEvaluationError(RoutingError):
    """Raised when condition evaluation fails."""
    pass