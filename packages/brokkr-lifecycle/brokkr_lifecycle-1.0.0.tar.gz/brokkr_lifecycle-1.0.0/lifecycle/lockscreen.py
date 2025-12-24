#!/usr/bin/env python3
"""
Brokkr Lockscreen - Dynamic System Information Display

This script generates a dynamic lockscreen that displays system information,
network configuration, BMC details, and discovery status. It reads configuration
from environment variables loaded by systemd from the .env file.
"""

import hashlib
import logging

# Add current and parent directory to path for imports
import os
import socket
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifecycle.src.common import clear_console
from lifecycle.src.lockscreen import (
    get_bridge_api_version,
    get_discovery_version,
    get_mac_address,
    get_primary_ip_address_with_cidr,
    process_version_string,
    read_bmc,
    read_raw_file,
    read_status_file,
)


def get_file_checksum(file_path: str) -> str:
    """Get MD5 checksum of a file."""
    try:
        hasher = hashlib.new("md5")
        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None


def check_active_tty1_session() -> bool:
    """
    Check if there's an active user session on tty1.

    Returns:
        True if there's an active user logged into tty1, False otherwise
    """
    try:
        # Use 'who' command to check who is logged in
        result = subprocess.run(["who"], capture_output=True, text=True, check=False, timeout=5)

        if result.returncode == 0 and result.stdout:
            # Parse the output looking for tty1 sessions
            for line in result.stdout.strip().split("\n"):
                if line:
                    # who output format: username tty date time ...
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "tty1":
                        logging.info(f"Active user session detected on tty1: {parts[0]}")
                        return True

        return False

    except subprocess.TimeoutExpired:
        logging.warning("Timeout checking for active sessions, assuming no active session")
        return False
    except Exception as e:
        logging.warning(f"Error checking for active sessions: {e}, assuming no active session")
        return False


def update_lockscreen():
    """Update the lockscreen with current system information."""
    # Get the current lockscreen content and write to file
    content = get_lockscreen_content()
    generate_lockscreen_from_content(content)


def get_system_info():
    """Get kernel and architecture information."""
    try:
        # Get kernel information (equivalent to \r)
        kernel_result = subprocess.run(["uname", "-r"], capture_output=True, text=True, timeout=5)
        kernel = kernel_result.stdout.strip() if kernel_result.returncode == 0 else "Unknown"

        # Get architecture information (equivalent to \m)
        arch_result = subprocess.run(["uname", "-m"], capture_output=True, text=True, timeout=5)
        architecture = arch_result.stdout.strip() if arch_result.returncode == 0 else "Unknown"

        return kernel, architecture
    except Exception:
        return "Unknown", "Unknown"


def get_netbird_fqdn():
    """Get NetBird FQDN from netbird status --json."""
    try:
        # Get NetBird status
        result = subprocess.run(["netbird", "status", "--json"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout:
            import json

            status_data = json.loads(result.stdout)
            return status_data.get("fqdn", "Not configured")
        else:
            return "NetBird not running"
    except subprocess.TimeoutExpired:
        return "NetBird timeout"
    except json.JSONDecodeError:
        return "Invalid NetBird status"
    except FileNotFoundError:
        return "NetBird not installed"
    except Exception:
        return "NetBird error"


def get_lockscreen_content():
    """Get the current lockscreen content as a string."""
    # Configuration values - use environment variables with fallbacks
    iso_version_path = "/opt/brokkr/iso-version"
    wipe_status_path = "/opt/brokkr/wipe-status.json"
    collection_status_path = "/opt/brokkr/discovery-status.json"
    bridge_api_version_path = "/opt/brokkr/bridge-api-version"

    # Get device data from environment variables at runtime
    device_id = os.getenv("DEVICE_ID", "Unknown device ID")
    job_id = os.getenv("JOB_ID", "Unknown job ID")
    device_status = os.getenv("DEVICE_STATUS", "Unknown status")

    # Get system information
    kernel, architecture = get_system_info()
    netbird_fqdn = get_netbird_fqdn()
    primary_ipv4_with_cidr = get_primary_ip_address_with_cidr(socket.AF_INET)
    primary_ipv6_with_cidr = get_primary_ip_address_with_cidr(socket.AF_INET6)
    mac_address = get_mac_address()
    iso_version = process_version_string(read_raw_file(iso_version_path))
    current_job_id = job_id if job_id else "None"
    current_device_id = device_id if device_id else "Unknown"
    bmc_info = read_bmc()
    bmc_ipv4 = bmc_info["ipv4"] or "Not configured"
    bmc_ipv6 = bmc_info["ipv6"] or "Not configured"
    bmc_mac = bmc_info["mac"] or "Not available"
    wipe_status = read_status_file(wipe_status_path)
    collection_status = read_status_file(collection_status_path)
    discovery_version = get_discovery_version()
    bridge_api_version = get_bridge_api_version(bridge_api_version_path)

    # Generate lockscreen content
    return f"""
    ______________________________________________________________________________

        B r o k k r  L i v e  O S
    ______________________________________________________________________________

        System Information
            • Kernel             : {kernel}
            • Architecture       : {architecture}
    ______________________________________________________________________________

        Primary Network Information
            • Primary NIC MAC    : {mac_address or "Unknown"}
            • Primary IPv4       : {primary_ipv4_with_cidr or "Not configured"}
            • Primary IPv6       : {primary_ipv6_with_cidr or "Not configured"}
    ______________________________________________________________________________

        BMC Information
            • BMC MAC            : {bmc_mac}
            • BMC IPv4           : {bmc_ipv4}
            • BMC IPv6           : {bmc_ipv6}
    ______________________________________________________________________________

        Brokkr Information
            • Live OS Version    : {iso_version}
            • Discovery Version  : {discovery_version}
            • Bridge API Version : {bridge_api_version}
    ______________________________________________________________________________

        Device Information
            • Device ID          : {current_device_id}
            • Job ID             : {current_job_id}
            • Netbird FQDN       : {netbird_fqdn}
            • Status             : {device_status}

    ______________________________________________________________________________

        Collection Status        : {collection_status}
        Wipe Status              : {wipe_status}
    ______________________________________________________________________________

    """


def generate_lockscreen_from_content(content):
    """Write lockscreen content to /etc/issue and handle getty restart."""
    dest_path = "/etc/issue"
    start_checksum = get_file_checksum(dest_path)

    with open(dest_path, "w") as file:
        file.write(content)

    end_checksum = get_file_checksum(dest_path)

    if start_checksum != end_checksum:
        if not check_active_tty1_session():
            subprocess.run(
                "systemctl restart getty@tty1",
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )


def main():
    """Main function to run lockscreen updates in a loop."""
    import time

    # Get interval from environment variable
    interval = int(os.getenv("LOCKSCREEN_INTERVAL", "0"))

    # Minimal logging setup - just for errors
    logging.basicConfig(
        level=logging.WARNING,  # Only show warnings/errors
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    if interval > 0:
        print(f"🔄 Lockscreen monitoring - updates every {interval} seconds (displays only when changed)")

        last_content = ""
        while True:
            current_content = get_lockscreen_content()

            if current_content != last_content:
                clear_console()
                print(current_content, flush=True)
                last_content = current_content

                # Update actual lockscreen file
                generate_lockscreen_from_content(current_content)

            time.sleep(interval)
    else:
        update_lockscreen()


if __name__ == "__main__":
    main()
