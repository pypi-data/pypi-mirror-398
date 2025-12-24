#!/usr/bin/env python3
"""
Brokkr Decommission Script - Disk Wipe Operations

This script handles disk wiping operations for decommissioning devices.
It reads configuration from environment variables.
"""

import logging
import os
import sys

# Add current and parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifecycle.src.common import update_status_and_stop
from lifecycle.src.decommission import (
    BridgeClient,
    WipeStatusTracker,
    configure_efi_boot,
    get_primary_mac,
    perform_disk_wipe,
)


def main() -> None:
    """Main function to perform disk wipe operations."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
        force=True,
    )

    logging.info("Starting Brokkr Decommission Script")

    # Get device data from environment variables
    device_id = os.getenv("DEVICE_ID", "unknown-device-id")
    job_id = os.getenv("JOB_ID", "unknown-job-id")
    device_status = os.getenv("DEVICE_STATUS", "unknown")

    # Configuration from environment variables
    bridge_url = os.getenv("BRIDGE_URL", "")
    wipe_status_output = os.getenv("WIPE_STATUS_OUTPUT", "/opt/brokkr/wipe-status.json")

    logging.info(f"Device ID: {device_id}, Job ID: {job_id}, Status: {device_status}")

    # Get MAC address for configuration functions
    mac = get_primary_mac()
    logging.info(f"Using MAC Address: {mac}")

    # Create bridge client and wipe status tracker
    bridge_client = BridgeClient(bridge_url=bridge_url)
    wipe_tracker = WipeStatusTracker(wipe_status_output)

    # Perform disk wipe
    perform_disk_wipe(device_id, device_status, bridge_client, wipe_tracker)

    # Configure system settings
    configure_efi_boot(device_status)

    # Update device status and stop allocation to force constraint re-evaluation
    logging.info("Updating status to 'inventory' and stopping allocation...")
    update_status_and_stop("inventory")


if __name__ == "__main__":
    main()
