"""
NetBox Device Creation Module

Creates device records in NetBox with associated network interfaces.
"""

import logging
import os
from dataclasses import dataclass

import requests

from .get_macs import NetworkInterface

logger = logging.getLogger(__name__)


@dataclass
class CreatedDevice:
    """Information about a newly created device."""

    id: str
    name: str
    status: str
    url: str


class NetBoxDeviceCreator:
    """Creates devices and interfaces in NetBox."""

    def __init__(self):
        """Initialize the device creator with NetBox credentials."""
        self.netbox_url = os.environ.get("NETBOX_URL", "").rstrip("/")
        self.netbox_token = os.environ.get("NETBOX_TOKEN", "")

        if not self.netbox_url:
            raise ValueError("NETBOX_URL environment variable is required")
        if not self.netbox_token:
            raise ValueError("NETBOX_TOKEN environment variable is required")

        self.api_url = f"{self.netbox_url}/api"
        self.headers = {
            "Authorization": f"Token {self.netbox_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info(f"Initialized NetBoxDeviceCreator for {self.netbox_url}")

    def create_device(self, interfaces: list[NetworkInterface]) -> CreatedDevice | None:
        """
        Create a device in NetBox with the provided network interfaces.

        Args:
            interfaces: List of NetworkInterface objects

        Returns:
            CreatedDevice if successful, None otherwise
        """
        logger.info("Creating device in NetBox")

        # Get required environment variables
        device_type_id = os.environ.get("NB_DISCOVERY_DEVICE_TYPE_ID")
        role_id = os.environ.get("NB_DISCOVERY_ROLE_ID")
        tenant_id = os.environ.get("NETBOX_TENANT")
        site_id = os.environ.get("NETBOX_SITE")
        location_id = os.environ.get("NETBOX_LOCATION")
        tag_ids = os.environ.get("NB_DISCOVERY_TAG_ID")
        netplan_template_id = os.environ.get("NB_NETPLAN_TEMPLATE")

        # Skip device creation if tenant, site, and location are all 0
        if tenant_id and site_id and location_id:
            tenant_int = int(tenant_id) if tenant_id else 0
            site_int = int(site_id) if site_id else 0
            location_int = int(location_id) if location_id else 0

            if tenant_int == 0 and site_int == 0 and location_int == 0:
                logger.info("Device creation skipped: NETBOX_TENANT, NETBOX_SITE, and NETBOX_LOCATION are all 0")
                return None

        # Validate required fields
        required_vars = {
            "NETBOX_DISCOVERY_DEVICE_TYPE": device_type_id,
            "NETBOX_DISCOVERY_DEVICE_ROLE": role_id,
            "NETBOX_TENANT": tenant_id,
            "NETBOX_SITE": site_id,
            "NETBOX_LOCATION": location_id,
            "NB_NETPLAN_TEMPLATE": netplan_template_id,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return None

        # Generate device name from first MAC (typically IPMI)
        primary_mac = interfaces[0].mac_address if interfaces else "unknown"
        device_name = primary_mac.replace(":", "")

        # Parse tag IDs from comma-separated string
        tag_list = []
        if tag_ids.strip():
            try:
                tag_list = [int(tag_id.strip()) for tag_id in tag_ids.split(",") if tag_id.strip()]
            except ValueError as e:
                logger.warning(f"Invalid tag IDs in NB_DISCOVERY_TAG_ID: '{tag_ids}', error: {e}")

        # Debug: Show environment variables
        logger.info("Environment variables:")
        logger.info(f"  NB_DISCOVERY_DEVICE_TYPE_ID: '{device_type_id}'")
        logger.info(f"  NB_DISCOVERY_ROLE_ID: '{role_id}'")
        logger.info(f"  NETBOX_TENANT: '{tenant_id}'")
        logger.info(f"  NETBOX_SITE: '{site_id}'")
        logger.info(f"  NETBOX_LOCATION: '{location_id}'")
        logger.info(f"  NB_DISCOVERY_TAG_ID: '{tag_ids}' -> {tag_list}")
        logger.info(f"  NB_NETPLAN_TEMPLATE: {netplan_template_id}")

        # Create device payload
        device_payload = {
            "name": device_name,
            "device_type": int(device_type_id),
            "role": int(role_id),
            "tenant": int(tenant_id),
            "site": int(site_id),
            "location": int(location_id),
            "status": "planned",
            "config_template": int(netplan_template_id),
        }

        # Add tags if provided
        if tag_list:
            device_payload["tags"] = tag_list

        logger.info(f"Device payload: {device_payload}")

        try:
            # Create device
            logger.info(f"Creating device: {device_name}")
            response = requests.post(
                f"{self.api_url}/dcim/devices/", headers=self.headers, json=device_payload, timeout=30
            )

            if response.status_code == 201:
                device_data = response.json()
                device_id = str(device_data["id"])
                device_url = device_data["url"]

                logger.info(f"Device created successfully: {device_id}")

                # Create interfaces for the device
                self._create_interfaces(device_id, interfaces)

                return CreatedDevice(id=device_id, name=device_name, status="planned", url=device_url)

            else:
                logger.error(f"Failed to create device: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            logger.error(f"Network error while creating device: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating device: {e}")
            return None

    def _create_interfaces(self, device_id: str, interfaces: list[NetworkInterface]) -> None:
        """Create network interfaces for a device."""
        logger.info(f"Creating {len(interfaces)} interfaces for device {device_id}")

        for interface in interfaces:
            if interface.name == "ipmi":
                interface.name = "IPMI"
            interface_payload = {
                "device": int(device_id),
                "name": interface.name,
                "mac_address": interface.mac_address,
                "type": "other",  # Default type
                "enabled": True,
                "mark_connected": interface.is_up,
            }

            try:
                logger.debug(f"Creating interface {interface.name}: {interface.mac_address}")
                response = requests.post(
                    f"{self.api_url}/dcim/interfaces/", headers=self.headers, json=interface_payload, timeout=30
                )

                if response.status_code == 201:
                    logger.debug(f"Interface {interface.name} created successfully")
                else:
                    logger.warning(
                        f"Failed to create interface {interface.name}: {response.status_code} - {response.text}"
                    )

            except requests.RequestException as e:
                logger.error(f"Network error creating interface {interface.name}: {e}")
            except Exception as e:
                logger.error(f"Error creating interface {interface.name}: {e}")


def create_device_in_netbox(interfaces: list[NetworkInterface]) -> CreatedDevice | None:
    """
    Convenience function to create a device in NetBox.

    Args:
        interfaces: List of NetworkInterface objects

    Returns:
        CreatedDevice if successful, None otherwise
    """
    creator = NetBoxDeviceCreator()
    return creator.create_device(interfaces)
