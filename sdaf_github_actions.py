import requests
import json
import getpass
import os
import subprocess
import platform
import sys
import time
import shutil
from github import Github

def run_az_command(args, capture_output=True, check=False, text=True):
    """
    Run an Azure CLI command with improved cross-platform compatibility.
    
    Args:
        args: List of arguments to pass to the az command
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise an exception on non-zero exit
        text: Whether to decode output as text
    
    Returns:
        A CompletedProcess instance with attributes:
        - args: The command arguments
        - returncode: The exit code
        - stdout: The captured stdout (if capture_output=True)
        - stderr: The captured stderr (if capture_output=True)
    """
    # Find Azure CLI executable with cross-platform support
    exe = shutil.which("az") or shutil.which("az.cmd")
    if not exe:
        raise FileNotFoundError("Azure CLI not found in PATH. Install or add to PATH.")
    
    cmd = [exe] + args
    
    # Run the command
    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, check=check, text=text)
        else:
            result = subprocess.run(cmd, check=check, text=text)
            
        return result
    except FileNotFoundError as e:
        print(f"Error: Azure CLI command not found. Make sure Azure CLI is installed and in your PATH.")
        print(f"Attempted to run: {' '.join(cmd)}")
        if check:
            raise e
        # Create a fake CompletedProcess to mimic the expected return type
        class FakeCompletedProcess:
            def __init__(self):
                self.returncode = 127  # Standard "command not found" error code
                self.args = cmd
                self.stdout = ""
                self.stderr = f"Command not found: {cmd[0]}"
        return FakeCompletedProcess()

def check_prerequisites():
    """
    Check if the necessary tools are available, particularly the Azure CLI and required Python packages.
    """
    print("\nChecking prerequisites...\n")

    # Check Azure CLI
    try:
        exe = shutil.which("az") or shutil.which("az.cmd")
        if not exe:
            raise FileNotFoundError("Azure CLI not found in PATH.")
        # Check if Azure CLI is installed and working
        print("Azure CLI found. Checking version...")
        cmd = [exe, "--version"]
        version_result = subprocess.run(cmd, capture_output=True, check=True, universal_newlines=True)
        print("Azure CLI is installed.")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Azure CLI not found. Please install it:")
        instructions = {
            "Windows": "https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows",
            "macOS"  : "https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-macos",
            "Linux"  : "https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-linux"
        }
        system = platform.system().lower()
        print(instructions.get(system, "Visit Azure CLI installation docs."))
        sys.exit(1)

    # Check Python packages
    try:
        import github
        print("Required Python packages are installed.")
    except ImportError:
        print("Missing Python dependency. Please run: pip install requests PyGithub")
        sys.exit(1)

    print(f"Running on {platform.system()} {platform.release()}")
    if platform.system().lower() == "windows":
        print("Note: On Windows, run the script with administrator privileges if needed.")
    
    # Verify Azure CLI login status but don't enforce login
    is_logged_in = verify_azure_login()
    if not is_logged_in:
        print("\nWARNING: You are not logged in to Azure CLI.")
        print("Please run 'az login' in a terminal before proceeding with Azure operations.")
        print("You can continue setting up GitHub App, but Azure operations will fail if not logged in.")
        choice = input("Do you want to continue without logging in to Azure? (y/n): ")
        if choice.lower() not in ["y", "yes"]:
            print("Exiting. Please run 'az login' and then restart this script.")
            sys.exit(1)

