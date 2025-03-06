"""
Text User Interface (TUI) for the SAP Azure Automation tool.
Built using Textual, a modern Python TUI framework.
"""

from typing import Dict, Any, List, Optional, Callable
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Button,
    Input,
    Label,
    Static,
    Checkbox,
    LoadingIndicator,
)
from textual.widget import Widget
from textual.reactive import reactive
from textual.screen import Screen
from textual.binding import Binding
from textual import events, work
from textual.css.query import NoMatches
import time
import os

from .validators import (
    validate_not_empty,
    validate_max_length,
    validate_repo_name,
    validate_environment_code,
    validate_vnet_name,
    validate_azure_region,
    validate_subscription_id,
    validate_tenant_id,
    validate_app_id,
    validate_file_exists,
    validate_token,
)


class ValidatedInput(Widget):
    """Input widget with validation"""

    def __init__(
        self,
        label: str,
        placeholder: str = "",
        validators: List[Callable[[str], Optional[str]]] = None,
        value: str = "",
        password: bool = False,
        id: Optional[str] = None,
    ):
        """
        Initialize validated input widget.

        Args:
            label: Input label
            placeholder: Placeholder text
            validators: List of validator functions
            value: Initial value
            password: Whether to mask input as password
            id: Widget identifier
        """
        super().__init__(id=id)
        self.label_text = label
        self.validators = validators or []
        self.validation_error = ""
        self.placeholder = placeholder
        self._value = value
        self.password = password

    def compose(self) -> ComposeResult:
        """Compose the input with label and validation message"""
        yield Label(self.label_text, classes="input-label")
        yield Input(
            value=self._value,
            placeholder=self.placeholder,
            password=self.password,
            id=f"{self.id}-input" if self.id else None,
        )
        yield Label(
            "", classes="validation-error", id=f"{self.id}-error" if self.id else None
        )

    @property
    def value(self) -> str:
        """Get the current input value"""
        try:
            return self.query_one(Input).value
        except NoMatches:
            return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        """Set the input value"""
        self._value = new_value
        try:
            input_widget = self.query_one(Input)
            input_widget.value = new_value
        except NoMatches:
            pass  # Widget not mounted yet

    def validate(self, value=None) -> bool:
        """
        Validate input against all validators.

        Args:
            value: Value to validate (uses self.value if None)

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.validation_error = ""

        # Use provided value or current input value
        val = value if value is not None else self.value

        for validator in self.validators:
            error = validator(val)
            if error:
                self.validation_error = error
                break

        try:
            error_label = self.query_one(f"#{self.id}-error", Label)
            error_label.update(self.validation_error)
        except NoMatches:
            pass

        return self.validation_error == ""

    def on_input_changed(self, event) -> None:
        """Handle input change events"""
        # Validate on input change if needed
        pass


class WelcomeScreen(Screen):
    """Welcome screen with instructions"""

    def compose(self) -> ComposeResult:
        """Compose welcome screen"""
        yield Header(show_clock=True)

        with Container(id="welcome-container"):
            yield Static("# SAP on Azure Automation Tool", classes="title")
            yield Static(
                "## Welcome to the SAP on Azure Automation Setup", classes="subtitle"
            )

            yield Static(
                "This tool helps you automate the setup of a GitHub App, repository secrets, "
                "and environment for deploying SAP Deployment Automation Framework on Azure.",
                classes="description",
            )

            yield Static("### Prerequisites", classes="section-title")
            yield Static(
                "Before proceeding, please ensure you have:\n\n"
                "1. Created a repository using the Azure SAP Automation Deployer template\n"
                "   [GitHub Template](https://github.com/new?template_name=azure-sap-automation-deployer&template_owner=NSpirit7)\n\n"
                "2. Created a GitHub personal access token (PAT) with 'repo' and 'admin:repo_hook' permissions\n"
                "   [Generate Token](https://github.com/settings/tokens)\n\n"
                "3. Your repository name (e.g., 'owner/repository') ready\n\n"
                "4. Access to an Azure subscription where you have Owner permissions",
                classes="instructions",
            )

            with Horizontal(classes="button-container"):
                yield Button("Get Started", id="start-button", variant="primary")
                yield Button("Exit", id="exit-button", variant="error")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if event.button.id == "start-button":
            self.app.push_screen("github-config")
        elif event.button.id == "exit-button":
            self.app.exit()


class GitHubConfigScreen(Screen):
    """GitHub configuration screen"""

    def compose(self) -> ComposeResult:
        """Compose GitHub configuration screen"""
        yield Header(show_clock=True)

        with Container(id="github-config-container"):
            yield Static("# GitHub Configuration", classes="title")

            with Vertical(id="github-form"):
                yield ValidatedInput(
                    "GitHub Personal Access Token",
                    placeholder="Enter your GitHub PAT",
                    validators=[validate_not_empty, validate_token],
                    password=True,
                    id="github-token",
                )

                yield ValidatedInput(
                    "Repository Name",
                    placeholder="owner/repository",
                    validators=[validate_not_empty, validate_repo_name],
                    id="repo-name",
                )

                yield ValidatedInput(
                    "GitHub Server URL",
                    placeholder="https://github.com",
                    value="https://github.com",
                    id="server-url",
                )

                yield Static(
                    "### GitHub App\n\n"
                    "You need to create a GitHub App before continuing. "
                    "After pressing 'Create GitHub App', you'll be provided with "
                    "instructions on how to create and configure the app.",
                    classes="instructions",
                )

                with Horizontal(classes="button-container"):
                    yield Button(
                        "Create GitHub App", id="create-app-button", variant="primary"
                    )
                    yield Button("I Already Have an App", id="have-app-button")

            with Vertical(id="github-app-form", classes="hidden"):
                yield ValidatedInput(
                    "GitHub App Name",
                    placeholder="e.g., my-org-sap-on-azure",
                    validators=[validate_not_empty],
                    id="app-name",
                )

                yield ValidatedInput(
                    "GitHub App ID",
                    placeholder="Enter the App ID from GitHub App settings",
                    validators=[validate_not_empty, validate_app_id],
                    id="app-id",
                )

                yield ValidatedInput(
                    "Private Key File Path",
                    placeholder="Path to the downloaded private key file",
                    validators=[validate_not_empty, validate_file_exists],
                    id="private-key-path",
                )

                with Horizontal(classes="button-container"):
                    yield Button("Back", id="back-button")
                    yield Button("Continue", id="continue-button", variant="primary")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize screen on mount"""
        # Load saved values if available
        config = self.app.get_config()

        try:
            token_input = self.query_one("#github-token", ValidatedInput)
            token_input.value = config.get("github_token", "")

            repo_input = self.query_one("#repo-name", ValidatedInput)
            repo_input.value = config.get("repository_name", "")

            server_input = self.query_one("#server-url", ValidatedInput)
            server_input.value = config.get("server_url", "https://github.com")

            app_name_input = self.query_one("#app-name", ValidatedInput)
            app_name_input.value = config.get("github_app_name", "")

            app_id_input = self.query_one("#app-id", ValidatedInput)
            app_id_input.value = config.get("github_app_id", "")
        except NoMatches:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if event.button.id == "create-app-button":
            # Validate inputs
            token_input = self.query_one("#github-token", ValidatedInput)
            repo_input = self.query_one("#repo-name", ValidatedInput)
            server_input = self.query_one("#server-url", ValidatedInput)

            if not (token_input.validate() and repo_input.validate()):
                return

            # Show app creation instructions
            self.show_app_creation_dialog(
                server_url=server_input.value, repo_name=repo_input.value
            )

        elif event.button.id == "have-app-button":
            # Show GitHub App form
            try:
                self.query_one("#github-form").add_class("hidden")
                self.query_one("#github-app-form").remove_class("hidden")
            except NoMatches:
                pass

        elif event.button.id == "back-button":
            # Show GitHub form again
            try:
                self.query_one("#github-app-form").add_class("hidden")
                self.query_one("#github-form").remove_class("hidden")
            except NoMatches:
                pass

        elif event.button.id == "continue-button":
            # Validate all inputs
            all_inputs = self.query(ValidatedInput)
            all_valid = True

            for input_widget in all_inputs:
                if not input_widget.validate():
                    all_valid = False

            if not all_valid:
                return

            # Save configuration
            self.save_github_config()

            # Navigate to Azure configuration screen
            self.app.push_screen("azure-config")

    def show_app_creation_dialog(self, server_url: str, repo_name: str) -> None:
        """Show GitHub App creation instructions dialog"""
        # Prepare app creation URL with parameters
        owner = repo_name.split("/")[0]
        app_url = (
            f"{server_url}/settings/apps/new?name={owner}-sap-on-azure"
            f"&description=Used%20to%20create%20environments,%20update%20and%20create%20secrets"
            f"%20and%20variables%20for%20your%20SAP%20on%20Azure%20Setup"
            f"&callback=false&request_oauth_on_install=false&public=true"
            f"&actions=read&administration=write&contents=write"
            f"&environments=write&issues=write&secrets=write"
            f"&actions_variables=write&workflows=write"
            f"&webhook_active=false&url={server_url}/{repo_name}"
        )

        # Show GitHub App creation dialog
        class AppCreationDialog(Screen):
            BINDINGS = [Binding("escape", "close_dialog", "Close")]

            def compose(self) -> ComposeResult:
                with Container(id="app-creation-dialog"):
                    yield Static("# Create GitHub App", classes="title")

                    yield Static(
                        "Please follow these steps to create your GitHub App:\n\n"
                        "1. Click the link below to open GitHub App creation page\n"
                        "2. Fill in the required details (pre-populated in the URL)\n"
                        "3. Generate and download a private key from the App settings\n"
                        "4. Install the App on your repository\n\n"
                        "After completing these steps, come back and click 'Continue'.",
                        classes="instructions",
                    )

                    yield Static(f"## GitHub App Creation URL", classes="subtitle")
                    yield Static(app_url, classes="url")

                    if os.name == "posix":  # Unix-like
                        yield Static(
                            "\nIf you're on Linux/macOS, you can paste this command "
                            "to open the URL in your default browser:",
                            classes="hint",
                        )
                        yield Static(f"open '{app_url}'", classes="command")
                    elif os.name == "nt":  # Windows
                        yield Static(
                            "\nIf you're on Windows, you can paste this command "
                            "to open the URL in your default browser:",
                            classes="hint",
                        )
                        yield Static(f"start {app_url}", classes="command")

                    with Horizontal(classes="button-container"):
                        yield Button("Continue", id="done-button", variant="primary")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "done-button":
                    self.app.pop_screen()

                    # Show GitHub App form
                    try:
                        self.app.screen.query_one("#github-form").add_class("hidden")
                        self.app.screen.query_one("#github-app-form").remove_class(
                            "hidden"
                        )
                    except NoMatches:
                        pass

            def action_close_dialog(self) -> None:
                """Close dialog when Escape is pressed"""
                self.app.pop_screen()

        self.app.push_screen(AppCreationDialog())

    def save_github_config(self) -> None:
        """Save GitHub configuration"""
        try:
            token_input = self.query_one("#github-token", ValidatedInput)
            repo_input = self.query_one("#repo-name", ValidatedInput)
            server_input = self.query_one("#server-url", ValidatedInput)
            app_name_input = self.query_one("#app-name", ValidatedInput)
            app_id_input = self.query_one("#app-id", ValidatedInput)
            private_key_path_input = self.query_one("#private-key-path", ValidatedInput)

            # Read private key file
            private_key = ""
            try:
                with open(private_key_path_input.value, "r") as f:
                    private_key = f.read()
            except Exception as e:
                self.app.notify(
                    f"Error reading private key file: {e}", severity="error"
                )
                return

            # Save to app config
            config_updates = {
                "github_token": token_input.value,
                "repository_name": repo_input.value,
                "server_url": server_input.value,
                "github_app_name": app_name_input.value,
                "github_app_id": app_id_input.value,
                "github_private_key": private_key,
                "owner": (
                    repo_input.value.split("/")[0] if "/" in repo_input.value else ""
                ),
            }

            self.app.update_config(config_updates)
        except NoMatches:
            self.app.notify("Error saving GitHub configuration", severity="error")


