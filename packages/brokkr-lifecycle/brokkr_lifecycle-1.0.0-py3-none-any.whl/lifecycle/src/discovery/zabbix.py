import ipaddress
import logging
import os
import random
import secrets
import time
from dataclasses import dataclass

from zabbix_utils import ZabbixAPI

logger = logging.getLogger(__name__)


@dataclass
class ZabbixManager:
    device_id: str
    mode: str  # Required: "lifecycle", "discovery", or "bridge"
    job_id: str = None
    # Optional parameters for discovery mode
    device: object = None
    discovery_doc: object = None
    associated_bridges_ids: list = None
    associated_bridges_wt0_ips: list = None
    netbox: object = None
    vrf: object = None
    # Optional parameters for bridge mode
    bridge_wt0_ip: str = None
    bridge_device: object = None
    vault_instance: object = None

    def __post_init__(self):
        self.logger = logging.getLogger(__name__)
        logger.warning(f"Entering {os.path.basename(__file__)} Zabbix class")

        # Validate mode parameter
        if self.mode not in ["lifecycle", "discovery", "bridge"]:
            raise ValueError(f"Invalid mode '{self.mode}'. Must be 'lifecycle', 'discovery', or 'bridge'")

        logger.info(f"Zabbix mode: {self.mode}")

        self.zabbix_uri = f"https://brokkr.monitor.{os.environ['HH_ENV']}.hydra.host"
        logger.info(f"Zabbix URI: {self.zabbix_uri}")

        # Initialize mode-specific attributes
        if self.mode == "lifecycle":
            self.zabbix_psk = secrets.token_hex(16)
            self.zabbix_psk_id = str(self.device_id)
        elif self.mode == "discovery":
            self._initialize_discovery_mode()
        elif self.mode == "bridge":
            self._initialize_bridge_mode()

        try:
            logger.info(f"Attempting to connect to Zabbix at: {self.zabbix_uri}")
            # Retry logic for connection
            max_retries = 3
            retry_delay = 5  # seconds

            for attempt in range(max_retries):
                try:
                    # Initialize Zabbix API with timeout settings
                    self.zabbix_api = ZabbixAPI(url=self.zabbix_uri, skip_version_check=False, timeout=30)

                    # Login with token
                    self.zabbix_api.login(token=os.environ["MONITOR_ZABBIX_TOKEN"])
                    logger.info(f"Successfully connected to Zabbix on attempt {attempt + 1}")
                    break

                except Exception as retry_error:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Connection attempt {attempt + 1} failed: {str(retry_error)}. Retrying in {retry_delay} seconds...",
                        )
                        time.sleep(retry_delay)
                    else:
                        raise retry_error

            # Execute mode-specific operations
            if self.mode == "lifecycle":
                zabbix_success = self.update_host()
                if zabbix_success:
                    logger.info("Zabbix host updated successfully")
                else:
                    logger.error("Zabbix update failed")
            elif self.mode == "discovery":
                self.create_host_group()
                self.manage_host()
            elif self.mode == "bridge":
                self.create_bridge_host_groups()
                self.manage_bridge_host()

        except Exception as e:
            logger.error(f"Error connecting to Zabbix: {str(e)}")
            raise e

    def _initialize_discovery_mode(self):
        """Initialize discovery mode specific attributes"""
        if not self.device:
            raise ValueError("Device object required for discovery mode")
        if not self.discovery_doc:
            raise ValueError("Discovery document required for discovery mode")
        if not self.netbox:
            raise ValueError("NetBox object required for discovery mode")
        if not self.vrf:
            raise ValueError("VRF object required for discovery mode")

        self.zabbix_host_group = f"bridge-{self.device.tenant.id}-{self.device.site.id}-{self.device.location.id}"
        logger.info(f"Calculated Zabbix host group: {self.zabbix_host_group}")

        # Extract monitoring IPs from discovery document
        bmc_raw = self.discovery_doc.get("bmc", {}).get("ipv4", None)
        self.bmc_ip = str(ipaddress.ip_interface(bmc_raw).ip) if bmc_raw else None
        self.station_ip = self.discovery_doc.get("bdi", {}).get("station_ip", None)

        if self.discovery_doc.get("public_ips", {}).get("ipv4", None):
            self.gateway_exists = self._gateway_exists(self.discovery_doc.get("public_ips", {}).get("ipv4", None))
            if self.gateway_exists:
                self.public_ip = None
                logger.info(f"Gateway exists for IP {self.discovery_doc.get('public_ips', {}).get('ipv4', None)}")
            else:
                self.public_ip = self.discovery_doc.get("public_ips", {}).get("ipv4", None)
                logger.info(f"No gateway exists for IP {self.discovery_doc.get('public_ips', {}).get('ipv4', None)}")
        else:
            self.public_ip = None
            self.gateway_exists = False
            logger.info("No public IP found")
        logger.info(f"BMC IP: {self.bmc_ip}, Station IP: {self.station_ip}, Public IP: {self.public_ip}")

        self.monitoring_ip = self.bmc_ip or self.station_ip
        logger.info(f"Selected monitoring IP: {self.monitoring_ip}")

    def _initialize_bridge_mode(self):
        """Initialize bridge mode specific attributes"""
        if not self.bridge_device:
            raise ValueError("Bridge device object required for bridge mode")
        if not self.bridge_wt0_ip:
            raise ValueError("Bridge wt0 IP required for bridge mode")
        if not self.vault_instance:
            raise ValueError("Vault instance required for bridge mode")

        # Extract clean IP without CIDR notation if present
        self.bridge_ip_clean = self.bridge_wt0_ip.split("/")[0]

        # Set up host name format
        self.bridge_host_name = (
            f"bridge-{self.bridge_device.tenant.id}-{self.bridge_device.site.id}-"
            f"{self.bridge_device.location.id}-{self.bridge_device.id}.{os.environ['HH_ENV']}.hydra.host"
        )

        # Get PSK from Vault
        self._get_bridge_psk()

        logger.info(f"Bridge mode initialized - Host name: {self.bridge_host_name}")
        logger.info(f"Bridge wt0 IP: {self.bridge_ip_clean}")

    def _get_bridge_psk(self):
        """Get or create PSK for bridge from Vault"""
        zabbix_psk_path = (
            f"{self.bridge_device.tenant.id}/{self.bridge_device.site.id}/"
            f"{self.bridge_device.location.id}/application/zabbix/psk"
        )

        try:
            psk_data = self.vault_instance.get_secret(zabbix_psk_path, mount_point="brokkr")
            logger.info("Zabbix PSK already exists in Vault.")
            self.zabbix_psk = psk_data.get("psk_key")
        except Exception:
            logger.info("No Zabbix PSK available in Vault. Generating new PSK.")
            # Generate a 32-character hexadecimal PSK (128-bit)
            self.zabbix_psk = secrets.token_hex(16)

            psk_data = {"psk_key": self.zabbix_psk}
            self.vault_instance.set_secret(mount_point="brokkr", secret_path=zabbix_psk_path, secret_data=psk_data)
            logger.info(f"New Zabbix PSK saved in Vault at {zabbix_psk_path}.")

        # PSK identity is the netbox device ID
        self.zabbix_psk_id = str(self.bridge_device.id)
        logger.info(f"PSK Identity: {self.zabbix_psk_id}")

    def update_host(self):
        """Update Zabbix host with PSK encryption settings or create if it doesn't exist"""
        logger.info(f"Looking for Zabbix host with device ID: {self.device_id}")

        try:
            # Find the host by device ID (which is used as the host name)
            existing_host = self.zabbix_api.host.get(filter={"host": self.device_id})
            logger.info(f"Host query result: {len(existing_host) if existing_host else 0} hosts found")

            if not existing_host:
                logger.info(f"Host with device ID {self.device_id} not found in Zabbix, creating new host")
                create_result = self._create_host()
                if create_result:
                    logger.info(f"Successfully created new host for device ID {self.device_id}")
                else:
                    logger.error(f"Failed to create new host for device ID {self.device_id}")
                return create_result

            host = existing_host[0]
            host_id = host["hostid"]
            host_name = host.get("name", "Unknown")

            logger.info(f"Found Zabbix host: ID {host_id}, Name: {host_name}")

            # Log current encryption settings before update
            current_tls_connect = host.get("tls_connect", "1")  # 1=No encryption, 2=PSK, 4=Certificate
            current_tls_accept = host.get("tls_accept", "1")
            current_psk_identity = host.get("tls_psk_identity", "")

            # Log current vs new encryption settings
            tls_connect_map = {"1": "No encryption", "2": "PSK", "4": "Certificate"}
            current_connect_desc = tls_connect_map.get(str(current_tls_connect), f"Unknown ({current_tls_connect})")
            current_accept_desc = tls_connect_map.get(str(current_tls_accept), f"Unknown ({current_tls_accept})")

            logger.info(f"Current encryption - Connect: {current_connect_desc}, Accept: {current_accept_desc}")
            logger.info(f"Current PSK Identity: '{current_psk_identity}'")

            # Determine monitoring configuration
            use_proxy, marketplace_proxy_group_id, monitoring_description = self._determine_monitoring_config(
                self.device_id
            )

            current_monitored_by = host.get("monitored_by", "0")
            current_proxy_groupid = host.get("proxy_groupid", "0")

            # Check if PSK settings need updating
            psk_needs_update = (
                str(current_tls_connect) != "2"
                or str(current_tls_accept) != "2"
                or current_psk_identity != self.zabbix_psk_id
            )

            # Check if proxy group assignment needs updating
            proxy_needs_update = False
            if use_proxy and marketplace_proxy_group_id:
                # Should use proxy group
                proxy_needs_update = str(current_monitored_by) != "2" or str(current_proxy_groupid) != str(
                    marketplace_proxy_group_id
                )
            else:
                # Should use server monitoring
                proxy_needs_update = str(current_monitored_by) != "0"

            if psk_needs_update:
                logger.info(f"PSK encryption needs updating - updating host {host_id}")
                logger.info(f"New PSK Identity: '{self.zabbix_psk_id}'")
                logger.info(f"New PSK Key length: {len(self.zabbix_psk)} characters")
            else:
                logger.info(f"PSK encryption already configured correctly for host {host_id}")

            if proxy_needs_update:
                logger.info(f"Proxy assignment needs updating - {monitoring_description}")
            else:
                logger.info("Host already has correct monitoring assignment")

            # Get existing macros for the host first
            existing_macros = self.zabbix_api.usermacro.get(hostids=host_id)
            logger.debug(f"Found {len(existing_macros)} existing macros on host")

            # Build the macros list starting with existing ones
            macros = []

            # Process existing macros
            last_job_macro_exists = False
            for macro in existing_macros:
                if macro.get("macro") == "{$LAST_JOB_ID}":
                    # Update the existing LAST_JOB_ID macro
                    if self.job_id:
                        macros.append(
                            {
                                "macro": "{$LAST_JOB_ID}",
                                "value": str(self.job_id),
                                "description": "Last lifecycle job ID",
                            }
                        )
                        last_job_macro_exists = True
                        logger.info(f"Updating existing LAST_JOB_ID macro with value: {self.job_id}")
                else:
                    # Keep all other existing macros unchanged
                    macro_dict = {
                        "macro": macro["macro"],
                        "value": macro["value"],
                        "description": macro.get("description", ""),
                    }
                    if "type" in macro:
                        macro_dict["type"] = macro["type"]
                    macros.append(macro_dict)

            # Add new LAST_JOB_ID macro if it doesn't exist and we have a job_id
            macro_needs_update = False
            if self.job_id and not last_job_macro_exists:
                macros.append(
                    {"macro": "{$LAST_JOB_ID}", "value": str(self.job_id), "description": "Last lifecycle job ID"}
                )
                macro_needs_update = True
                logger.info(f"Adding new LAST_JOB_ID macro with value: {self.job_id}")

            # Only update if PSK settings, proxy group, or macros need updating
            if psk_needs_update or proxy_needs_update or macro_needs_update or last_job_macro_exists:
                update_params = {
                    "hostid": host_id,
                    "tls_connect": 2,
                    "tls_accept": 2,
                    "tls_psk_identity": self.zabbix_psk_id,
                    "tls_psk": self.zabbix_psk,
                }

                # Add monitoring settings based on device ID and proxy availability
                if use_proxy and marketplace_proxy_group_id:
                    update_params.update(
                        {
                            "monitored_by": 2,  # Monitored by proxy group
                            "proxy_groupid": marketplace_proxy_group_id,
                        }
                    )
                else:
                    update_params["monitored_by"] = 0  # Monitored by server

                # Add macros if we have any
                if macros:
                    update_params["macros"] = macros

                logger.info(f"Performing Zabbix host update for host {host_id}")

                # Retry logic for handling race conditions and slow DB
                max_retries = 5
                retry_delay = 2  # Initial delay in seconds

                for attempt in range(max_retries):
                    try:
                        result = self.zabbix_api.host.update(**update_params)
                        break  # Success, exit retry loop
                    except Exception as update_error:
                        error_str = str(update_error).lower()

                        # Check if it's a duplicate key/macro conflict
                        if "duplicate" in error_str or "sql" in error_str:
                            if attempt < max_retries - 1:
                                # Add jitter to avoid thundering herd
                                jittered_delay = retry_delay * (1 + random.random() * 0.3)
                                logger.warning(
                                    f"Host update failed (attempt {attempt + 1}/{max_retries}) - likely race condition. "
                                    f"Retrying in {jittered_delay:.1f} seconds...",
                                )
                                time.sleep(jittered_delay)

                                # Exponential backoff
                                retry_delay = min(retry_delay * 2, 30)  # Cap at 30 seconds

                                # Re-fetch macros to avoid conflicts
                                try:
                                    existing_macros = self.zabbix_api.usermacro.get(hostids=host_id)
                                    # Rebuild macros list with fresh data
                                    macros = []
                                    for macro in existing_macros:
                                        if macro.get("macro") == "{$LAST_JOB_ID}":
                                            if self.job_id:
                                                macros.append(
                                                    {
                                                        "macro": "{$LAST_JOB_ID}",
                                                        "value": str(self.job_id),
                                                        "description": "Last lifecycle job ID",
                                                    }
                                                )
                                        else:
                                            macro_dict = {
                                                "macro": macro["macro"],
                                                "value": macro["value"],
                                                "description": macro.get("description", ""),
                                            }
                                            if "type" in macro:
                                                macro_dict["type"] = macro["type"]
                                            macros.append(macro_dict)

                                    # Update params with refreshed macros
                                    if macros:
                                        update_params["macros"] = macros
                                except Exception as refresh_error:
                                    logger.warning(f"Failed to refresh macros: {refresh_error}")
                            else:
                                # Final attempt failed
                                raise update_error
                        else:
                            # Not a duplicate error, don't retry
                            raise update_error
            else:
                logger.info(f"No updates needed for host {host_id} - skipping API call")
                result = True  # Consider it successful since no update was needed

            if result:
                logger.info(f"Successfully updated PSK encryption for host {host_id} ({host_name})")
                return True
            else:
                logger.error(f"Failed to update PSK encryption for host {host_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating host PSK encryption: {str(e)}")

            # Log additional error details if available
            if hasattr(e, "error"):
                logger.error(f"Zabbix API error details: {e.error}")

            return False

    def _create_host(self):
        """Create a new Zabbix host with PSK encryption settings"""
        try:
            # Use default Brokkr host group (similar to discovery function pattern)
            host_group_name = "Brokkr"
            existing_group = self.zabbix_api.hostgroup.get(filter={"name": host_group_name})

            if not existing_group:
                logger.info(f"Host group '{host_group_name}' not found in Zabbix, creating it")
                try:
                    created_group = self.zabbix_api.hostgroup.create(name=host_group_name)
                    host_group_id = created_group["groupids"][0]
                    logger.info(f"Created host group '{host_group_name}' with ID: {host_group_id}")
                except Exception as group_error:
                    logger.error(f"Failed to create host group '{host_group_name}': {str(group_error)}")
                    return False
            else:
                host_group_id = existing_group[0]["groupid"]
                logger.info(f"Using existing host group: {host_group_name} (ID: {host_group_id})")

            # Use device_id as host name, ensuring it's a string
            host_name = str(self.device_id)

            # Determine monitoring configuration
            use_proxy, marketplace_proxy_group_id, monitoring_description = self._determine_monitoring_config(
                self.device_id
            )

            # Prepare basic host data (following discovery function pattern)
            tags = [{"tag": "device_id", "value": host_name}, {"tag": "source", "value": "self_help_onboarding"}]

            # Prepare macros
            macros = []
            if self.job_id:
                macros.append(
                    {"macro": "{$LAST_JOB_ID}", "value": str(self.job_id), "description": "Last lifecycle job ID"}
                )

            # Create host without interfaces first (following discovery function pattern)
            host_params = {
                "host": host_name,
                "name": host_name,
                "groups": [{"groupid": host_group_id}],
                "tags": tags,
                "macros": macros,
                "tls_connect": 2,  # PSK encryption
                "tls_accept": 2,  # PSK encryption
                "tls_psk_identity": self.zabbix_psk_id,
                "tls_psk": self.zabbix_psk,
            }

            # Add monitoring settings based on configuration
            if use_proxy and marketplace_proxy_group_id:
                host_params.update(
                    {
                        "monitored_by": 2,  # Monitored by proxy group
                        "proxy_groupid": marketplace_proxy_group_id,
                    }
                )
            else:
                host_params["monitored_by"] = 0  # Monitored by server

            logger.info(f"Creating host - {monitoring_description}")

            logger.info(f"Creating new Zabbix host with device ID: {host_name}")
            logger.info(f"PSK Identity: '{self.zabbix_psk_id}'")
            logger.info(f"PSK Key length: {len(self.zabbix_psk)} characters")

            # Create host first (without templates, following discovery pattern)
            result = self.zabbix_api.host.create(**host_params)

            if result and "hostids" in result:
                host_id = result["hostids"][0]
                logger.info(f"Successfully created new Zabbix host {host_name} with ID: {host_id}")

                # Add basic ICMP template (following discovery function pattern)
                try:
                    template_name = "Brokkr - Hydra Host - ICMP Ping IPMI Primary Address"
                    template = self.zabbix_api.template.get(filter={"host": template_name})
                    if template:
                        template_id = template[0]["templateid"]
                        self.zabbix_api.host.update(hostid=host_id, templates=[{"templateid": template_id}])
                        logger.info(f"Applied template '{template_name}' to host {host_name}")
                    else:
                        logger.warning(f"Template '{template_name}' not found, skipping template assignment")
                except Exception as template_error:
                    logger.warning(f"Warning: Failed to apply template to new host: {str(template_error)}")

                return True
            else:
                logger.error(f"Failed to create new Zabbix host {host_name}")
                return False

        except Exception as e:
            logger.error(f"Error creating new Zabbix host: {str(e)}")

            # Log additional error details if available
            if hasattr(e, "error"):
                logger.error(f"Zabbix API error details: {e.error}")

            return False

    # Discovery mode methods
    def create_host_group(self):
        """Create host group for discovery mode"""
        if self.mode != "discovery":
            raise ValueError("create_host_group() only available in discovery mode")

        logger.info(f"Checking if host group '{self.zabbix_host_group}' exists in Zabbix")
        existing = self.zabbix_api.hostgroup.get(filter={"name": [self.zabbix_host_group]})
        if existing:
            self.zabbix_host_group_id = existing[0]["groupid"]
            logger.info(f"Host group already exists with ID {self.zabbix_host_group_id}")
        else:
            logger.info(f"Host group '{self.zabbix_host_group}' not found. Creating new group.")
            created = self.zabbix_api.hostgroup.create(name=self.zabbix_host_group)
            self.zabbix_host_group_id = created["groupids"][0]
            logger.info(f"Created new host group with ID {self.zabbix_host_group_id}")

    def get_template_names(self, device_status, host_name, agent_interface_available=False):
        """
        Build Zabbix template list progressively based on device conditions.
        Templates are appended as checks are validated.
        """
        if self.mode != "discovery":
            raise ValueError("get_template_names() only available in discovery mode")

        zabbix_template_names = []

        # Base ICMP IPMI template - always added for all devices
        zabbix_template_names.append("Brokkr - Hydra Host - ICMP Ping IPMI Address - API")
        logger.info(f"Added base IPMI template for device {host_name}")

        # Private network ping - always added for all devices
        zabbix_template_names.append("Brokkr - Hydra Host - ICMP Ping Private Address - API")
        logger.info(f"Added private ping template for device {host_name}")

        # Public IP ping template - only if public IP exists
        if self.public_ip:
            zabbix_template_names.append("Brokkr - Hydra Host - ICMP Ping Public Primary Address")
            logger.info(f"Added public ping template for device {host_name} (public IP: {self.public_ip})")
        else:
            logger.info(f"No public IP found for device {host_name}")

        # Advanced monitoring templates
        if device_status in ["inventory", "planned", "provisioning", "decommissioning"]:
            # Agent-based templates - only if agent interface is available
            if agent_interface_available:
                # BMC data collection via agent
                if self.bmc_ip:
                    zabbix_template_names.append("Brokkr - Hydra Host - BMC Data Collector - API")
                    logger.info(f"Added BMC data collector template for device {host_name}")

                # IPMI sensor collection via agent
                if self.bmc_ip:
                    zabbix_template_names.append("Brokkr - Hydra Host - IPMI Sensor Collector - API")
                    logger.info(f"Added IPMI sensor template for device {host_name}")

                # IPMI security monitoring via agent
                if self.bmc_ip:
                    zabbix_template_names.append("Brokkr - Hydra Host - Security Collector - API")
                    logger.info(f"Added Security Collector template for device {host_name}")

                # Linux agent monitoring
                zabbix_template_names.append("Brokkr - Hydra Host - Linux by Zabbix agent")
                logger.info(f"Added Linux agent template for device {host_name}")

                # NVIDIA monitoring - only if GPU count is greater than 0
                gpu_count = self.device.custom_fields.get("gpu_count")
                if gpu_count and gpu_count > 0:
                    zabbix_template_names.append("Brokkr - Hydra Host - NVIDIA Extension Metrics by Zabbix Agent")
                    zabbix_template_names.append("Nvidia by Zabbix agent 2")
                    logger.info(f"Added NVIDIA monitoring templates for device {host_name} (GPU count: {gpu_count})")
            else:
                logger.info(f"Device {host_name} has no agent interface available - skipping agent-based templates")

        # Log final template selection
        template_count = len(zabbix_template_names)
        if device_status == "planned":
            logger.info(f"Device {host_name} is in planned state - using {template_count} templates (ICMP set)")
        elif device_status in ["inventory", "provisioning", "decommissioning"]:
            logger.info(
                f"Device {host_name} is in {device_status} state - using {template_count} templates (full monitoring set)"
            )

        return zabbix_template_names

    def manage_host(self):
        """Manage Zabbix host for discovery mode"""
        if self.mode != "discovery":
            raise ValueError("manage_host() only available in discovery mode")

        host_name = str(self.device.id)
        device_status = str(self.device.status).lower()

        # Get PSK from device custom fields
        logger.info(f"Getting PSK from device custom fields for device {host_name}")
        monitor_psk = self.device.custom_fields.get("monitor_psk")
        if monitor_psk:
            logger.info(f"Found monitor_psk for device {host_name}")
        else:
            logger.warning(f"No monitor_psk found for device {host_name}")

        # Prepare basic host data first
        tags = [
            {"tag": "tenant", "value": str(self.device.tenant.id)},
            {"tag": "site", "value": str(self.device.site.id)},
            {"tag": "location", "value": str(self.device.location.id)},
            {"tag": "role", "value": str(self.device.role.name)},
            {"tag": "device_id", "value": str(self.device.id)},
        ]
        logger.info(f"Tags: {tags}")

        macros = []
        if self.bmc_ip:
            macros.append({"macro": "{$HOST.IPMI.ADDRESS}", "value": str(self.bmc_ip)})
        if self.station_ip:
            macros.append({"macro": "{$HOST.PRIVATE.ADDRESS}", "value": str(self.station_ip)})
        if self.public_ip:
            macros.append({"macro": "{$HOST.PUBLIC.ADDRESS}", "value": str(self.public_ip)})

        # Add IPMI macros
        macros.append({"macro": "{$IPMI.PORT}", "value": "623"})

        # Construct vault path for IPMI credentials using the specified format
        # Format: brokkr/<tenant ID>/<site id>/<location id>/marketplace-hosts/<device id>/bmc:bmc_<secret>
        vault_path = f"brokkr/{self.device.tenant.id}/{self.device.site.id}/{self.device.location.id}/marketplace-hosts/{self.device.id}/bmc"

        # Create vault macros with proper Zabbix API format
        macros.append(
            {
                "macro": "{$IPMI.USERNAME}",
                "value": f"{vault_path}:bmc_user",
                "type": "2",  # Zabbix vault macro type
            }
        )
        macros.append(
            {
                "macro": "{$IPMI.PASSWORD}",
                "value": f"{vault_path}:bmc_pass",
                "type": "2",  # Zabbix vault macro type
            }
        )

        logger.info(f"Added IPMI vault macros: vault_path={vault_path}")

        if self.associated_bridges_ids:
            logger.info(f"Adding tag for associated bridge IDs: {self.associated_bridges_ids}")
            tags.append({"tag": "associated_bridges", "value": ",".join(str(i) for i in self.associated_bridges_ids)})

            # Find primary bridge in provisioned/provisioning state
            primary_bridge_ip = self._get_primary_bridge_wt0_ip()
            if primary_bridge_ip:
                macros.append({"macro": "{$PRIMARY_BRIDGE_WT0_ADDRESS}", "value": primary_bridge_ip})
                logger.info(f"Added primary bridge macro: {{$PRIMARY_BRIDGE_WT0_ADDRESS}} = {primary_bridge_ip}")
            else:
                logger.warning("No primary bridge in provisioned/provisioning state found")

        if device_status == "planned":
            # Add other macros
            macros.extend([{"macro": "{$LAST_JOB_ID}", "value": "discovery"}])

        # Determine required interfaces and agent availability
        interfaces = []
        agent_interface_available = False

        # Agent interface condition: specific status AND public IP
        if device_status in ["inventory", "planned", "provisioning", "decommissioning"] and self.public_ip:
            interfaces = [
                {
                    "type": 1,  # Agent interface
                    "main": 1,
                    "useip": 1,
                    "ip": self.public_ip,
                    "dns": "",
                    "port": "10050",
                }
            ]
            agent_interface_available = True
            logger.info(f"Will create agent interface with IP: {self.public_ip}")

        try:
            # Determine monitoring configuration
            use_proxy, marketplace_proxy_group_id, monitoring_description = self._determine_monitoring_config(
                self.device.id
            )

            existing_host = self.zabbix_api.host.get(filter={"host": host_name})
            logger.info(f"Existing host: {existing_host}")

            if existing_host:
                host_id = existing_host[0]["hostid"]
                logger.info(f"Host {host_name} already exists in Zabbix (ID: {host_id}), updating...")

                # Step 1: Update basic host info (without templates initially)
                update_params = {
                    "hostid": host_id,
                    "name": host_name,
                    "groups": [{"groupid": self.zabbix_host_group_id}],
                    "tags": tags,
                    "macros": macros,
                }

                # Add monitoring settings based on configuration
                if use_proxy and marketplace_proxy_group_id:
                    update_params.update(
                        {
                            "monitored_by": 2,  # Monitored by proxy group
                            "proxy_groupid": marketplace_proxy_group_id,
                        }
                    )
                else:
                    update_params["monitored_by"] = 0  # Monitored by server

                logger.info(f"Updating host {host_name} - {monitoring_description}")

                # Add PSK parameters if available and agent interface exists
                if monitor_psk and agent_interface_available:
                    update_params.update(
                        {
                            "tls_connect": 2,
                            "tls_accept": 2,
                            "tls_psk_identity": str(self.device.id),
                            "tls_psk": monitor_psk,
                        }
                    )
                    logger.info(f"Adding PSK configuration for host {host_name}")

                # Retry logic for host update
                max_retries = 5
                retry_delay = 2

                for attempt in range(max_retries):
                    try:
                        self.zabbix_api.host.update(**update_params)
                        break
                    except Exception as update_error:
                        error_str = str(update_error).lower()
                        if ("duplicate" in error_str or "sql" in error_str) and attempt < max_retries - 1:
                            jittered_delay = retry_delay * (1 + random.random() * 0.3)
                            logger.warning(
                                f"Host update failed (attempt {attempt + 1}/{max_retries}) - retrying in {jittered_delay:.1f}s",
                            )
                            time.sleep(jittered_delay)
                            retry_delay = min(retry_delay * 2, 30)
                        else:
                            raise update_error

                # Step 2: Handle interfaces first
                if interfaces:
                    existing_interfaces = self.zabbix_api.hostinterface.get(hostids=[host_id], filter={"type": "1"})
                    desired_ip = interfaces[0]["ip"]
                    matched = False

                    for iface in existing_interfaces:
                        if iface["ip"] == desired_ip:
                            matched = True
                            logger.info(f"Matching agent interface already exists with IP: {desired_ip}")
                            break

                    if not matched:
                        if existing_interfaces:
                            iface = existing_interfaces[0]
                            self.zabbix_api.hostinterface.update(
                                interfaceid=iface["interfaceid"],
                                ip=desired_ip,
                                useip=1,
                                dns="",
                                port="10050",
                                main=1,
                                type=1,
                                hostid=host_id,
                            )
                            logger.info(f"Updated existing agent interface to IP: {desired_ip}")
                        else:
                            self.zabbix_api.hostinterface.create(
                                hostid=host_id, type=1, main=1, useip=1, ip=desired_ip, dns="", port="10050"
                            )
                            logger.info(f"Created new agent interface with IP: {desired_ip}")

                # Step 3: Now apply templates (after interfaces are ready)
                # Skip template updates for maintenance status devices to preserve existing templates
                if device_status != "maintenance":
                    zabbix_template_names = self.get_template_names(device_status, host_name, agent_interface_available)
                    template_ids = self._get_template_ids(zabbix_template_names)

                    # Retry logic for template update
                    for attempt in range(max_retries):
                        try:
                            self.zabbix_api.host.update(hostid=host_id, templates=template_ids)
                            logger.info(f"Successfully updated templates for Zabbix host {host_name}")
                            break
                        except Exception as template_error:
                            error_str = str(template_error).lower()
                            if ("duplicate" in error_str or "sql" in error_str) and attempt < max_retries - 1:
                                jittered_delay = retry_delay * (1 + random.random() * 0.3)
                                logger.warning(
                                    f"Template update failed (attempt {attempt + 1}/{max_retries}) - retrying in {jittered_delay:.1f}s",
                                )
                                time.sleep(jittered_delay)
                                retry_delay = min(retry_delay * 2, 30)
                            else:
                                raise template_error
                else:
                    logger.info(f"Skipping template update for Zabbix host {host_name} in maintenance status")

            else:
                # Creating new host
                logger.info(f"Creating new Zabbix host {host_name}")

                # For new hosts, we can include interfaces from the start
                host_params = {
                    "host": host_name,
                    "name": host_name,
                    "groups": [{"groupid": self.zabbix_host_group_id}],
                    "tags": tags,
                    "macros": macros,
                }

                # Add monitoring settings based on configuration
                if use_proxy and marketplace_proxy_group_id:
                    host_params.update(
                        {
                            "monitored_by": 2,  # Monitored by proxy group
                            "proxy_groupid": marketplace_proxy_group_id,
                        }
                    )
                else:
                    host_params["monitored_by"] = 0  # Monitored by server

                logger.info(f"Creating new host {host_name} - {monitoring_description}")
                logger.info(f"Host params: {host_params}")

                # Add PSK parameters if available and agent interface will be created
                if monitor_psk and agent_interface_available:
                    host_params.update(
                        {
                            "tls_connect": 2,
                            "tls_accept": 2,
                            "tls_psk_identity": str(self.device.id),
                            "tls_psk": monitor_psk,
                        }
                    )
                    logger.info(f"Adding PSK configuration for new host {host_name}")

                # Add interfaces if available
                if interfaces:
                    host_params["interfaces"] = interfaces
                    logger.info(f"Host params with interfaces: {host_params}")
                else:
                    logger.info(f"Host params without any interfaces: {host_params}")
                # Create host first (without templates)
                result = self.zabbix_api.host.create(**host_params)
                host_id = result["hostids"][0]
                logger.info(f"Created Zabbix host {host_name} with ID: {host_id}")

                # Now add templates to the created host
                # Skip template assignment for maintenance status devices to preserve existing templates
                if device_status != "maintenance":
                    zabbix_template_names = self.get_template_names(device_status, host_name, agent_interface_available)
                    template_ids = self._get_template_ids(zabbix_template_names)

                    if template_ids:
                        self.zabbix_api.host.update(hostid=host_id, templates=template_ids)
                        logger.info(f"Successfully applied templates to new Zabbix host {host_name}")
                else:
                    logger.info(f"Skipping template assignment for new Zabbix host {host_name} in maintenance status")

        except Exception as e:
            logger.error(f"Failed to create/update Zabbix host {host_name}: {str(e)}")
            raise

    def _gateway_exists(self, ip_address):
        """
        Check if an IP address exists as a gateway in NetBox using pynetbox client.

        Args:
            ip_address (str): The IP address to check (can be string IP or IP with CIDR)

        Returns:
            str or None: Returns the gateway IP if it exists, None otherwise
        """
        if self.mode != "discovery":
            raise ValueError("_gateway_exists() only available in discovery mode")

        try:
            logger.info(f"Checking for existing gateway with IP {ip_address} in VRF {self.vrf.id}")

            # First, find the IP address object in NetBox
            ip_addresses = list(self.netbox.ipam.ip_addresses.filter(address=ip_address, vrf_id=self.vrf.id))

            if not ip_addresses:
                logger.info(f"IP address {ip_address} not found in NetBox VRF {self.vrf.id}")
                return None

            ip_address_obj = ip_addresses[0]
            logger.info(f"Found IP address object: ID {ip_address_obj.id}")

            # Query the nb-gateways plugin using pynetbox
            existing_gateways = list(
                self.plugins.nb_gateways.gateway.filter(vrf=self.vrf.id, gateway_ip=ip_address_obj.id)
            )

            if existing_gateways:
                # Return the first matching gateway IP
                gateway = existing_gateways[0]
                logger.info(f"Gateway exists: ID {gateway.id}, IP {gateway.gateway_ip}")
                return True
            else:
                logger.info(f"No gateway found for IP {ip_address} in VRF {self.vrf.id}")
                return False

        except Exception as e:
            logger.error(f"Error checking gateway existence for IP {ip_address}: {str(e)}")
            return False

    def _get_primary_bridge_wt0_ip(self):
        """
        Find a bridge in provisioned/provisioning state and return its wt0 IP address.
        Returns the first available IP from a bridge in the desired state.
        """
        if self.mode != "discovery":
            raise ValueError("_get_primary_bridge_wt0_ip() only available in discovery mode")

        try:
            # Get all bridges for this tenant/site/location
            bridges = self.netbox.dcim.devices.filter(
                tenant_id=self.device.tenant.id,
                site_id=self.device.site.id,
                location_id=self.device.location.id,
                role="brokkr-bridge",
                status=["provisioned", "provisioning"],
            )

            logger.info(f"Found {len(bridges)} bridges in provisioned/provisioning state")

            for bridge in bridges:
                logger.info(f"Checking bridge: {bridge.name} (ID: {bridge.id}, Status: {bridge.status})")

                # Get wt0 interface for this bridge
                interfaces = list(self.netbox.dcim.interfaces.filter(device_id=bridge.id, name="wt0"))
                if not interfaces:
                    logger.info(f"No wt0 interface found on bridge {bridge.name}")
                    continue

                interface = interfaces[0]
                logger.info(f"Found wt0 interface (ID: {interface.id}) on bridge {bridge.name}")

                # Get IP addresses for this interface
                ip_addresses = list(self.netbox.ipam.ip_addresses.filter(interface_id=interface.id))
                if not ip_addresses:
                    logger.info(f"No IP addresses found on wt0 interface for bridge {bridge.name}")
                    continue

                # Prefer IPv4 addresses
                for ip in ip_addresses:
                    if getattr(ip.family, "value", None) == 4:
                        clean_ip = ip.address.split("/")[0]
                        logger.info(f"Selected primary bridge IP: {clean_ip} from bridge {bridge.name}")
                        return clean_ip

                # Fallback to any IP if no IPv4 found
                if ip_addresses:
                    clean_ip = ip_addresses[0].address.split("/")[0]
                    logger.info(f"Selected primary bridge IP (fallback): {clean_ip} from bridge {bridge.name}")
                    return clean_ip

            logger.warning("No usable bridge IP found in provisioned/provisioning state")
            return None

        except Exception as e:
            logger.error(f"Error finding primary bridge IP: {str(e)}")
            return None

    def _get_template_ids(self, template_names):
        """Helper method to convert template names to template IDs"""
        template_ids = []
        for template_name in template_names:
            logger.info(f"Looking up Zabbix template: {template_name}")
            template = self.zabbix_api.template.get(filter={"host": template_name})
            if template:
                template_id = template[0]["templateid"]
                logger.info(f"Found template '{template_name}' with ID {template_id}")
                template_ids.append({"templateid": template_id})
            else:
                logger.error(f"Template '{template_name}' not found")
                raise ValueError(f"Template '{template_name}' not found")
        return template_ids

    def _get_marketplace_proxy_group_id(self):
        """Find the Brokkr Public Proxies proxy group and return its ID, or None if not available"""
        proxy_group_name = "Brokkr Public Proxies"

        try:
            # Check if proxy group already exists
            logger.info(f"Checking if proxy group '{proxy_group_name}' exists in Zabbix")
            existing_proxy_groups = self.zabbix_api.proxygroup.get(filter={"name": proxy_group_name})

            if existing_proxy_groups:
                proxy_group_id = existing_proxy_groups[0]["proxy_groupid"]
                logger.info(f"Found existing proxy group '{proxy_group_name}' with ID {proxy_group_id}")
                return proxy_group_id
            else:
                logger.warning(f"Proxy group '{proxy_group_name}' not found. Will default to server monitoring")
                return None
        except Exception as e:
            logger.warning(
                f"Error looking up proxy group '{proxy_group_name}': {str(e)}. Will default to server monitoring",
            )
            return None

    def _determine_monitoring_config(self, device_id):
        """
        Determine monitoring configuration - all hosts use Brokkr Public Proxies proxy group.
        Returns tuple: (use_proxy, proxy_group_id, log_message)

        Args:
            device_id: The device ID (string or int)

        Returns:
            tuple: (bool, int|None, str) - (should_use_proxy, proxy_group_id, description)
        """
        device_id_int = int(device_id)

        # All hosts attempt to use proxy group
        proxy_group_id = self._get_marketplace_proxy_group_id()

        if proxy_group_id:
            return (
                True,
                proxy_group_id,
                f"Device ID {device_id_int} - using Brokkr Public Proxies proxy group (ID: {proxy_group_id})",
            )
        else:
            return (
                False,
                None,
                f"Device ID {device_id_int} - no proxy group available, falling back to server monitoring",
            )

    def create_bridge_host_groups(self):
        """Create host groups for bridge mode"""
        if self.mode != "bridge":
            raise ValueError("create_bridge_host_groups() only available in bridge mode")

        self.bridge_host_group_ids = []

        # Define required host groups
        required_groups = [
            "brokkr_proxy",
            f"location_{self.bridge_device.location.id}",
            f"site_{self.bridge_device.site.id}",
            f"tenant_{self.bridge_device.tenant.id}",
        ]

        for group_name in required_groups:
            logger.info(f"Checking if host group '{group_name}' exists in Zabbix")
            existing = self.zabbix_api.hostgroup.get(filter={"name": group_name})

            if existing:
                group_id = existing[0]["groupid"]
                logger.info(f"Host group '{group_name}' already exists with ID {group_id}")
            else:
                logger.info(f"Host group '{group_name}' not found. Creating new group.")
                created = self.zabbix_api.hostgroup.create(name=group_name)
                group_id = created["groupids"][0]
                logger.info(f"Created new host group '{group_name}' with ID {group_id}")

            self.bridge_host_group_ids.append({"groupid": group_id})

    def manage_bridge_host(self):
        """Manage Zabbix host for bridge mode"""
        if self.mode != "bridge":
            raise ValueError("manage_bridge_host() only available in bridge mode")

        # Prepare tags
        tags = [
            {"tag": "device_id", "value": str(self.bridge_device.id)},
            {"tag": "location_id", "value": str(self.bridge_device.location.id)},
            {"tag": "role", "value": str(self.bridge_device.role.name)},
            {"tag": "site_id", "value": str(self.bridge_device.site.id)},
            {"tag": "tenant_id", "value": str(self.bridge_device.tenant.id)},
            {"tag": "brokkr-bridge", "value": "true"},
        ]

        # Prepare macros
        macros = [
            {"macro": "{$NOMAD.CLIENT.API.PORT}", "value": "8444"},
            {"macro": "{$NOMAD.CLIENT.API.SCHEME}", "value": "https"},
            {"macro": "{$NOMAD.ENDPOINT.API.URL}", "value": self.bridge_ip_clean},
            {"macro": "{$NOMAD.TOKEN}", "value": "brokkr/monitoring-zabbix:nomad-token", "type": "2"},
        ]

        # Prepare interfaces - agent interface with wt0 IP
        interfaces = [
            {
                "type": 1,  # Agent interface
                "main": 1,
                "useip": 1,
                "ip": self.bridge_ip_clean,
                "dns": "",
                "port": "10050",
            }
        ]

        # Define templates
        template_names = ["Linux by Zabbix agent", "HashiCorp Nomad Client by HTTP"]

        try:
            # Determine monitoring configuration
            use_proxy, marketplace_proxy_group_id, monitoring_description = self._determine_monitoring_config(
                self.bridge_device.id
            )

            # Check if host already exists
            existing_host = self.zabbix_api.host.get(filter={"host": self.bridge_host_name})

            if existing_host:
                host_id = existing_host[0]["hostid"]
                logger.info(f"Bridge host {self.bridge_host_name} already exists (ID: {host_id}), updating...")

                # Update existing host
                update_params = {
                    "hostid": host_id,
                    "name": self.bridge_host_name,
                    "groups": self.bridge_host_group_ids,
                    "tags": tags,
                    "macros": macros,
                    "tls_connect": 2,  # PSK
                    "tls_accept": 2,  # PSK
                    "tls_psk_identity": self.zabbix_psk_id,
                    "tls_psk": self.zabbix_psk,
                }

                # Add monitoring settings based on configuration
                if use_proxy and marketplace_proxy_group_id:
                    update_params.update(
                        {
                            "monitored_by": 2,  # Monitored by proxy group
                            "proxy_groupid": marketplace_proxy_group_id,
                        }
                    )
                else:
                    update_params["monitored_by"] = 0  # Monitored by server

                logger.info(f"Updating bridge host {self.bridge_host_name} - {monitoring_description}")

                self.zabbix_api.host.update(**update_params)
                logger.info("Updated bridge host basic configuration")

                # Update interfaces
                existing_interfaces = self.zabbix_api.hostinterface.get(hostids=[host_id], filter={"type": "1"})

                if existing_interfaces:
                    # Update existing interface
                    iface = existing_interfaces[0]
                    self.zabbix_api.hostinterface.update(
                        interfaceid=iface["interfaceid"],
                        ip=self.bridge_ip_clean,
                        useip=1,
                        dns="",
                        port="10050",
                        main=1,
                        type=1,
                        hostid=host_id,
                    )
                    logger.info(f"Updated existing agent interface to IP: {self.bridge_ip_clean}")
                else:
                    # Create new interface
                    self.zabbix_api.hostinterface.create(
                        hostid=host_id, type=1, main=1, useip=1, ip=self.bridge_ip_clean, dns="", port="10050"
                    )
                    logger.info(f"Created new agent interface with IP: {self.bridge_ip_clean}")

                # Update templates
                template_ids = self._get_template_ids(template_names)
                self.zabbix_api.host.update(hostid=host_id, templates=template_ids)
                logger.info("Successfully updated templates for bridge host")

            else:
                # Create new host
                logger.info(f"Creating new bridge host {self.bridge_host_name}")

                host_params = {
                    "host": self.bridge_host_name,
                    "name": self.bridge_host_name,
                    "groups": self.bridge_host_group_ids,
                    "tags": tags,
                    "macros": macros,
                    "interfaces": interfaces,
                    "tls_connect": 2,  # PSK
                    "tls_accept": 2,  # PSK
                    "tls_psk_identity": self.zabbix_psk_id,
                    "tls_psk": self.zabbix_psk,
                }

                # Add monitoring settings based on configuration
                if use_proxy and marketplace_proxy_group_id:
                    host_params.update(
                        {
                            "monitored_by": 2,  # Monitored by proxy group
                            "proxy_groupid": marketplace_proxy_group_id,
                        }
                    )
                else:
                    host_params["monitored_by"] = 0  # Monitored by server

                logger.info(f"Creating new bridge host {self.bridge_host_name} - {monitoring_description}")

                # Create host
                result = self.zabbix_api.host.create(**host_params)
                host_id = result["hostids"][0]
                logger.info(f"Created bridge host with ID: {host_id}")

                # Add templates
                template_ids = self._get_template_ids(template_names)
                if template_ids:
                    self.zabbix_api.host.update(hostid=host_id, templates=template_ids)
                    logger.info("Successfully applied templates to new bridge host")

        except Exception as e:
            logger.error(f"Failed to create/update bridge host {self.bridge_host_name}: {str(e)}")
            raise


def create_discovery_zabbix(
    device_id,
    device,
    discovery_doc,
    associated_bridges_ids,
    associated_bridges_wt0_ips,
    netbox,
    vrf,
    job_id="discovery",
):
    """Create ZabbixManager instance for discovery operations"""
    return ZabbixManager(
        device_id=device_id,
        mode="discovery",
        job_id=job_id,
        device=device,
        discovery_doc=discovery_doc,
        associated_bridges_ids=associated_bridges_ids,
        associated_bridges_wt0_ips=associated_bridges_wt0_ips,
        netbox=netbox,
        vrf=vrf,
    )
