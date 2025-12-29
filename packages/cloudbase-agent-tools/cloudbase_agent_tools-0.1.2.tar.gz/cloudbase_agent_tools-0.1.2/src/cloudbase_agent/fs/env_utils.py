"""Environment utilities for loading .env files

This module provides utilities to load environment variables from .env files
for testing and development purposes.
"""

import os
from pathlib import Path
from typing import Dict, Optional


def load_env_file(env_file_path: Optional[str] = None) -> Dict[str, str]:
    """Load environment variables from a .env file

    Args:
        env_file_path: Path to the .env file. If None, searches for .env in common locations:
            - Current working directory
            - Python SDK root directory
            - Project root directory (Cloudbase Agent)

    Returns:
        Dictionary of loaded environment variables

    Raises:
        FileNotFoundError: If .env file doesn't exist in any of the search locations
    """
    if env_file_path is None:
        # Search for .env in common locations
        search_paths = [
            Path.cwd() / ".env",  # Current working directory
            Path(__file__).parent.parent.parent.parent / ".env",  # Python SDK root
            Path(__file__).parent.parent.parent.parent.parent / ".env",  # Cloudbase Agent root
            Path.cwd().parent / ".env",  # Parent of current working directory (in case we're in a subdirectory)
        ]

        env_file_path = None
        for path in search_paths:
            if path.exists():
                env_file_path = str(path)
                break

        if env_file_path is None:
            raise FileNotFoundError(f"No .env file found in any of these locations: {[str(p) for p in search_paths]}")

    # Load .env file
    env_vars = {}
    try:
        with open(env_file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Parse KEY=VALUE format
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]

                    env_vars[key] = value
                else:
                    print(f"Warning: Invalid line format in {env_file_path}:{line_num}: {line}")

    except Exception as e:
        raise RuntimeError(f"Failed to load .env file {env_file_path}: {e}")

    return env_vars


def load_env_if_exists(env_file_path: Optional[str] = None) -> Dict[str, str]:
    """Load environment variables from a .env file if it exists

    Args:
        env_file_path: Path to the .env file. If None, searches for .env in common locations

    Returns:
        Dictionary of loaded environment variables. Empty dict if .env file doesn't exist
    """
    try:
        return load_env_file(env_file_path)
    except FileNotFoundError:
        return {}


def setup_env_from_file(env_file_path: Optional[str] = None, override_existing: bool = False) -> bool:
    """Load .env file and set environment variables

    Args:
        env_file_path: Path to the .env file. If None, searches for .env in common locations
        override_existing: If True, override existing environment variables.
                          If False, only set variables that don't already exist

    Returns:
        True if .env file was loaded successfully, False if .env file doesn't exist
    """
    try:
        env_vars = load_env_file(env_file_path)

        # Set environment variables
        for key, value in env_vars.items():
            if override_existing or key not in os.environ:
                os.environ[key] = value

        print(f"✓ Loaded {len(env_vars)} environment variables from .env file")
        return True

    except FileNotFoundError:
        print("⚠️  No .env file found, using existing environment variables")
        return False
    except Exception as e:
        print(f"✗ Failed to load .env file: {e}")
        return False


def get_e2b_api_key() -> Optional[str]:
    """Get E2B API key from environment variables

    Checks for the following environment variables in order:
    1. AG_KIT_SANDBOX_API_KEY
    2. E2B_API_KEY

    Returns:
        API key if found, None otherwise
    """
    return os.getenv("AG_KIT_SANDBOX_API_KEY") or os.getenv("E2B_API_KEY")


def setup_e2b_env() -> Optional[str]:
    """Setup E2B environment by loading .env file and returning API key

    Returns:
        E2B API key if available (from .env or existing env), None otherwise
    """
    # Try to load .env file
    setup_env_from_file()

    # Get API key
    api_key = get_e2b_api_key()

    if api_key:
        print(f"✓ E2B API key found: {api_key[:8]}...")
    else:
        print("⚠️  E2B API key not found in environment variables")

    return api_key
