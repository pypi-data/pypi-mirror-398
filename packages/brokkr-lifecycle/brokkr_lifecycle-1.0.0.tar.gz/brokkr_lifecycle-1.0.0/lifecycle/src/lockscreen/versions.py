"""
Version information management for Brokkr scripts.

This module provides functions for retrieving and managing version information
for various components including bridge API and discovery tools.
"""

import logging
import os
import subprocess


def get_discovery_version() -> str:
    """
    Get discovery version by running brokkr-collector -v command.

    Returns:
        Discovery version string or "Unknown" if not available
    """
    try:
        result = subprocess.run(
            ["brokkr-collector", "-v"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout:
            # Extract version from output (usually format like "brokkr-collector version X.Y.Z")
            version_line = result.stdout.strip()
            if "version" in version_line.lower():
                # Extract just the version number
                parts = version_line.split()
                if len(parts) >= 3:
                    return parts[-1]  # Last part is usually the version
            return version_line
        else:
            return "Unknown"
    except (
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        FileNotFoundError,
    ):
        return "Unknown"
    except Exception as e:
        logging.warning(f"Failed to get discovery version: {e}")
        return "Error"


def get_bridge_api_version(file_path: str) -> str:
    """
    Read bridge API version from file saved by lifecycle script.

    Args:
        file_path: Path to bridge API version file

    Returns:
        Bridge API version string or "Unknown" if not available
    """
    try:
        if os.path.isfile(file_path):
            with open(file_path) as f:
                version = f.read().strip()
                return version if version else "Unknown"
        else:
            return "Unknown"
    except Exception as e:
        logging.warning(f"Failed to read bridge API version from {file_path}: {e}")
        return "Error"


def process_version_string(version_string: str | None) -> str:
    """
    Process version string by extracting the part after the last colon.

    Args:
        version_string: Raw version string from file

    Returns:
        Processed version string
    """
    if not version_string:
        return "Unknown"
    return version_string.split(":")[-1].strip()


def read_raw_file(path: str) -> str | None:
    """
    Read raw contents from a file.

    Args:
        path: File path to read

    Returns:
        File contents or None if not readable
    """
    try:
        with open(path) as file:
            return file.read().strip()
    except Exception:
        return None
