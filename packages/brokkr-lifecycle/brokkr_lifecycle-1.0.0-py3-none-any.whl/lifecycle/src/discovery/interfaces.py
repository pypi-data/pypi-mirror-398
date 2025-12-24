import logging
import os
import re
from dataclasses import dataclass

import pynetbox
import requests

logger = logging.getLogger(__name__)


def get_interface_type(speed: int) -> str:
    """
    Map interface speed to NetBox interface type

    Args:
        speed: Interface speed in Mbps

    Returns:
        str: NetBox interface type identifier
    """
    # Interface types mapped to NetBox enum values
    interface_types = {
        -1: "other",
        10: "100base-tx",  # Map 10Mbps to closest available
        100: "100base-tx",
        1000: "1000base-t",
        2500: "2.5gbase-t",
        5000: "5gbase-t",
        10000: "10gbase-t",
        25000: "25gbase-x-sfp28",
        40000: "40gbase-x-qsfpp",
        50000: "50gbase-x-sfp28",
        100000: "100gbase-x-qsfp28",
        200000: "200gbase-x-qsfp56",
        400000: "400gbase-x-qsfp112",
        800000: "800gbase-x-qsfpdd",
    }

    interface_type = interface_types.get(speed)
    if interface_type:
        return interface_type
    else:
        # For unsupported speeds (like 100000, 200000, 400000), fall back to "other"
        logger.warning(f"Unsupported interface speed {speed} Mbps, using 'other' interface type")
        return "other"


