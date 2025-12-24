"""
Status file reading and parsing utilities for Brokkr scripts.

This module provides functions for reading various status files including
wipe status, collection status, and other JSON-formatted status files.
"""

import json
import logging
import os


def read_status_file(file_path: str) -> str:
    """
    Read and parse a JSON status file, returning status or 'Starting' if not available.

    Args:
        file_path: Path to the status JSON file

    Returns:
        Status string with first letter capitalized
    """
    try:
        if os.path.isfile(file_path):
            with open(file_path) as f:
                status_data = json.load(f)
                # Handle different possible status field names
                status = None
                if "wipe_status" in status_data:
                    status = status_data["wipe_status"]
                elif "status" in status_data:
                    status = status_data["status"]
                elif "collection_status" in status_data:
                    status = status_data["collection_status"]
                else:
                    return "Unknown"

                # Capitalize first letter if status is a string
                if isinstance(status, str) and status:
                    return status.capitalize()
                else:
                    return str(status).capitalize() if status else "Unknown"
        else:
            return "Starting"
    except (OSError, json.JSONDecodeError, KeyError) as e:
        logging.warning(f"Failed to read status from {file_path}: {e}")
        return "Error"