class AzureConfigScreen(Screen):
    """Azure configuration screen"""

    def compose(self) -> ComposeResult:
        """Compose Azure configuration screen"""
        yield Header(show_clock=True)

        with Container(id="azure-config-container"):
            yield Static("# Azure Configuration", classes="title")

            with Vertical(id="azure-form"):
                yield Static("## Environment Settings", classes="section-title")

                yield ValidatedInput(
                    "Control Plane Code (max 5 characters)",
                    placeholder="e.g., MGMT, PROD",
                    validators=[validate_not_empty, validate_environment_code],
                    id="environment-code",
                )

                yield ValidatedInput(
                    "Deployer VNet Name (max 7 characters)",
                    placeholder="e.g., DEP01",
                    validators=[validate_not_empty, validate_vnet_name],
                    id="vnet-name",
                )

                yield ValidatedInput(
                    "Azure Region",
                    placeholder="e.g., northeurope, westeurope, eastus2",
                    validators=[validate_not_empty, validate_azure_region],
                    id="azure-region",
                )

                yield Static("## Azure Subscription", classes="section-title")

                yield ValidatedInput(
                    "Subscription ID",
                    placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    validators=[validate_not_empty, validate_subscription_id],
                    id="subscription-id",
                )

                yield ValidatedInput(
                    "Tenant ID",
                    placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    validators=[validate_not_empty, validate_tenant_id],
                    id="tenant-id",
                )

                yield ValidatedInput(
                    "Service Principal Name",
                    placeholder="Name for the new Azure Service Principal",
                    validators=[validate_not_empty],
                    id="spn-name",
                )

                yield Static(
                    "## SAP S-User Credentials (Optional)", classes="section-title"
                )

                yield Checkbox("Include SAP S-User credentials", id="include-suser")

                with Vertical(id="suser-form", classes="hidden"):
                    yield ValidatedInput(
                        "SAP S-Username",
                        placeholder="Your SAP S-Username",
                        id="s-username",
                    )

                    yield ValidatedInput(
                        "SAP S-User Password",
                        placeholder="Your SAP S-User password",
                        password=True,
                        id="s-password",
                    )

                with Horizontal(classes="button-container"):
                    yield Button("Back", id="back-button")
                    yield Button("Continue", id="continue-button", variant="primary")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize screen on mount"""
        # Load saved values if available
        config = self.app.get_config()

        try:
            env_input = self.query_one("#environment-code", ValidatedInput)
            env_input.value = config.get("environment", "")

            vnet_input = self.query_one("#vnet-name", ValidatedInput)
            vnet_input.value = config.get("vnet_name", "")

            region_input = self.query_one("#azure-region", ValidatedInput)
            region_input.value = config.get("region_map", "")

            sub_input = self.query_one("#subscription-id", ValidatedInput)
            sub_input.value = config.get("subscription_id", "")

            tenant_input = self.query_one("#tenant-id", ValidatedInput)
            tenant_input.value = config.get("tenant_id", "")

            spn_input = self.query_one("#spn-name", ValidatedInput)
            spn_input.value = config.get("spn_name", "")

            s_username_input = self.query_one("#s-username", ValidatedInput)
            s_username_input.value = config.get("s_username", "")

            s_password_input = self.query_one("#s-password", ValidatedInput)
            s_password_input.value = config.get("s_password", "")

            # Show S-User form if credentials are saved
            if config.get("s_username") or config.get("s_password"):
                include_suser = self.query_one("#include-suser", Checkbox)
                include_suser.value = True
                suser_form = self.query_one("#suser-form")
                suser_form.remove_class("hidden")
        except NoMatches:
            pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox change events"""
        if event.checkbox.id == "include-suser":
            try:
                suser_form = self.query_one("#suser-form")
                if event.checkbox.value:
                    suser_form.remove_class("hidden")
                else:
                    suser_form.add_class("hidden")
            except NoMatches:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if event.button.id == "back-button":
            self.app.pop_screen()
        elif event.button.id == "continue-button":
            # Validate inputs
            all_inputs = self.query(ValidatedInput)
            all_valid = True

            for input_widget in all_inputs:
                # Skip validation for S-User inputs if not included
                if (
                    input_widget.id in ["s-username", "s-password"]
                    and not self.query_one("#include-suser", Checkbox).value
                ):
                    continue

                if not input_widget.validate():
                    all_valid = False

            if not all_valid:
                return

            # Save configuration
            self.save_azure_config()

            # Navigate to review screen
            self.app.push_screen("review")

    def save_azure_config(self) -> None:
        """Save Azure configuration"""
        try:
            env_input = self.query_one("#environment-code", ValidatedInput)
            vnet_input = self.query_one("#vnet-name", ValidatedInput)
            region_input = self.query_one("#azure-region", ValidatedInput)
            sub_input = self.query_one("#subscription-id", ValidatedInput)
            tenant_input = self.query_one("#tenant-id", ValidatedInput)
            spn_input = self.query_one("#spn-name", ValidatedInput)

            include_suser = self.query_one("#include-suser", Checkbox)
            s_username = ""
            s_password = ""

            if include_suser.value:
                s_username_input = self.query_one("#s-username", ValidatedInput)
                s_password_input = self.query_one("#s-password", ValidatedInput)
                s_username = s_username_input.value
                s_password = s_password_input.value

            # Save to app config
            config_updates = {
                "environment": env_input.value,
                "vnet_name": vnet_input.value,
                "region_map": region_input.value,
                "subscription_id": sub_input.value,
                "tenant_id": tenant_input.value,
                "spn_name": spn_input.value,
                "s_username": s_username,
                "s_password": s_password,
            }

            self.app.update_config(config_updates)
        except NoMatches:
            self.app.notify("Error saving Azure configuration", severity="error")


