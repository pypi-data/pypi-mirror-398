"""MixClient - Client for Mixtrain SDK

This module provides the core MixClient class that handles authentication,
workspace management, and all API operations for the Mixtrain platform.
"""

import json
import os
from enum import Enum
from functools import lru_cache
from logging import getLogger
from typing import Any, Dict, List, Optional, Union

import httpx
from mixtrain.routing.engine import RoutingEngine, RoutingEngineFactory
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table

from .utils import auth as auth_utils
from .utils.config import get_config

logger = getLogger(__name__)


class AuthMethod(Enum):
    """Authentication methods supported by MixClient."""

    API_KEY = "api_key"
    LOGIN_TOKEN = "login_token"


def detect_rule_changes(
    old_rules: List[Dict[str, Any]], new_rules: List[Dict[str, Any]]
) -> str:
    """Detect changes between rule sets using JSON diff approach."""

    def rules_are_equal(rule1: Dict[str, Any], rule2: Dict[str, Any]) -> bool:
        """Compare two rules ignoring ID fields."""
        clean1 = {k: v for k, v in rule1.items() if k != "id"}
        clean2 = {k: v for k, v in rule2.items() if k != "id"}
        return json.dumps(clean1, sort_keys=True) == json.dumps(clean2, sort_keys=True)

    def get_rule_name(rule: Dict[str, Any], index: int) -> str:
        """Generate rule name for display."""
        return rule.get("name") or f"Rule {index + 1}"

    # Handle initial configuration
    if not old_rules:
        if new_rules:
            rule_names = [get_rule_name(rule, i) for i, rule in enumerate(new_rules)]
            return f"Added {', '.join(rule_names)}"
        return "Initial configuration"

    # Handle all rules deleted
    if not new_rules:
        rule_names = [get_rule_name(rule, i) for i, rule in enumerate(old_rules)]
        return f"Deleted all rules ({', '.join(rule_names)})"

    old_len = len(old_rules)
    new_len = len(new_rules)

    changes = []
    edited = []
    added = []
    deleted = []

    # Compare rules that exist in both (up to the shorter length)
    min_len = min(old_len, new_len)
    for i in range(min_len):
        if not rules_are_equal(old_rules[i], new_rules[i]):
            edited.append(get_rule_name(new_rules[i], i))

    # Handle length differences
    if new_len > old_len:
        # Rules were added
        for i in range(old_len, new_len):
            added.append(get_rule_name(new_rules[i], i))
    elif old_len > new_len:
        # Rules were deleted
        for i in range(new_len, old_len):
            deleted.append(get_rule_name(old_rules[i], i))

    # Build summary
    if added:
        changes.append(f"Added {', '.join(added)}")
    if edited:
        changes.append(f"Edited {', '.join(edited)}")
    if deleted:
        changes.append(f"Deleted {', '.join(deleted)}")

    return "; ".join(changes) if changes else "No rule changes"


