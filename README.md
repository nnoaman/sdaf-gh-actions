# sdaf-gh-actions

This script helps to automate the setup of a GitHub App, repository secrets, environment, and connection to Azure for deploying SAP Deployment Automation Framework on Azure

### Prerequisites

1. **Python**: Ensure Python 3.x is installed on your machine. You can download it from [Python offcial website](https://www.python.org/downloads/).
2. **Azure CLI**: Ensure the Azure CLI is installed. You can download it from [Azure CLI installation guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli).

### Installation

1. **Clone the Repository**: clone the repository

    `git clone https://github.com/nnoaman/sdaf-gh-actions.git`

2. **Create a Virtual Environment**: Create and activate a virtual environment.

    `python3 -m venv venv`
    `source venv/bin/activate  # On Windows use venv\Scripts\activate`

3. **Install Dependencies**: Install the required Python libraries.

    `pip install -r requirements.txt`

4. Running the Script

    `python sdaf_github_actions.py`
