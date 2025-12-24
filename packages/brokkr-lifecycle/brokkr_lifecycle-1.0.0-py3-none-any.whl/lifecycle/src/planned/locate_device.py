"""
NetBox Device Locator Module

Locates device records in NetBox using MAC addresses via GraphQL API.
"""

import logging
import os
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """Device information from NetBox."""

    id: str
    status: str
    primary_ip: str | None  # IPv6 preferred, then IPv4, then None
    platform_slug: str | None
    tenant_id: str | None
    site_id: str | None
    location_id: str | None
    mac_address: str  # The MAC that found this device


class DeviceLocator:
    """Locates devices in NetBox using MAC addresses."""

    def __init__(self):
        """Initialize the device locator with NetBox credentials."""
        self.netbox_url = os.environ.get("NETBOX_URL", "").rstrip("/")
        self.netbox_token = os.environ.get("NETBOX_TOKEN", "")

        if not self.netbox_url:
            raise ValueError("NETBOX_URL environment variable is required")
        if not self.netbox_token:
            raise ValueError("NETBOX_TOKEN environment variable is required")

        self.graphql_url = f"{self.netbox_url}/graphql/"
        self.headers = {
            "Authorization": f"Token {self.netbox_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info(f"Initialized DeviceLocator for {self.netbox_url}")

    def locate_device_by_mac(self, mac_address: str) -> DeviceInfo | None:
        """
        Locate a device in NetBox using MAC address.

        Args:
            mac_address: MAC address to search for

        Returns:
            DeviceInfo if found, None otherwise
        """
        logger.info(f"Searching for device with MAC address: {mac_address}")

        graphql_query = {
            "query": """
            {
              interface_list(filters: {mac_address: "%s"}){
                device {
                  id
                  status
                  primary_ip4 {
                    display
                  }
                  primary_ip6 {
                    display
                  }
                  platform {
                    slug
                  }
                  tenant {
                    id
                  }
                  site {
                    id
                  }
                  location {
                    id
                  }
                }
              }
            }
            """
            % mac_address
        }

        try:
            response = requests.post(self.graphql_url, headers=self.headers, json=graphql_query, timeout=30)

            if response.status_code == 200:
                data = response.json()

                print(data)

                if data.get("errors"):
                    logger.error(f"GraphQL errors for MAC {mac_address}: {data['errors']}")
                    return None

                interface_list = data.get("data", {}).get("interface_list", [])

                if interface_list and len(interface_list) > 0:
                    device_data = interface_list[0]["device"]

                    primary_ip4 = device_data.get("primary_ip4")
                    primary_ip6 = device_data.get("primary_ip6")
                    platform = device_data.get("platform")
                    tenant = device_data.get("tenant")
                    site = device_data.get("site")
                    location = device_data.get("location")

                    # Determine primary IP: IPv6 first, then IPv4, then None
                    primary_ip = None
                    if primary_ip6 and primary_ip6.get("display"):
                        primary_ip = primary_ip6["display"]
                    elif primary_ip4 and primary_ip4.get("display"):
                        primary_ip = primary_ip4["display"]

                    device_info = DeviceInfo(
                        id=device_data["id"],
                        status=device_data["status"],
                        primary_ip=primary_ip,
                        platform_slug=platform["slug"] if platform else None,
                        tenant_id=tenant["id"] if tenant else None,
                        site_id=site["id"] if site else None,
                        location_id=location["id"] if location else None,
                        mac_address=mac_address,
                    )

                    logger.info(f"Found device {device_info.id} (status: {device_info.status}) for MAC {mac_address}")
                    return device_info
                else:
                    logger.debug(f"No device found for MAC address: {mac_address}")
                    return None

            else:
                logger.error(f"NetBox API request failed: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            logger.error(f"Network error while searching for MAC {mac_address}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error searching for device with MAC {mac_address}: {e}")
            return None

    def set_hostname(self, device_info: DeviceInfo) -> None:
        """
        Set the system hostname based on device information.

        Args:
            device_info: Device information from NetBox
        """
        # Get environment from VAULT_ADDR or HH_ENV
        env = os.environ.get("HH_ENV", "")
        if not env:
            # Try to extract from VAULT_ADDR
            vault_addr = os.environ.get("VAULT_ADDR", "")
            if ".dev." in vault_addr:
                env = "dev"
            elif ".stg." in vault_addr:
                env = "stg"
            elif ".prod." in vault_addr:
                env = "prod"

        if not env:
            logger.warning("Could not determine environment, skipping hostname update")
            return

        # Build hostname: host-{tenant}-{site}-{location}-{device}.{env}.hydra.host
        hostname = f"host-{device_info.tenant_id}-{device_info.site_id}-{device_info.location_id}-{device_info.id}.{env}.hydra.host"

        logger.info(f"Setting hostname to: {hostname}")

        try:
            import subprocess

            subprocess.run(["hostnamectl", "set-hostname", hostname], check=True)
            logger.info(f"✅ Hostname set successfully: {hostname}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set hostname: {e}")
        except Exception as e:
            logger.error(f"Error setting hostname: {e}")

    def find_primary_device(self, mac_addresses: list[str]) -> DeviceInfo | None:
        """
        Find the primary device from a list of MAC addresses.

        Returns the first device found, typically from IPMI MAC.

        Args:
            mac_addresses: List of MAC addresses (IPMI first)

        Returns:
            First DeviceInfo found, None if no devices found
        """
        logger.info("Searching for primary device from MAC list")

        for i, mac in enumerate(mac_addresses):
            device_info = self.locate_device_by_mac(mac)
            if device_info:
                mac_type = "IPMI" if i == 0 else "network interface"
                logger.info(f"Primary device found: {device_info.id} via {mac_type} MAC {mac}")

                # Set hostname based on device information
                self.set_hostname(device_info)

                return device_info

        logger.warning("No device found with any of the provided MAC addresses")
        return None


def locate_device(mac_addresses: list[str]) -> DeviceInfo | None:
    """
    Locate device using MAC addresses.

    Args:
        mac_addresses: List of MAC addresses (IPMI first)

    Returns:
        DeviceInfo if found, None otherwise
    """
    locator = DeviceLocator()
    return locator.find_primary_device(mac_addresses)
