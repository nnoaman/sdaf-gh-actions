"""
Input validators for the SAP Azure Automation tool TUI.
"""

import re
from typing import Optional, Callable, Any
from pathlib import Path


def validate_not_empty(value: str) -> Optional[str]:
    """
    Validate that input is not empty.

    Args:
        value: Input string to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not value or value.strip() == "":
        return "This field cannot be empty"
    return None


def validate_max_length(max_length: int) -> Callable[[str], Optional[str]]:
    """
    Create a validator for maximum string length.

    Args:
        max_length: Maximum allowed length

    Returns:
        Validator function
    """

    def validator(value: str) -> Optional[str]:
        if len(value) > max_length:
            return f"Maximum length is {max_length} characters"
        return None

    return validator


def validate_repo_name(value: str) -> Optional[str]:
    """
    Validate GitHub repository name format (owner/repo).

    Args:
        value: Input string to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not value:
        return "Repository name cannot be empty"

    # Check for owner/repo format
    pattern = r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$"
    if not re.match(pattern, value):
        return "Repository name must be in the format 'owner/repo'"

    return None


def validate_environment_code(value: str) -> Optional[str]:
    """
    Validate environment code (max 5 characters).

    Args:
        value: Input string to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not value:
        return "Environment code cannot be empty"

    if len(value) > 5:
        return "Environment code must be at most 5 characters"

    if not value.isalnum():
        return "Environment code should only contain letters and numbers"

    return None


def validate_vnet_name(value: str) -> Optional[str]:
    """
    Validate VNet name (max 7 characters).

    Args:
        value: Input string to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not value:
        return "VNet name cannot be empty"

    if len(value) > 7:
        return "VNet name must be at most 7 characters"

    if not value.isalnum():
        return "VNet name should only contain letters and numbers"

    return None


def validate_azure_region(value: str) -> Optional[str]:
    """
    Validate Azure region name.

    Args:
        value: Input string to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not value:
        return "Azure region cannot be empty"

    # Common Azure regions (not exhaustive)
    common_regions = [
        "eastus",
        "eastus2",
        "westus",
        "westus2",
        "westus3",
        "centralus",
        "northcentralus",
        "southcentralus",
        "northeurope",
        "westeurope",
        "uksouth",
        "ukwest",
        "eastasia",
        "southeastasia",
        "japaneast",
        "japanwest",
        "australiaeast",
        "australiasoutheast",
        "centralindia",
        "southindia",
        "westindia",
        "koreacentral",
        "koreasouth",
        "canadacentral",
        "canadaeast",
        "germanywestcentral",
        "francecentral",
        "uaenorth",
        "southafricanorth",
        "brazilsouth",
        "switzerlandnorth",
        "norwayeast",
    ]

    # Convert to lowercase for case-insensitive comparison
    value_lower = value.lower()

    if value_lower not in common_regions:
        return "Please enter a valid Azure region (e.g., 'northeurope', 'westeurope')"

    return None


def validate_subscription_id(value: str) -> Optional[str]:
    """
    Validate Azure Subscription ID format.

    Args:
        value: Input string to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not value:
        return "Subscription ID cannot be empty"

    # Check for UUID format
    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    if not re.match(pattern, value, re.IGNORECASE):
        return "Subscription ID must be in GUID format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)"

    return None


def validate_tenant_id(value: str) -> Optional[str]:
    """
    Validate Azure Tenant ID format.

    Args:
        value: Input string to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not value:
        return "Tenant ID cannot be empty"

    # Check for UUID format
    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    if not re.match(pattern, value, re.IGNORECASE):
        return "Tenant ID must be in GUID format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)"

    return None


def validate_app_id(value: str) -> Optional[str]:
    """
    Validate GitHub App ID format.

    Args:
        value: Input string to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not value:
        return "App ID cannot be empty"

    if not value.isdigit():
        return "App ID should contain only digits"

    return None


def validate_file_exists(value: str) -> Optional[str]:
    """
    Validate that a file exists at the specified path.

    Args:
        value: Input string to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not value:
        return "File path cannot be empty"

    if not Path(value).is_file():
        return "File does not exist at the specified path"

    return None


def validate_token(value: str) -> Optional[str]:
    """
    Validate GitHub token format.

    Args:
        value: Input string to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not value:
        return "Token cannot be empty"

    # GitHub tokens often start with 'ghp_' for personal access tokens
    # or 'github_pat_' for fine-grained tokens
    common_prefixes = ["ghp_", "github_pat_"]

    # Check if token has minimum length and optionally starts with common prefixes
    if len(value) < 20:
        return "Token appears to be too short"

    # This is a simple validation, GitHub tokens have specific formats
    # but this is a basic sanity check
    if not any(char.isalnum() for char in value):
        return "Token must contain alphanumeric characters"

    return None