class ReviewScreen(Screen):
    """Review configuration screen"""

    def compose(self) -> ComposeResult:
        """Compose review screen"""
        yield Header(show_clock=True)

        with Container(id="review-container"):
            yield Static("# Review Configuration", classes="title")

            with Vertical(id="review-form"):
                yield Static("## GitHub Configuration", classes="section-title")

                with Vertical(id="github-review"):
                    yield Static("Loading...", id="github-review-content")

                yield Static("## Azure Configuration", classes="section-title")

                with Vertical(id="azure-review"):
                    yield Static("Loading...", id="azure-review-content")

                with Horizontal(classes="button-container"):
                    yield Button("Back", id="back-button")
                    yield Button("Start Setup", id="setup-button", variant="primary")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize screen on mount"""
        self.update_review_content()

    def update_review_content(self) -> None:
        """Update review content with current configuration"""
        config = self.app.get_config()

        # GitHub review content
        github_content = f"""
Repository: {config.get('repository_name', 'N/A')}
Server URL: {config.get('server_url', 'https://github.com')}
GitHub App Name: {config.get('github_app_name', 'N/A')}
GitHub App ID: {config.get('github_app_id', 'N/A')}
Has Private Key: {'Yes' if config.get('github_private_key', '') else 'No'}
"""

        # Azure review content
        azure_content = f"""
