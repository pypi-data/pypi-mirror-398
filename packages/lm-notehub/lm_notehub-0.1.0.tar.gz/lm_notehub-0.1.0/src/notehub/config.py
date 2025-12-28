# config.py - Configuration Management

"""Read and write git config values for notehub settings."""

import os
import subprocess


def get_git_config(key: str, global_only: bool = False) -> str | None:
    """Retrieve git config value for notehub.{key}."""
    pass


def set_git_config(key: str, value: str, global_scope: bool = False) -> None:
    """Set git config notehub.{key} = value."""
    pass


def get_editor() -> str:
    """
    Get editor command from environment or default.

    Priority:
    1. $EDITOR environment variable
    2. 'vi' (universal default)

    Returns:
        Editor command as string
    """
    return os.environ.get('EDITOR', 'vi')