def display_instructions():
    print("""
        This script helps you automate the setup of a GitHub App, repository secrets,
        and environment for deploying SAP Deployment Automation Framework on Azure.

        Please follow these steps before running the script:
        1. Keep your repository name and owner ready.
        2. Be prepared to generate and download a private key for the GitHub App.
        """)

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
    gh_app_id = input("Enter the App ID (displayed in the GitHub App settings): ").strip()

    while True:
        private_key_path = input("Enter the path to the downloaded private key file: ").strip('"\'')
        normalized_path = os.path.normpath(private_key_path)
        # Read the private key
        try:
            with open(normalized_path, "r") as file:
                private_key = file.read()
            break
        except FileNotFoundError:
            print(f"Error: Could not find the private key file at: {private_key_path}")
            print("Make sure you've entered the correct file path.")
        except PermissionError:
            print(f"Error: Permission denied when trying to read: {private_key_path}")
            print("Make sure you have the necessary permissions to read this file.")
        except Exception as e:
            print(f"Error reading private key file: {str(e)}")
            print("Please check the file path and try again.")
            continue

    # Provide the installation URL for the GitHub App
    installation_url = f"https://github.com/settings/apps/{gh_app_name}/installations"
    print(
        f"\nPlease visit the following URL and press install the GitHub App: {installation_url}"
    )
    input("Press Enter after installing the GitHub App.\n")

    while True:
        environment = input("Enter the Control Plane code (e.g., 'MGMT', 'PROD', etc), max five characters: ").strip()
        if len(environment) <= 5:
            break
        print(
            "Error: The Control Plane code must be a maximum of five characters. Please try again."
        )

    while True:
        vnet_name = input("Enter the Deployer VNet name (e.g., 'DEP01', etc), max seven characters: ").strip()
        if len(vnet_name) <= 7:
            break
        print(
            "Error: The Deployer VNet name must be a maximum of seven characters. Please try again."
        )

    region_map = input(
        "Enter Azure region to deploy the environment to. Please use the short name (e.g., 'northeurope', 'westeurope', 'eastus2', etc): "
    ).strip()

    # Azure details
    # Check if the user is logged in and get subscription and tenant details
    is_logged_in = verify_azure_login()
    
    subscription_id = ""
    tenant_id = ""
    
    if is_logged_in:
        # Get the current subscription ID automatically
        print("Fetching your current Azure subscription details...")
        sub_result = run_az_command([
            "account", 
            "show", 
            "--query", 
            "id", 
            "-o", 
            "tsv"
        ], capture_output=True, text=True)
        
        if sub_result.returncode == 0 and sub_result.stdout.strip():
            subscription_id = sub_result.stdout.strip()
            print(f"Using subscription ID: {subscription_id}")
            
            # Get the tenant ID automatically
            tenant_result = run_az_command([
                "account", 
                "show", 
                "--query", 
                "tenantId", 
                "-o", 
                "tsv"
            ], capture_output=True, text=True)
            
            if tenant_result.returncode == 0 and tenant_result.stdout.strip():
                tenant_id = tenant_result.stdout.strip()
                print(f"Using tenant ID: {tenant_id}")
            else:
                print("Could not automatically detect tenant ID.")
        else:
            print("Could not automatically detect subscription ID.")
    
    # Only prompt if we couldn't get the values automatically
    if not subscription_id:
        subscription_id = input("\nEnter your Azure Subscription ID: ").strip()
    
    if not tenant_id:
        tenant_id = input("Enter your Azure Tenant ID: ").strip()

    # Ask user to choose between Service Principal and Managed Identity
    print("\nChoose authentication method for GitHub Actions:")
    print("1. Service Principal (SPN) - traditional app registration with client secret")
    print("2. User Managed Identity (MSI) - more secure, no need for secrets")
    
    auth_choice = ""
    while auth_choice not in ["1", "2"]:
        auth_choice = input("Enter your choice (1/2): ").strip()
        if auth_choice not in ["1", "2"]:
            print("Invalid choice. Please enter 1 or 2.")
    
    use_managed_identity = (auth_choice == "2")
    
    # Initialize Service Principal related variables
    use_existing_spn = False
    spn_name = ""
    spn_appid = None
    spn_password = None
    spn_object_id = None
    
    # Only proceed with Service Principal questions if that option was selected
    if not use_managed_identity:  # If Service Principal was selected
        use_existing_spn = input("\nDo you want to use an existing Service Principal? (y/n): ").strip().lower() in ['y', 'yes']
    
        if use_existing_spn:
            spn_name = input("Enter the name of your existing Service Principal: ").strip()
            spn_appid = input("Enter the Application (client) ID of your Service Principal: ").strip()
            generate_new_secret = input("Do you want to generate a new client secret? (y/n): ").strip().lower() in ['y', 'yes']
            
            if generate_new_secret:
                print("Generating a new client secret...")
                # First try to reset credential at the app level
                app_secret_args = [
                    "ad", 
                    "app", 
                    "credential", 
                    "reset",
                    "--id", 
                    spn_appid,
                    "--display-name", "rbac",
                ]
                secret_result = run_az_command(app_secret_args, capture_output=True, text=True)
                
                # If app credential reset fails, try service principal credential reset
                if secret_result.returncode != 0:
                    print("App credential reset failed, trying service principal credential reset...")
                    sp_secret_args = [
                        "ad", 
                        "sp", 
                        "credential", 
                        "reset",
                        "--id", 
                        spn_appid,
                        "--name", "rbac",
                    ]
                    secret_result = run_az_command(sp_secret_args, capture_output=True, text=True)
                
                if secret_result.returncode != 0:
                    print("Failed to generate new client secret. Please check the error and try again.")
                    print(secret_result.stderr)
                    exit(1)
                    
                try:
                    secret_data = json.loads(secret_result.stdout)
                    # Handle different JSON formats from different CLI versions/commands
                    # Some return "password" directly, others may have it nested under "credentials"
                    if "password" in secret_data:
                        spn_password = secret_data.get("password")
                    elif "credential" in secret_data:
                        spn_password = secret_data.get("credential")
                    elif "credentials" in secret_data and isinstance(secret_data["credentials"], list) and len(secret_data["credentials"]) > 0:
                        spn_password = secret_data["credentials"][0].get("password")
                    else:
                        raise ValueError("Could not find password in the response")
                        
                    if not spn_password:
                        print("Failed to get the generated client secret.")
                        exit(1)
                    print("Successfully generated a new client secret.")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Failed to decode JSON for client secret: {str(e)}")
                    print(secret_result.stdout)
                    exit(1)
            else:
                spn_password = getpass.getpass("Enter the client secret for your Service Principal: ").strip()
                
            # Get the object ID for the existing service principal
            print("Retrieving Object ID for the Service Principal...")
            spn_show_args = [
                "ad",
                "sp",
                "show",
                "--id",
                spn_appid
            ]
            spn_show_result = run_az_command(spn_show_args, capture_output=True, text=True)
            
            if spn_show_result.returncode != 0:
                print("Failed to retrieve Service Principal information.")
                print(spn_show_result.stderr)
                exit(1)
                
            try:
                spn_show_data = json.loads(spn_show_result.stdout)
                spn_object_id = spn_show_data["id"]
                print(f"Successfully retrieved Object ID: {spn_object_id}")
            except (json.JSONDecodeError, KeyError):
                print("Failed to get Object ID from Service Principal data.")
                print(spn_show_result.stdout)
                exit(1)
                
        else:
            # Only ask for SPN name if creating a new one
            spn_name = input("Enter the name for the new Azure Service Principal: ").strip()
            # Flag to indicate we need to create a new SPN
            spn_appid = None
            spn_password = None
            spn_object_id = None
    
    # SAP S-User credentials
    add_suser = input("\nDo you want to add SAP S-User credentials? (y/n): ").strip().lower()
    s_username = ""
    s_password = ""
    if add_suser in ['y', 'yes']:
        s_username = input("Enter your SAP S-Username: ").strip()
        s_password = getpass.getpass("Enter your SAP S-User password: ").strip()
    
    # Ask for resource group name only if Managed Identity is selected
    resource_group_name = ""
    if use_managed_identity:
        print("\nYou need to specify a resource group for creating the Managed Identity.")
        default_resource_group = f"{environment}-INFRASTRUCTURE-RG"
        print(f"The default resource group name would be: {default_resource_group}")
        use_default_rg = input(f"Would you like to use this default name? (y/n): ").strip().lower()
        resource_group_name = default_resource_group
        if use_default_rg not in ['y', 'yes']:
            while True:
                resource_group_name = input("Enter your desired resource group name: ").strip()
                if resource_group_name:
                    break
                print("Resource group name cannot be empty. Please enter a valid name.")

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
        "auth_choice": auth_choice,  # Add authentication choice
        "spn_name": spn_name,
        "use_existing_spn": use_existing_spn if 'use_existing_spn' in locals() else False,
        "spn_appid": spn_appid if 'spn_appid' in locals() else None,
        "spn_password": spn_password if 'spn_password' in locals() else None,
        "spn_object_id": spn_object_id if 'spn_object_id' in locals() else None,
        "s_username": s_username,
        "s_password": s_password,
        "resource_group": resource_group_name,
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
        # Skip empty values
        if secret_value is None or secret_value == "":
            print(f"Skipping secret {secret_name} because it has an empty value.")
            continue
            
        try:
            environment.create_secret(secret_name, secret_value)
            print(f"*** Secret {secret_name} added to environment {environment_name} in {repo_full_name}.***")
        except Exception as e:
            print(f"Error adding secret {secret_name}: {str(e)}")
            print("Continuing with other secrets...")


