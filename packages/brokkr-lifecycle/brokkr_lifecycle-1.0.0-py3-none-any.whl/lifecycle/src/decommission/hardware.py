"""
Hardware and network utilities for Brokkr scripts.

This module provides functions for retrieving hardware information,
network interfaces, MAC addresses, and BMC data.
"""

import socket

import psutil


def get_primary_mac() -> str | None:
    """
    Get primary MAC address for the main network interface.

    Returns:
        Primary MAC address if found, None otherwise
    """
    for interface_name, addrs in psutil.net_if_addrs().items():
        if interface_name not in ["lo", "docker0"]:
            stats = psutil.net_if_stats()[interface_name]
            if stats.isup:
                mac_address = None
                has_ip = False
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        has_ip = True
                    elif addr.family == psutil.AF_LINK:
                        mac_address = addr.address
                if has_ip and mac_address:
                    return mac_address
    return None
