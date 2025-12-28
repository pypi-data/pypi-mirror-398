"""Command-line interface for the application"""

import argparse
import sys

from .config import load_config, get_config_path


def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(
        prog="python_app_template_starter",
        description="A Python application template starter with pre-configured structure for building Python applications.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    config_path = get_config_path()
    
    if config_path and "message" in config:
        print(config["message"])
    else:
        print("No .hello.yml found in git root or home directory")


if __name__ == "__main__":
    main()
