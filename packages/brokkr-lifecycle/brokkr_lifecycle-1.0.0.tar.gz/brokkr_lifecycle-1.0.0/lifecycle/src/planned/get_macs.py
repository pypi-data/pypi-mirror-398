"""
Network Interface Collection Module

Gathers network interface information including IPMI and all network interfaces,
excluding Docker interfaces.
"""

import json
import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NetworkInterface:
    """Network interface information."""

    name: str
    mac_address: str
    is_up: bool
    is_ipmi: bool = False


class MacAddressCollector:
    """Collects MAC addresses from IPMI and network interfaces."""

    def __init__(self):
        """Initialize the MAC address collector."""
        self.ipmi_mac = None
        self.interface_macs = []

    def get_ipmi_mac(self) -> str | None:
        """Get IPMI MAC address using ipmitool."""
        logger.info("Attempting to get IPMI MAC address")

        try:
            result = subprocess.run(["ipmitool", "lan", "print"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "MAC Address" in line and ":" in line:
                        # Extract MAC address from line like "MAC Address             : aa:bb:cc:dd:ee:ff"
                        mac = line.split(":", 1)[1].strip()
                        if mac and mac != "00:00:00:00:00:00":
                            logger.info(f"Found IPMI MAC address: {mac}")
                            return mac.lower()

            logger.warning("No valid IPMI MAC address found in ipmitool output")
            return None

        except subprocess.TimeoutExpired:
            logger.warning("Timeout while getting IPMI MAC address")
            return None
        except FileNotFoundError:
            logger.warning("ipmitool not found - IPMI MAC address unavailable")
            return None
        except Exception as e:
            logger.error(f"Error getting IPMI MAC address: {e}")
            return None

    def get_network_interfaces(self) -> list[NetworkInterface]:
        """Get network interface information from all physical network interfaces."""
        logger.info("Collecting network interface information")
        interfaces = []

        try:
            result = subprocess.run(["ip", "-j", "a"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                interface_data = json.loads(result.stdout)
                logger.debug(f"Found {len(interface_data)} network interfaces")

                for interface in interface_data:
                    if_name = interface.get("ifname", "unknown")
                    mac_address = interface.get("address", "").lower()

                    # Skip loopback, Docker, and invalid MACs
                    if (
                        if_name == "lo"
                        or if_name.startswith("docker")
                        or if_name.startswith("br-")
                        or if_name.startswith("veth")
                        # https://www.thomas-krenn.com/en/wiki/Virtual_network_interface_enx_of_Supermicro_Motherboards
                        or if_name.startswith("enxb")
                        or not mac_address
                        or mac_address == "00:00:00:00:00:00"
                        or ":" not in mac_address
                    ):
                        logger.debug(f"Skipping interface {if_name}: {mac_address}")
                        continue

                    # Determine if interface is up
                    state = interface.get("operstate", "unknown").lower()
                    is_up = state == "up"

                    logger.debug(f"Found interface {if_name}: {mac_address} ({state})")

                    interfaces.append(
                        NetworkInterface(
                            name=if_name,
                            mac_address=mac_address,
                            is_up=is_up,
                            is_ipmi=False,  # Will be marked later if matches IPMI MAC
                        )
                    )

            else:
                logger.error(f"ip command failed with return code {result.returncode}")

        except subprocess.TimeoutExpired:
            logger.warning("Timeout while getting network interfaces")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ip command JSON output: {e}")
        except Exception as e:
            logger.error(f"Error getting network interface MAC addresses: {e}")

        logger.info(f"Collected {len(interfaces)} network interfaces")
        return interfaces

    def collect_all_interfaces(self) -> list[NetworkInterface]:
        """
        Collect all network interfaces with IPMI first, then network interfaces.

        Returns:
            List of NetworkInterface objects with IPMI first (if available)
        """
        logger.info("Starting network interface collection")
        all_interfaces = []

        # Get IPMI MAC first
        self.ipmi_mac = self.get_ipmi_mac()

        # Get network interfaces
        network_interfaces = self.get_network_interfaces()

        # Add IPMI interface first if available
        if self.ipmi_mac:
            # Check if IPMI MAC matches any network interface
            ipmi_interface_found = False
            for interface in network_interfaces:
                if interface.mac_address == self.ipmi_mac:
                    # Mark this interface as IPMI and add it first
                    interface.is_ipmi = True
                    all_interfaces.append(interface)
                    ipmi_interface_found = True
                    break

            # If IPMI MAC doesn't match any network interface, create a virtual IPMI interface
            if not ipmi_interface_found:
                ipmi_interface = NetworkInterface(
                    name="ipmi",
                    mac_address=self.ipmi_mac,
                    is_up=True,  # Assume IPMI is functional
                    is_ipmi=True,
                )
                all_interfaces.append(ipmi_interface)

        # Add remaining network interfaces (excluding any already added IPMI interface)
        for interface in network_interfaces:
            if not interface.is_ipmi:  # Only add if not already added as IPMI
                all_interfaces.append(interface)

        logger.info(f"Collection complete: {len(all_interfaces)} total network interfaces")
        return all_interfaces

    def collect_all_macs(self) -> list[str]:
        """
        Legacy method: Collect all MAC addresses as a simple list.

        Returns:
            List of MAC addresses with IPMI first (if available)
        """
        interfaces = self.collect_all_interfaces()
        return [interface.mac_address for interface in interfaces]


def get_network_interfaces() -> list[NetworkInterface]:
    """
    Convenience function to get all network interfaces.

    Returns:
        List of NetworkInterface objects with IPMI first (if available)
    """
    collector = MacAddressCollector()
    return collector.collect_all_interfaces()


def get_mac_addresses() -> list[str]:
    """
    Legacy convenience function to get all MAC addresses as a simple list.

    Returns:
        List of MAC addresses with IPMI first (if available)
    """
    collector = MacAddressCollector()
    return collector.collect_all_macs()
