import requests
import json
import getpass
import os
import subprocess
import time
from github import Github


def display_instructions():
    print(
        "This script helps you automate the setup of a GitHub App, repository secrets, "
        "and environment for deploying SAP Deployment Automation Framework on Azure.\n"
    )
    print("Please follow these steps before proceeding:")
    print(
        "1. **Create a repository using the Azure SAP Automation Deployer template**:"
    )
    print(
        "   Use this link: https://github.com/new?template_name=azure-sap-automation-deployer&template_owner=NSpirit7"
    )
    print(
        "2. **Create a GitHub personal access token (PAT)** with 'repo' and 'admin:repo_hook' permissions:"
    )
    print("   Generate your token here: https://github.com/settings/tokens")
    print("3. Keep your repository name (e.g., 'owner/repository') and owner ready.")
    print("4. Be prepared to generate and download a private key for the GitHub App.\n")


def get_user_input():
    """
    Collect necessary inputs from the user interactively.
    """
    input(
        "Step 1: Create a repository using the Azure SAP Automation Deployer template.\n"
        "Visit this link to create the repository: https://github.com/new?template_name=azure-sap-automation-deployer&template_owner=NSpirit7\n"
        "Please make sure to make it Public, since we are using enviroment variables.\n"
        "Press Enter after creating the repository.\n"
    )

    token = getpass.getpass(
        "Step 2: Visit this link to create the PAT: https://github.com/settings/tokens/new?scopes=repo,admin:repo_hook,workflow\n"
        "Enter your GitHub Personal Access Token (PAT): "
    ).strip()
    repo_name = input(
        "Step 3: Enter the full repository name (e.g., 'owner/repository'): "
    ).strip()
    owner = repo_name.split("/")[0]
    server_url = (
        input(
            "Step 4: Enter the GitHub server URL (default: 'https://github.com'): "
        ).strip()
        or "https://github.com"
    )

    print("\nCreating the GitHub App...\n")
    print(f"Visit the following link to create your GitHub App:")
    print(
        f"You can use the following link to create the app requirements: "
        f"{server_url}/settings/apps/new?name={owner}-sap-on-azure&description=Used%20to%20create%20environments,%20update%20and%20create%20secrets%20and%20variables%20for%20your%20SAP%20on%20Azure%20Setup."
        f"&callback=false&request_oauth_on_install=false&public=true&actions=read&administration=write&contents=write"
        f"&environments=write&issues=write&secrets=write&actions_variables=write&workflows=write&webhook_active=false&url={server_url}/{repo_name}"
    )
    input(
        "\nPress Enter after creating the GitHub App and downloading the private key."
    )

    gh_app_name = input("Enter the GitHub App name: ").strip()
    gh_app_id = input(
        "Enter the App ID (displayed in the GitHub App settings): "
    ).strip()
    private_key_path = input(
        "Enter the path to the downloaded private key file: "
    ).strip()

    # Provide the installation URL for the GitHub App
    installation_url = f"https://github.com/settings/apps/{gh_app_name}/installations"
    print(
        f"\nPlease visit the following URL and press install the GitHub App: {installation_url}"
    )
    input("Press Enter after installing the GitHub App.\n")

    while True:
        environment = input(
            "Enter the Control Plane code (e.g., 'MGMT', 'PROD', etc), max five characters: "
        ).strip()
        if len(environment) <= 5:
            break
        print(
            "Error: The Control Plane code must be a maximum of five characters. Please try again."
        )

    while True:
        vnet_name = input(
            "Enter the Deployer VNet name (e.g., 'DEP01', etc), max seven characters: "
        ).strip()
        if len(vnet_name) <= 7:
            break
        print(
            "Error: The Deployer VNet name must be a maximum of seven characters. Please try again."
        )

    region_map = input(
        "Enter Azure region to deploy the environment to. Please use the short name (e.g., 'northeurope', 'westeurope', 'eastus2', etc): "
    ).strip()

    # Azure details
    subscription_id = input("Enter your Azure Subscription ID: ").strip()
    tenant_id = input("Enter your Azure Tenant ID: ").strip()
    spn_name = input("Enter the name for the new Azure Service Principal: ").strip()

    # SAP S-User credentials
    add_suser = (
        input("\nDo you want to add SAP S-User credentials? (y/n): ").strip().lower()
    )
    s_username = ""
    s_password = ""
    if add_suser in ["y", "yes"]:
        s_username = input("Enter your SAP S-Username: ").strip()
        s_password = getpass.getpass("Enter your SAP S-User password: ").strip()

    # Read the private key
    with open(private_key_path, "r") as file:
        private_key = file.read()

    return {
        "token": token,
        "repo_name": repo_name,
        "owner": owner,
        "server_url": server_url,
        "gh_app_name": gh_app_name,
        "gh_app_id": gh_app_id,
        "private_key": private_key,
        "environment": environment,
        "vnet_name": vnet_name,
        "region_map": region_map,
        "subscription_id": subscription_id,
        "tenant_id": tenant_id,
        "spn_name": spn_name,
        "s_username": s_username,
        "s_password": s_password,
    }


