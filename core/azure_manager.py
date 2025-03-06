"""
Azure operations manager for the SAP Azure Automation tool.
Handles Azure login, service principal creation, and federated identity configuration.
"""

import json
import subprocess
from typing import Dict, Any, Optional, Tuple


class AzureManager:
    """Manager for Azure operations"""

    def __init__(self):
        """Initialize the Azure manager."""
        self.logged_in = False

    def login(self) -> bool:
        """
        Login to Azure using the Azure CLI.

        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            print("\nLogging in to Azure...")
            login_command = [
                "az",
                "login",
                "--scope",
                "https://graph.microsoft.com//.default",
            ]
            result = subprocess.run(login_command, capture_output=True, text=True)

            if result.returncode != 0:
                print(
                    "Failed to login to Azure. Please check your credentials and try again."
                )
                print(result.stderr)
                return False

            print("Successfully logged in to Azure.")
            self.logged_in = True
            return True
        except Exception as e:
            print(f"Error during Azure login: {e}")
            return False

    def validate_login(self) -> bool:
        """
        Validate current Azure login status.

        Returns:
            bool: True if currently logged in, False otherwise
        """
        try:
            account_command = ["az", "account", "show"]
            result = subprocess.run(account_command, capture_output=True, text=True)

            if result.returncode != 0:
                self.logged_in = False
                return False

            self.logged_in = True
            return True
        except Exception:
            self.logged_in = False
            return False

    def create_service_principal(
        self, subscription_id: str, spn_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create an Azure service principal with Contributor role.

        Args:
            subscription_id: Azure Subscription ID
            spn_name: Name for the new Service Principal

        Returns:
            Dictionary with service principal details or None if failed
        """
        if not self.validate_login():
            print("Not logged in to Azure. Please login first.")
            return None

        try:
            print(f"\nCreating Azure Service Principal '{spn_name}'...")
            spn_create_command = [
                "az",
                "ad",
                "sp",
                "create-for-rbac",
                "--name",
                spn_name,
                "--role",
                "contributor",
                "--scopes",
                f"/subscriptions/{subscription_id}",
                "--only-show-errors",
            ]
            result = subprocess.run(spn_create_command, capture_output=True, text=True)

            if result.returncode != 0:
                print("Failed to create service principal.")
                print(result.stderr)
                return None

            try:
                spn_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                print("Failed to decode JSON from the output.")
                print(result.stdout)
                return None

            # Get service principal object ID
            print("Retrieving Service Principal object ID...")
            spn_show_command = [
                "az",
                "ad",
                "sp",
                "show",
                "--id",
                spn_data["appId"],
            ]
            spn_show_result = subprocess.run(
                spn_show_command, capture_output=True, text=True
            )

            if spn_show_result.returncode != 0:
                print("Failed to retrieve service principal object ID.")
                print(spn_show_result.stderr)
                return None

            try:
                spn_show_data = json.loads(spn_show_result.stdout)
                spn_object_id = spn_show_data["id"]
            except json.JSONDecodeError:
                print("Failed to decode JSON from the output.")
                print(spn_show_result.stdout)
                return None

            spn_data["object_id"] = spn_object_id

            # Return the service principal data
            return spn_data
        except Exception as e:
            print(f"Error creating service principal: {e}")
            return None

    def assign_role(
        self, app_id: str, subscription_id: str, role: str = "User Access Administrator"
    ) -> bool:
        """
        Assign a role to a service principal.

        Args:
            app_id: Service Principal Application ID
            subscription_id: Azure Subscription ID
            role: Role to assign (default: User Access Administrator)

        Returns:
            bool: True if role was assigned successfully, False otherwise
        """
        if not self.validate_login():
            print("Not logged in to Azure. Please login first.")
            return False

        try:
            print(f"Assigning '{role}' role to service principal...")
            role_assignment_command = [
                "az",
                "role",
                "assignment",
                "create",
                "--assignee",
                app_id,
                "--role",
                role,
                "--scope",
                f"/subscriptions/{subscription_id}",
            ]
            result = subprocess.run(
                role_assignment_command, capture_output=True, text=True
            )

            if result.returncode != 0:
                print(f"Failed to assign {role} role.")
                print(result.stderr)
                return False

            print(f"Successfully assigned {role} role.")
            return True
        except Exception as e:
            print(f"Error assigning role: {e}")
            return False

    def configure_federated_identity(
        self, app_id: str, repo_name: str, environment_name: str
    ) -> bool:
        """
        Configure federated identity credential for GitHub Actions.

        Args:
            app_id: Service Principal Application ID
            repo_name: Full repository name (owner/repo)
            environment_name: GitHub environment name

        Returns:
            bool: True if federated identity was configured successfully, False otherwise
        """
        if not self.validate_login():
            print("Not logged in to Azure. Please login first.")
            return False

        try:
            print("Configuring federated identity credential...")

            # Create federated identity credential parameters
            params = {
                "name": "GitHubActions",
                "issuer": "https://token.actions.githubusercontent.com",
                "subject": f"repo:{repo_name}:environment:{environment_name}",
                "description": f"{environment_name}-deploy",
                "audiences": ["api://AzureADTokenExchange"],
            }

            # Convert parameters to JSON string for CLI command
            params_json = json.dumps(params)

            # Create federated identity credential
            federated_credential_command = [
                "az",
                "ad",
                "app",
                "federated-credential",
                "create",
                "--id",
                app_id,
                "--parameters",
                params_json,
            ]

            result = subprocess.run(
                federated_credential_command, capture_output=True, text=True
            )

            if result.returncode != 0:
                print("Failed to configure federated identity credential.")
                print(result.stderr)
                return False

            print("Federated identity credential configured successfully.")
            return True
        except Exception as e:
            print(f"Error configuring federated identity: {e}")
            return False

    def get_subscription_info(self) -> Optional[Dict[str, str]]:
        """
        Get current subscription information.

        Returns:
            Dictionary with subscription information or None if failed
        """
        if not self.validate_login():
            print("Not logged in to Azure. Please login first.")
            return None

        try:
            account_command = ["az", "account", "show"]
            result = subprocess.run(account_command, capture_output=True, text=True)

            if result.returncode != 0:
                print("Failed to retrieve subscription information.")
                print(result.stderr)
                return None

            try:
                account_data = json.loads(result.stdout)
                return {
                    "subscription_id": account_data.get("id", ""),
                    "tenant_id": account_data.get("tenantId", ""),
                    "subscription_name": account_data.get("name", ""),
                }
            except json.JSONDecodeError:
                print("Failed to decode JSON from the output.")
                print(result.stdout)
                return None
        except Exception as e:
            print(f"Error retrieving subscription information: {e}")
            return None

    def create_service_principal_workflow(
        self, subscription_id: str, spn_name: str
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Workflow to create a service principal and assign necessary roles.

        Args:
            subscription_id: Azure Subscription ID
            spn_name: Name for the new Service Principal

        Returns:
            Tuple of (SPN data dictionary, success boolean)
        """
        # Login if not already logged in
        if not self.validate_login():
            if not self.login():
                return None, False

        # Create service principal
        spn_data = self.create_service_principal(subscription_id, spn_name)
        if not spn_data:
            return None, False

        # Assign User Access Administrator role
        role_success = self.assign_role(
            spn_data["appId"], subscription_id, "User Access Administrator"
        )

        return spn_data, role_success
