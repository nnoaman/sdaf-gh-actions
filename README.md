# SAP Azure Automation Tool

A modular tool for automating the setup of SAP Deployment Automation Framework on Azure.

## Overview

This tool helps you streamline the process of setting up a GitHub repository with the necessary configurations to deploy SAP systems on Azure. It handles:

- GitHub App creation and configuration
- Repository secrets setup
- Azure Service Principal creation
- Environment configuration
- Federated identity credential setup

## Features

- **Text User Interface (TUI)**: Easy-to-use interactive interface
- **Modular Architecture**: Well-organized code for maintainability
- **Secure Credential Handling**: Safe storage of sensitive information
- **Step-by-Step Guidance**: Clear instructions throughout the process
- **Validation**: Input validation to prevent errors

## Prerequisites

Before using the tool, ensure you have:

1. Created a repository using the Azure SAP Automation Deployer template
   - [GitHub Template](https://github.com/new?template_name=azure-sap-automation-deployer&template_owner=NSpirit7)
2. Created a GitHub personal access token (PAT) with necessary permissions
   - [Generate Token](https://github.com/settings/tokens)
3. Access to an Azure subscription where you have Owner permissions
4. Python 3.8 or newer installed on your system

## Installation

### Using pip

```bash
pip install sdaf-gh-actions
```

### From source

```bash
git clone https://github.com/nnoaman/sdaf-gh-actions.git
cd sdaf-gh-actions
pip install -e .
```

## Usage

### Interactive Mode (TUI)

Simply run the tool to start the interactive Text User Interface:

```bash
sdaf-gh-actions
```

The TUI will guide you through the setup process step by step.

### Configuration

By default, configuration is stored in `~/.sap_deployment_automation/`. You can specify a different location:

```bash
sdaf-gh-actions --config-dir /path/to/config
```

## Development

### Project Structure

```
sdaf-gh-actions/
├── core/                     # Core functionality
│   ├── github_manager.py     # GitHub operations
│   ├── azure_manager.py      # Azure operations
│   ├── config_manager.py     # Configuration handling
│   └── workflow_manager.py   # Workflow automation
├── ui/                       # User interface
│   ├── tui.py                # Text User Interface
│   └── validators.py         # Input validation
├── utils/                    # Utilities
│   ├── logging_utils.py      # Logging utilities
└── tests/                    # Tests
```

### Development Setup

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run tests:
   ```bash
   pytest
   ```

## TODO
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
   
## License

This project is licensed under the MIT License - see the LICENSE file for details.