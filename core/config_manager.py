"""
Configuration manager for the SAP Azure Automation tool.
Handles loading, saving, and validating configuration.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages application configuration"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Optional directory path for configuration files.
                        Defaults to ~/.sap_deployment_automation
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".sap_deployment_automation"

        self.config_file = self.config_dir / "config.json"
        self.credentials_file = self.config_dir / "credentials.json"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Default configuration
        self.config: Dict[str, Any] = {
            "server_url": "https://github.com",
            "environment": "",
            "vnet_name": "",
            "region_map": "",
            "subscription_id": "",
            "tenant_id": "",
            "spn_name": "",
        }

        # Default credentials (empty)
        self.credentials: Dict[str, Any] = {
            "github_token": "",
            "github_app_id": "",
            "github_app_name": "",
            "github_private_key": "",
            "repository_name": "",
            "owner": "",
            "azure_client_id": "",
            "azure_client_secret": "",
            "azure_object_id": "",
            "s_username": "",
            "s_password": "",
        }

        # Load configuration if exists
        self.load_config()
        self.load_credentials()

    def load_config(self) -> None:
        """Load configuration from file if it exists"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    loaded_config = json.load(f)
                    # Update config with loaded values
                    self.config.update(loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading configuration: {e}")

    def load_credentials(self) -> None:
        """Load credentials from file if it exists"""
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, "r") as f:
                    loaded_credentials = json.load(f)
                    # Update credentials with loaded values
                    self.credentials.update(loaded_credentials)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading credentials: {e}")

    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Error saving configuration: {e}")

    def save_credentials(self) -> None:
        """Save credentials to file"""
        try:
            with open(self.credentials_file, "w") as f:
                json.dump(self.credentials, f, indent=2)
        except IOError as e:
            print(f"Error saving credentials: {e}")

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update configuration with new values.

        Args:
            new_config: Dictionary containing configuration updates
        """
        self.config.update(new_config)
        self.save_config()

    def update_credentials(self, new_credentials: Dict[str, Any]) -> None:
        """
        Update credentials with new values.

        Args:
            new_credentials: Dictionary containing credential updates
        """
        self.credentials.update(new_credentials)
        self.save_credentials()

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()

    def get_credentials(self) -> Dict[str, Any]:
        """Get current credentials"""
        return self.credentials.copy()

    def get_combined_data(self) -> Dict[str, Any]:
        """Get combined configuration and credentials data"""
        combined = self.config.copy()
        combined.update(self.credentials)
        return combined

    def clear_credentials(self) -> None:
        """Clear all stored credentials"""
        self.credentials = {key: "" for key in self.credentials}
        self.save_credentials()
