import json
import logging
import os
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


@dataclass
class PrimaryIps:
    netbox: object  # Not used but kept for compatibility
    public_ips: dict
    primary_interface_mac: str
    ip_data: dict

    tenant: int
    vrf: int
    site: int
    device: object

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        self.netbox_url = os.environ.get("NETBOX_URL", "").rstrip("/")
        self.netbox_headers = {
            "Authorization": f"Token {os.environ.get('NETBOX_TOKEN', '')}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Check if device has discovery-primary-ip-sync tag
        if not self._has_primary_ip_sync_tag():
            logger.info("Device does not have 'discovery-primary-ip-sync' tag - skipping primary IP synchronization")
            return

        self.private_ipv4 = None
        self.primary_interface_id = None

        # Find the primary interface ID by MAC address
        if self.primary_interface_mac:
            self.primary_interface_id = self._find_interface_by_mac(self.primary_interface_mac)

        for ip_data in self.ip_data:
            if self.primary_interface_mac:
                # Check if ip_data has 'address' key, otherwise look for 'ifname' or other keys
                interface_identifier = ip_data.get("address") or ip_data.get("ifname") or ip_data.get("mac")
                if interface_identifier and interface_identifier.lower() == self.primary_interface_mac.lower():
                    for ip_address in ip_data["addr_info"]:
                        if ip_address["family"] == "inet":
                            self.private_ipv4 = ip_address["local"]
                            logger.info(f"Identified private IPv4: {self.private_ipv4}")

        if "ipv4" in self.public_ips and self.public_ips["ipv4"] not in [None, ""]:
            logger.info(f"Processing public IPv4 address: {self.public_ips['ipv4']}")

            # Check if this is a direct-bound scenario (public IP == private IP)
            is_direct_bound = self.private_ipv4 and self.private_ipv4 == self.public_ips["ipv4"]

            if is_direct_bound:
                logger.info(
                    f"Direct-bound scenario detected: public IP {self.public_ips['ipv4']} is bound directly to interface"
                )

            # Get IPv4 prefix
            logger.debug(f"Looking up prefix for IPv4 address: {self.public_ips['ipv4']}")
            prefix = self._lookup_prefix(ip_address=self.public_ips["ipv4"], family=4)

            if prefix:
                ip_address = f"{self.public_ips['ipv4']}/{prefix}"
                logger.info(f"Successfully found prefix {prefix} for IPv4. Composed address: {ip_address}")
            else:
                logger.warning(f"Warning: No prefix found for IPv4 {self.public_ips['ipv4']}")
                ip_address = self.public_ips["ipv4"]

            # Check if IPv4 public IP address exists
            logger.debug(f"Checking if IPv4 address {ip_address} exists in NetBox")
            url = f"{self.netbox_url}/api/ipam/ip-addresses/"
            params = {"address": ip_address}
            response = requests.get(url, headers=self.netbox_headers, params=params)
            response.raise_for_status()
            data = response.json()
            ipv4_object = data["results"][0] if data.get("results") else None

            if ipv4_object:
                logger.info(f"IPv4 address {ip_address} found in NetBox with ID: {ipv4_object['id']}")

                # Check if IPv4 is already assigned to an interface (from interfaces.py processing)
                if ipv4_object.get("assigned_object_id"):
                    interface_id = ipv4_object["assigned_object_id"]
                    interface_name = ipv4_object.get("assigned_object", {}).get("name", f"ID:{interface_id}")
                    logger.info(
                        f"IPv4 {ip_address} already assigned to interface {interface_name} - preserving assignment"
                    )
                else:
                    logger.info(f"IPv4 {ip_address} is floating/unassigned - keeping as floating")
            else:
                logger.info(f"IPv4 address {ip_address} not found in NetBox")

            # Create missing IPv4 address if they dont exist
            if not ipv4_object:
                logger.info(f"IPv4 {ip_address} not found, creating new IP address entry")
                # For direct-bound scenario, assign to interface; otherwise create floating
                interface_for_creation = self.primary_interface_id if is_direct_bound else None
                ipv4_object = self._create_pub_ip(ip_address=ip_address, interface_id=interface_for_creation)
                if ipv4_object:
                    logger.info(f"Successfully created IPv4 address {ip_address} with ID: {ipv4_object['id']}")
                else:
                    logger.error(f"Failed to create IPv4 address {ip_address}")

            # Assign primary IPv4 address
            if ipv4_object:
                logger.debug(f"Checking if IPv4 {ip_address} (ID: {ipv4_object['id']}) exists as gateway")
                if not self._gateway_exists(ip_address_id=ipv4_object["id"]):
                    logger.info(f"IPv4 {ip_address} is not a gateway, proceeding with primary assignment")

                    # Handle NAT inside assignment if private IPv4 exists
                    if self.private_ipv4:
                        logger.debug(f"Private IPv4 {self.private_ipv4} found, setting up NAT relationship")

                        # Find the full private IP address with prefix from the network data
                        private_ip_with_prefix = self._find_private_ip_with_prefix(self.private_ipv4)
                        logger.info(f"Searching for private IP: {private_ip_with_prefix}")

                        private_params = {
                            "address": private_ip_with_prefix,
                            "tenant_id": self.tenant["id"],
                            "vrf_id": self.vrf["id"],
                        }
                        private_response = requests.get(url, headers=self.netbox_headers, params=private_params)
                        private_response.raise_for_status()
                        private_data = private_response.json()
                        private_ipv4_object = private_data["results"][0] if private_data.get("results") else None

                        # If private IP doesn't exist, create it
                        if not private_ipv4_object:
                            logger.info(f"Private IP {private_ip_with_prefix} not found, creating it")
                            private_ipv4_object = self._create_pub_ip(
                                ip_address=private_ip_with_prefix, interface_id=self.primary_interface_id
                            )

                        if private_ipv4_object:
                            logger.debug(f"Found private IPv4 object with ID: {private_ipv4_object['id']}")
                            self._set_nat_inside(public_ip_address=ipv4_object, private_ip_address=private_ipv4_object)
                            logger.info(
                                f"NAT relationship established between public {ip_address} and private {self.private_ipv4}"
                            )
                        else:
                            logger.warning(f"Private IPv4 object not found for address {self.private_ipv4}")
                    else:
                        logger.debug("No private IPv4 address found, skipping NAT setup")

                    # Assign as primary IPv4
                    logger.info(f"Assigning IPv4 {ip_address} as primary IP for device")
                    self._assign_primary_ip(ip_adress=ipv4_object, family=4)
                    logger.info(f"Successfully assigned IPv4 {ip_address} as primary IP")
                else:
                    logger.info(f"IPv4 {ip_address} exists as gateway, skipping primary IP assignment")
            else:
                logger.warning("No valid IPv4 object available for primary assignment")

        if "ipv6" in self.public_ips and self.public_ips["ipv6"] not in [None, ""]:
            logger.info(f"Processing public IPv6 address: {self.public_ips['ipv6']}")

            # Get IPv6 prefix
            logger.debug(f"Looking up prefix for IPv6 address: {self.public_ips['ipv6']}")
            prefix = self._lookup_prefix(ip_address=self.public_ips["ipv6"], family=6)

            if prefix:
                ip_address = f"{self.public_ips['ipv6']}/{prefix}"
                logger.info(f"Successfully found prefix {prefix} for IPv6. Composed address: {ip_address}")
            else:
                logger.warning(f"Warning: No prefix found for IPv6 {self.public_ips['ipv6']}")
                ip_address = self.public_ips["ipv6"]

            # Check if IPv6 address exists
            logger.debug(f"Checking if IPv6 address {ip_address} exists in NetBox")
            params = {"address": ip_address, "tenant_id": self.tenant["id"], "vrf_id": self.vrf["id"]}
            response = requests.get(url, headers=self.netbox_headers, params=params)
            response.raise_for_status()
            data = response.json()
            ipv6_object = data["results"][0] if data.get("results") else None

            if ipv6_object:
                logger.info(f"IPv6 address {ip_address} found in NetBox with ID: {ipv6_object['id']}")

                # Check if IPv6 is already assigned to the correct interface
                if (
                    not ipv6_object.get("assigned_object_id")
                    or ipv6_object.get("assigned_object_id") != self.primary_interface_id
                ):
                    logger.info(
                        f"IPv6 address {ip_address} needs to be assigned to primary interface {self.primary_interface_id}"
                    )
                    # Update IPv6 to assign it to the primary interface
                    update_url = f"{self.netbox_url}/api/ipam/ip-addresses/{ipv6_object['id']}/"
                    update_data = {
                        "assigned_object_type": "dcim.interface",
                        "assigned_object_id": self.primary_interface_id,
                        "is_primary": False,
                    }
                    update_response = requests.patch(update_url, headers=self.netbox_headers, json=update_data)
                    if update_response.status_code == 200:
                        ipv6_object = update_response.json()
                        logger.info(f"Successfully assigned IPv6 {ip_address} to interface {self.primary_interface_id}")
                    else:
                        logger.error(f"Failed to assign IPv6 to interface: {update_response.text}")
            else:
                logger.info(f"IPv6 address {ip_address} not found in NetBox")

            # Create missing IPv6 address if they dont exist
            if not ipv6_object:
                logger.info(f"IPv6 {ip_address} not found, creating new IP address entry")
                ipv6_object = self._create_pub_ip(ip_address=ip_address, interface_id=self.primary_interface_id)
                if ipv6_object:
                    logger.info(f"Successfully created IPv6 address {ip_address} with ID: {ipv6_object['id']}")
                else:
                    logger.error(f"Failed to create IPv6 address {ip_address}")

            # Assign primary IPv6 address
            if ipv6_object:
                logger.debug(f"Checking if IPv6 {ip_address} (ID: {ipv6_object['id']}) exists as gateway")
                if not self._gateway_exists(ip_address_id=ipv6_object["id"]):
                    logger.info(f"IPv6 {ip_address} is not a gateway, proceeding with primary assignment")
                    logger.info(f"Assigning IPv6 {ip_address} as primary IP for device")
                    self._assign_primary_ip(ip_adress=ipv6_object, family=6)
                    logger.info(f"Successfully assigned IPv6 {ip_address} as primary IP")
                else:
                    logger.info(f"IPv6 {ip_address} exists as gateway, skipping primary IP assignment")
            else:
                logger.warning("No valid IPv6 object available for primary assignment")

        logger.info("Device primary IP assignment completed.")

        # Remove the discovery-ip-sync tag after processing
        self._remove_ip_sync_tag()

    def _has_primary_ip_sync_tag(self) -> bool:
        """Check if device has the 'discovery-primary-ip-sync' tag"""
        try:
            # Get device tags
            device_url = f"{self.netbox_url}/api/dcim/devices/{self.device.id}/"
            response = requests.get(device_url, headers=self.netbox_headers)
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
                    logger.info("Found 'discovery-primary-ip-sync' tag on device - enabling primary IP synchronization")
                    return True

            logger.info(
                f"Device does not have 'discovery-primary-ip-sync' tag - found tags: {[t.get('name') if isinstance(t, dict) else t for t in tags]}"
            )
            return False

        except Exception as e:
            logger.error(f"Error checking device tags: {str(e)}")
            logger.info("Assuming primary IP sync should proceed due to error")
            return True  # Default to allowing sync if we can't check tags

    def _remove_ip_sync_tag(self) -> None:
        """Remove the 'discovery-primary-ip-sync' tag from the device after processing"""
        try:
            # Get current device data
            device_url = f"{self.netbox_url}/api/dcim/devices/{self.device.id}/"
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

                if tag_name == "discovery-primary-ip-sync":
                    tag_found = True
                    logger.info("Removing 'discovery-primary-ip-sync' tag from device")
                else:
                    updated_tags.append(tag_id if isinstance(tag, dict) else tag)

            # Update device tags if the tag was found
            if tag_found:
                update_data = {"tags": updated_tags}
                update_response = requests.patch(device_url, headers=self.netbox_headers, json=update_data)
                if update_response.status_code == 200:
                    logger.info("Successfully removed 'discovery-primary-ip-sync' tag from device")
                else:
                    logger.error(f"Failed to remove discovery-primary-ip-sync tag: {update_response.text}")
            else:
                logger.debug("No discovery-primary-ip-sync tag found to remove")

        except Exception as e:
            logger.error(f"Error removing discovery-primary-ip-sync tag: {str(e)}")

    def _find_interface_by_mac(self, mac_address: str) -> int:
        """Find interface ID by MAC address"""
        try:
            url = f"{self.netbox_url}/api/dcim/interfaces/"
            params = {"device_id": self.device.id, "mac_address": mac_address.upper()}
            response = requests.get(url, headers=self.netbox_headers, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("results"):
                interface = data["results"][0]
                logger.info(
                    f"Found primary interface {interface['name']} (ID: {interface['id']}) with MAC {mac_address}"
                )
                return interface["id"]
            else:
                logger.warning(f"No interface found with MAC address {mac_address}")
                return None
        except Exception as e:
            logger.error(f"Error finding interface by MAC {mac_address}: {str(e)}")
            return None

    def _find_private_ip_with_prefix(self, private_ip: str) -> str:
        """Find the private IP with its prefix from the network data"""
        try:
            for ip_data in self.ip_data:
                if ip_data.get("addr_info"):
                    for addr in ip_data["addr_info"]:
                        if addr.get("family") == "inet" and addr.get("local") == private_ip:
                            prefix_len = addr.get("prefixlen", 24)  # Default to /24 if not found
                            full_address = f"{private_ip}/{prefix_len}"
                            logger.info(f"Found private IP with prefix: {full_address}")
                            return full_address

            # If not found in network data, default to /24
            logger.warning(f"Private IP {private_ip} not found in network data, defaulting to /24")
            return f"{private_ip}/24"
        except Exception as e:
            logger.error(f"Error finding private IP prefix: {str(e)}")
            return f"{private_ip}/24"

    def _prefix_search(self, **kwargs):
        """Search for prefixes with filters using REST API"""
        try:
            logger.debug(f"Searching for prefixes with filters: {kwargs}")
            url = f"{self.netbox_url}/api/ipam/prefixes/"
            params = {}
            for key, value in kwargs.items():
                params[key] = value

            response = requests.get(url, headers=self.netbox_headers, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("results"):
                logger.debug(f"Found {len(data['results'])} prefixes")
                return data["results"][0]
            else:
                logger.warning("No prefixes found with provided filters")
                return None
        except Exception as e:
            logger.error(f"Unexpected error during prefix search: {str(e)}")
            return None

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

    def _lookup_prefix(self, ip_address: str, family: str) -> str:
        # Perform the prefix search
        prefix_search_kwargs = {
            "contains": ip_address,
            "tenant_id": self.tenant["id"],
            "site_id": self.site["id"],
            "vrf_id": self.vrf["id"],
        }
        ip_prefix = self._prefix_search(**prefix_search_kwargs)
        if ip_prefix:
            prefix = ip_prefix["prefix"].split("/")[1]
            logger.info(f"Prefix found: {prefix}")
        else:
            if family == 4:
                prefix = 32
            elif family == 6:
                prefix = 128
                logger.info(f"No prefix found; defaulting to {prefix}")
        return prefix

    def _create_pub_ip(self, ip_address: str, interface_id: int = None) -> None:
        logger.info(f"Creating IP address: {ip_address} in tenant {self.tenant['id']}, VRF {self.vrf['id']}")

        # Prepare IP creation data
        ip_data = {
            "address": ip_address,
            "tenant": self.tenant["id"],
            "status": "active",
            "vrf": self.vrf["id"],
            "is_primary": False,  # Explicitly disable the "Make this the primary IP" checkbox
        }

        # If interface is provided, assign IP to that interface (for private IPs)
        if interface_id:
            ip_data["assigned_object_type"] = "dcim.interface"
            ip_data["assigned_object_id"] = interface_id
            logger.info(f"Assigning IP {ip_address} to interface ID {interface_id}")
        else:
            logger.info(f"Creating unassigned IP {ip_address} (will be set as primary on device)")

        netbox_ip = self._create_or_update_ip_address(**ip_data)

        if netbox_ip:
            logger.info(f"Successfully created IP address {ip_address} with ID: {netbox_ip['id']}")
        else:
            logger.error(f"Failed to create IP address {ip_address}")

        return netbox_ip

    def _set_nat_inside(self, public_ip_address, private_ip_address: object) -> None:
        if str(public_ip_address["address"]) != str(private_ip_address["address"]):
            logger.info(f"Setting NAT inside: {public_ip_address['address']} → {private_ip_address['address']}")
            nat_inside_id = private_ip_address["id"]
        else:
            logger.info("Public and private IPs are the same, unsetting NAT inside.")
            nat_inside_id = None

        update_url = f"{self.netbox_url}/api/ipam/ip-addresses/{public_ip_address['id']}/"
        update_data = {"nat_inside": nat_inside_id}
        response = requests.patch(update_url, headers=self.netbox_headers, json=update_data)
        response.raise_for_status()

    def _assign_primary_ip(self, ip_adress: object, family: int) -> None:
        logger.info(f"Assigning primary IP (family {family}): {ip_adress}")

        # Check if another device already has this IP as primary
        if family == 4:
            devices_url = f"{self.netbox_url}/api/dcim/devices/"
            params = {"primary_ip4_id": ip_adress["id"]}
            response = requests.get(devices_url, headers=self.netbox_headers, params=params)
            response.raise_for_status()
            data = response.json()
            existing_devices = data.get("results", [])

            if existing_devices:
                existing_device = existing_devices[0]
                if existing_device["id"] != self.device.id:
                    logger.warning(
                        f"IP {ip_adress} is already primary IPv4 for device {existing_device['id']}, unsetting it first",
                    )
                    update_url = f"{self.netbox_url}/api/dcim/devices/{existing_device['id']}/"
                    update_data = {"primary_ip4": None}
                    requests.patch(update_url, headers=self.netbox_headers, json=update_data)

            # Update current device with primary IPv4 using REST API
            device_update_url = f"{self.netbox_url}/api/dcim/devices/{self.device.id}/"
            device_update_data = {"primary_ip4": ip_adress["id"]}
            device_response = requests.patch(device_update_url, headers=self.netbox_headers, json=device_update_data)
            if device_response.status_code != 200:
                logger.warning(f"NetBox rejected unassigned IP as primary IPv4: {device_response.text}")
                logger.info(f"Skipping primary IPv4 assignment for floating IP {ip_adress['address']}")
            else:
                logger.info(f"Successfully set primary IPv4 {ip_adress['address']} on device")
        elif family == 6:
            devices_url = f"{self.netbox_url}/api/dcim/devices/"
            params = {"primary_ip6_id": ip_adress["id"]}
            response = requests.get(devices_url, headers=self.netbox_headers, params=params)
            response.raise_for_status()
            data = response.json()
            existing_devices = data.get("results", [])

            if existing_devices:
                existing_device = existing_devices[0]
                if existing_device["id"] != self.device.id:
                    logger.warning(
                        f"IP {ip_adress} is already primary IPv6 for device {existing_device['id']}, unsetting it first",
                    )
                    update_url = f"{self.netbox_url}/api/dcim/devices/{existing_device['id']}/"
                    update_data = {"primary_ip6": None}
                    requests.patch(update_url, headers=self.netbox_headers, json=update_data)

            # Update current device with primary IPv6 using REST API
            device_update_url = f"{self.netbox_url}/api/dcim/devices/{self.device.id}/"
            device_update_data = {"primary_ip6": ip_adress["id"]}
            device_response = requests.patch(device_update_url, headers=self.netbox_headers, json=device_update_data)
            if device_response.status_code != 200:
                logger.warning(f"NetBox rejected unassigned IP as primary IPv6: {device_response.text}")
                logger.info(f"Skipping primary IPv6 assignment for floating IP {ip_adress['address']}")
            else:
                logger.info(f"Successfully set primary IPv6 {ip_adress['address']} on device")

    def _gateway_exists(self, ip_address_id: int) -> bool:
        url = f"{self.netbox_url}/api/plugins/nb-gateways/gateway/?gateway_ip={ip_address_id}&vrf={self.vrf['id']}"
        logger.info(f"Checking for existing gateway with IP ID {ip_address_id}")
        response = requests.get(url, headers=self.netbox_headers)
        logger.debug(response.status_code)
        logger.debug(response.text)

        if response.status_code == 200:
            json_response = json.loads(response.text)
            if "count" in json_response and json_response["count"] > 0:
                logger.info(f"Gateway exists for IP ID {ip_address_id}")
                return True
        logger.info(f"No gateway found for IP ID {ip_address_id}")
        return False
