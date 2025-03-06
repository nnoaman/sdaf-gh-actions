#!/usr/bin/env python3
"""
SAP Azure Automation Tool

A modular tool for automating the setup of SAP Deployment Automation Framework on Azure.
"""

import sys
import argparse
from pathlib import Path

from core.config_manager import ConfigManager
from ui.tui import SAPAzureAutomatorApp


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="SAP Azure Automation Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config-dir",
        help="Configuration directory",
        default=str(Path.home() / ".sap_deployment_automation"),
    )
    parser.add_argument(
        "--no-tui",
        help="Run in non-interactive mode (not implemented yet)",
        action="store_true",
    )
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()

    # Initialize configuration manager
    config_manager = ConfigManager(args.config_dir)

    # Start the TUI application
    if not args.no_tui:
        app = SAPAzureAutomatorApp(config_manager)
        app.run()
    else:
        print("Non-interactive mode not implemented yet")
        sys.exit(1)


if __name__ == "__main__":
    main()
