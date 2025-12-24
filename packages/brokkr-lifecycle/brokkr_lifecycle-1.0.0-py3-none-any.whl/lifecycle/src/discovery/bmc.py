import asyncio
import logging
import os
from dataclasses import dataclass

import requests

from .ipmi import IPMIService
from .vault import get_secret

logger = logging.getLogger(__name__)


@dataclass
class BmcInfo:
    netbox: object  # Not used but kept for compatibility
    device: object
    tenant: int
    site: int
    vrf: int
    bmc_data: dict = None
    associated_bridges_ids: list | None = None

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")
        logger.info(f"Entering with device {self.device}")

        self.netbox_url = os.environ.get("NETBOX_URL", "").rstrip("/")
        self.netbox_headers = {
            "Authorization": f"Token {os.environ.get('NETBOX_TOKEN', '')}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        self.interfaces = []
        self.ip_addresses = []
        self.field_data = {}
        self.netbird = None
        self.ipmi_enabled = False

    async def initialize_async(self):
        """Async initialization that should be called after __post_init__"""

        # Check if device has discovery-bmc-ip-sync tag
        if not self._has_bmc_ip_sync_tag():
            logger.info("Device does not have 'discovery-bmc-ip-sync' tag - skipping BMC IP synchronization")
            return

        await self.set_facts()
        if self.ipmi_enabled:
            self.set_interface()

    def _is_blank_mac_address(self, mac: str) -> bool:
        """Check if MAC address is blank/invalid"""
        if not mac:
            return True
        mac = mac.strip().upper()
        return mac in ["", "00:00:00:00:00:00", "00-00-00-00-00-00"]

    def _get_existing_ipmi_mac(self) -> str | None:
        """Get the MAC address from existing IPMI interface in NetBox"""
        try:
            # Find existing IPMI interface using REST API
            url = f"{self.netbox_url}/api/dcim/interfaces/"
            params = {"device_id": self.device["id"], "name": "IPMI"}
            response = requests.get(url, headers=self.netbox_headers, params=params)
            response.raise_for_status()

            data = response.json()
            for interface in data.get("results", []):
                if interface.get("mac_address"):
                    logger.info(f"Found existing IPMI MAC in NetBox: {interface['mac_address']}")
                    return str(interface["mac_address"])
            logger.warning("No existing IPMI interface found in NetBox with MAC address")
            return None
        except Exception as e:
            logger.error(f"Error retrieving existing IPMI MAC from NetBox: {e}")
            return None

    async def _perform_ipmi_hard_reset(self, ipmi_mac: str) -> bool:
        """Perform IPMI hard reset using existing IPMI MAC"""
        try:
            logger.warning(f"Attempting IPMI hard reset for MAC: {ipmi_mac}")

            # Get BMC credentials
            secret_path = f"{self.tenant['id']}/{self.site['id']}/{self.device['location']['id']}/marketplace-hosts/{self.device['id']}/bmc"
            bmc_creds = await get_secret(path=secret_path, mount_point="brokkr")

            if not bmc_creds:
                logger.error("No BMC credentials found for IPMI reset")
                return False

            # Get bridge server URL from associated bridges
            if not self.associated_bridges_ids:
                logger.error("No associated bridge IDs provided for IPMI service")
                return False

            # For simplicity, we'll construct the server URL based on tenant/site/location
            # This assumes a predictable bridge URL pattern
            # Use brokkr.lan as the bridge server URL
            bridge_server_url = "https://brokkr.lan"

            # Create IPMI service and perform hard reset
            ipmi_service = IPMIService(
                server_url=bridge_server_url,
                mac_address=ipmi_mac,
                bmc_user=bmc_creds["bmc_user"],
                bmc_pass=bmc_creds["bmc_pass"],
                bmc_port=bmc_creds.get("bmc_port", 623),
                uefi=False,  # Not relevant for BMC reset
            )

            result = await ipmi_service.perform_ipmi_operation("cold")

            if result:
                logger.info("IPMI cold reset completed successfully")
                # Wait for BMC to fully restart (cold reset typically takes 30-60 seconds)
                logger.info("Waiting 45 seconds for BMC to complete cold reset...")
                await asyncio.sleep(45)
            else:
                logger.error("IPMI cold reset failed")

            return result

        except Exception as e:
            logger.error(f"Error during IPMI hard reset: {e}")
            return False
        finally:
            # No cleanup needed for direct API calls
            pass

    def _create_or_update_interface(
        self,
        object_name: str,
        device,
        type: str,
        enabled: bool,
        mac_address: str,
        mark_connected: bool,
        mgmt_only: bool,
        description: str = "",
    ):
        """Create or update interface with idempotent logic using REST API"""
        try:
            # Search for existing interface
            url = f"{self.netbox_url}/api/dcim/interfaces/"
            params = {"device_id": device["id"], "name": object_name}
            response = requests.get(url, headers=self.netbox_headers, params=params)
            response.raise_for_status()

            data = response.json()
            netbox_record = None

            if data.get("results"):
                netbox_record = data["results"][0]
                logger.info(f"Found existing interface: {object_name} for device ID {device['id']}")

                # Check and update interface properties
                update_dict = {}
                interface_data = {
                    "type": type,
                    "enabled": enabled,
                    "mac_address": mac_address.upper() if mac_address else None,
                    "mark_connected": mark_connected,
                    "mgmt_only": mgmt_only,
                    "description": description,
                }

                for field, value in interface_data.items():
                    if not isinstance(netbox_record, dict):
                        logger.error(f"netbox_record is not a dict: {type(netbox_record)} - {netbox_record}")
                        return None
                    current_value = netbox_record.get(field)
                    if isinstance(current_value, dict) and "value" in current_value:
                        current_value = current_value["value"]
                    if str(current_value).lower() != str(value).lower() and value is not None:
                        logger.info(
                            f"Updating interface {field} from {current_value} to {value}: {device['name'] if 'name' in device else device['id']} - {object_name}"
                        )
                        update_dict[field] = value

                # Apply updates if any
                if update_dict:
                    update_url = f"{self.netbox_url}/api/dcim/interfaces/{netbox_record['id']}/"
                    update_response = requests.patch(update_url, headers=self.netbox_headers, json=update_dict)
                    if update_response.status_code == 200:
                        device_name = (
                            device.get("name", device["id"])
                            if isinstance(device, dict)
                            else getattr(device, "name", device.id)
                        )
                        logger.info(f"Interface properties update successful: {device_name} - {object_name}")
                        netbox_record.update(update_dict)
                    else:
                        device_name = (
                            device.get("name", device["id"])
                            if isinstance(device, dict)
                            else getattr(device, "name", device.id)
                        )
                        logger.error(f"Interface properties update failed: {device_name} - {object_name}")
            else:
                logger.info(f"Creating new interface: {object_name} for device ID {device['id']}")
                interface_data = {
                    "device": device["id"],
                    "name": object_name,
                    "type": type,
                    "enabled": enabled,
                    "mac_address": mac_address.upper() if mac_address else None,
                    "mark_connected": mark_connected,
                    "mgmt_only": mgmt_only,
                    "description": description,
                }
                create_response = requests.post(url, headers=self.netbox_headers, json=interface_data)
                create_response.raise_for_status()
                netbox_record = create_response.json()

        except Exception as e:
            logger.error(f"Failed to process interface request: {str(e)}")
            return None

        return netbox_record

    def _create_or_update_ip_address(self, **kwargs):
        """Create or update IP address with idempotent logic using REST API"""
        try:
            logger.debug("Fetching IP address")
            search_params = {}

            # For searching, we need tenant_id, but for creation we use tenant
            if "tenant" in kwargs:
                search_params["tenant_id"] = kwargs["tenant"]
                search_params["address"] = kwargs["address"]
            else:
                raise ValueError("Missing required parameter 'tenant' for IP address operation")

            # Include VRF in search if provided
            if "vrf" in kwargs:
                if isinstance(kwargs["vrf"], int):
                    search_params["vrf_id"] = kwargs["vrf"]
                elif hasattr(kwargs["vrf"], "id"):
                    search_params["vrf_id"] = kwargs["vrf"].id

            # Search for existing IP address
            url = f"{self.netbox_url}/api/ipam/ip-addresses/"
            response = requests.get(url, headers=self.netbox_headers, params=search_params)
            response.raise_for_status()

            data = response.json()
            netbox_record = None

            if data.get("results"):
                netbox_record = data["results"][0]
                logger.info(f"IP address {netbox_record['address']} found, checking assignments")

                # Update properties if needed
                update_dict = {}
                for prop, new_value in kwargs.items():
                    if prop in ["address", "tenant"]:  # Skip search keys
                        continue

                    current_value = netbox_record.get(prop)
                    if isinstance(current_value, dict) and "id" in current_value:
                        current_value = current_value["id"]
                    elif isinstance(current_value, dict) and "value" in current_value:
                        current_value = current_value["value"]

                    if str(current_value) != str(new_value) and new_value is not None:
                        logger.info(f"Updating IP {prop} from {current_value} to {new_value}")
                        update_dict[prop] = new_value

                # Apply updates if any
                if update_dict:
                    update_url = f"{self.netbox_url}/api/ipam/ip-addresses/{netbox_record['id']}/"
                    update_response = requests.patch(update_url, headers=self.netbox_headers, json=update_dict)
                    if update_response.status_code != 200:
                        logger.error("IP address properties update failed")
                    else:
                        netbox_record.update(update_dict)

            if not netbox_record:
                logger.info("No IP address found, creating new one")

                # Prepare creation data with proper field mapping
                create_data = dict(kwargs)

                # Handle VRF field mapping - API expects 'vrf' field with ID value
                if "vrf" in create_data and isinstance(create_data["vrf"], int):
                    # VRF is already an ID, keep as is
                    pass
                elif "vrf" in create_data and hasattr(create_data["vrf"], "id"):
                    create_data["vrf"] = create_data["vrf"].id

                logger.info(f"Creating IP address with data: {create_data}")
                create_response = requests.post(url, headers=self.netbox_headers, json=create_data)

                if create_response.status_code != 201:
                    logger.error(f"IP creation failed with status {create_response.status_code}")
                    logger.error(f"Response: {create_response.text}")
                    logger.error(f"Request URL: {url}")
                    logger.error(f"Request data: {create_data}")

                create_response.raise_for_status()
                netbox_record = create_response.json()
                logger.info(f"IP address {netbox_record['address']} created")

        except Exception as e:
            logger.error(f"Failed to fetch or create IP address: {str(e)}")
            return None

        return netbox_record

    async def set_facts(self):
        if "mac" in self.bmc_data:
            self.ipmi_enabled = True
            self.ipmi_interface_mac = self.bmc_data.get("mac", None)
            self.ipmi_ipv4address = self.bmc_data.get("ipv4", None)
            self.ipmi_ipv6address = self.bmc_data.get("ipv6", None)

            logger.info("IPMI Enabled: True")

            # Check for blank/invalid MAC address
            if self._is_blank_mac_address(self.ipmi_interface_mac):
                logger.warning(f"Detected blank/invalid IPMI MAC address: {self.ipmi_interface_mac}")

                # Try to get existing IPMI MAC from NetBox
                existing_mac = self._get_existing_ipmi_mac()
                if existing_mac and not self._is_blank_mac_address(existing_mac):
                    logger.warning("Found existing IPMI MAC, attempting hard reset")

                    # Perform async IPMI reset
                    if self.associated_bridges_ids:
                        reset_result = await self._perform_ipmi_hard_reset(existing_mac)
                        if reset_result:
                            logger.warning("IPMI reset completed, BMC should now respond with proper MAC")
                        else:
                            logger.warning("IPMI reset failed, proceeding without BMC reset")
                    else:
                        logger.error("Cannot perform IPMI reset: no associated bridge IDs provided")
                else:
                    logger.warning("No valid existing IPMI MAC found, cannot perform reset")

                # Don't process this MAC further
                self.ipmi_interface_mac = None
            else:
                self.ipmi_interface_mac = self.ipmi_interface_mac.upper()
                logger.info(f"IPMI MAC Address: {self.ipmi_interface_mac}")

            def is_empty_or_invalid_ip(ip):
                if not ip:
                    return True
                base_ip = ip.split("/")[0]
                # Check for empty or network ID addresses
                return base_ip in ["0.0.0.0", "::", "", None] or ip in ["::/64", "::/48", "0.0.0.0/0"]

            if self.ipmi_ipv4address and not is_empty_or_invalid_ip(self.ipmi_ipv4address):
                logger.info(f"IPMI IPv4 Address: {self.ipmi_ipv4address}")
            else:
                self.ipmi_ipv4address = None

            if self.ipmi_ipv6address and not is_empty_or_invalid_ip(self.ipmi_ipv6address):
                logger.info(f"IPMI IPv6 Address: {self.ipmi_ipv6address}")
            else:
                self.ipmi_ipv6address = None

        else:
            logger.info("IPMI Enabled: False")

    def set_interface(self):
        primary_oob_ip = None

        # Create/get the IPMI interface
        logger.info("Creating/updating IPMI interface")
        # Create/update IPMI interface using idempotent logic (extracted from HydraNetbox)
        interface = self._create_or_update_interface(
            object_name="IPMI",
            device=self.device,
            type="other",
            enabled=True,
            mac_address=self.ipmi_interface_mac,
            mark_connected=True,
            mgmt_only=True,
            description="",
        )

        if not interface:
            logger.error("Failed to create/update IPMI interface")
            return
        logger.info(f"IPMI interface created/updated with ID: {interface['id']}")

        # Get all existing IP addresses assigned to this interface (regardless of VRF)
        logger.debug(f"Fetching existing IP addresses for interface {interface['id']}")
        try:
            url = f"{self.netbox_url}/api/ipam/ip-addresses/"
            params = {"assigned_object_id": interface["id"], "tenant_id": self.tenant["id"]}
            response = requests.get(url, headers=self.netbox_headers, params=params)
            response.raise_for_status()

            data = response.json()
            existing_ips = data.get("results", [])
            logger.info(f"Found {len(existing_ips)} existing IP addresses on interface for tenant {self.tenant['id']}")

            # Log details of existing IPs for debugging
            for existing_ip in existing_ips:
                vrf_info = f"VRF: {existing_ip['vrf']['id']}" if existing_ip.get("vrf") else "VRF: None"
                logger.debug(f"Existing IP: {existing_ip['address']} (ID: {existing_ip['id']}, {vrf_info})")
        except Exception as filter_error:
            logger.error(f"Error fetching existing IPs: {str(filter_error)}")
            existing_ips = []

        # Process IPv4 address
        if self.ipmi_ipv4address:
            logger.info(f"Processing IPv4 address: {self.ipmi_ipv4address}")

            # Strip mask if present to get clean IP for comparison
            clean_ipv4 = self.ipmi_ipv4address.split("/")[0] if "/" in self.ipmi_ipv4address else self.ipmi_ipv4address
            logger.debug(f"Clean IPv4 for matching: {clean_ipv4}")

            # Look for existing IP that matches the clean IP
            matching_ipv4 = None
            for existing_ip in existing_ips:
                existing_clean_ip = (
                    existing_ip["address"].split("/")[0]
                    if "/" in str(existing_ip["address"])
                    else str(existing_ip["address"])
                )
                if existing_clean_ip == clean_ipv4:
                    matching_ipv4 = existing_ip
                    logger.info(f"Found matching IPv4 address: {existing_ip['address']} (ID: {existing_ip['id']})")
                    break

            if matching_ipv4:
                logger.info(
                    f"Found existing IPv4 {matching_ipv4['address']} (ID: {matching_ipv4['id']}) - updating with new properties",
                )

                # Update the existing IP using REST API
                try:
                    # Prepare update data
                    update_data = {
                        "address": self.ipmi_ipv4address,
                        "assigned_object_type": "dcim.interface",
                        "assigned_object_id": interface["id"],
                        "tenant": self.tenant["id"],
                        "vrf": self.vrf["id"],
                        "site": self.site["id"],
                        "status": "active",
                    }

                    # Update the IP address using REST API
                    update_url = f"{self.netbox_url}/api/ipam/ip-addresses/{matching_ipv4['id']}/"
                    update_response = requests.patch(update_url, headers=self.netbox_headers, json=update_data)

                    if update_response.status_code == 200:
                        primary_oob_ip = update_response.json()
                        logger.info(
                            f"Successfully updated existing IPv4 {primary_oob_ip['address']} with new properties"
                        )
                    else:
                        logger.error(f"Failed to update existing IPv4 {matching_ipv4['address']}")
                        # Fall back to creating a new IP if update fails
                        primary_oob_ip = self._create_or_update_ip_address(
                            address=self.ipmi_ipv4address,
                            assigned_object_type="dcim.interface",
                            assigned_object_id=interface["id"],
                            tenant=self.tenant["id"],
                            status="active",
                            vrf=self.vrf["id"],
                        )

                except Exception as e:
                    logger.error(f"Error updating existing IPv4: {str(e)}")
                    logger.debug(f"Full error details: {repr(e)}")
                    # Fall back to creating a new IP if update fails
                    try:
                        primary_oob_ip = self._create_or_update_ip_address(
                            address=self.ipmi_ipv4address,
                            assigned_object_type="dcim.interface",
                            assigned_object_id=interface["id"],
                            tenant=self.tenant["id"],
                            status="active",
                            vrf=self.vrf["id"],
                        )
                    except Exception as create_error:
                        logger.error(f"Error creating new IPv4 after update failed: {str(create_error)}")
            else:
                logger.info(
                    f"No matching IPv4 found in tenant {self.tenant['id']}, creating new IP address: {self.ipmi_ipv4address}",
                )
                # Create new IP address
                primary_oob_ip = self._create_or_update_ip_address(
                    address=self.ipmi_ipv4address,
                    assigned_object_type="dcim.interface",
                    assigned_object_id=interface["id"],
                    tenant=self.tenant["id"],
                    status="active",
                    vrf=self.vrf["id"],
                )

            self.field_data["management_ip"] = self.ipmi_ipv4address
            self.ip_addresses.append(self.ipmi_ipv4address)

        # Process IPv6 address
        if self.ipmi_ipv6address:
            logger.info(f"Processing IPv6 address: {self.ipmi_ipv6address}")

            # Strip mask if present to get clean IP for comparison
            clean_ipv6 = self.ipmi_ipv6address.split("/")[0] if "/" in self.ipmi_ipv6address else self.ipmi_ipv6address
            logger.debug(f"Clean IPv6 for matching: {clean_ipv6}")

            # Look for existing IP that matches the clean IP
            matching_ipv6 = None
            for existing_ip in existing_ips:
                existing_clean_ip = (
                    existing_ip["address"].split("/")[0]
                    if "/" in str(existing_ip["address"])
                    else str(existing_ip["address"])
                )
                if existing_clean_ip == clean_ipv6:
                    matching_ipv6 = existing_ip
                    logger.info(f"Found matching IPv6 address: {existing_ip['address']} (ID: {existing_ip['id']})")
                    break

            if matching_ipv6:
                logger.info(
                    f"Found existing IPv6 {matching_ipv6['address']} - updating with new VRF {self.vrf['id']} and other properties"
                )
                # Update the existing IPv6 using REST API
                try:
                    update_data = {
                        "address": self.ipmi_ipv6address,
                        "assigned_object_type": "dcim.interface",
                        "assigned_object_id": interface["id"],
                        "tenant": self.tenant["id"],
                        "vrf": self.vrf["id"],
                        "site": self.site["id"],
                        "status": "active",
                    }

                    update_url = f"{self.netbox_url}/api/ipam/ip-addresses/{matching_ipv6['id']}/"
                    update_response = requests.patch(update_url, headers=self.netbox_headers, json=update_data)

                    if update_response.status_code == 200:
                        updated_ipv6 = update_response.json()
                        logger.info(f"Successfully updated existing IPv6 {updated_ipv6['address']}")
                    else:
                        logger.warning("Failed to update existing IPv6, creating new")
                        self._create_or_update_ip_address(
                            address=self.ipmi_ipv6address,
                            assigned_object_type="dcim.interface",
                            assigned_object_id=interface["id"],
                            tenant=self.tenant["id"],
                            status="active",
                            vrf=self.vrf["id"],
                        )
                except Exception as e:
                    logger.error(f"Error updating existing IPv6: {str(e)}")
                    # Fall back to creating
                    self._create_or_update_ip_address(
                        address=self.ipmi_ipv6address,
                        assigned_object_type="dcim.interface",
                        assigned_object_id=interface["id"],
                        tenant=self.tenant["id"],
                        status="active",
                        vrf=self.vrf["id"],
                    )
            else:
                logger.info(
                    f"No matching IPv6 found in tenant {self.tenant['id']}, creating new IP address: {self.ipmi_ipv6address}",
                )
                # Create/update IPv6 address
                self._create_or_update_ip_address(
                    address=self.ipmi_ipv6address,
                    assigned_object_type="dcim.interface",
                    assigned_object_id=interface["id"],
                    tenant=self.tenant["id"],
                    status="active",
                    vrf=self.vrf["id"],
                )

            self.ip_addresses.append(self.ipmi_ipv6address)

        # Update interface tracking
        self.interfaces.append("IPMI")

        # Set OOB IP on device for accumulative push
        if primary_oob_ip:
            logger.info(f"Setting primary OOB IP: {primary_oob_ip['address']} (ID: {primary_oob_ip['id']})")
            # Set on device object instead of immediate API call
            self.device.oob_ip = primary_oob_ip["id"]
            logger.info("✅ Device OOB IP set for accumulative update")
        else:
            logger.warning("Missing primary OOB IP")

        # Remove the discovery-bmc-ip-sync tag after BMC processing
        self._remove_ip_sync_tag()

    def _has_bmc_ip_sync_tag(self) -> bool:
        """Check if device has the 'discovery-bmc-ip-sync' tag"""
        try:
            # Get device tags
            device_url = f"{self.netbox_url}/api/dcim/devices/{self.device['id']}/"
            response = requests.get(device_url, headers=self.netbox_headers)
            response.raise_for_status()

            device_data = response.json()
            tags = device_data.get("tags", [])

            # Check if discovery-bmc-ip-sync tag exists
            for tag in tags:
                if isinstance(tag, dict):
                    tag_name = tag.get("name", "")
                elif isinstance(tag, str):
                    tag_name = tag
                else:
                    continue

                if tag_name == "discovery-bmc-ip-sync":
                    logger.info("Found 'discovery-bmc-ip-sync' tag on device - enabling BMC IP synchronization")
                    return True

            logger.info(
                f"Device does not have 'discovery-bmc-ip-sync' tag - found tags: {[t.get('name') if isinstance(t, dict) else t for t in tags]}"
            )
            return False

        except Exception as e:
            logger.error(f"Error checking device tags: {str(e)}")
            logger.info("Assuming BMC IP sync should proceed due to error")
            return True  # Default to allowing sync if we can't check tags

    def _remove_ip_sync_tag(self) -> None:
        """Remove the 'discovery-bmc-ip-sync' tag from the device after processing"""
        try:
            # Get current device data
            device_url = f"{self.netbox_url}/api/dcim/devices/{self.device['id']}/"
            response = requests.get(device_url, headers=self.netbox_headers)
            response.raise_for_status()

            device_data = response.json()
            current_tags = device_data.get("tags", [])

            # Filter out the discovery-ip-sync tag
            updated_tags = []
            tag_found = False

            for tag in current_tags:
                if isinstance(tag, dict):
                    tag_name = tag.get("name", "")
                    tag_id = tag.get("id")
                elif isinstance(tag, str):
                    tag_name = tag
                    tag_id = tag
                else:
                    continue

                if tag_name == "discovery-bmc-ip-sync":
                    tag_found = True
                    logger.info("Removing 'discovery-bmc-ip-sync' tag from device")
                else:
                    updated_tags.append(tag_id if isinstance(tag, dict) else tag)

            # Update device tags if the tag was found
            if tag_found:
                update_data = {"tags": updated_tags}
                update_response = requests.patch(device_url, headers=self.netbox_headers, json=update_data)
                if update_response.status_code == 200:
                    logger.info("Successfully removed 'discovery-bmc-ip-sync' tag from device")
                else:
                    logger.error(f"Failed to remove discovery-bmc-ip-sync tag: {update_response.text}")
            else:
                logger.debug("No discovery-bmc-ip-sync tag found to remove")

        except Exception as e:
            logger.error(f"Error removing discovery-bmc-ip-sync tag: {str(e)}")
