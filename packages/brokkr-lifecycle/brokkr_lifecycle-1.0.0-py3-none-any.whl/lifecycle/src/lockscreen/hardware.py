"""
Hardware and network utilities for Brokkr scripts.

This module provides functions for retrieving hardware information,
network interfaces, MAC addresses, and BMC data.
"""

import re
import socket

import netifaces
import psutil


def get_primary_ip_address_with_cidr(family: int) -> str | None:
    """
    Get the primary IP address with CIDR notation.

    Args:
        family: Address family (socket.AF_INET or socket.AF_INET6)

    Returns:
        Primary IP address with CIDR or None if not found
    """
    import ipaddress

    for _interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == family:
                # Skip local-link IPv6 addresses and loopback addresses
                if (
                    (snic.family == socket.AF_INET6 and snic.address.startswith("fe80"))
                    or snic.address.startswith("127.")
                    or snic.address.startswith("ffff:")
                    or snic.address == "::1"
                ):
                    continue
                # For IPv4, convert the netmask to CIDR notation and return the address with it
                if snic.family == socket.AF_INET:
                    try:
                        cidr = ipaddress.IPv4Network(f"{snic.address}/{snic.netmask}", strict=False).prefixlen
                        return f"{snic.address}/{cidr}"
                    except ValueError:
                        continue
                # For IPv6, convert the netmask to a prefix length
                elif snic.family == socket.AF_INET6:
                    try:
                        netmask = ipaddress.IPv6Address(snic.netmask).exploded
                        prefix_length = sum(bin(int(x, 16)).count("1") for x in netmask.split(":"))
                        return f"{snic.address}/{prefix_length}"
                    except ValueError:
                        continue
    return None


def extract_bootif_mac_address(filepath: str) -> str | None:
    """
    Extract BOOTIF MAC address from a file (usually /proc/cmdline).

    Args:
        filepath: Path to file containing BOOTIF parameter

    Returns:
        MAC address if found, None otherwise
    """
    try:
        with open(filepath) as file:
            content = file.read()
            match = re.search(r"BOOTIF=([0-9a-fA-F:]+)", content)
            if match:
                return match.group(1)
    except FileNotFoundError:
        pass
    return None


def get_fallback_mac_address() -> str | None:
    """
    Get MAC address from the first available network interface with IP.

    Returns:
        MAC address if found, None otherwise
    """
    for interface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET not in addrs or netifaces.AF_LINK not in addrs:
            continue

        ipv4_info = addrs[netifaces.AF_INET]
        link_info = addrs[netifaces.AF_LINK]
        if ipv4_info and "addr" in ipv4_info[0] and link_info and "addr" in link_info[0]:
            ip_address = ipv4_info[0]["addr"]

            # Skip MAC addresses for common private/virtual IP patterns
            if (
                ip_address == "127.0.0.1"
                or ip_address.startswith("169.254")
                or ip_address.startswith("172.17")  # Docker networks only, not 172.16
            ):
                continue
            return link_info[0]["addr"]
    return None


def get_mac_address() -> str | None:
    """
    Get MAC address, first trying BOOTIF, then falling back to network scan.

    Returns:
        MAC address if found, None otherwise
    """
    # First, try to get the MAC from /proc/cmdline
    bootif_mac = extract_bootif_mac_address("/proc/cmdline")
    if bootif_mac:
        return bootif_mac
    # Fallback to scanning network interfaces
    return get_fallback_mac_address()
