"""Model reference system for convenient model access.

This module provides a Model proxy class that makes it easy to reference
and interact with models in a workspace.

Example:
    >>> from mixtrain import get_model
    >>> model = get_model("my-model")
    >>> result = model.run({"text": "Hello world"})
    >>> print(result)
"""

from typing import Any, Dict, List, Optional

from .client import MixClient


class Model:
    """Proxy class for convenient model access and operations.

    This class wraps MixClient model operations and provides a clean,
    object-oriented interface for working with models.

    Args:
        name: Name of the model
        client: Optional MixClient instance (creates new one if not provided)

    Attributes:
        name: Model name
        client: MixClient instance for API operations

    Example:
        >>> model = Model("sentiment-analyzer")
        >>> result = model.run({"text": "Great product!"})
        >>> print(model.metadata)
        >>> print(model.runs)
    """

    def __init__(self, name: str, client: Optional[MixClient] = None):
        """Initialize Model proxy.

        Args:
            name: Name of the model
            client: Optional MixClient instance (creates new one if not provided)
        """
        self.name = name
        self.client = client or MixClient()
        self._metadata: Optional[Dict[str, Any]] = None
        self._runs_cache: Optional[List[Dict[str, Any]]] = None

    def run(
        self,
        inputs: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run model inference.

        Args:
            inputs: Input data for the model
            config: Optional configuration overrides

        Returns:
            Run result with outputs

        Example:
            >>> model = Model("sentiment-analyzer")
            >>> result = model.run({"text": "Great product!"})
            >>> print(result["outputs"])
        """
        return self.client.run_model(self.name, inputs=inputs, config=config)

    def run_batch(
        self,
        inputs_list: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Run model inference on multiple inputs.

        Args:
            inputs_list: List of input dictionaries
            config: Optional configuration overrides applied to all runs

        Returns:
            List of run results

        Example:
            >>> model = Model("sentiment-analyzer")
            >>> results = model.run_batch([
            ...     {"text": "Great!"},
            ...     {"text": "Terrible!"}
            ... ])
        """
        return [self.run(inputs=inputs, config=config) for inputs in inputs_list]

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get model metadata (cached after first access).

        Returns:
            Model details including name, source, description, etc.

        Example:
            >>> model = Model("my-model")
            >>> print(model.metadata["source"])
            >>> print(model.metadata["description"])
        """
        if self._metadata is None:
            self._metadata = self.client.get_model(self.name)
        return self._metadata

    @property
    def spec(self) -> Optional[Dict[str, Any]]:
        """Get model specification.

        Returns:
            Model spec dictionary or None
        """
        return self.metadata.get("spec")

    @property
    def source(self) -> str:
        """Get model source (native, fal, modal, openai, anthropic, etc.).

        Returns:
            Model source string
        """
        return self.metadata.get("source", "")

    @property
    def description(self) -> str:
        """Get model description.

        Returns:
            Model description string
        """
        return self.metadata.get("description", "")

    @property
    def runs(self) -> List[Dict[str, Any]]:
        """Get recent model runs (cached).

        Returns:
            List of model runs

        Example:
            >>> model = Model("my-model")
            >>> for run in model.runs:
            ...     print(f"Run #{run['run_number']}: {run['status']}")
        """
        if self._runs_cache is None:
            response = self.client.list_model_runs(self.name)
            self._runs_cache = response.get("runs", [])
        return self._runs_cache

    def get_runs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get model runs with optional limit.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of model runs

        Example:
            >>> model = Model("my-model")
            >>> recent_runs = model.get_runs(limit=5)
        """
        response = self.client.list_model_runs(self.name)
        runs = response.get("runs", [])
        if limit:
            runs = runs[:limit]
        return runs

    def get_run(self, run_number: int) -> Dict[str, Any]:
        """Get details of a specific model run.

        Args:
            run_number: Run number

        Returns:
            Run details

        Example:
            >>> model = Model("my-model")
            >>> run = model.get_run(5)
            >>> print(run["status"])
        """
        return self.client.get_model_run(self.name, run_number)

    def get_logs(self, run_number: Optional[int] = None) -> str:
        """Get logs for a model run.

        Args:
            run_number: Optional run number (defaults to latest run)

        Returns:
            Log content as string

        Example:
            >>> model = Model("my-model")
            >>> logs = model.get_logs()  # Latest run
            >>> print(logs)
        """
        logs_data = self.client.get_model_run_logs(self.name, run_number)
        return logs_data.get("logs", "")

    def get_code(self) -> str:
        """Get model source code (for native models).

        Returns:
            Model code as string

        Example:
            >>> model = Model("my-model")
            >>> code = model.get_code()
            >>> print(code)
        """
        code_data = self.client.get_model_code(self.name)
        return code_data.get("code", "")

    def update_code(self, code: str) -> Dict[str, Any]:
        """Update model source code (for native models).

        Args:
            code: New code content

        Returns:
            Update result

        Example:
            >>> model = Model("my-model")
            >>> model.update_code("def run():\\n    return {'result': 'success'}")
        """
        return self.client.update_model_code(self.name, code)

    def list_files(self) -> List[Dict[str, Any]]:
        """List files in the model.

        Returns:
            List of files

        Example:
            >>> model = Model("my-model")
            >>> files = model.list_files()
            >>> for file in files:
            ...     print(file["path"])
        """
        response = self.client.list_model_files(self.name)
        return response.get("files", [])

    def get_file(self, file_path: str) -> str:
        """Get content of a specific model file.

        Args:
            file_path: Path to file within model

        Returns:
            File content as string

        Example:
            >>> model = Model("my-model")
            >>> content = model.get_file("requirements.txt")
        """
        response = self.client.get_model_file(self.name, file_path)
        return response.get("content", "")

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update model metadata.

        Args:
            name: Optional new name
            description: Optional new description

        Returns:
            Updated model data

        Example:
            >>> model = Model("my-model")
            >>> model.update(description="Updated description")
        """
        result = self.client.update_model(self.name, name=name, description=description)
        # Update local name if changed
        if name:
            self.name = name
        # Clear metadata cache
        self._metadata = None
        return result

    def delete(self) -> Dict[str, Any]:
        """Delete the model.

        Returns:
            Deletion result

        Example:
            >>> model = Model("my-model")
            >>> model.delete()
        """
        return self.client.delete_model(self.name)

    def refresh(self):
        """Clear cached data and force refresh on next access.

        Example:
            >>> model = Model("my-model")
            >>> model.refresh()
            >>> print(model.metadata)  # Will fetch fresh data
        """
        self._metadata = None
        self._runs_cache = None

    def __repr__(self) -> str:
        """String representation of the Model."""
        return f"Model(name='{self.name}', source='{self.source}')"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Model: {self.name} ({self.source})"


def get_model(name: str, client: Optional[MixClient] = None) -> Model:
    """Get a model reference by name.

    This is the primary way to access models in a workspace.

    Args:
        name: Model name
        client: Optional MixClient instance

    Returns:
        Model proxy instance

    Example:
        >>> from mixtrain import get_model
        >>> model = get_model("sentiment-analyzer")
        >>> result = model.run({"text": "Great!"})
    """
    return Model(name, client=client)


def list_models(
    provider: Optional[str] = None,
    client: Optional[MixClient] = None
) -> List[Model]:
    """List all models in the workspace.

    Args:
        provider: Optional filter by provider type
        client: Optional MixClient instance

    Returns:
        List of Model instances

    Example:
        >>> from mixtrain import list_models
        >>> models = list_models()
        >>> for model in models:
        ...     print(model.name)
    """
    if client is None:
        client = MixClient()

    response = client.list_models(provider=provider)
    models_data = response.get("models", [])

    return [Model(m["name"], client=client) for m in models_data]


def run_model(
    name: str,
    inputs: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
    client: Optional[MixClient] = None,
) -> Dict[str, Any]:
    """Run a model by name (convenience function).

    Args:
        name: Model name
        inputs: Input data
        config: Optional configuration
        client: Optional MixClient instance

    Returns:
        Run result with outputs

    Example:
        >>> from mixtrain import run_model
        >>> result = run_model("sentiment-analyzer", {"text": "Great!"})
    """
    model = Model(name, client=client)
    return model.run(inputs=inputs, config=config)


def find_model(
    pattern: str,
    client: Optional[MixClient] = None
) -> List[Model]:
    """Find models matching a pattern.

    Args:
        pattern: Pattern to match (simple substring matching)
        client: Optional MixClient instance

    Returns:
        List of matching Model instances

    Example:
        >>> from mixtrain import find_model
        >>> models = find_model("sentiment")
        >>> for model in models:
        ...     print(model.name)
    """
    all_models = list_models(client=client)
    pattern_lower = pattern.lower()
    return [m for m in all_models if pattern_lower in m.name.lower()]