class MixClient:
    """Main client for interacting with the Mixtrain platform.

    Handles authentication, workspace management, and all API operations.

    Usage:
        # Auto-detect authentication and workspace
        client = MixClient()

        # API key authentication - scoped to the key's workspace and role
        client = MixClient(api_key="mix-abc123")

        # Login token with specific workspace
        client = MixClient(workspace_name="my-workspace")

    Note:
        API keys authenticate to a specific workspace with a specific role (ADMIN/MEMBER/VIEWER).
        Each API key can only access its assigned workspace and cannot perform user-specific
        operations like managing invitations or creating new workspaces.

        The workspace_name parameter is automatically determined from the API key and should
        not be manually specified when using API key authentication.
    """

    def __init__(
        self, workspace_name: Optional[str] = None, api_key: Optional[str] = None
    ):
        """Initialize MixClient.

        Args:
            workspace_name: Workspace to use (only for login token auth).
                          For API keys, workspace is auto-determined.
            api_key: API key for authentication. If not provided, will check environment
                    or fall back to login token.
        """
        self._explicit_workspace = workspace_name
        self._explicit_api_key = api_key
        self._auth_method = self._detect_auth_method()

        # Validate that workspace_name is not provided with API key
        if self._auth_method == AuthMethod.API_KEY and workspace_name:
            raise ValueError(
                "workspace_name should not be specified when using API key authentication. "
                "The workspace is automatically determined from the API key."
            )

        self._workspace_name = self._determine_workspace_name()

    def _detect_auth_method(self) -> AuthMethod:
        """Detect which authentication method to use."""
        # Priority: explicit API key > env API key > login token
        if self._explicit_api_key:
            if not self._explicit_api_key.startswith("mix-"):
                raise ValueError("API key must start with 'mix-'")
            return AuthMethod.API_KEY

        env_api_key = os.getenv("MIXTRAIN_API_KEY")
        if env_api_key:
            if not env_api_key.startswith("mix-"):
                raise ValueError(
                    "MIXTRAIN_API_KEY environment variable must start with 'mix-'"
                )
            return AuthMethod.API_KEY

        # Check if we have a login token
        config = get_config()
        if config.get_auth_token():
            return AuthMethod.LOGIN_TOKEN

        raise ValueError(
            "No authentication method available. "
            "Please set MIXTRAIN_API_KEY environment variable or authenticate with 'mixtrain login'"
        )

    def _determine_workspace_name(self) -> str:
        """Determine which workspace to use."""
        if self._explicit_workspace:
            return self._explicit_workspace

        if self._auth_method == AuthMethod.API_KEY:
            # For API key auth, the key is workspace-specific, so we can determine the workspace
            # from the key itself by calling the workspaces endpoint. Since the API key belongs to
            # a specific workspace, it will only have access to that workspace.
            workspaces = self._list_workspaces_raw()
            workspace_list = workspaces.get("data", [])
            if not workspace_list:
                raise ValueError("No workspaces available with current API key")

            # Since API keys are workspace-specific, there should typically be only one workspace
            # If there are multiple, use the first one (the key has access to it)
            return workspace_list[0]["name"]

        else:  # LOGIN_TOKEN
            # For login token, use configured active workspace
            config = get_config()
            active_workspace = next((w for w in config.workspaces if w.active), None)
            if not active_workspace:
                raise ValueError(
                    "No active workspace found. Please authenticate with 'mixtrain login'"
                )
            return active_workspace.name

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if self._auth_method == AuthMethod.API_KEY:
            api_key = self._explicit_api_key or os.getenv("MIXTRAIN_API_KEY")
            return {"X-API-Key": api_key}
        else:  # LOGIN_TOKEN
            config = get_config()
            auth_token = config.get_auth_token()
            if not auth_token:
                raise ValueError("No auth token available")
            return {"Authorization": f"Bearer {auth_token}"}

    def _get_platform_url(self) -> str:
        """Get platform URL with environment variable override."""
        return os.getenv("MIXTRAIN_PLATFORM_URL", "https://platform.mixtrain.ai/api/v1")

    def _make_request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make HTTP request to the platform API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (will be prefixed with platform URL)
            json: JSON payload
            files: Files to upload
            params: Query parameters
            headers: Additional headers

        Returns:
            HTTP response object

        Raises:
            Exception: On HTTP errors or connection issues
        """
        with httpx.Client(timeout=10.0) as client:
            # Prepare headers
            request_headers = self._get_auth_headers()
            if headers:
                request_headers.update(headers)

            # Build full URL
            url = f"{self._get_platform_url()}{path}"

            logger.debug(f"Making {method} request to {url}")

            try:
                if files:
                    response = client.request(
                        method, url, files=files, params=params, headers=request_headers
                    )
                else:
                    response = client.request(
                        method, url, json=json, params=params, headers=request_headers
                    )

                # Check for success status codes (2xx)
                if not (200 <= response.status_code < 300):
                    try:
                        error_detail = response.json().get("detail", response.text)
                    except:
                        error_detail = response.text

                    logger.error(f"API error {response.status_code}: {error_detail}")
                    raise Exception(
                        f"API error ({response.status_code}): {error_detail}"
                    )

                return response

            except httpx.RequestError as exc:
                logger.error(f"Request error for {url}: {exc}")
                raise Exception(f"Network error: {exc}")

    @property
    def workspace_name(self) -> str:
        """Get current workspace name."""
        return self._workspace_name

    @property
    def auth_method(self) -> AuthMethod:
        """Get current authentication method."""
        return self._auth_method

    def model(self, name: str):
        """Get a Model proxy for convenient access.

        Args:
            name: Model name

        Returns:
            Model proxy instance

        Example:
            >>> client = MixClient()
            >>> model = client.model("my-model")
            >>> result = model.run({"text": "Hello"})
        """
        # Late import to avoid circular dependency
        from .models import Model
        return Model(name, client=self)

    # Workspace operations
    def _list_workspaces_raw(self) -> Dict[str, Any]:
        """Internal method to list workspaces (used during initialization)."""
        response = self._make_request("GET", "/workspaces/list")
        return response.json()

    def list_workspaces(self) -> Dict[str, Any]:
        """List all workspaces the user has access to."""
        response = self._make_request("GET", "/workspaces/list")
        return response.json()

    def create_workspace(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new workspace."""
        response = self._make_request(
            "POST", "/workspaces/", json={"name": name, "description": description}
        )
        return response.json()

    def delete_workspace(self, workspace_name: str) -> Dict[str, Any]:
        """Delete a workspace."""
        response = self._make_request("DELETE", f"/workspaces/{workspace_name}")
        # 204 No Content responses don't have JSON body
        if response.status_code == 204:
            return {"success": True, "message": "Workspace deleted successfully"}
        return response.json()

    # Dataset operations
    def list_datasets(self) -> Dict[str, Any]:
        """List all datasets in the current workspace."""
        response = self._make_request(
            "GET", f"/lakehouse/workspaces/{self._workspace_name}/tables"
        )
        return response.json()

    # Evaluation operations
    def list_evaluations(self) -> Dict[str, Any]:
        """List all evaluations in the current workspace."""
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/evaluations/"
        )
        return response.json()

    def create_evaluation(
        self, name: str, config: Dict[str, Any], description: str = ""
    ) -> Dict[str, Any]:
        """Create a new evaluation in the current workspace."""
        payload = {"name": name, "description": description, "config": config}
        response = self._make_request(
            "POST", f"/workspaces/{self._workspace_name}/evaluations/", json=payload
        )
        return response.json()

    def get_evaluation(self, evaluation_name: str) -> Dict[str, Any]:
        """Get a specific evaluation by name.

        Args:
            evaluation_name: Name of the evaluation (slug format: lowercase, hyphens only)

        Returns:
            Evaluation data
        """
        # evaluation_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/evaluations/{evaluation_name}"
        )
        return response.json()

    def update_evaluation(
        self,
        evaluation_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update fields on an evaluation.

        Args:
            evaluation_name: Current name of the evaluation
            name: Optional new name for the evaluation
            description: Optional new description
            config: Optional new config
            status: Optional new status

        Returns:
            Updated evaluation data
        """
        # evaluation_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if config is not None:
            payload["config"] = config
        if status is not None:
            payload["status"] = status
        response = self._make_request(
            "PATCH",
            f"/workspaces/{self._workspace_name}/evaluations/{evaluation_name}",
            json=payload,
        )
        return response.json()

    def delete_evaluation(self, evaluation_name: str) -> Dict[str, Any]:
        """Delete an evaluation by name.

        Args:
            evaluation_name: Name of the evaluation to delete

        Returns:
            Deletion result
        """
        # evaluation_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._make_request(
            "DELETE",
            f"/workspaces/{self._workspace_name}/evaluations/{evaluation_name}",
        )
        # 204 No Content responses don't have JSON body
        if response.status_code == 204:
            return {"success": True, "message": "Evaluation deleted successfully"}
        return response.json()

    def get_evaluation_data(
        self,
        datasets: List[Dict[str, Any]],
        evaluation_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Fetch evaluation data for side-by-side comparison across datasets.

        Args:
            datasets: List of dataset configs with keys: tableName, columnName, dataType.
            evaluation_name: Optional evaluation name for caching.
            limit: Page size.
            offset: Offset for pagination.
        """
        payload: Dict[str, Any] = {
            "datasets": datasets,
            "limit": limit,
            "offset": offset,
        }
        if evaluation_name is not None:
            payload["evaluationName"] = evaluation_name
        response = self._make_request(
            "POST",
            f"/lakehouse/workspaces/{self._workspace_name}/evaluation/data",
            json=payload,
        )
        return response.json()

    def create_dataset_from_file(
        self,
        name: str,
        file_path: str,
        description: Optional[str] = None,
        provider_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a dataset from a file using the lakehouse API."""
        headers = {}
        if description:
            headers["X-Description"] = description

        if not provider_type:
            provider_type = "apache_iceberg"

        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f, "application/octet-stream")}
            response = self._make_request(
                "POST",
                f"/lakehouse/workspaces/{self._workspace_name}/tables/{name}?provider_type={provider_type}",
                files=files,
                headers=headers,
            )
        return response.json()

    def delete_dataset(self, name: str) -> httpx.Response:
        """Delete a dataset."""
        return self._make_request(
            "DELETE", f"/lakehouse/workspaces/{self._workspace_name}/tables/{name}"
        )

    def upload_file(self, dataset_name: str, file_path: str) -> Dict[str, Any]:
        """Upload a file to a dataset."""
        with open(file_path, "rb") as f:
            response = self._make_request(
                "POST",
                f"/datasets/{self._workspace_name}/{dataset_name}/upload",
                files={"file": f},
            )
            return response.json().get("data")

    @lru_cache(maxsize=1)
    def get_catalog(self) -> Any:
        """Get PyIceberg catalog for the workspace."""
        try:
            provider_secrets = self._make_request(
                "GET",
                f"/workspaces/{self._workspace_name}/dataset-providers/type/apache_iceberg",
            ).json()

            if provider_secrets["provider_type"] != "apache_iceberg":
                raise Exception(
                    f"Dataset provider {provider_secrets['provider_type']} is not supported"
                )

            if (
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is None
                and provider_secrets["secrets"]["CATALOG_WAREHOUSE_URI"].startswith(
                    "gs://"
                )
                and provider_secrets["secrets"]["SERVICE_ACCOUNT_JSON"]
            ):
                service_account_json = provider_secrets["secrets"][
                    "SERVICE_ACCOUNT_JSON"
                ]
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                    f"/tmp/{self._workspace_name}/service_account.json"
                )

                # Set up Google Cloud credentials (temporary file)
                os.makedirs(f"/tmp/mixtrain/{self._workspace_name}", exist_ok=True)
                with open(
                    f"/tmp/mixtrain/{self._workspace_name}/service_account.json", "w"
                ) as f:
                    f.write(service_account_json)

                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                    f"/tmp/mixtrain/{self._workspace_name}/service_account.json"
                )

            # Load the catalog
            catalog_config = {
                "type": provider_secrets["secrets"]["CATALOG_TYPE"],
                "uri": provider_secrets["secrets"]["CATALOG_URI"],
                "warehouse": provider_secrets["secrets"]["CATALOG_WAREHOUSE_URI"],
                "pool_pre_ping": "true",
                "pool_recycle": "3600",
                "pool_size": "5",
                "max_overflow": "10",
                "pool_timeout": "30",
            }
            catalog = load_catalog("default", **catalog_config)
            return catalog

        except Exception as e:
            raise Exception(f"Failed to load catalog: {e}")

    def get_dataset(self, name: str) -> Table:
        """Get an Iceberg table using workspace secrets and PyIceberg catalog API."""
        catalog = self.get_catalog()
        table_identifier = f"{self._workspace_name}.{name}"
        table = catalog.load_table(table_identifier)
        return table

    def get_dataset_metadata(self, name: str) -> Any:
        """Get detailed metadata for a table."""
        return self.get_dataset(name).metadata

    # Dataset provider operations
    def list_dataset_providers(self) -> Dict[str, Any]:
        """List available and onboarded dataset providers."""
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/dataset-providers/"
        )
        return response.json()

    def create_dataset_provider(
        self, provider_type: str, secrets: Dict[str, str]
    ) -> Dict[str, Any]:
        """Onboard a new dataset provider for the workspace."""
        payload = {"provider_type": provider_type, "secrets": secrets}
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/dataset-providers/",
            json=payload,
        )
        return response.json()

    def update_dataset_provider(
        self, provider_id: int, secrets: Dict[str, str]
    ) -> Dict[str, Any]:
        """Update secrets for an existing dataset provider."""
        payload = {"secrets": secrets}
        response = self._make_request(
            "PUT",
            f"/workspaces/{self._workspace_name}/dataset-providers/{provider_id}",
            json=payload,
        )
        return response.json()

    def delete_dataset_provider(self, provider_id: int) -> Dict[str, Any]:
        """Remove a dataset provider from the workspace."""
        response = self._make_request(
            "DELETE",
            f"/workspaces/{self._workspace_name}/dataset-providers/{provider_id}",
        )
        return response.json()

    # Model provider operations
    def list_model_providers(self) -> Dict[str, Any]:
        """List available and onboarded model providers."""
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/models/providers"
        )
        return response.json()

    def create_model_provider(
        self, provider_type: str, secrets: Dict[str, str]
    ) -> Dict[str, Any]:
        """Onboard a new model provider for the workspace."""
        payload = {"provider_type": provider_type, "secrets": secrets}
        response = self._make_request(
            "POST", f"/workspaces/{self._workspace_name}/models/providers", json=payload
        )
        return response.json()

    def update_model_provider(
        self, provider_id: int, secrets: Dict[str, str]
    ) -> Dict[str, Any]:
        """Update secrets for an existing model provider."""
        payload = {"secrets": secrets}
        response = self._make_request(
            "PUT",
            f"/workspaces/{self._workspace_name}/models/providers/{provider_id}",
            json=payload,
        )
        return response.json()

    def delete_model_provider(self, provider_id: int) -> Dict[str, Any]:
        """Remove a model provider from the workspace."""
        response = self._make_request(
            "DELETE",
            f"/workspaces/{self._workspace_name}/models/providers/{provider_id}",
        )
        return response.json()

    # Secret operations
    def get_secret(self, secret_name: str) -> str:
        """Get a secret value by name.

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            The decoded secret value as a string

        Raises:
            Exception: If secret is not found or there's an API error
        """
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/secrets/{secret_name}"
        )
        secret_data = response.json()
        return secret_data.get("value", "")

    def get_all_secrets(self) -> Dict[str, Any]:
        """Get all secrets in the current workspace."""
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/secrets/"
        )
        return response.json()

    def list_models(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """List models in the current workspace.

        Args:
            provider: Optional filter by model type - "native", "provider", or None for all

        Returns:
            Dict with 'data' key containing list of models
        """
        params = {"provider": provider} if provider else None
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/models/", params=params
        )
        return response.json()

    def get_catalog_models(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Browse provider model catalog.

        Args:
            provider: Optional filter by provider name

        Returns:
            Dict with available provider models
        """
        params = {"provider": provider} if provider else None
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/models/catalog", params=params
        )
        return response.json()

    def get_model(self, model_name: str) -> Dict[str, Any]:
        """Get model details.

        Args:
            model_name: Name of the model

        Returns:
            Model details
        """
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/models/{model_name}"
        )
        return response.json()

    def create_model(
        self,
        name: str,
        file_paths: List[str],
        description: str = "",
        entrypoint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a native model from local files/folders.

        Args:
            name: Model name
            file_paths: List of file or folder paths to upload
            description: Model description
            entrypoint: Optional entrypoint file for the model

        Returns:
            Created model data
        """
        import os
        from pathlib import Path

        files = []
        
        # Add form fields
        files.append(("name", (None, name)))
        files.append(("description", (None, description)))
        if entrypoint:
            files.append(("entrypoint", (None, entrypoint)))

        # Process file paths (files and folders)
        file_handles = []
        for file_path in file_paths:
            path = Path(file_path)
            if path.is_file():
                file_handle = open(file_path, "rb")
                file_handles.append(file_handle)
                files.append(
                    ("files", (os.path.basename(file_path), file_handle, "application/octet-stream"))
                )
            elif path.is_dir():
                # Upload all files in directory recursively
                for root, _, filenames in os.walk(file_path):
                    for filename in filenames:
                        full_path = os.path.join(root, filename)
                        file_handle = open(full_path, "rb")
                        file_handles.append(file_handle)
                        # Preserve directory structure
                        relative_path = os.path.relpath(full_path, path.parent)
                        files.append(
                            ("files", (relative_path, file_handle, "application/octet-stream"))
                        )

        try:
            response = self._make_request(
                "POST",
                f"/workspaces/{self._workspace_name}/models/",
                files=files,
            )
            return response.json()
        finally:
            # Close all file handles
            for handle in file_handles:
                handle.close()

    def register_model(
        self,
        name: str,
        provider: str,
        provider_model_id: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """Register a provider model.

        Args:
            name: Model name in workspace
            provider: Provider name (e.g., "openai", "anthropic")
            provider_model_id: Model ID from provider
            description: Model description

        Returns:
            Registered model data
        """
        payload = {
            "name": name,
            "provider": provider,
            "provider_model_id": provider_model_id,
            "description": description,
        }
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/models/register",
            json=payload,
        )
        return response.json()

    def update_model(
        self,
        model_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update model metadata and/or file.

        Args:
            model_name: Current model name
            name: Optional new name
            description: Optional new description
            file_path: Optional path to new model file

        Returns:
            Updated model data
        """
        # If file is provided, use multipart/form-data
        if file_path:
            import os
            
            files = []
            
            if name:
                files.append(("display_name", (None, name)))
            if description:
                files.append(("description", (None, description)))
                
            file_handle = open(file_path, "rb")
            try:
                files.append((
                    "files",
                    (
                        os.path.basename(file_path),
                        file_handle,
                        "application/octet-stream",
                    )
                ))
                
                response = self._make_request(
                    "PATCH",
                    f"/workspaces/{self._workspace_name}/models/{model_name}",
                    files=files,
                )
                return response.json()
            finally:
                file_handle.close()
        
        # JSON mode (metadata only)
        else:
            payload = {}
            if name is not None:
                payload["display_name"] = name
            if description is not None:
                payload["description"] = description

            response = self._make_request(
                "PATCH",
                f"/workspaces/{self._workspace_name}/models/{model_name}",
                json=payload,
            )
            return response.json()

    def delete_model(self, model_name: str) -> Dict[str, Any]:
        """Delete a model.

        Args:
            model_name: Name of the model to delete

        Returns:
            Deletion result
        """
        response = self._make_request(
            "DELETE", f"/workspaces/{self._workspace_name}/models/{model_name}"
        )
        # 204 No Content responses don't have JSON body
        if response.status_code == 204:
            return {"success": True, "message": "Model deleted successfully"}
        return response.json()

    def get_model_code(self, model_name: str) -> Dict[str, Any]:
        """Get model source code.

        Args:
            model_name: Name of the model

        Returns:
            Model code content
        """
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/models/{model_name}/code"
        )
        return response.json()

    def update_model_code(self, model_name: str, code: str) -> Dict[str, Any]:
        """Update model source code.

        Args:
            model_name: Name of the model
            code: New code content

        Returns:
            Update result
        """
        payload = {"code": code}
        response = self._make_request(
            "PUT",
            f"/workspaces/{self._workspace_name}/models/{model_name}/code",
            json=payload,
        )
        return response.json()

    def list_model_files(self, model_name: str) -> Dict[str, Any]:
        """List files in a model.

        Args:
            model_name: Name of the model

        Returns:
            List of files
        """
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/models/{model_name}/files"
        )
        return response.json()

    def get_model_file(self, model_name: str, file_path: str) -> Dict[str, Any]:
        """Get content of a specific model file.

        Args:
            model_name: Name of the model
            file_path: Path to file within model

        Returns:
            File content
        """
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/models/{model_name}/files/{file_path}",
        )
        return response.json()

    def run_model(
        self,
        model_name: str,
        inputs: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        sandbox: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run model inference.

        Args:
            model_name: Name of the model
            inputs: Input data for the model
            config: Optional configuration overrides
            sandbox: Optional sandbox configuration (GPU, memory, etc.)

        Returns:
            Run result with outputs
        """
        payload_config = config or {}
        if sandbox:
            payload_config["sandbox"] = sandbox

        payload = {
            "inputs": inputs or {},
            "config": payload_config,
        }
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/models/{model_name}/run",
            json=payload,
        )
        return response.json()

    def list_model_runs(self, model_name: str) -> Dict[str, Any]:
        """List all runs for a model.

        Args:
            model_name: Name of the model

        Returns:
            List of model runs
        """
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/models/{model_name}/runs"
        )
        return response.json()

    def get_model_run(self, model_name: str, run_number: int) -> Dict[str, Any]:
        """Get details of a specific model run.

        Args:
            model_name: Name of the model
            run_number: Run number

        Returns:
            Run details
        """
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/models/{model_name}/runs/{run_number}",
        )
        return response.json()

    def update_model_run_status(
        self,
        model_name: str,
        run_number: int,
        status: str,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update model run status.

        Args:
            model_name: Name of the model
            run_number: Run number
            status: New status (pending, running, completed, failed)
            outputs: Optional run outputs
            error: Optional error message

        Returns:
            Updated run data
        """
        payload = {"status": status}
        if outputs is not None:
            payload["outputs"] = outputs
        if error is not None:
            payload["error"] = error

        response = self._make_request(
            "PATCH",
            f"/workspaces/{self._workspace_name}/models/{model_name}/runs/{run_number}",
            json=payload,
        )
        return response.json()

    def get_model_run_logs(
        self, model_name: str, run_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get logs for a model run.

        Args:
            model_name: Name of the model
            run_number: Optional run number (defaults to latest run)

        Returns:
            Run logs
        """
        if run_number is not None:
            path = f"/workspaces/{self._workspace_name}/models/{model_name}/runs/{run_number}/logs"
        else:
            # Get latest run's logs
            runs_response = self.list_model_runs(model_name)
            runs = runs_response.get("runs", [])
            if not runs:
                return {"logs": "No runs found for this model"}
            latest_run = runs[0]
            run_number = latest_run.get("run_number")
            path = f"/workspaces/{self._workspace_name}/models/{model_name}/runs/{run_number}/logs"

        response = self._make_request("GET", path)
        if not response.text:
            return {"logs": "No logs available for this run"}
        # Logs endpoint returns plain text, not JSON
        return {"logs": response.text}

    # Routing configuration operations
    def list_routers(self, status: Optional[str] = None) -> Dict[str, Any]:
        """List all routing configurations in the workspace.

        Args:
            status: Optional filter by status ('active', 'inactive')

        Returns:
            Dict with 'data' key containing list of routing configuration summaries
        """
        params = {"status": status} if status else None
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/inference/routers",
            params=params,
        )
        return response.json()

    def get_routing_config(
        self, router_name: str, version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get a specific router configuration.

        Args:
            router_name: Name of the router
            version: Optional specific version to retrieve

        Returns:
            Full router configuration with rules and metadata
        """
        params = {"version": version} if version else None
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/inference/routers/{router_name}",
            params=params,
        )
        return response.json()

    def get_routing_engine(
        self, router_name: str, version: Optional[int] = None
    ) -> RoutingEngine:
        """Get a routing engine instance for a specific router configuration.

        Args:
            router_name: Name of the router
            version: Optional specific version to use

        Returns:
            Routing engine instance configured with the specified router's rules
        """
        config = self.get_routing_config(router_name, version=version)
        return RoutingEngineFactory.from_json(config)

    def create_routing_config(
        self,
        name: str,
        description: str,
        rules: List[Dict[str, Any]],
        settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new router configuration.

        Args:
            name: Name of the router
            description: Description of the router
            rules: List of routing rules
            settings: Optional deployment settings dict with keys:
                - inference_uri: URL where this router serves inference requests
                - update_uri: URL to call when deploying to reload configuration

        Returns:
            Created router configuration
        """
        payload = {"name": name, "description": description, "rules": rules}
        if settings is not None:
            payload["settings"] = settings
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/inference/routers",
            json=payload,
        )
        return response.json()

    def update_routing_config(
        self,
        router_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        rules: Optional[List[Dict[str, Any]]] = None,
        settings: Optional[Dict[str, Any]] = None,
        change_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a router configuration (creates a new version).

        Args:
            router_name: Name of the router to update
            name: Optional new name
            description: Optional new description
            rules: Optional new rules list
            settings: Optional deployment settings dict with keys:
                - inference_uri: URL where this router serves inference requests
                - update_uri: URL to call when deploying to reload configuration
            change_message: Optional change summary message

        Returns:
            Updated router configuration
        """
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if settings is not None:
            payload["settings"] = settings
        if rules is not None:
            payload["rules"] = rules

            # Detect rule changes and generate change summary
            try:
                # Get current config to compare rules
                current_config = self.get_routing_config(router_name)
                old_rules = current_config.get("rules", [])
                _change_message = change_message or detect_rule_changes(
                    old_rules, rules
                )
                payload["change_message"] = _change_message
            except Exception as e:
                # If we can't get the current config, fall back to generic message
                logger.warning(
                    f"Failed to detect rule changes for router {router_name}: {e}"
                )
                payload["change_message"] = "Configuration updated via CLI"

        response = self._make_request(
            "PUT",
            f"/workspaces/{self._workspace_name}/inference/routers/{router_name}",
            json=payload,
        )
        return response.json()

    def activate_routing_config(
        self, router_name: str, version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Deploy/activate a router configuration.

        This sets the specified version as the active deployment for this router
        and notifies the router's update_uri (if configured) to reload its config.

        Note: Each router is independently deployable - activating one router does
        not affect other routers in the workspace.

        Args:
            router_name: Name of the router to deploy
            version: Optional specific version to deploy (defaults to latest)

        Returns:
            Deployment result with version info
        """
        payload = {}
        if version is not None:
            payload["version"] = version

        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/inference/routers/{router_name}/activate",
            json=payload,
        )
        return response.json()

    def delete_routing_config(self, router_name: str) -> Dict[str, Any]:
        """Delete a router configuration and all its versions.

        Args:
            router_name: Name of the router to delete

        Returns:
            Deletion result
        """
        response = self._make_request(
            "DELETE",
            f"/workspaces/{self._workspace_name}/inference/routers/{router_name}",
        )
        return response.json()

    def test_routing_config(
        self, router_name: str, test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test router configuration against sample data.

        Args:
            router_name: Name of the router to test
            test_data: Sample request data for testing

        Returns:
            Test results with matched rule and targets
        """
        payload = {"test_data": test_data}
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/inference/routers/{router_name}/test",
            json=payload,
        )
        return response.json()

    def get_routing_config_versions(self, router_name: str) -> Dict[str, Any]:
        """Get all versions of a router configuration.

        Args:
            router_name: Name of the router

        Returns:
            List of all router versions
        """
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/inference/routers/{router_name}/versions",
        )
        return response.json()

    # Router request operations
    def list_router_requests(
        self,
        router_name: str,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        matched_rule: Optional[str] = None,
        response_code: Optional[int] = None,
        invocation_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List router requests for a router with filtering.

        Args:
            router_name: Name of the router
            limit: Number of results (1-100, default 20)
            offset: Pagination offset
            status: Filter by status (pending, routing, executing, completed, failed)
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            matched_rule: Filter by matched rule name
            response_code: Filter by HTTP response code
            invocation_type: Filter by invocation type (model, workflow, external)

        Returns:
            Dict with data array, total count, and pagination info
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if matched_rule:
            params["matched_rule"] = matched_rule
        if response_code:
            params["response_code"] = response_code
        if invocation_type:
            params["invocation_type"] = invocation_type

        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/inference/routers/{router_name}/requests",
            params=params,
        )
        return response.json()

    def get_router_request(
        self,
        router_name: str,
        request_id: int,
    ) -> Dict[str, Any]:
        """Get details of a specific router request.

        Args:
            router_name: Name of the router
            request_id: The request ID (numeric)

        Returns:
            Full router request details including input, routing result, and response
        """
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/inference/routers/{router_name}/requests/{request_id}",
        )
        return response.json()

    def get_router_request_filters(
        self,
        router_name: str,
    ) -> Dict[str, Any]:
        """Get available filter options for router requests.

        Args:
            router_name: Name of the router

        Returns:
            Dict with available filter values (e.g., distinct matched_rule names)
        """
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/inference/routers/{router_name}/requests/filters",
        )
        return response.json()

    def create_router_request(
        self,
        router_name: str,
        input_request: Dict[str, Any],
        status: Optional[str] = None,
        matched_rule_name: Optional[str] = None,
        routing_result: Optional[Dict[str, Any]] = None,
        selected_target: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        response_status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        routing_latency_ms: Optional[float] = None,
        execution_latency_ms: Optional[float] = None,
        total_latency_ms: Optional[float] = None,
        invocation_type: Optional[str] = None,
        invoked_model_run_id: Optional[int] = None,
        invoked_workflow_run_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a router request log entry.

        Used by external systems to log requests processed outside the platform.

        Args:
            router_name: Name of the router
            input_request: The original request payload
            status: Initial status (pending, routing, executing, completed, failed)
            matched_rule_name: Name of the matched routing rule
            routing_result: Full routing decision result
            selected_target: Selected target endpoint
            response_data: Response from target
            response_status_code: HTTP response status code
            error_message: Error message if failed
            routing_latency_ms: Time spent on routing decision
            execution_latency_ms: Time spent on execution
            total_latency_ms: Total request latency
            invocation_type: Type of downstream invocation (model, workflow, external)
            invoked_model_run_id: ID of invoked model run
            invoked_workflow_run_id: ID of invoked workflow run

        Returns:
            Created router request details
        """
        payload: Dict[str, Any] = {"input_request": input_request}
        if status:
            payload["status"] = status
        if matched_rule_name:
            payload["matched_rule_name"] = matched_rule_name
        if routing_result:
            payload["routing_result"] = routing_result
        if selected_target:
            payload["selected_target"] = selected_target
        if response_data:
            payload["response_data"] = response_data
        if response_status_code:
            payload["response_status_code"] = response_status_code
        if error_message:
            payload["error_message"] = error_message
        if routing_latency_ms:
            payload["routing_latency_ms"] = routing_latency_ms
        if execution_latency_ms:
            payload["execution_latency_ms"] = execution_latency_ms
        if total_latency_ms:
            payload["total_latency_ms"] = total_latency_ms
        if invocation_type:
            payload["invocation_type"] = invocation_type
        if invoked_model_run_id:
            payload["invoked_model_run_id"] = invoked_model_run_id
        if invoked_workflow_run_id:
            payload["invoked_workflow_run_id"] = invoked_workflow_run_id

        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/inference/routers/{router_name}/requests",
            json=payload,
        )
        return response.json()

    def update_router_request(
        self,
        router_name: str,
        request_id: int,
        status: Optional[str] = None,
        matched_rule_name: Optional[str] = None,
        routing_result: Optional[Dict[str, Any]] = None,
        selected_target: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        response_status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        routing_latency_ms: Optional[float] = None,
        execution_latency_ms: Optional[float] = None,
        total_latency_ms: Optional[float] = None,
        invocation_type: Optional[str] = None,
        invoked_model_run_id: Optional[int] = None,
        invoked_workflow_run_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update a router request log entry.

        Used by external systems to update request status and results.

        Args:
            router_name: Name of the router
            request_id: The request ID (numeric)
            status: New status (pending, routing, executing, completed, failed)
            matched_rule_name: Name of the matched routing rule
            routing_result: Full routing decision result
            selected_target: Selected target endpoint
            response_data: Response from target
            response_status_code: HTTP response status code
            error_message: Error message if failed
            routing_latency_ms: Time spent on routing decision
            execution_latency_ms: Time spent on execution
            total_latency_ms: Total request latency
            invocation_type: Type of downstream invocation (model, workflow, external)
            invoked_model_run_id: ID of invoked model run
            invoked_workflow_run_id: ID of invoked workflow run

        Returns:
            Updated router request details
        """
        payload: Dict[str, Any] = {}
        if status:
            payload["status"] = status
        if matched_rule_name:
            payload["matched_rule_name"] = matched_rule_name
        if routing_result:
            payload["routing_result"] = routing_result
        if selected_target:
            payload["selected_target"] = selected_target
        if response_data:
            payload["response_data"] = response_data
        if response_status_code:
            payload["response_status_code"] = response_status_code
        if error_message:
            payload["error_message"] = error_message
        if routing_latency_ms:
            payload["routing_latency_ms"] = routing_latency_ms
        if execution_latency_ms:
            payload["execution_latency_ms"] = execution_latency_ms
        if total_latency_ms:
            payload["total_latency_ms"] = total_latency_ms
        if invocation_type:
            payload["invocation_type"] = invocation_type
        if invoked_model_run_id:
            payload["invoked_model_run_id"] = invoked_model_run_id
        if invoked_workflow_run_id:
            payload["invoked_workflow_run_id"] = invoked_workflow_run_id

        response = self._make_request(
            "PATCH",
            f"/workspaces/{self._workspace_name}/inference/routers/{router_name}/requests/{request_id}",
            json=payload,
        )
        return response.json()

    # Workflow operations
    def list_workflows(self) -> Dict[str, Any]:
        """List all workflows in the workspace."""
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/workflows/"
        )
        return response.json()

    def create_workflow(
        self,
        name: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """Create a new workflow."""
        payload = {
            "name": name,
            "description": description,
        }
        response = self._make_request(
            "POST", f"/workspaces/{self._workspace_name}/workflows/", json=payload
        )
        return response.json()

    def create_workflow_with_files(
        self,
        name: str,
        workflow_file: str,
        src_files: List[str],
        description: str = "",
    ) -> Dict[str, Any]:
        """Create a new workflow with file uploads."""
        import os

        # Prepare files list for multipart/form-data
        files = []

        # Add form fields
        files.append(("name", (None, name)))
        files.append(("description", (None, description)))

        # Add workflow file
        workflow_file_handle = open(workflow_file, "rb")
        files.append((
            "workflow_file",
            (
                os.path.basename(workflow_file),
                workflow_file_handle,
                "application/octet-stream",
            )
        ))

        # Add source files
        src_file_handles = []
        for src_file in src_files:
            src_file_handle = open(src_file, "rb")
            src_file_handles.append(src_file_handle)
            files.append((
                "src_files",
                (
                    os.path.basename(src_file),
                    src_file_handle,
                    "application/octet-stream",
                )
            ))

        try:
            response = self._make_request(
                "POST",
                f"/workspaces/{self._workspace_name}/workflows/",
                files=files,
            )
            return response.json()
        finally:
            # Close all file handles
            workflow_file_handle.close()
            for handle in src_file_handles:
                handle.close()

    def get_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Get a specific workflow with its runs.

        Args:
            workflow_name: Name of the workflow (slug format: lowercase, hyphens only)

        Returns:
            Workflow data with runs
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/workflows/{workflow_name}"
        )
        return response.json()

    def update_workflow(
        self,
        workflow_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        workflow_file: Optional[str] = None,
        src_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update a workflow.

        Args:
            workflow_name: Current name of the workflow
            name: Optional new name for the workflow
            description: Optional new description
            workflow_file: Optional path to new workflow file
            src_files: Optional list of paths to new source files

        Returns:
            Updated workflow data
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        
        # If files are provided, use multipart/form-data
        if workflow_file or src_files:
            import os
            
            # Use list of tuples for files to handle multiple files with same key 'files'
            # and to avoid 'list object has no attribute read' error with httpx
            files = []
            
            if name:
                files.append(("name", (None, name)))
            if description:
                files.append(("description", (None, description)))
                
            file_handles = []
            try:
                # Add workflow file if provided
                if workflow_file:
                    workflow_file_handle = open(workflow_file, "rb")
                    file_handles.append(workflow_file_handle)
                    files.append((
                        "files",
                        (
                            os.path.basename(workflow_file),
                            workflow_file_handle,
                            "application/octet-stream",
                        )
                    ))
                
                # Add source files if provided
                if src_files:
                    for src_file in src_files:
                        src_file_handle = open(src_file, "rb")
                        file_handles.append(src_file_handle)
                        files.append((
                            "files",
                            (
                                os.path.basename(src_file),
                                src_file_handle,
                                "application/octet-stream",
                            )
                        ))
                
                response = self._make_request(
                    "PUT",
                    f"/workspaces/{self._workspace_name}/workflows/{workflow_name}",
                    files=files,
                )
                return response.json()
                
            finally:
                # Close all file handles
                for handle in file_handles:
                    handle.close()
        
        # JSON mode (metadata only)
        else:
            payload = {}
            if name is not None:
                payload["name"] = name
            if description is not None:
                payload["description"] = description

            response = self._make_request(
                "PUT",
                f"/workspaces/{self._workspace_name}/workflows/{workflow_name}",
                json=payload,
            )
            return response.json()

    def delete_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Delete a workflow.

        Args:
            workflow_name: Name of the workflow to delete

        Returns:
            Deletion result
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._make_request(
            "DELETE", f"/workspaces/{self._workspace_name}/workflows/{workflow_name}"
        )
        # 204 No Content responses don't have JSON body
        if response.status_code == 204:
            return {"success": True, "message": "Workflow deleted successfully"}
        return response.json()

    def list_workflow_runs(self, workflow_name: str) -> Dict[str, Any]:
        """List all runs for a workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            List of workflow runs
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/workflows/{workflow_name}/runs"
        )
        return response.json()

    def start_workflow_run(
        self, workflow_name: str, json_config: Optional[Union[Dict[str, Any], str]] = None
    ) -> Dict[str, Any]:
        """Start a new workflow run with optional configuration overrides.

        Args:
            workflow_name: Name of the workflow to run
            json_config: Optional configuration to override workflow defaults.
                        Can be a dictionary, a JSON string, or a path to a JSON file.

        Returns:
            Workflow run data
        """
        # Handle json_config if it's a string (file path or JSON string)
        config_dict = {}
        if json_config:
            if isinstance(json_config, str):
                if os.path.exists(json_config):
                    with open(json_config, 'r') as f:
                        config_dict = json.load(f)
                else:
                    try:
                        config_dict = json.loads(json_config)
                    except json.JSONDecodeError:
                        # If it's not a valid JSON string and not a file, raise error
                        raise ValueError("json_config must be a valid JSON string or an existing file path")
            else:
                config_dict = json_config

        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        payload = {"json_config": config_dict}
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/workflows/{workflow_name}/runs",
            json=payload,
        )
        return response.json()

    def get_workflow_run(self, workflow_name: str, run_number: int) -> Dict[str, Any]:
        """Get a specific workflow run.

        Args:
            workflow_name: Name of the workflow
            run_number: Per-workflow run number (1, 2, 3...)

        Returns:
            Workflow run data
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9-]{0,62}$), encoding not needed
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/workflows/{workflow_name}/runs/{run_number}",
        )
        return response.json()

    def update_workflow_run_status(
        self,
        workflow_name: str,
        run_number: int,
        status: Optional[str] = None,
        json_config: Optional[Dict[str, Any]] = None,
        logs_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a workflow run status and other fields.

        Args:
            workflow_name: Name of the workflow
            run_number: Per-workflow run number
            status: Optional new status. Valid values: 'pending', 'running', 'completed', 'failed', 'cancelled'
            json_config: Optional configuration to override
            logs_url: Optional URL to the run logs

        Returns:
            Updated workflow run data
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9-]{0,62}$), encoding not needed
        payload = {}
        if status is not None:
            payload["status"] = status
        if json_config is not None:
            payload["json_config"] = json_config
        if logs_url is not None:
            payload["logs_url"] = logs_url

        response = self._make_request(
            "PATCH",
            f"/workspaces/{self._workspace_name}/workflows/{workflow_name}/runs/{run_number}",
            json=payload,
        )
        return response.json()

    def cancel_workflow_run(
        self, workflow_name: str, run_number: int
    ) -> Dict[str, Any]:
        """Cancel a running workflow.

        Args:
            workflow_name: Name of the workflow
            run_number: Per-workflow run number to cancel

        Returns:
            Cancellation result
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9-]{0,62}$), encoding not needed
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/workflows/{workflow_name}/runs/{run_number}/cancel",
            json={},
        )
        return response.json()

    # Authentication operations
    def authenticate_browser(self) -> str:
        """Authenticate using browser-based OAuth flow."""
        return auth_utils.authenticate_browser(get_config, self._make_request_for_auth)

    def authenticate_with_token(self, token: str, provider: str) -> str:
        """Authenticate using OAuth token (GitHub or Google)."""
        return auth_utils.authenticate_with_token(
            token, provider, get_config, self._make_request_for_auth
        )

    def authenticate_github(self, access_token: str) -> str:
        """Authenticate using GitHub access token."""
        return auth_utils.authenticate_github(
            access_token, get_config, self._make_request_for_auth
        )

    def authenticate_google(self, id_token: str) -> str:
        """Authenticate using Google ID token."""
        return auth_utils.authenticate_google(
            id_token, get_config, self._make_request_for_auth
        )

    def _make_request_for_auth(
        self, method: str, path: str, **kwargs
    ) -> httpx.Response:
        """Helper method for authentication flows that don't need full client setup."""
        # This is a simpler version used during auth flows before client is fully initialized
        with httpx.Client(timeout=10.0) as client:
            url = f"{self._get_platform_url()}{path}"
            response = client.request(method, url, **kwargs)
            if response.status_code != 200:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text
                raise Exception(f"Auth error ({response.status_code}): {error_detail}")
            return response