@dataclass
class InterfaceData:
    netbox: pynetbox.api
    ip_a: list[dict]
    bdi: dict
    device: object

    tenant: object
    site: object
    vrf: object
    network: dict

    discovered_interfaces: list[str]

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        self.network = self.network.get("network", None)
        self.interface_dict = {}
        self.interface_master_map = {}

        logger.info(f"device: {self.device}")
        logger.info(f"tenant: {self.tenant}")
        logger.info(f"site: {self.site}")
        logger.info(f"vrf: {self.vrf}")

        self.create_interfaces()
        self.link_interfaces_to_bridges()
        self.remove_interfaces()

        # Sync IP addresses if tag is present
        self.sync_ip_addresses()

    def _create_or_update_interface(
        self,
        object_name: str,
        device,
        interface_type: str,
        enabled: bool,
        mac_address: str,
        mark_connected: bool,
        mgmt_only: bool,
        description: str = "",
    ):
        """Create or update interface with idempotent logic (extracted from HydraNetbox)"""
        try:
            # Retrieve the interface or create it if it doesn't exist
            netbox_record = self.netbox.dcim.interfaces.get(device_id=device.id, name=object_name)

            if netbox_record is None:
                logger.info(f"Creating new interface: {object_name} for device ID {device.id}")
                netbox_record = self.netbox.dcim.interfaces.create(
                    {
                        "device": device.id,
                        "name": object_name,
                        "type": interface_type,
                        "enabled": enabled,
                        "mac_address": mac_address.upper() if mac_address else None,
                        "mark_connected": mark_connected,
                        "mgmt_only": mgmt_only,
                        "description": description,
                    }
                )
            else:
                # Check and update interface properties (excluding enabled - user controlled after creation)
                update_dict = {}
                for field, value in {
                    "type": interface_type,
                    "mac_address": mac_address.upper() if mac_address else None,
                    "mark_connected": mark_connected,
                    "mgmt_only": mgmt_only,
                    "description": description,
                }.items():
                    current_value = getattr(netbox_record, field, None)
                    if hasattr(current_value, "value"):
                        current_value = current_value.value
                    if str(current_value).lower() != str(value).lower() and value is not None:
                        logger.info(
                            f"Updating interface {field} from {current_value} to {value}: {device} - {object_name}"
                        )
                        update_dict[field] = value

                # Apply updates if any
                if update_dict:
                    for key, value in update_dict.items():
                        setattr(netbox_record, key, value)
                    save_result = netbox_record.save()
                    if save_result:
                        logger.info(f"Interface properties update successful: {device} - {object_name}")
                    else:
                        logger.error(f"Interface properties update failed: {device} - {object_name}")

        except Exception as e:
            logger.error(f"Failed to process interface request: {str(e)}")
            return None

        return netbox_record

    def _remove_wt0_interface(self):
        """Remove wt0 interface if it exists (for marketplace-hosts devices)"""
        try:
            existing_wt0 = self.netbox.dcim.interfaces.get(device_id=self.device.id, name="wt0")
            if existing_wt0:
                existing_wt0.delete()
                logger.info(f"Removed wt0 interface (ID: {existing_wt0.id}) from device {self.device.name}")
            else:
                logger.debug("No wt0 interface found to remove")
        except Exception as e:
            logger.error(f"Error removing wt0 interface: {e}")

    def _link_interface_to_bridge(self, member_interface, master_interface):
        """Link interface to bridge (extracted from HydraNetbox)"""
        try:
            # Update the bridge attribute of the member interface
            member_interface.bridge = master_interface.id

            # Save the updated member interface
            updated_member_interface = member_interface.save()

            logger.info(f"Successfully linked interface {member_interface.name} to bridge {master_interface.name}")
            return updated_member_interface

        except Exception as e:
            logger.error(
                f"Failed to link interface {member_interface.name} to bridge {master_interface.name}: {str(e)}"
            )
            return None

    def _list_interfaces(self, device_id: int):
        """List all interfaces for a device (extracted from HydraNetbox)"""
        return self.netbox.dcim.interfaces.filter(device_id=device_id)

    def get_interface_speed_by_mac(self, mac_address: str) -> str:
        """Get interface speed by MAC address using functional approach"""
        if not self.network or "nics" not in self.network:
            return "-1"

        return next(
            (str(nic.get("speed", "-1")) for nic in self.network["nics"] if nic.get("mac_address") == mac_address), "-1"
        )

    def parse_speed_to_mbps(self, speed_str: str) -> int:
        """
        Parse speed string to integer Mbps value.
        Handles formats like: "10000Mb/s", "10Gb/s", "Unknown!", "-1", "1000"

        Returns:
            int: Speed in Mbps, or -1 for unknown/invalid speeds
        """
        if not speed_str:
            return -1

        speed_clean = str(speed_str).strip()

        # Handle known invalid formats
        if speed_clean.lower() in ["unknown!", "unknown", "", "null", "none"]:
            return -1

        # Handle plain -1
        if speed_clean == "-1":
            return -1

        # Handle Gb/s separately (convert to Mb/s)
        if any(unit in speed_str.lower() for unit in ["gb/s", "gbps"]):
            speed_clean = (
                speed_str.replace("Gb/s", "").replace("Gbps", "").replace("gb/s", "").replace("gbps", "").strip()
            )
            try:
                return int(float(speed_clean) * 1000)
            except ValueError:
                return -1

        # Remove Mb/s units and clean up
        speed_clean = (
            speed_clean.replace("Mb/s", "").replace("Mbps", "").replace("mb/s", "").replace("mbps", "").strip()
        )

        # Try to parse as integer
        try:
            return int(float(speed_clean))
        except ValueError:
            return -1

    def create_interfaces(self):
        # First pass: create interfaces and map members to their bridges
        for device_interface in self.ip_a:
            ifname = device_interface["ifname"]

            # Skip loopback and known virtual interfaces
            if ifname in ["lo", "docker0"] or re.match(r"(kube|vxlan|nodelocaldns)", ifname):
                logger.info(f"Skipping system interface: {ifname}")
                continue

            # Handle wt0 interface based on device role
            if ifname == "wt0":
                if hasattr(self.device.role, "slug") and self.device.role.slug == "brokkr-bridge":
                    logger.info("Creating wt0 interface for brokkr-bridge device")
                    # Continue with wt0 creation for brokkr-bridge
                elif hasattr(self.device.role, "slug") and self.device.role.slug == "marketplace-hosts":
                    logger.info("Removing wt0 interface for marketplace-hosts device")
                    self._remove_wt0_interface()
                    continue
                else:
                    logger.info(
                        f"Skipping wt0 interface for device role: {getattr(self.device.role, 'slug', 'unknown')}"
                    )
                    continue

            # Skip bonds, VLANs, and other virtual interfaces
            if re.match(r"(bond\d+|vlan\d+|br-|virbr|veth|tun\d+|tap\d+|dummy\d+|gre\d+|sit\d+|ip6tnl\d+)", ifname):
                logger.info(f"Skipping virtual interface: {ifname}")
                continue

            # Skip VLAN interfaces in the format eth0.100 or em1.200
            if re.match(r".*\.\d+$", ifname):
                logger.info(f"Skipping VLAN interface: {ifname}")
                continue

            # Skip bridge interfaces (alternative patterns)
            if device_interface.get("link_type") in ["bridge", "bond", "vlan", "vxlan", "tun", "tap"]:
                logger.info(f"Skipping {device_interface.get('link_type')} interface: {ifname}")
                continue

            self.discovered_interfaces.append(ifname)

            mark_connected = device_interface["operstate"] == "UP"

            interface_address = device_interface.get("permaddr", device_interface.get("address", ""))

            # Get interface speed from network data using MAC address
            interface_speed = self.get_interface_speed_by_mac(interface_address)

            # Parse speed string to integer Mbps value
            speed_value = self.parse_speed_to_mbps(interface_speed)
            if speed_value != -1:
                logger.info(f"Using network data speed {speed_value} for interface {ifname} (MAC: {interface_address})")
            else:
                logger.info(f"Could not parse speed '{interface_speed}' for interface {ifname}, using -1 (other)")

            interface_type = get_interface_type(speed_value)

            # Create/update interface using idempotent logic (extracted from HydraNetbox)
            interface = self._create_or_update_interface(
                object_name=ifname,
                device=self.device,
                interface_type=interface_type,
                enabled=mark_connected,
                mac_address=interface_address,
                mark_connected=mark_connected,
                mgmt_only=False,
                description="",
            )

            if not interface:
                logger.error(f"Failed to create/update interface {ifname}")
                continue
            logger.info(f"interface: {interface}")

            self.interface_dict[ifname] = interface
            logger.info(f"Added interface {ifname} to interface_dict")

            # Store the master bridge if exists
            if "master" in device_interface:
                self.interface_master_map[ifname] = device_interface["master"]
                logger.info(f"Interface {ifname} is a member of bridge {device_interface['master']}")

            for ip in device_interface["addr_info"]:
                if ip["scope"] == "link":
                    continue
                if ip["prefixlen"] in [0, "", None]:
                    continue
                if ip["local"] in ["::", "0.0.0.0", "", None]:
                    continue
                if any(ip["local"].startswith(prefix) for prefix in ["fd00", "fe80"]):
                    continue

        # Log the final interface dictionary for verification
        logger.info(f"Final interface_dict: {self.interface_dict}")
        logger.info(f"Final interface_master_map: {self.interface_master_map}")

    def link_interfaces_to_bridges(self):
        # Link interfaces to their master bridges
        for member_ifname, master_ifname in self.interface_master_map.items():
            logger.info(f"Attempting to link interface {member_ifname} to bridge {master_ifname}")
            member_interface = self.interface_dict.get(member_ifname)
            master_interface = self.interface_dict.get(master_ifname)
            if member_interface:
                logger.info(f"Found member interface: {member_ifname} with ID {member_interface.id}")
            else:
                logger.info(f"Member interface {member_ifname} not found in interface_dict")

            if master_interface:
                logger.info(f"Found master interface: {master_ifname} with ID {master_interface.id}")
            else:
                logger.info(f"Master interface {master_ifname} not found in interface_dict")

            if member_interface and master_interface:
                try:
                    self._link_interface_to_bridge(member_interface, master_interface)
                    logger.info(f"Linked interface {member_ifname} to bridge {master_ifname}")
                except Exception as e:
                    logger.info(f"Failed to link interface {member_ifname} to bridge {master_ifname}: {str(e)}")
            else:
                logger.info(f"Cannot link {member_ifname} to {master_ifname} due to missing interfaces")

    def remove_interfaces(self):
        netbox_interfaces = self._list_interfaces(self.device.id)
        for interface in netbox_interfaces:
            # Remove interfaces that weren't discovered (except IPMI which is managed elsewhere)
            if interface.name not in self.discovered_interfaces and str(interface.name).upper() != "IPMI":
                logger.info(f"Removing unknown interface: {interface.name}")
                interface.delete()

    def _has_primary_ip_sync_tag(self) -> bool:
        """Check if device has the 'discovery-primary-ip-sync' tag"""
        try:
            # Get NetBox configuration
            netbox_url = os.environ.get("NETBOX_URL", "").rstrip("/")
            netbox_token = os.environ.get("NETBOX_TOKEN")

            if not all([netbox_url, netbox_token]):
                logger.warning("NetBox configuration not available for tag check")
                return False

            headers = {
                "Authorization": f"Token {netbox_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            # Get device tags
            device_url = f"{netbox_url}/api/dcim/devices/{self.device.id}/"
            response = requests.get(device_url, headers=headers)
            response.raise_for_status()

            device_data = response.json()
            tags = device_data.get("tags", [])

            # Check if discovery-primary-ip-sync tag exists
            for tag in tags:
                if isinstance(tag, dict):
                    tag_name = tag.get("name", "")
                elif isinstance(tag, str):
                    tag_name = tag
                else:
                    continue

                if tag_name == "discovery-primary-ip-sync":
                    logger.info("Found 'discovery-primary-ip-sync' tag on device - enabling IP synchronization")
                    return True

            logger.info("Device does not have 'discovery-primary-ip-sync' tag - skipping IP synchronization")
            return False

        except Exception as e:
            logger.error(f"Error checking device tags: {e}")
            return False

    def sync_ip_addresses(self):
        """Synchronize IP addresses from ip_a data to NetBox interfaces"""
        # Check if IP sync is enabled via tag
        if not self._has_primary_ip_sync_tag():
            return

        logger.info("Synchronizing IP addresses from discovered interfaces...")

        # Get NetBox configuration
        netbox_url = os.environ.get("NETBOX_URL", "").rstrip("/")
        netbox_token = os.environ.get("NETBOX_TOKEN")

        if not all([netbox_url, netbox_token]):
            logger.warning("NetBox configuration not available for IP sync")
            return

        headers = {
            "Authorization": f"Token {netbox_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        for interface_data in self.ip_a:
            ifname = interface_data.get("ifname")
            addr_info = interface_data.get("addr_info", [])

            # Skip loopback and virtual interfaces
            if not ifname or ifname == "lo" or not addr_info:
                continue

            # Skip virtual interfaces (docker, wt0, etc.)
            if re.match(r"(docker|wt|veth|br-|virbr)", ifname):
                continue

            logger.info(f"Processing IP addresses for interface: {ifname}")

            # Find the NetBox interface by name
            interface_id = self._find_netbox_interface_by_name(ifname, headers, netbox_url)
            if not interface_id:
                logger.warning(f"NetBox interface not found for {ifname}, skipping IP sync")
                continue

            # Process each IP address
            discovered_ips = []
            for addr in addr_info:
                if addr.get("family") == "inet":  # IPv4
                    ip_address = f"{addr['local']}/{addr['prefixlen']}"
                    discovered_ips.append(ip_address)
                    self._sync_ip_address(ip_address, interface_id, headers, netbox_url)

            # Remove IPs from NetBox that aren't on the machine (source of truth)
            self._remove_obsolete_ips(interface_id, discovered_ips, headers, netbox_url, ifname)

    def _find_netbox_interface_by_name(self, ifname: str, headers: dict, netbox_url: str) -> int:
        """Find NetBox interface ID by name"""
        try:
            url = f"{netbox_url}/api/dcim/interfaces/"
            params = {"device_id": self.device.id, "name": ifname}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("results"):
                return data["results"][0]["id"]

            return None
        except Exception as e:
            logger.error(f"Error finding interface {ifname}: {e}")
            return None

    def _sync_ip_address(self, ip_address: str, interface_id: int, headers: dict, netbox_url: str):
        """Create or update IP address in NetBox"""
        try:
            # Check if IP already exists
            url = f"{netbox_url}/api/ipam/ip-addresses/"
            params = {"address": ip_address}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("results"):
                # IP exists, check if it's assigned to correct interface
                existing_ip = data["results"][0]
                assigned_object = existing_ip.get("assigned_object")

                if assigned_object and assigned_object.get("id") == interface_id:
                    logger.info(f"IP {ip_address} already correctly assigned to interface")
                    return
                elif assigned_object:
                    logger.info(
                        f"IP {ip_address} reassigning from interface {assigned_object.get('id')} to {interface_id}"
                    )

                # Update assignment
                update_data = {"assigned_object_id": interface_id, "assigned_object_type": "dcim.interface"}
                update_url = f"{netbox_url}/api/ipam/ip-addresses/{existing_ip['id']}/"
                update_response = requests.patch(update_url, headers=headers, json=update_data)

                if update_response.status_code == 200:
                    logger.info(f"✅ Updated IP assignment: {ip_address}")
                else:
                    logger.error(f"Failed to update IP assignment: {ip_address}")
            else:
                # Create new IP
                ip_data = {
                    "address": ip_address,
                    "assigned_object_id": interface_id,
                    "assigned_object_type": "dcim.interface",
                    "tenant": self.tenant.id if self.tenant else None,
                    "vrf": self.vrf.id if self.vrf else None,
                    "status": "active",
                }

                create_response = requests.post(url, headers=headers, json=ip_data)
                if create_response.status_code == 201:
                    logger.info(f"✅ Created IP address: {ip_address}")
                else:
                    logger.error(f"Failed to create IP address: {ip_address} - {create_response.text}")

        except Exception as e:
            logger.error(f"Error syncing IP address {ip_address}: {e}")

    def _remove_obsolete_ips(
        self, interface_id: int, discovered_ips: list, headers: dict, netbox_url: str, ifname: str
    ):
        """Remove IP addresses from NetBox that aren't present on the machine"""
        try:
            # Get all IPs currently assigned to this interface in NetBox
            url = f"{netbox_url}/api/ipam/ip-addresses/"
            params = {
                "assigned_object_id": interface_id,
                "assigned_object_type__app_label": "dcim",
                "assigned_object_type__model": "interface",
            }
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            netbox_ips = data.get("results", [])

            for netbox_ip in netbox_ips:
                netbox_address = netbox_ip["address"]

                # Check if this NetBox IP exists on the machine
                if netbox_address not in discovered_ips:
                    logger.info(
                        f"Removing obsolete IP {netbox_address} from interface {ifname} (not present on machine)"
                    )

                    # Delete the IP from NetBox
                    delete_url = f"{netbox_url}/api/ipam/ip-addresses/{netbox_ip['id']}/"
                    delete_response = requests.delete(delete_url, headers=headers)

                    if delete_response.status_code == 204:
                        logger.info(f"✅ Removed obsolete IP: {netbox_address}")
                    else:
                        logger.error(f"Failed to remove IP {netbox_address}: {delete_response.status_code}")

        except Exception as e:
            logger.error(f"Error removing obsolete IPs from interface {ifname}: {e}")