Environment Code: {config.get('environment', 'N/A')}
VNet Name: {config.get('vnet_name', 'N/A')}
Azure Region: {config.get('region_map', 'N/A')}
Subscription ID: {config.get('subscription_id', 'N/A')}
Tenant ID: {config.get('tenant_id', 'N/A')}
Service Principal Name: {config.get('spn_name', 'N/A')}
SAP S-User Credentials: {'Included' if config.get('s_username', '') else 'Not included'}
"""

        try:
            github_review = self.query_one("#github-review-content", Static)
            github_review.update(github_content)

            azure_review = self.query_one("#azure-review-content", Static)
            azure_review.update(azure_content)
        except NoMatches:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if event.button.id == "back-button":
            self.app.pop_screen()
        elif event.button.id == "setup-button":
            # Navigate to setup screen
            self.app.push_screen("setup")


class SetupScreen(Screen):
    """Setup process screen"""

    BINDINGS = [Binding("ctrl+c", "quit", "Quit")]

    def __init__(self):
        """Initialize setup screen"""
        super().__init__()
        self.setup_tasks = [
            "setup_github_app",
            "login_azure",
            "create_service_principal",
            "create_environment",
            "setup_environment_secrets",
            "configure_federated_identity",
        ]
        self.current_task = 0
        self.task_status = {task: "pending" for task in self.setup_tasks}
        self.task_results = {}

    def compose(self) -> ComposeResult:
        """Compose setup screen"""
        yield Header(show_clock=True)

        with Container(id="setup-container"):
            yield Static("# Setting Up SAP on Azure", classes="title")

            with Vertical(id="progress-container"):
                yield LoadingIndicator(id="loading-indicator")
                yield Static("Initializing...", id="current-task")

                with Vertical(id="task-status-container"):
                    for task in self.setup_tasks:
                        task_name = task.replace("_", " ").title()
                        yield Static(f"[ ] {task_name}", id=f"task-{task}")

                yield Static("", id="task-log", classes="log")

            with Horizontal(classes="button-container", id="setup-buttons"):
                yield Button("Cancel", id="cancel-button", variant="error")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize screen on mount"""
        # Start setup process
        self.run_setup()

    @work(thread=True)
    def run_setup(self) -> None:
        """Run the setup process in a background thread"""
        self.update_task_status("Initializing setup process")

        # Get configuration
        config = self.app.get_combined_config()

        # Initialize managers from app
        github_manager = self.app.github_manager
        azure_manager = self.app.azure_manager
        workflow_manager = self.app.workflow_manager

        # Setup GitHub App
        self.update_task("setup_github_app", "running")
        self.update_task_status("Setting up GitHub App...")

        github_success = workflow_manager.setup_github_app(
            config["repository_name"],
            config["github_app_id"],
            config["github_private_key"],
        )

        if github_success:
            self.update_task("setup_github_app", "success")
            self.update_task_status("GitHub App setup completed successfully.")
        else:
            self.update_task("setup_github_app", "error")
            self.update_task_status("GitHub App setup failed.")
            self.show_setup_error("GitHub App setup failed")
            return

        # Login to Azure
        self.update_task("login_azure", "running")
        self.update_task_status("Logging in to Azure...")

        azure_login = azure_manager.validate_login()
        if not azure_login:
            azure_login = azure_manager.login()

        if azure_login:
            self.update_task("login_azure", "success")
            self.update_task_status("Azure login successful.")
        else:
            self.update_task("login_azure", "error")
            self.update_task_status("Azure login failed.")
            self.show_setup_error("Azure login failed")
            return

        # Create Service Principal
        self.update_task("create_service_principal", "running")
        self.update_task_status("Creating Azure Service Principal...")

        spn_data, role_success = azure_manager.create_service_principal_workflow(
            config["subscription_id"], config["spn_name"]
        )

        if spn_data and role_success:
            self.update_task("create_service_principal", "success")
            self.update_task_status(
                f"Service Principal '{config['spn_name']}' created successfully."
            )
            self.task_results["spn_data"] = spn_data
        else:
            self.update_task("create_service_principal", "error")
            self.update_task_status("Service Principal creation failed.")
            self.show_setup_error("Service Principal creation failed")
            return

        # Create Environment
        self.update_task("create_environment", "running")
        self.update_task_status("Creating GitHub environment...")

        env_success = workflow_manager.create_environment(
            config["repository_name"],
            config["environment"],
            config["vnet_name"],
            config["region_map"],
        )

        if env_success:
            self.update_task_status("Waiting for environment to be created...")
            environment_name = workflow_manager.wait_for_environment(
                config["repository_name"], config["environment"]
            )

            if environment_name:
                self.update_task("create_environment", "success")
                self.update_task_status(
                    f"Environment '{environment_name}' created successfully."
                )
                self.task_results["environment_name"] = environment_name
            else:
                self.update_task("create_environment", "error")
                self.update_task_status("Environment creation timed out.")
                self.show_setup_error("Environment creation timed out")
                return
        else:
            self.update_task("create_environment", "error")
            self.update_task_status("Failed to trigger environment creation workflow.")
            self.show_setup_error("Failed to trigger environment creation workflow")
            return

        # Setup Environment Secrets
        self.update_task("setup_environment_secrets", "running")
        self.update_task_status("Setting up environment secrets...")

        secrets_success = workflow_manager.setup_environment_secrets(
            config["repository_name"],
            environment_name,
            spn_data,
            config["subscription_id"],
            config["tenant_id"],
            config.get("s_username", ""),
            config.get("s_password", ""),
        )

        if secrets_success:
            self.update_task("setup_environment_secrets", "success")
            self.update_task_status("Environment secrets setup completed successfully.")
        else:
            self.update_task("setup_environment_secrets", "error")
            self.update_task_status("Environment secrets setup failed.")
            self.show_setup_error("Environment secrets setup failed")
            return

        # Configure Federated Identity
        self.update_task("configure_federated_identity", "running")
        self.update_task_status("Configuring federated identity...")

        federated_success = workflow_manager.setup_federated_identity(
            spn_data["appId"], config["repository_name"], environment_name
        )

        if federated_success:
            self.update_task("configure_federated_identity", "success")
            self.update_task_status("Federated identity configured successfully.")
        else:
            self.update_task("configure_federated_identity", "error")
            self.update_task_status("Federated identity configuration failed.")
            self.show_setup_error("Federated identity configuration failed")
            return

        # All tasks completed successfully
        self.update_task_status("Setup completed successfully!")
        self.show_setup_complete(environment_name)

    def update_task(self, task: str, status: str) -> None:
        """Update task status display"""
        self.task_status[task] = status

        status_icons = {
            "pending": "[ ]",
            "running": "[>]",
            "success": "[✓]",
            "error": "[✗]",
        }

        try:
            task_display = self.query_one(f"#task-{task}", Static)
            task_name = task.replace("_", " ").title()
            task_display.update(f"{status_icons[status]} {task_name}")

            # Update styles based on status
            for cls in ["pending", "running", "success", "error"]:
                if cls in task_display.classes:
                    task_display.remove_class(cls)
            task_display.add_class(status)

            # Update current task display
            if status == "running":
                current_task = self.query_one("#current-task", Static)
                current_task.update(f"Running: {task_name}")
        except NoMatches:
            pass

    def update_task_status(self, message: str) -> None:
        """Update task status message"""
        try:
            task_log = self.query_one("#task-log", Static)
            task_log.update(task_log.renderable + f"\n{message}")
        except NoMatches:
            pass

    def show_setup_error(self, message: str) -> None:
        """Show setup error message and completion buttons"""
        try:
            buttons = self.query_one("#setup-buttons", Horizontal)
            buttons.remove_all()
            buttons.mount(Button("Back to Review", id="back-button"))
            buttons.mount(Button("Exit", id="exit-button", variant="error"))

            header = self.query_one("Header")
            header.sub_title = "Setup Error"

            loading = self.query_one("#loading-indicator", LoadingIndicator)
            loading.display = False
        except NoMatches:
            pass

    def show_setup_complete(self, environment_name: str) -> None:
        """Show setup complete message and completion buttons"""
        try:
            buttons = self.query_one("#setup-buttons", Horizontal)
            buttons.remove_all()
            buttons.mount(Button("Exit", id="exit-button", variant="success"))

            header = self.query_one("Header")
            header.sub_title = "Setup Complete"

            loading = self.query_one("#loading-indicator", LoadingIndicator)
            loading.display = False

            # Add completion message with repository URL
            config = self.app.get_config()
            repo_url = f"{config.get('server_url', 'https://github.com')}/{config.get('repository_name', '')}"

            completion_message = f"""
## Setup Completed Successfully!

Your SAP on Azure automation environment has been set up successfully:

- Environment: {environment_name}
- Repository: {config.get('repository_name', 'N/A')}
- Azure Service Principal: {config.get('spn_name', 'N/A')}

### Next Steps

1. Visit your repository to start deploying:
   {repo_url}

2. Check the README.md file for usage instructions
"""
            task_log = self.query_one("#task-log", Static)
            task_log.update(completion_message)
        except NoMatches:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if event.button.id == "cancel-button":
            self.app.pop_screen()
        elif event.button.id == "back-button":
            self.app.pop_screen()
        elif event.button.id == "exit-button":
            self.app.exit()

    def action_quit(self) -> None:
        """Quit the application"""
        self.app.exit()


