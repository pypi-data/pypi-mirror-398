"""
Decommission module for Brokkr Bridge Discovery Processor.

This module provides functionality for disk wiping operations and status tracking
during the decommissioning process of devices.
"""

__version__ = "1.0.0"

# Import functions that are used by decommission.py
from .bridge import BridgeClient
from .disk_operations import WipeStatusTracker, perform_disk_wipe
from .hardware import get_primary_mac
from .system_config import configure_efi_boot

__all__ = [
    "WipeStatusTracker",
    "perform_disk_wipe",
    "BridgeClient",
    "get_primary_mac",
    "configure_efi_boot",
]