def add_repository_secrets(github_client, repo_full_name, secrets):
    """
    Add secrets to the repository.
    """
    repo = github_client.get_repo(repo_full_name)
    for secret_name, secret_value in secrets.items():
        repo.create_secret(secret_name, secret_value)
        print(f"*** Secret {secret_name} added to {repo_full_name}.***")


def add_environment_secrets(github_client, repo_full_name, environment_name, secrets):
    """
    Add secrets to a specific environment in the repository.
    """
    repo = github_client.get_repo(repo_full_name)
    environment = repo.get_environment(environment_name)
    for secret_name, secret_value in secrets.items():
        environment.create_secret(secret_name, secret_value)
        print(
            f"*** Secret {secret_name} added to environment {environment_name} in {repo_full_name}.***"
        )


def azure_login():
    """
    Login to Azure using the Azure CLI.
    """
    print("\nLogging in to Azure...\n")
    login_command = ["az", "login", "--scope", "https://graph.microsoft.com//.default"]
    result = subprocess.run(login_command, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to login to Azure. Please check your credentials and try again.")
        print(result.stderr)
        exit(1)
    print("Successfully logged in to Azure.")


def create_azure_service_principal(user_data):
    """
    Create an Azure service principal and assign roles.
    """
    print("\nCreating Azure Service Principal...\n")
    spn_create_command = [
        "az",
        "ad",
        "sp",
        "create-for-rbac",
        "--name",
        user_data["spn_name"],
        "--role",
        "contributor",
        "--scopes",
        f"/subscriptions/{user_data['subscription_id']}",
        "--only-show-errors",
    ]
    result = subprocess.run(spn_create_command, capture_output=True, text=True)
    if result.returncode != 0:
        print(
            "Failed to create service principal. Please ensure you are logged in to Azure and try again."
        )
        print(result.stderr)
        return None

    try:
        spn_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(
            "Failed to decode JSON from the output. Please check the Azure CLI command output."
        )
        print(result.stdout)
        return None

    # Get the service principal object ID
    spn_show_command = [
        "az",
        "ad",
        "sp",
        "show",
        "--id",
        spn_data["appId"],
    ]
    spn_show_result = subprocess.run(spn_show_command, capture_output=True, text=True)
    if spn_show_result.returncode != 0:
        print(
            "Failed to retrieve service principal object ID. Please check the Azure CLI command output."
        )
        print(spn_show_result.stderr)
        return None

    try:
        spn_show_data = json.loads(spn_show_result.stdout)
        spn_object_id = spn_show_data["id"]
    except json.JSONDecodeError:
        print(
            "Failed to decode JSON from the output. Please check the Azure CLI command output."
        )
        print(spn_show_result.stdout)
        return None

    # Assign User Access Administrator role
    role_assignment_command = [
        "az",
        "role",
        "assignment",
        "create",
        "--assignee",
        spn_data["appId"],
        "--role",
        "User Access Administrator",
        "--scope",
        f"/subscriptions/{user_data['subscription_id']}",
    ]
    try:
        subprocess.run(role_assignment_command, check=True)
        print(
            f"Service Principal '{user_data['spn_name']}' created and roles assigned."
        )
    except subprocess.CalledProcessError as e:
        print(f"Error assigning roles to Service Principal: {e.output}")

    spn_data["object_id"] = spn_object_id
    return spn_data


def configure_federated_identity(user_data, spn_data):
    """
    Configure federated identity credential on the Microsoft Entra application.
    """
    print("\nConfiguring federated identity credential...\n")
    federated_credential_command = (
        f"az ad app federated-credential create --id {spn_data['appId']} "
        f"--parameters '{{"
        f'"name": "GitHubActions", '
        f'"issuer": "https://token.actions.githubusercontent.com", '
        f"\"subject\": \"repo:{user_data['repo_name']}:environment:{user_data['environment_name']}\", "
        f"\"description\": \"{user_data['environment_name']}-deploy\", "
        f'"audiences": ["api://AzureADTokenExchange"]'
        f"}}'"
    )
    os.system(federated_credential_command)
    print("Federated identity credential configured.")


def trigger_github_workflow(user_data, workflow_id):
    """
    Trigger a GitHub Actions workflow.
    """
    url = f"https://api.github.com/repos/{user_data['repo_name']}/actions/workflows/{workflow_id}/dispatches"
    headers = {
        "Authorization": f"token {user_data['token']}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "ref": "main",
        "inputs": {
            "environment": user_data["environment"],
            "region": user_data["region_map"],
            "deployer_vnet": user_data["vnet_name"],
        },
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 204:
        print(f"Workflow '{workflow_id}' triggered successfully.")
        time.sleep(70)
    else:
        print(f"Failed to trigger workflow '{workflow_id}': {response.status_code}")
        print(response.text)


def main():
    display_instructions()

    # Get user inputs
    user_data = get_user_input()

    # Authenticate with GitHub
    github_client = Github(user_data["token"])

    # Step 2: Add secrets to the repository
    print("\nAdding secrets to the repository...")
    secrets = {
        "APPLICATION_PRIVATE_KEY": user_data["private_key"],
        "APPLICATION_ID": user_data["gh_app_id"],
    }
    add_repository_secrets(github_client, user_data["repo_name"], secrets)

    # Ensure Azure CLI is installed and login
    azure_login()

    # Create Azure Service Principal
    spn_data = create_azure_service_principal(user_data)
    if spn_data is None:
        return

    trigger_github_workflow(user_data, "create-environment.yaml")

    # Prompt for environment name after triggering the workflow
    environment_name = input(
        f"Visit this link https://github.com/{user_data['repo_name']}/settings/environments\n"
        "Enter the environment name you just created: "
    ).strip()
    user_data["environment_name"] = environment_name

    # Add secrets to the environment
    environment_secrets = {
        "AZURE_CLIENT_ID": spn_data["appId"],
        "AZURE_CLIENT_SECRET": spn_data["password"],
        "AZURE_OBJECT_ID": spn_data["object_id"],
        "AZURE_SUBSCRIPTION_ID": user_data["subscription_id"],
        "AZURE_TENANT_ID": user_data["tenant_id"],
        "S_USERNAME": user_data["s_username"],
        "S_PASSWORD": user_data["s_password"],
    }

    add_environment_secrets(
        github_client,
        user_data["repo_name"],
        user_data["environment_name"],
        environment_secrets,
    )

    # Configure federated identity credential
    configure_federated_identity(user_data, spn_data)

    # Trigger multiple GitHub Actions workflows
    # workflows = ["create-environment.yaml"]  # Add your workflow IDs here
    # for workflow_id in workflows:


if __name__ == "__main__":
    main()
