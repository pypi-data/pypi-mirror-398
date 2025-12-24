#!/usr/bin/env python3
"""
Planned Device Discovery Script

Collects all MAC addresses from the current machine and searches NetBox
for the corresponding device record.
"""

import logging
import os
import sys

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lifecycle.src.common.update_nomad_config import update_device_info_and_stop
from lifecycle.src.planned.create_device import create_device_in_netbox
from lifecycle.src.planned.get_macs import get_network_interfaces
from lifecycle.src.planned.locate_device import locate_device

logger = logging.getLogger(__name__)


def main():
    """Main function to collect MACs and locate device."""
    # Configure basic logging for Nomad job execution
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stdout, force=True
    )

    logger.info("Starting planned device discovery")

    try:
        # Step 1: Collect all network interfaces (with detailed info)
        logger.info("Step 1: Collecting network interfaces")
        interfaces = get_network_interfaces()
        mac_addresses = [interface.mac_address for interface in interfaces]

        if not interfaces:
            logger.error("No network interfaces found on this machine")
            return None

        logger.info(f"Found {len(interfaces)} network interfaces")
        for i, interface in enumerate(interfaces, 1):
            ipmi_marker = " (IPMI)" if interface.is_ipmi else ""
            state = "UP" if interface.is_up else "DOWN"
            logger.debug(f"Interface {i}: {interface.name} - {interface.mac_address} ({state}){ipmi_marker}")

        # Step 2: Search NetBox for existing device
        logger.info("Step 2: Searching NetBox for existing device")
        device_info = locate_device(mac_addresses)

        if device_info:
            logger.info(
                f"Device located: {device_info.id} (status: {device_info.status}, platform: {device_info.platform_slug}, found via MAC: {device_info.mac_address})"
            )

            # Step 3: Update Nomad configuration with discovered device information
            logger.info("Step 3: Updating Nomad configuration")
            try:
                update_device_info_and_stop(
                    device_id=device_info.id,
                    status="inventory",  # we switch to inventory in the nomad config but not the device record to force discovery to run
                    platform=device_info.platform_slug,
                    primary_ip=device_info.primary_ip,
                    tenant_id=device_info.tenant_id,
                    site_id=device_info.site_id,
                    location_id=device_info.location_id,
                )
                logger.info("Nomad configuration updated successfully")
            except Exception as e:
                logger.error(f"Failed to update Nomad configuration: {e}")
                return None

            return device_info
        else:
            # Step 2b: Create new device if not found
            logger.info("Step 2b: Device not found, creating new device in NetBox")
            try:
                created_device = create_device_in_netbox(interfaces)
                if not created_device:
                    logger.error("Failed to create device in NetBox")
                    return None

                logger.info(f"Device created: {created_device.id} ({created_device.name})")

                # Re-query NetBox to get the device info in the same format as locate_device
                device_info = locate_device([interfaces[0].mac_address])  # Use first MAC to find the new device
                if not device_info:
                    logger.error("Could not locate newly created device")
                    return None

                logger.info(f"Retrieved created device info: {device_info.id}")

            except Exception as e:
                logger.error(f"Failed to create device in NetBox: {e}")
                return None

    except Exception as e:
        logger.error(f"Device discovery failed: {e}")
        return None


if __name__ == "__main__":
    device = main()
    sys.exit(0 if device else 1)
