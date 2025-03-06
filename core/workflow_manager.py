"""
Workflow manager for the SAP Azure Automation tool.
Orchestrates the automated setup process for SAP on Azure.
"""

import time
from typing import Dict, Any, Optional, List, Tuple
from .github_manager import GitHubManager
from .azure_manager import AzureManager


class WorkflowManager:
    """Manager for automation workflows"""

    def __init__(self, github_manager: GitHubManager, azure_manager: AzureManager):
        """
        Initialize the workflow manager.

        Args:
            github_manager: GitHubManager instance
            azure_manager: AzureManager instance
        """
        self.github_manager = github_manager
        self.azure_manager = azure_manager

    def setup_github_app(self, repo_name: str, app_id: str, private_key: str) -> bool:
        """
        Setup GitHub App secrets in the repository.

        Args:
            repo_name: Full repository name (owner/repo)
            app_id: GitHub App ID
            private_key: GitHub App private key

        Returns:
            bool: True if setup was successful, False otherwise
        """
        # Add GitHub App secrets to the repository
        secrets = {"APPLICATION_ID": app_id, "APPLICATION_PRIVATE_KEY": private_key}

        return self.github_manager.add_repository_secrets(repo_name, secrets)

    def create_environment(
        self, repo_name: str, environment: str, vnet_name: str, region: str
    ) -> bool:
        """
        Trigger environment creation workflow.

        Args:
            repo_name: Full repository name (owner/repo)
            environment: Environment code (e.g., "MGMT")
            vnet_name: Deployer VNet name (e.g., "DEP01")
            region: Azure region (e.g., "northeurope")

        Returns:
            bool: True if workflow was triggered successfully, False otherwise
        """
        # Prepare workflow inputs
        inputs = {
            "environment": environment,
            "region": region,
            "deployer_vnet": vnet_name,
        }

        # Trigger environment creation workflow
        return self.github_manager.trigger_workflow(
            repo_name, "create-environment.yaml", inputs
        )

    def wait_for_environment(
        self,
        repo_name: str,
        environment_prefix: str,
        timeout: int = 180,
        check_interval: int = 10,
    ) -> Optional[str]:
        """
        Wait for environment to be created.

        Args:
            repo_name: Full repository name (owner/repo)
            environment_prefix: Environment prefix to look for
            timeout: Maximum time to wait in seconds
            check_interval: Time between checks in seconds

        Returns:
            Environment name if created, None if timed out
        """
        print(
            f"Waiting for environment with prefix '{environment_prefix}' to be created..."
        )

        elapsed = 0
        while elapsed < timeout:
            # Get current environments
            environments = self.github_manager.get_environments(repo_name)

            # Check if any environment starts with the prefix
            matching_envs = [
                env for env in environments if env.startswith(environment_prefix)
            ]

            if matching_envs:
                # Return the first matching environment
                return matching_envs[0]

            # Wait before checking again
            time.sleep(check_interval)
            elapsed += check_interval
            print(f"Still waiting... ({elapsed}s elapsed)")

        print(f"Timed out waiting for environment creation after {timeout}s")
        return None

    def setup_environment_secrets(
        self,
        repo_name: str,
        environment_name: str,
        spn_data: Dict[str, Any],
        subscription_id: str,
        tenant_id: str,
        s_username: str = "",
        s_password: str = "",
    ) -> bool:
        """
        Setup secrets for the created environment.

        Args:
            repo_name: Full repository name (owner/repo)
            environment_name: GitHub environment name
            spn_data: Service Principal data
            subscription_id: Azure Subscription ID
            tenant_id: Azure Tenant ID
            s_username: Optional SAP S-User username
            s_password: Optional SAP S-User password

        Returns:
            bool: True if setup was successful, False otherwise
        """
        # Prepare environment secrets
        secrets = {
            "AZURE_CLIENT_ID": spn_data["appId"],
            "AZURE_CLIENT_SECRET": spn_data["password"],
            "AZURE_OBJECT_ID": spn_data["object_id"],
            "AZURE_SUBSCRIPTION_ID": subscription_id,
            "AZURE_TENANT_ID": tenant_id,
        }

        # Add SAP S-User credentials if provided
        if s_username and s_password:
            secrets["S_USERNAME"] = s_username
            secrets["S_PASSWORD"] = s_password

        # Add secrets to the environment
        return self.github_manager.add_environment_secrets(
            repo_name, environment_name, secrets
        )

    def setup_federated_identity(
        self, app_id: str, repo_name: str, environment_name: str
    ) -> bool:
        """
        Configure federated identity for the environment.

        Args:
            app_id: Service Principal Application ID
            repo_name: Full repository name (owner/repo)
            environment_name: GitHub environment name

        Returns:
            bool: True if setup was successful, False otherwise
        """
        return self.azure_manager.configure_federated_identity(
            app_id, repo_name, environment_name
        )

    def run_full_setup(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Run the full setup workflow.

        Args:
            config: Configuration dictionary with all required parameters

        Returns:
            Tuple of (success boolean, result dictionary)
        """
        results = {
            "github_app_setup": False,
            "azure_login": False,
            "spn_creation": False,
            "environment_creation": False,
            "environment_name": "",
            "environment_secrets": False,
            "federated_identity": False,
        }

        # Setup GitHub App
        results["github_app_setup"] = self.setup_github_app(
            config["repository_name"],
            config["github_app_id"],
            config["github_private_key"],
        )

        if not results["github_app_setup"]:
            return False, results

        # Ensure Azure login
        results["azure_login"] = self.azure_manager.validate_login()
        if not results["azure_login"]:
            results["azure_login"] = self.azure_manager.login()
            if not results["azure_login"]:
                return False, results

        # Create Azure Service Principal
        spn_data, role_success = self.azure_manager.create_service_principal_workflow(
            config["subscription_id"], config["spn_name"]
        )

        if not spn_data or not role_success:
            results["spn_creation"] = False
            return False, results

        results["spn_creation"] = True

        # Create environment
        results["environment_creation"] = self.create_environment(
            config["repository_name"],
            config["environment"],
            config["vnet_name"],
            config["region_map"],
        )

        if not results["environment_creation"]:
            return False, results

        # Wait for environment to be created
        environment_name = self.wait_for_environment(
            config["repository_name"], config["environment"]
        )

        if not environment_name:
            return False, results

        results["environment_name"] = environment_name

        # Setup environment secrets
        results["environment_secrets"] = self.setup_environment_secrets(
            config["repository_name"],
            environment_name,
            spn_data,
            config["subscription_id"],
            config["tenant_id"],
            config.get("s_username", ""),
            config.get("s_password", ""),
        )

        if not results["environment_secrets"]:
            return False, results

        # Setup federated identity
        results["federated_identity"] = self.setup_federated_identity(
            spn_data["appId"], config["repository_name"], environment_name
        )

        # Return overall success and detailed results
        overall_success = all(
            [
                results["github_app_setup"],
                results["azure_login"],
                results["spn_creation"],
                results["environment_creation"],
                results["environment_name"] != "",
                results["environment_secrets"],
                results["federated_identity"],
            ]
        )

        return overall_success, results
