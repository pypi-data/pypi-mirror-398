"""Configuration management for the application"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import yaml


def get_git_root() -> Optional[Path]:
    """Get the root directory of the current git repository.
    
    Returns:
        Path to git root if inside a git repo, None otherwise
    """
    try:
        git_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return Path(git_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def find_config_file() -> Optional[Path]:
    """Find the config file in order of precedence.
    
    Precedence:
    1. .hello.yml in current git project root (if inside a git repo)
    2. .hello.yml in home directory
    
    Returns:
        Path to config file if found, None otherwise
    """
    # Check if we're in a git project
    git_root = get_git_root()
    if git_root:
        git_config = git_root / ".hello.yml"
        if git_config.exists():
            return git_config
    
    # Check home directory
    home_config = Path.home() / ".hello.yml"
    if home_config.exists():
        return home_config
    
    return None


def load_config() -> Dict[str, Any]:
    """Load configuration from the first available config file.
    
    Returns:
        Dictionary containing config data, or empty dict if no config found
    """
    config_file = find_config_file()
    
    if not config_file:
        return {}
    
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
        return config
    except (IOError, yaml.YAMLError) as e:
        print(f"Warning: Failed to load config from {config_file}: {e}")
        return {}


def get_config_path() -> Optional[str]:
    """Get the path to the currently loaded config file.
    
    Returns:
        String path to config file or None if not found
    """
    config_file = find_config_file()
    return str(config_file) if config_file else None
