"""
System configuration utilities for Brokkr discovery.

This module handles system-level configuration including EFI boot management
and power management settings.
"""

import logging
import subprocess


def configure_efi_boot(status: str) -> None:
    """
    Manage EFI boot entries for decommissioning devices.

    This function removes OS boot entries (ubuntu, debian, proxmox, iPXE Disk)
    when devices are in decommissioning status.

    Args:
        status: Device status
    """
    try:
        if status in ["decommissioning"]:
            logging.info("Device is decommissioning, managing EFI boot entries...")

            # Get current EFI boot menu
            result = subprocess.run(["efibootmgr"], capture_output=True, text=True, check=True, timeout=30)

            # Parse current menu using jc
            import jc

            current_menu = jc.parse("efibootmgr", result.stdout)
            new_menu = jc.parse("efibootmgr", result.stdout)

            # Remove specific OS boot entries
            for entry in current_menu["boot_options"]:
                display_name = entry.get("display_name", "").lower()
                if display_name in ["ubuntu", "debian", "proxmox"] or "ipxe disk" in display_name:
                    device_entry = entry["boot_option_reference"].replace("Boot", "")
                    logging.info(f"Removing EFI boot entry: {entry['display_name']} ({device_entry})")

                    command = ["efibootmgr", "-B", "-b", device_entry]
                    result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)

                    # Update menu state
                    new_menu = jc.parse("efibootmgr", result.stdout)

            # Log changes if any were made
            if current_menu != new_menu:
                logging.info("EFI boot menu changed")
                logging.info(f"Updated menu: {new_menu}")
        else:
            logging.info(f"Device status '{status}' does not require EFI boot management")

    except Exception as e:
        logging.error(f"efibootmgr failure: {str(e)}")
        # Don't raise - EFI boot management failures shouldn't stop the workflow
