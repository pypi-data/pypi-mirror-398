"""
BMC (Baseboard Management Controller) utilities for Brokkr discovery.

This module provides functions for retrieving BMC information including
MAC addresses, IP addresses, and other management interface data.
"""

import logging
import os
import re
import subprocess


def read_bmc() -> dict[str, str | None]:
    """
    Collect BMC information directly using ipmitool commands.

    Returns:
        Dictionary with BMC information (mac, ipv4, ipv6) with None as a default value
    """

    # Initialize variables to defaults
    output = {
        "mac": None,
        "ipv4": None,
        "ipv6": None,
    }

    # Check for BMC device
    device_paths = ["/dev/ipmi0", "/dev/ipmi/0", "/dev/ipmidev/0"]
    if not any(os.path.exists(path) for path in device_paths):
        logging.debug("BMC: No BMC device found")
        return output

    try:
        # Get IPv4 and MAC using ipmitool lan print
        result = subprocess.run(["ipmitool", "lan", "print"], capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and result.stdout:
            ipmi_output = result.stdout

            # Extract MAC address
            mac_regex = r"MAC Address\s+:\s+((?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})"
            mac_match = re.search(mac_regex, ipmi_output)
            if mac_match:
                output["mac"] = mac_match.group(1)

            # Extract IPv4 address and convert to CIDR
            ip4_regex = r"IP Address\s+:\s+((?:[0-9]{1,3}\.){3}[0-9]{1,3})"
            netmask_regex = r"Subnet Mask\s+:\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"

            ip4_match = re.search(ip4_regex, ipmi_output)
            netmask_match = re.search(netmask_regex, ipmi_output)

            if ip4_match and netmask_match:
                ip4 = ip4_match.group(1)
                netmask = netmask_match.group(1)

                # Convert netmask to CIDR
                octets = netmask.split(".")
                binary_str = "".join([bin(int(octet))[2:].zfill(8) for octet in octets])
                cidr = binary_str.count("1")
                output["ipv4"] = f"{ip4}/{cidr}"
            elif ip4_match:
                output["ipv4"] = ip4_match.group(1)

    except (
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        FileNotFoundError,
    ) as e:
        logging.warning(f"Failed to get BMC IPv4/MAC: {e}")

    try:
        # Get IPv6 using ipmitool lan6 print
        result = subprocess.run(["ipmitool", "lan6", "print"], capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and result.stdout:
            ipmi_output = result.stdout

            # Extract IPv6 addresses
            ip6_regex = r"Address:\s+([0-9a-fA-F:]+\/\d+)"
            ipv6_addresses = re.findall(ip6_regex, ipmi_output)

            # Filter out link-local, multicast, and unspecified addresses
            ipv6_addresses = [
                addr
                for addr in ipv6_addresses
                if not addr.startswith("fe80:") and not addr.startswith("ffff:") and not addr.split("/")[0] == "::"
            ]

            if ipv6_addresses:
                output["ipv6"] = ipv6_addresses[0]

    except (
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        FileNotFoundError,
    ) as e:
        logging.warning(f"Failed to get BMC IPv6: {e}")

    # Return appropriate values or fallbacks
    return output