def mixparam(
    default: Optional[Any] = None,
    description: Optional[str] = None,
) -> Any:
    """Define a configurable parameter for a MixFlow workflow or MixModel.

    This function marks a class attribute as a configurable parameter.
    The parameter metadata (type, description, default value) will be extracted
    automatically when the workflow/model is created and shown in the UI.

    Args:
        default: Default value for the parameter (optional)
        description: Human-readable description of the parameter (optional)

    Returns:
        The default value (for use in the class definition)

    Example:
        ```python
        from mixtrain import MixFlow, MixModel, mixparam

        class MyWorkflow(MixFlow):
            # With type annotation and description
            learning_rate: float = mixparam(
                default=0.001,
                description="Learning rate for training"
            )

            # With type annotation, no default
            model_name: str = mixparam(
                description="Name of the model to use"
            )

            # Simple case - just a default value
            batch_size: int = mixparam(default=32)

            def run(self):
                print(f"Using learning_rate: {self.learning_rate}")
                print(f"Using model: {self.model_name}")
                print(f"Batch size: {self.batch_size}")
        ```

    Note:
        Parameters defined with mixparam() will be:
        - Extracted automatically when the workflow/model is created
        - Displayed in the web UI with their types and descriptions
        - Configurable via a form interface or JSON when running the workflow/model
    """
    return default