class SAPAzureAutomatorApp(App):
    """SAP Azure Automator TUI Application"""

    CSS = """
    Screen {
        background: $surface;
    }

    Container {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    .title {
        text-style: bold;
        content-align: center middle;
        margin: 1 0;
    }

    .subtitle {
        text-style: bold;
        margin: 1 0;
    }

    .section-title {
        text-style: bold;
        margin: 1 0;
    }

    .description, .instructions {
        margin: 1 0;
    }

    #welcome-container {
        margin: 2 4;
    }

    .button-container {
        margin: 2 0;
        align: right middle;
    }

    .button-container Button {
        margin: 0 1;
    }

    .input-label {
        margin-top: 1;
    }

    .validation-error {
        color: $error;
        height: 1;
    }

    .hidden {
        display: none;
    }

    .url {
        background: $surface-lighten-1;
        padding: 1;
        border: solid $primary;
        margin: 1 0;
    }

    .command {
        background: $surface-lighten-1;
        padding: 1;
        margin: 1 0;
    }

    .hint {
        color: $text-muted;
    }

    #task-status-container {
        margin: 1 0;
        height: auto;
    }

    #task-status-container Static {
        margin: 0;
    }

    #task-status-container .pending {
        color: $text-muted;
    }

    #task-status-container .running {
        color: $accent;
        text-style: bold;
    }

    #task-status-container .success {
        color: $success;
    }

    #task-status-container .error {
        color: $error;
    }

    #task-log {
        margin: 1 0;
        height: auto;
        max-height: 50vh;
        overflow-y: auto;
    }

    #current-task {
        text-style: bold;
        margin: 1 0;
    }

    #loading-indicator {
        align: center middle;
    }

    #app-creation-dialog {
        width: 90%;
        height: 80%;
        border: thick $primary;
        padding: 1;
        background: $surface;
    }
    """

    TITLE = "SAP Azure Automation Tool"
    SCREENS = {
        "welcome": WelcomeScreen,
        "github-config": GitHubConfigScreen,
        "azure-config": AzureConfigScreen,
        "review": ReviewScreen,
        "setup": SetupScreen,
    }

    def __init__(self, config_manager=None):
        """
        Initialize the application.

        Args:
            config_manager: Optional ConfigManager instance
        """
        super().__init__()
        self.config_manager = config_manager
        self.github_manager = None
        self.azure_manager = None
        self.workflow_manager = None

    def on_mount(self) -> None:
        """Initialize the app on mount"""
        # Initialize managers
        if self.config_manager:
            # Get GitHub token from config
            token = self.config_manager.credentials.get("github_token", "")
            if token:
                self.github_manager = self.create_github_manager(token)

            # Initialize Azure manager
            self.azure_manager = self.create_azure_manager()

            # Initialize workflow manager if GitHub manager exists
            if self.github_manager:
                self.workflow_manager = self.create_workflow_manager(
                    self.github_manager, self.azure_manager
                )

        # Show welcome screen
        self.push_screen("welcome")

    def create_github_manager(self, token: str):
        """Create GitHub manager instance"""
        from core.github_manager import GitHubManager

        return GitHubManager(token)

    def create_azure_manager(self):
        """Create Azure manager instance"""
        from core.azure_manager import AzureManager

        return AzureManager()

    def create_workflow_manager(self, github_manager, azure_manager):
        """Create workflow manager instance"""
        from core.workflow_manager import WorkflowManager

        return WorkflowManager(github_manager, azure_manager)

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        if self.config_manager:
            return self.config_manager.get_combined_data()
        return {}

    def get_combined_config(self) -> Dict[str, Any]:
        """Get combined configuration and credentials"""
        if self.config_manager:
            return self.config_manager.get_combined_data()
        return {}

    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """Update configuration"""
        if not self.config_manager:
            return

        # Split updates into config and credentials
        config_updates_dict = {}
        credentials_updates_dict = {}

        # List of credentials keys
        credentials_keys = [
            "github_token",
            "github_app_id",
            "github_app_name",
            "github_private_key",
            "s_username",
            "s_password",
        ]

        for key, value in config_updates.items():
            if key in credentials_keys:
                credentials_updates_dict[key] = value
            else:
                config_updates_dict[key] = value

        # Update config and credentials
        if config_updates_dict:
            self.config_manager.update_config(config_updates_dict)

        if credentials_updates_dict:
            self.config_manager.update_credentials(credentials_updates_dict)

        # If GitHub token is updated, recreate GitHub manager
        if "github_token" in credentials_updates_dict:
            token = credentials_updates_dict["github_token"]
            if token:
                self.github_manager = self.create_github_manager(token)

                # Update workflow manager if needed
                if self.github_manager and self.azure_manager:
                    self.workflow_manager = self.create_workflow_manager(
                        self.github_manager, self.azure_manager
                    )
