"""
GitHub operations manager for the SAP Azure Automation tool.
Handles GitHub App setup, repository and environment secrets.
"""

import requests
from typing import Dict, Any, List, Optional
from github import Github, GithubException


class GitHubManager:
    """Manager for GitHub operations"""

    def __init__(self, token: str):
        """
        Initialize the GitHub manager.

        Args:
            token: GitHub Personal Access Token
        """
        self.token = token
        self.client = Github(token)
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def validate_connection(self) -> bool:
        """
        Validate GitHub API connection.

        Returns:
            bool: True if connection is valid, False otherwise
        """
        try:
            # Try to get user information to validate token
            user = self.client.get_user()
            return True
        except GithubException:
            return False

    def get_repository(self, repo_full_name: str):
        """
        Get repository object.

        Args:
            repo_full_name: Full repository name (owner/repo)

        Returns:
            Repository object or None if not found
        """
        try:
            return self.client.get_repo(repo_full_name)
        except GithubException as e:
            print(f"Error retrieving repository: {e}")
            return None

    def add_repository_secrets(
        self, repo_full_name: str, secrets: Dict[str, str]
    ) -> bool:
        """
        Add secrets to a repository.

        Args:
            repo_full_name: Full repository name (owner/repo)
            secrets: Dictionary of secret name/value pairs

        Returns:
            bool: True if all secrets were added successfully, False otherwise
        """
        try:
            repo = self.get_repository(repo_full_name)
            if not repo:
                return False

            success = True
            for secret_name, secret_value in secrets.items():
                try:
                    repo.create_secret(secret_name, secret_value)
                    print(f"Secret {secret_name} added to {repo_full_name}")
                except GithubException as e:
                    print(f"Error adding secret {secret_name}: {e}")
                    success = False

            return success
        except Exception as e:
            print(f"Error adding repository secrets: {e}")
            return False

    def add_environment_secrets(
        self, repo_full_name: str, environment_name: str, secrets: Dict[str, str]
    ) -> bool:
        """
        Add secrets to a specific environment in a repository.

        Args:
            repo_full_name: Full repository name (owner/repo)
            environment_name: Name of the environment
            secrets: Dictionary of secret name/value pairs

        Returns:
            bool: True if all secrets were added successfully, False otherwise
        """
        try:
            repo = self.get_repository(repo_full_name)
            if not repo:
                return False

            try:
                environment = repo.get_environment(environment_name)
            except GithubException as e:
                print(f"Error retrieving environment {environment_name}: {e}")
                return False

            success = True
            for secret_name, secret_value in secrets.items():
                try:
                    environment.create_secret(secret_name, secret_value)
                    print(
                        f"Secret {secret_name} added to environment {environment_name}"
                    )
                except GithubException as e:
                    print(f"Error adding environment secret {secret_name}: {e}")
                    success = False

            return success
        except Exception as e:
            print(f"Error adding environment secrets: {e}")
            return False

    def trigger_workflow(
        self,
        repo_full_name: str,
        workflow_id: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Trigger a GitHub Actions workflow.

        Args:
            repo_full_name: Full repository name (owner/repo)
            workflow_id: Workflow file name (e.g., "create-environment.yaml")
            inputs: Optional dictionary of workflow input parameters

        Returns:
            bool: True if workflow was triggered successfully, False otherwise
        """
        url = f"https://api.github.com/repos/{repo_full_name}/actions/workflows/{workflow_id}/dispatches"

        data = {"ref": "main"}
        if inputs:
            data["inputs"] = inputs

        try:
            response = requests.post(url, headers=self.headers, json=data)

            if response.status_code == 204:
                print(f"Workflow '{workflow_id}' triggered successfully")
                return True
            else:
                print(
                    f"Failed to trigger workflow '{workflow_id}': {response.status_code}"
                )
                print(response.text)
                return False
        except Exception as e:
            print(f"Error triggering workflow: {e}")
            return False

    def get_environments(self, repo_full_name: str) -> List[str]:
        """
        Get a list of environments for a repository.

        Args:
            repo_full_name: Full repository name (owner/repo)

        Returns:
            List of environment names or empty list if none found
        """
        try:
            repo = self.get_repository(repo_full_name)
            if not repo:
                return []

            environments = repo.get_environments()
            return [env.name for env in environments]
        except GithubException as e:
            print(f"Error retrieving environments: {e}")
            return []
