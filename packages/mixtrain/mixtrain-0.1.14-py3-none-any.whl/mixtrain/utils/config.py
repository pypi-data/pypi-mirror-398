"""Configuration management utilities for Mixtrain SDK."""

import json
import os
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel

logger = getLogger(__name__)


class WorkspaceConfig(BaseModel):
    """Configuration for a workspace."""
    name: str
    active: bool = False


class Config:
    """Configuration manager for Mixtrain SDK."""

    _instance = None

    @classmethod
    def _get_config_path(cls) -> Path:
        """Get the config file path, checking environment variable override."""
        config_path = os.getenv("MIXTRAIN_CONFIG")
        if config_path:
            return Path(config_path)
        else:
            return Path.home() / ".mixtrain" / "config.json"

    @property
    def _config_file(self) -> Path:
        """Get the config file path."""
        return self._get_config_path()

    @property
    def _config_dir(self) -> Path:
        """Get the config directory."""
        return self._config_file.parent
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def __repr__(self):
        return f"Config(workspaces={self.workspaces}, auth_token={self.auth_token})"

    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            if self._config_file.exists():
                config_data = json.loads(self._config_file.read_text())
                self.workspaces = [WorkspaceConfig(**w) for w in config_data.get("workspaces", [])]
                self.auth_token = config_data.get("auth_token")
            else:
                self.workspaces = []
                self.auth_token = None
                self._save_config()
        except Exception as e:
            logger.warning(f"Error loading config: {e}")
            self.workspaces = []
            self.auth_token = None

    def _save_config(self):
        """Save current configuration to JSON file.
        
        Config file format:
        {
          "auth_token": "...",
          "workspaces": [
            {
              "name": "workspace_name",
              "active": true
            }
          ]
        }
        """
        try:
            config_data = {
                "auth_token": self.auth_token,
                "workspaces": [w.model_dump() for w in self.workspaces]
            }
            self._config_file.write_text(json.dumps(config_data, indent=2))
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    @property
    def workspace_name(self) -> str:
        """Get current workspace name."""
        active_workspace = next((w for w in self.workspaces if w.active), None)
        if not active_workspace:
            raise Exception("No active workspace. Please authenticate first.")
        return active_workspace.name

    @property
    def platform_url(self) -> str:
        """Get platform URL with environment variable override."""
        return os.getenv("MIXTRAIN_PLATFORM_URL", "https://platform.mixtrain.ai/api/v1")
        
    def get_auth_token(self) -> Optional[str]:
        """Get common auth token (not workspace-specific)."""        
        return self.auth_token

    def set_auth_token(self, token: str, workspace_info: Optional[Dict[str, Any]] = None):
        """Store common auth token and optionally create/update workspace from server info."""
        # Store the common auth token
        self.auth_token = token
        
        if workspace_info:
            # Create or update workspace from server info
            workspace_name = workspace_info.get("name")
            if not workspace_name:
                raise Exception("Server did not provide workspace name")
            
            workspace = next((w for w in self.workspaces if w.name == workspace_name), None)
            if not workspace:
                # Create new workspace
                workspace = WorkspaceConfig(
                    name=workspace_name,
                    active=True
                )
                self.workspaces.append(workspace)
            else:
                # Update existing workspace
                workspace.active = True
            
            # Deactivate other workspaces
            for w in self.workspaces:
                if w.name != workspace_name:
                    w.active = False
        
        self._save_config()

    def set_workspace(self, name: str):
        """Switch to a different workspace, creating it if it doesn't exist."""
        if not self.workspaces:
            raise Exception("No workspaces available. Please authenticate first.")
            
        # First check if workspace exists
        workspace = next((w for w in self.workspaces if w.name == name), None)
        if not workspace:
            raise Exception(f"Workspace '{name}' not found. Available workspaces: {', '.join(w.name for w in self.workspaces)}")
        
        # Deactivate all workspaces and activate the selected one
        for w in self.workspaces:
            w.active = (w.name == name)
        
        self._save_config()


def get_config() -> Config:
    """Get the singleton Config instance."""
    return Config()