def add_environment_variables(github_client, repo_full_name, environment_name, variables):
    """
    Add variables to a specific environment in the repository.
    
    Args:
        github_client: The authenticated GitHub client
        repo_full_name: Full repository name (owner/repo)
        environment_name: Name of the GitHub environment
        variables: Dictionary of variables to add as environment variables
                  (non-sensitive information that can be visible in logs)
    """
    repo = github_client.get_repo(repo_full_name)
    environment = repo.get_environment(environment_name)
    for variable_name, variable_value in variables.items():
        # GitHub API doesn't allow empty values for variables
        if variable_value is None or variable_value == "":
            print(f"Skipping variable {variable_name} because it has an empty value.")
            continue
            
        try:
            environment.create_variable(variable_name, variable_value)
            print(
                f"*** Variable {variable_name} added to environment {environment_name} in {repo_full_name}.***"
            )
        except Exception as e:
            print(f"Error adding variable {variable_name}: {str(e)}")
            print("Continuing with other variables...")


# Azure login function removed as login is now expected to be done outside the script


def verify_azure_login():
    """
    Verify if the user is logged into Azure CLI.
    Returns True if logged in, False otherwise.
    """
    print("\nVerifying Azure CLI login status...\n")
    try:
        result = run_az_command(["account", "show", "--query", "name", "-o", "tsv"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print(f"Currently logged in to Azure account: {result.stdout.strip()}")
            return True
        else:
            print("Not logged in to Azure CLI.")
            return False
    except Exception as e:
        print(f"Error verifying Azure login: {str(e)}")
        return False

def verify_subscription(subscription_id):
    """
    Verify if the subscription exists and set it as the current subscription.
    
    Args:
        subscription_id: The Azure subscription ID
        
    Returns:
        True if subscription set successfully, False otherwise.
    """
    try:
        result = run_az_command(["account", "set", "--subscription", subscription_id], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Set subscription context to: {subscription_id}")
            return True
        else:
            print(f"Failed to set subscription context: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error verifying subscription: {str(e)}")
        return False

def verify_resource_group(resource_group, subscription_id):
    """
    Verify if the resource group exists in the specified subscription.
    
    Args:
        resource_group: The resource group name
        subscription_id: The Azure subscription ID
        
    Returns:
        True if resource group exists, False otherwise.
    """
    try:
        result = run_az_command(["group", "exists", "--name", resource_group], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip().lower() == "true":
            print(f"Resource group '{resource_group}' exists")
            return True
        else:
            print(f"Resource group '{resource_group}' does not exist in subscription '{subscription_id}'")
            return False
    except Exception as e:
        print(f"Error verifying resource group: {str(e)}")
        return False

def create_user_assigned_identity(identity_name, resource_group, subscription_id, location):
    """
    Create a user-assigned identity in Azure and assign required roles.
    
    Args:
        identity_name: Name of the user-assigned identity
        resource_group: Resource group where the identity will be created
        subscription_id: Azure subscription ID
        location: Azure region where the identity will be created
        
    Returns:
        Dictionary with identity details if successful, None otherwise.
    """
    print(f"\nCreating user-assigned identity '{identity_name}' in resource group '{resource_group}'...\n")
    
    # Define the roles to assign
    roles = [
        "Contributor",
        "Role Based Access Control Administrator",
        "Storage Blob Data Owner",
        "Key Vault Administrator",
        "App Configuration Data Owner"
    ]
    
    # Verify Azure login
    if not verify_azure_login():
        print("Please login to Azure CLI first using 'az login' before running this script")
        return None
    
    # Verify and set subscription
    if not verify_subscription(subscription_id):
        return None
    
    # Verify resource group exists
    if not verify_resource_group(resource_group, subscription_id):
        return None
    
    # Create the user-assigned identity
    try:
        identity_result = run_az_command([
            "identity", "create",
            "--name", identity_name,
            "--resource-group", resource_group,
            "--location", location,
            "--query", "{id:id, principalId:principalId, clientId:clientId}",
            "-o", "json"
        ], capture_output=True, text=True)
        
        if identity_result.returncode != 0:
            print(f"Failed to create user-assigned identity: {identity_result.stderr}")
            return None
        
        identity = json.loads(identity_result.stdout)
        print(f"Successfully created user-assigned identity '{identity_name}'")
        print(f"Identity ID: {identity['id']}")
        print(f"Principal ID: {identity['principalId']}")
        print(f"Client ID: {identity['clientId']}")
        
        # Assign roles to the identity
        role_assignments = []
        for role_name in roles:
            print(f"Assigning role {role_name} to the Managed Identity")
            role_result = run_az_command([
                "role", "assignment", "create",
                "--assignee-object-id", identity['principalId'],
                "--assignee-principal-type", "ServicePrincipal",
                "--role", role_name,
                "--scope", f"/subscriptions/{subscription_id}",
                "--query", "id",
                "--output", "tsv",
                "--only-show-errors"
            ], capture_output=True, text=True)
            
            if role_result.returncode == 0:
                print(f"Successfully assigned {role_name} role to identity")
                role_assignments.append({
                    "role": role_name,
                    "id": role_result.stdout.strip()
                })
            else:
                print(f"Warning: Failed to assign {role_name} role: {role_result.stderr}")
        
        # Return the identity details
        return {
            "name": identity_name,
            "resourceGroup": resource_group,
            "subscriptionId": subscription_id,
            "identityId": identity["id"],
            "principalId": identity["principalId"],
            "clientId": identity["clientId"],
            "roleAssignments": role_assignments
        }
    
    except Exception as e:
        print(f"An error occurred while creating the identity: {str(e)}")
        return None

def create_azure_service_principal(user_data):
    """
    Create or use an existing Azure service principal and assign roles.
    """
    # If using an existing Service Principal
    if user_data.get("use_existing_spn"):
        print(f"\nUsing existing Service Principal '{user_data['spn_name']}'...\n")
        
        # Create a data structure that matches the expected output
        spn_data = {
            "appId": user_data["spn_appid"],
            "password": user_data["spn_password"],
            "object_id": user_data["spn_object_id"]
        }
        
        # Diagnose any potential issues with the Service Principal
        success, diagnosis = diagnose_service_principal_issues(user_data["spn_appid"], user_data["subscription_id"])
        print(diagnosis)
        
        # Continue with verifying and assigning required roles
        print("Verifying and assigning required roles to the Service Principal...")
        
        # Check role assignment to avoid duplication errors
        check_role_args = [
            "role",
            "assignment",
            "list",
            "--assignee", 
            user_data["spn_appid"],
            "--role",
            "User Access Administrator",
            "--scope",
            f"/subscriptions/{user_data['subscription_id']}",
        ]
        
        check_result = run_az_command(check_role_args, capture_output=True, text=True)
        if check_result.returncode != 0:
            print("Failed to check existing role assignments.")
            print(check_result.stderr)
            return None
            
        # If role is not already assigned, assign it
        try:
            roles = json.loads(check_result.stdout)
            role_exists = len(roles) > 0
            
            if not role_exists:
                print("Assigning User Access Administrator role...")
                role_args = [
                    "role",
                    "assignment",
                    "create",
                    "--assignee",
                    user_data["spn_appid"],
                    "--role",
                    "User Access Administrator",
                    "--scope",
                    f"/subscriptions/{user_data['subscription_id']}",
                ]
                
                role_result = run_az_command(role_args, capture_output=True, text=True)
                if role_result.returncode != 0:
                    print("Failed to assign User Access Administrator role.")
                    print(role_result.stderr)
                else:
                    print("User Access Administrator role assigned successfully.")
            else:
                print("User Access Administrator role is already assigned.")
                
        except json.JSONDecodeError:
            print("Failed to parse role assignment check output.")
            print(check_result.stdout)
            
        return spn_data
        
    # If creating a new Service Principal
    else:
        print(f"\nCreating new Azure Service Principal '{user_data['spn_name']}'...\n")
        spn_create_args = [
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
        result = run_az_command(spn_create_args, capture_output=True, text=True)
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
        spn_show_args = [
            "ad",
            "sp",
            "show",
            "--id",
            spn_data["appId"],
        ]
        spn_show_result = run_az_command(spn_show_args, capture_output=True, text=True)
        if spn_show_result.returncode != 0:
            print(
                "Failed to retrieve service principal object ID. Please check the Azure CLI command output."
            )
            print(spn_show_result.stderr)
            return None

        try:
            spn_show_data = json.loads(spn_show_result.stdout)
            spn_data["object_id"] = spn_show_data["id"]
        except json.JSONDecodeError:
            print(
                "Failed to decode JSON from the output. Please check the Azure CLI command output."
            )
            print(spn_show_result.stdout)
            return None
            
        # Assign User Access Administrator role
        print("Assigning User Access Administrator role...")
        role_assignment_args = [
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
            role_result = run_az_command(role_assignment_args, capture_output=True, text=True)
            if role_result.returncode == 0:
                print(f"Service Principal '{user_data['spn_name']}' created and roles assigned successfully.")
            else:
                print(f"Warning: There may have been an issue assigning roles: {role_result.stderr}")
        except Exception as e:
            print(f"Error assigning roles to Service Principal: {str(e)}")

    return spn_data


def configure_federated_identity(user_data, spn_data):
    """
    Configure federated identity credential on the Microsoft Entra application.
    """
    print("\nConfiguring federated identity credential...\n")
    
    # Create parameters JSON for the federated credential
    parameters = {
        "name": "GitHubActions",
        "issuer": "https://token.actions.githubusercontent.com",
        "subject": f"repo:{user_data['repo_name']}:environment:{user_data['environment_name']}",
        "description": f"{user_data['environment_name']}-deploy",
        "audiences": ["api://AzureADTokenExchange"]
    }
    
    # Convert parameters to a JSON string
    parameters_json = json.dumps(parameters)
    
    # Create the federated credential
    federated_args = [
        "ad",
        "app", 
        "federated-credential", 
        "create", 
        "--id", 
        spn_data['appId'],
        "--parameters",
        parameters_json
    ]
    
    result = run_az_command(federated_args, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Federated identity credential configured successfully.")
    else:
        print("Warning: There was an issue configuring federated identity credential.")
        print(f"Error: {result.stderr}")
        print("You may need to set it up manually in the Azure portal.")


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


def diagnose_service_principal_issues(spn_appid, subscription_id):
    """
    Diagnoses common Service Principal permission and access issues.
    
    Args:
        spn_appid: The Service Principal application ID
        subscription_id: The Azure subscription ID
        
    Returns:
        A tuple of (bool, str) indicating success and diagnosis information
    """
    print("\nDiagnosing Service Principal permissions and access...\n")
    
    issues = []
    success = True
    
    # Check if the Service Principal exists
    print("Checking if Service Principal exists...")
    sp_show_args = ["ad", "sp", "show", "--id", spn_appid]
    sp_show_result = run_az_command(sp_show_args, capture_output=True, text=True)
    
    if sp_show_result.returncode != 0:
        issues.append("Service Principal does not exist or you don't have permission to access it.")
        success = False
    else:
        print("✓ Service Principal exists.")
        
        # Check subscription access
        print("Checking subscription access...")
        sub_role_args = [
            "role", 
            "assignment", 
            "list", 
            "--assignee", 
            spn_appid, 
            "--scope", 
            f"/subscriptions/{subscription_id}"
        ]
        sub_role_result = run_az_command(sub_role_args, capture_output=True, text=True)
        
        if sub_role_result.returncode != 0:
            issues.append("Error checking subscription role assignments.")
            success = False
        else:
            try:
                roles = json.loads(sub_role_result.stdout)
                if not roles:
                    issues.append(f"Service Principal has no role assignments on subscription {subscription_id}.")
                    success = False
                else:
                    role_names = [role.get("roleDefinitionName") for role in roles if "roleDefinitionName" in role]
                    print(f"✓ Service Principal has the following roles: {', '.join(role_names)}")
                    
                    # Check if it has the required roles
                    required_roles = ["Contributor", "User Access Administrator"]
                    missing_roles = [role for role in required_roles if role not in role_names]
                    
                    if missing_roles:
                        issues.append(f"Service Principal is missing the following recommended roles: {', '.join(missing_roles)}")
            except json.JSONDecodeError:
                issues.append("Unable to parse role assignments response.")
                success = False
    
    # Format the diagnosis result
    if success:
        diagnosis = "Service Principal permissions and access look good!\n"
    else:
        diagnosis = "The following issues were detected with the Service Principal:\n"
        for i, issue in enumerate(issues, 1):
            diagnosis += f"{i}. {issue}\n"
            
        diagnosis += "\nRecommendations:\n"
        diagnosis += "1. Ensure the Service Principal exists and is active.\n"
        diagnosis += "2. Make sure you have permissions to view and modify the Service Principal.\n"
        diagnosis += "3. Assign the necessary roles (Contributor, User Access Administrator) to the Service Principal.\n"
    
    return success, diagnosis

def generate_repository_secrets(user_data, app_id, private_key):
    """
    Generate repository-level secrets.
    
    Args:
        user_data: User input data dictionary
        app_id: GitHub App ID
        private_key: Private key for the GitHub App
    
    Returns:
        Dictionary with repository secrets
    """
    return {
        "APPLICATION_ID": app_id,
        "APPLICATION_PRIVATE_KEY": private_key,
    }

def get_current_subscription_info():
    """
    Gets information about the currently active Azure subscription.
    
    Returns:
        A tuple (success, subscription_id, subscription_name) where:
        - success is a boolean indicating if information was retrieved successfully
        - subscription_id is the current subscription ID or None
        - subscription_name is the current subscription name or None
    """
    print("\nRetrieving current Azure subscription information...\n")

    # Check if logged in first
    if not verify_azure_login():
        print("You need to be logged in to Azure CLI.")
        print("Please run 'az login' in a terminal before proceeding.")
        return False, None, None
    
    # Get current subscription info
    show_result = run_az_command([
        "account", 
        "show", 
        "--query", 
        "{name:name, id:id}", 
        "--output", 
        "json"
    ], capture_output=True, text=True)
    
    if show_result.returncode != 0:
        print(f"Error retrieving subscription information: {show_result.stderr}")
        return False, None, None
        
    try:
        subscription = json.loads(show_result.stdout)
        subscription_id = subscription.get("id")
        subscription_name = subscription.get("name")
        
        if subscription_id and subscription_name:
            print(f"Currently using subscription: {subscription_name} ({subscription_id})")
            return True, subscription_id, subscription_name
        else:
            print("Could not determine the current subscription.")
            return False, None, None
                
    except json.JSONDecodeError:
        print("Failed to parse subscription data.")
        print(show_result.stdout)
        return False, None, None

def main():
    """
    Main execution flow of the GitHub Repository/Environment/Secrets setup script.
    """
    display_instructions()
    check_prerequisites()

    print("\nStarting setup process...\n")
    user_data = get_user_input()
    
    # Check if user selected Managed Identity or Service Principal
    use_managed_identity = user_data.get("auth_choice", "1") == "2"
    
    # Only set up resource group if using Managed Identity
    resource_group = ""
    if use_managed_identity:
        resource_group = user_data["resource_group"]
        print(f"\nChecking if resource group {resource_group} exists...")
        if not verify_resource_group(resource_group, user_data["subscription_id"]):
            print(f"Resource group {resource_group} doesn't exist. Creating it...")
            # Location from user's region_map
            create_rg_args = [
                "group", 
                "create", 
                "--name", 
                resource_group, 
                "--location", 
                user_data["region_map"]
            ]
            rg_result = run_az_command(create_rg_args, capture_output=True, text=True)
            if rg_result.returncode != 0:
                print(f"Failed to create resource group {resource_group}:")
                print(rg_result.stderr)
                print("Cannot continue without a valid resource group. Exiting.")
                exit(1)

    print("\nCreating necessary credentials for GitHub Actions...\n")
    
    if use_managed_identity:
        # Create a User-Assigned Managed Identity
        identity_name = f"{user_data['environment']}-github-identity"
        print(f"Creating User-Assigned Managed Identity: {identity_name}")
        
        identity_data = create_user_assigned_identity(
            identity_name=identity_name,
            resource_group=resource_group,
            subscription_id=user_data["subscription_id"],
            location=user_data["region_map"]
        )
        
        if not identity_data:
            print("\nFailed to create/configure User-Assigned Managed Identity.")
            print("Cannot continue without creating the managed identity. Exiting.")
            exit(1)
    else:
        # Create or use existing Service Principal based on user input
        spn_data = create_azure_service_principal(user_data)
        if not spn_data:
            print("\nFailed to create/configure Service Principal.")
            print("Cannot continue without creating the service principal. Exiting.")
            exit(1)
    
    print("\nGenerating GitHub secrets...\n")
    
    # Enter GitHub token to add repository secrets
    github_client = Github(user_data["token"])
    
    # Get the repo client
    repo = github_client.get_repo(user_data["repo_name"])
    
    # Generate secrets for the repository
    repository_secrets = generate_repository_secrets(user_data, user_data["gh_app_id"], user_data["private_key"])
    add_repository_secrets(github_client, user_data["repo_name"], repository_secrets)
    
    # Prepare environment variables (non-sensitive information)
    environment_variables = {
        "AZURE_SUBSCRIPTION_ID": user_data["subscription_id"],
        "AZURE_TENANT_ID": user_data["tenant_id"],
        "USE_MSI": "true" if use_managed_identity else "false",
        # Add S_USERNAME with a placeholder if not provided
        "S_USERNAME": user_data["s_username"] if user_data["s_username"] else "Add SAP S Username here"
    }
    
    # Prepare environment secrets (sensitive information)
    environment_secrets = {}
    
    if use_managed_identity:
        # Set up environment variables for Managed Identity
        environment_variables.update({
            "AZURE_CLIENT_ID": identity_data["clientId"],
            "AZURE_OBJECT_ID": identity_data["principalId"],
        })
        print("Environment configuration prepared for User Managed Identity")
    else:
        # Set up environment variables and secrets for Service Principal
        environment_variables.update({
            "AZURE_CLIENT_ID": spn_data["appId"],
            "AZURE_OBJECT_ID": spn_data["object_id"],
        })
        # Add client secret to secrets (sensitive)
        environment_secrets["AZURE_CLIENT_SECRET"] = spn_data["password"]
        print("Environment configuration prepared for Service Principal (USE_MSI=false)")

    # Add SAP S-User password to secrets (sensitive), with a placeholder if not provided
    environment_secrets["S_PASSWORD"] = user_data["s_password"] if user_data["s_password"] else "Add SAP S Password here"
    
    print(
        f"\nInitial setup completed successfully!\n"
        f"Repository: {user_data['repo_name']}\n"
    )
    
    print("\nConfiguration status:")
    if use_managed_identity:
        print(f"- User-Assigned Managed Identity has been created: {identity_name}")
    else:
        print(f"- Service Principal has been created: {user_data['spn_name']}")
    
    # First trigger the environment creation workflow
    workflow_id = "create-environment.yml"
    print(f"\nTriggering workflow '{workflow_id}' to create the environment...")
    trigger_github_workflow(user_data, workflow_id)
    print("Environment creation workflow has been triggered.")
    
    # Prompt for environment name after triggering the workflow
    print("\nWait for the workflow to complete, then:")
    environment_name = input(
        f"Visit this link https://github.com/{user_data['repo_name']}/settings/environments\n"
        "Enter the environment name that was created: "
    ).strip()
    
    # Update the environment name for federated identity and secrets
    user_data["environment_name"] = environment_name
    
    # Add variables to the newly created environment (non-sensitive information)
    print(f"\nAdding variables to environment '{environment_name}'...")
    add_environment_variables(
        github_client, user_data["repo_name"], environment_name, environment_variables
    )
    
    # Add secrets to the newly created environment (sensitive information)
    if environment_secrets:
        print(f"\nAdding secrets to environment '{environment_name}'...")
        add_environment_secrets(
            github_client, user_data["repo_name"], environment_name, environment_secrets
        )
    
    # Configure federated identity if using Service Principal (after getting the environment name)
    if not use_managed_identity:
        configure_federated_identity(user_data, spn_data)
        
    print(f"\nSetup completed successfully!")
    print(f"Environment '{environment_name}' has been configured with all necessary variables and secrets.")
    print("You can now proceed with deploying your SAP environment using GitHub Actions.")
    


if __name__ == "__main__":
    main()