# Backward compatibility alias
mixflow_param = mixparam


class MixFlow:
    """Base class for workflows."""

    def __init__(self):
        self.mix = MixClient()

    def setup(self, run_config_override: dict[str, Any]=None):
        """Initialize the workflow. Override this method to perform setup operations."""
        pass

    def run(self, run_config_override: dict[str, Any]=None):
        raise NotImplementedError(
            "Run method should be implemented by the workflow subclass"
        )

    def cleanup(self):
        """Clean up resources after workflow execution. Override this method if needed."""
        pass


class MixModel(MixFlow):
    """Base class for models, extends MixFlow.

    Models are a special type of workflow optimized for inference operations.
    They support run() for single inference and run_batch() for batch processing.

    Example:
        ```python
        from mixtrain import MixModel, mixparam

        class TextGenerationModel(MixModel):
            temperature: float = mixparam(default=0.7, description="Sampling temperature")
            max_tokens: int = mixparam(default=512, description="Maximum tokens")

            def setup(self):
                # Load model weights
                self.model = load_model()

            def run(self, inputs=None):
                inputs = inputs or {}
                prompt = inputs.get("prompt", "")
                result = self.model.generate(prompt, temperature=self.temperature)
                return {"generated_text": result}

            def run_batch(self, batch):
                return [self.run(inputs) for inputs in batch]

            def cleanup(self):
                del self.model
        ```
    """

    def run(self, inputs: dict[str, Any]=None, run_config_override: dict[str, Any]=None):
        """Main inference method.

        Args:
            inputs: Input data for the model (optional, can also come from config)

        Returns:
            Model outputs (typically a dict)
        """
        raise NotImplementedError(
            "Run method must be implemented by the model subclass"
        )

    def run_batch(self, batch: list[dict[str, Any]], run_config_override: dict[str, Any]=None):
        """Batch inference method.

        Args:
            batch: List of input dictionaries

        Returns:
            List of output dictionaries
        """
        return [self.run(inputs) for inputs in batch]
