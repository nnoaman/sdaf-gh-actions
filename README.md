# sdaf-gh-actions

This script helps to automate the setup of a GitHub App, repository secrets, environment, and connection to Azure for deploying SAP Deployment Automation Framework on Azure

### Prerequisites

1. **Python**: Ensure Python 3.x is installed on your machine. You can download it from [Python official website](https://www.python.org/downloads/).
2. **Azure CLI**: Ensure the Azure CLI is installed. You can download it from [Azure CLI installation guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli).

### Installation

1. **Clone the Repository**: clone the repository

    `git clone https://github.com/nnoaman/sdaf-gh-actions.git`

2. Change directory
    `cd sdaf-gh-actions`

3. **Create a Virtual Environment**: Create and activate a virtual environment.

    `python3 -m venv venv`

    On Unix/Linux/macOS (bash/zsh):

    `source venv/bin/activate`

    On Windows (Command Prompt):

    `venv\Scripts\activate.bat`

    On Windows (PowerShell):

    `venv\Scripts\Activate.ps1`

4. **Install Dependencies**: Install the required Python libraries.

    `pip install -r requirements.txt`

5. Running the Script

    `python sdaf_github_actions.py`

### To-Do Section

 1. **Error Handling and Validation**

    - Validate user inputs.
    - Ensure `private_key_path` exists before reading the file.
    - Add validation for Azure CLI command outputs and GitHub API responses.

 2. **Dynamic Workflow Handling**

 3. **Logging**

    - Use `logging` module for better debug logs and traceability.

 4. **Retry Mechanism**

    - Implement retries for transient errors (e.g., API requests, Azure CLI commands).

 5. **Azure CLI Check**

    - Verify that Azure CLI is installed before attempting to use it.

 6. **Test Cases**
