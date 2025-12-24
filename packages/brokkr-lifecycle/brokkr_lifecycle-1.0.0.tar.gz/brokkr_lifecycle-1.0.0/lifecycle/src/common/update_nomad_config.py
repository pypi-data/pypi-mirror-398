#!/usr/bin/env python3
"""
Nomad Device Status Updater

This module provides a class to update device_status in Nomad client configuration
and restart the Nomad service to apply changes.
"""

import logging
import os
import re
import subprocess
import time


class NomadStatusUpdater:
    """Class to handle Nomad device status updates."""

    def __init__(self):
        """Initialize the status updater."""
        self.config_paths = [
            "/etc/nomad.d/nomad.hcl",
            "/etc/nomad/nomad.hcl",
            "/opt/nomad/nomad.hcl",
        ]

    def find_nomad_config(self):
        """Find the Nomad configuration file."""
        for path in self.config_paths:
            if os.path.exists(path):
                return path
        raise FileNotFoundError("Nomad configuration file not found in standard locations")

    def read_config_file(self, config_path: str) -> str:
        """Read the Nomad configuration file."""
        try:
            with open(config_path) as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Failed to read config file {config_path}: {e}") from e

    def update_device_status_content(self, config_content: str, new_status: str) -> str:
        """Update the device_status in the Nomad configuration content."""
        # Pattern to match the device_status line in the meta block
        pattern = r'(\s*"device_status"\s*=\s*")[^"]*(".*)'
        replacement = f"\\g<1>{new_status}\\g<2>"

        # Check if device_status exists
        if re.search(pattern, config_content):
            logging.info(f"Found existing device_status, updating to: {new_status}")
            updated_content = re.sub(pattern, replacement, config_content)
        else:
            # Need to add device_status to meta block
            logging.info(f"Adding device_status to meta block: {new_status}")

            # Find the meta block and add device_status
            meta_pattern = r"(\s*meta\s*\{[^}]*?)(\s*\})"
            meta_replacement = f'\\g<1>\\n    "device_status" = "{new_status}"\\g<2>'

            if re.search(meta_pattern, config_content, re.DOTALL):
                updated_content = re.sub(meta_pattern, meta_replacement, config_content, flags=re.DOTALL)
            else:
                raise Exception("Could not find meta block in Nomad configuration")

        return updated_content

    def update_device_id_content(self, config_content: str, new_device_id: str) -> str:
        """Update the device_id in the Nomad configuration content."""
        # Pattern to match the device_id line in the meta block
        pattern = r'(\s*"device_id"\s*=\s*")[^"]*(".*)'
        replacement = f"\\g<1>{new_device_id}\\g<2>"

        # Check if device_id exists
        if re.search(pattern, config_content):
            logging.info(f"Found existing device_id, updating to: {new_device_id}")
            updated_content = re.sub(pattern, replacement, config_content)
        else:
            # Need to add device_id to meta block
            logging.info(f"Adding device_id to meta block: {new_device_id}")

            # Find the meta block and add device_id
            meta_pattern = r"(\s*meta\s*\{[^}]*?)(\s*\})"
            meta_replacement = f'\\g<1>\\n    "device_id" = "{new_device_id}"\\g<2>'

            if re.search(meta_pattern, config_content, re.DOTALL):
                updated_content = re.sub(meta_pattern, meta_replacement, config_content, flags=re.DOTALL)
            else:
                raise Exception("Could not find meta block in Nomad configuration")

        return updated_content

    def update_platform_content(self, config_content: str, new_platform: str) -> str:
        """Update the platform in the Nomad configuration content."""
        # Pattern to match the platform line in the meta block
        pattern = r'(\s*"platform"\s*=\s*")[^"]*(".*)'
        replacement = f"\\g<1>{new_platform}\\g<2>"

        # Check if platform exists
        if re.search(pattern, config_content):
            logging.info(f"Found existing platform, updating to: {new_platform}")
            updated_content = re.sub(pattern, replacement, config_content)
        else:
            # Need to add platform to meta block
            logging.info(f"Adding platform to meta block: {new_platform}")

            # Find the meta block and add platform
            meta_pattern = r"(\s*meta\s*\{[^}]*?)(\s*\})"
            meta_replacement = f'\\g<1>\\n    "platform" = "{new_platform}"\\g<2>'

            if re.search(meta_pattern, config_content, re.DOTALL):
                updated_content = re.sub(meta_pattern, meta_replacement, config_content, flags=re.DOTALL)
            else:
                raise Exception("Could not find meta block in Nomad configuration")

        return updated_content

    def update_advertise_block_content(self, config_content: str, primary_ip: str = None) -> str:
        """Update or add the advertise block with primary IP."""
        if primary_ip:
            # Extract just the IP address without CIDR notation
            ip_address = primary_ip.split("/")[0] if "/" in primary_ip else primary_ip

            advertise_block = f'''advertise {{
  http = "{ip_address}"
  rpc  = "{ip_address}"
  serf = "{ip_address}"
}}'''

            # Check if advertise block already exists
            advertise_pattern = r"advertise\s*\{[^}]*\}"

            if re.search(advertise_pattern, config_content, re.DOTALL):
                logging.info(f"Found existing advertise block, updating with IP: {ip_address}")
                updated_content = re.sub(advertise_pattern, advertise_block, config_content, flags=re.DOTALL)
            else:
                # Replace "# Unknown primary_ip" comment with advertise block
                unknown_ip_pattern = r"#\s*Unknown\s+primary_ip\s*\n?"

                if re.search(unknown_ip_pattern, config_content, re.IGNORECASE):
                    logging.info(f"Replacing '# Unknown primary_ip' comment with advertise block: {ip_address}")
                    updated_content = re.sub(
                        unknown_ip_pattern, f"{advertise_block}\n\n", config_content, flags=re.IGNORECASE
                    )
                else:
                    # Add advertise block after client block
                    client_block_pattern = r"(client\s*\{[^}]*\}\s*)"
                    client_replacement = f"\\g<1>\n{advertise_block}\n\n"

                    if re.search(client_block_pattern, config_content, re.DOTALL):
                        logging.info(f"Adding advertise block after client block: {ip_address}")
                        updated_content = re.sub(
                            client_block_pattern, client_replacement, config_content, flags=re.DOTALL
                        )
                    else:
                        logging.warning("Could not find suitable location for advertise block")
                        updated_content = config_content
        else:
            # Remove advertise block if primary_ip is None
            advertise_pattern = r"advertise\s*\{[^}]*\}\s*"

            if re.search(advertise_pattern, config_content, re.DOTALL):
                logging.info("Removing advertise block (no primary IP)")
                updated_content = re.sub(advertise_pattern, "# Unknown primary_ip\n\n", config_content, flags=re.DOTALL)
            else:
                updated_content = config_content

        return updated_content

    def update_client_name_content(
        self, config_content: str, tenant_id: str, site_id: str, location_id: str, device_id: str
    ) -> str:
        """Update the client name with tenant-site-location-device format."""
        client_name = f"{tenant_id}-{site_id}-{location_id}-{device_id}"

        # Pattern to match the name line
        name_pattern = r'(\s*name\s*=\s*")[^"]*(".*)'
        replacement = f"\\g<1>{client_name}\\g<2>"

        if re.search(name_pattern, config_content):
            logging.info(f"Found existing name, updating to: {client_name}")
            updated_content = re.sub(name_pattern, replacement, config_content)
        else:
            # Add name after log_level if it doesn't exist
            log_level_pattern = r'(log_level\s*=\s*"[^"]*"\s*\n)'
            name_addition = f'\\g<1>\n# Client name\nname = "{client_name}"\n'

            if re.search(log_level_pattern, config_content):
                logging.info(f"Adding client name: {client_name}")
                updated_content = re.sub(log_level_pattern, name_addition, config_content)
            else:
                logging.warning("Could not find suitable location for client name")
                updated_content = config_content

        return updated_content

    def update_datacenter_content(self, config_content: str, datacenter: str) -> str:
        """Update the datacenter in the client block."""
        pattern = r'(\s*datacenter\s*=\s*")[^"]*(".*)'
        replacement = f"\\g<1>{datacenter}\\g<2>"

        if re.search(pattern, config_content):
            logging.info(f"Updating datacenter to: {datacenter}")
            updated_content = re.sub(pattern, replacement, config_content)
        else:
            logging.warning("Could not find datacenter in config")
            updated_content = config_content

        return updated_content

    def update_meta_field_content(self, config_content: str, field_name: str, field_value: str) -> str:
        """Update a specific field in the meta block."""
        pattern = rf'(\s*"{field_name}"\s*=\s*")[^"]*(".*)'
        replacement = f"\\g<1>{field_value}\\g<2>"

        if re.search(pattern, config_content):
            logging.info(f"Updating {field_name} to: {field_value}")
            updated_content = re.sub(pattern, replacement, config_content)
        else:
            # Add to meta block
            logging.info(f"Adding {field_name} to meta block: {field_value}")
            meta_pattern = r"(\s*meta\s*\{[^}]*?)(\s*\})"
            meta_replacement = f'\\g<1>\\n    "{field_name}" = "{field_value}"\\g<2>'

            if re.search(meta_pattern, config_content, re.DOTALL):
                updated_content = re.sub(meta_pattern, meta_replacement, config_content, flags=re.DOTALL)
            else:
                raise Exception("Could not find meta block in Nomad configuration")

        return updated_content

    def update_vault_create_from_role_content(self, config_content: str, role_id: str) -> str:
        """Update the vault.create_from_role field."""
        pattern = r'(\s*create_from_role\s*=\s*")[^"]*(".*)'
        replacement = f"\\g<1>{role_id}\\g<2>"

        if re.search(pattern, config_content):
            logging.info(f"Updating vault create_from_role to: {role_id}")
            updated_content = re.sub(pattern, replacement, config_content)
        else:
            logging.warning("Could not find create_from_role in vault block")
            updated_content = config_content

        return updated_content

    def write_config_file(self, config_path: str, content: str):
        """Write the updated configuration file."""
        try:
            # Write new content
            with open(config_path, "w") as f:
                f.write(content)
            logging.info(f"Updated config file: {config_path}")

        except Exception as e:
            raise Exception(f"Failed to write config file {config_path}: {e}") from e

    def restart_nomad_service(self):
        """Restart the Nomad service to apply configuration changes."""
        try:
            logging.info("Restarting Nomad service...")
            subprocess.run(["systemctl", "restart", "nomad"], check=True)
            logging.info("Nomad service restarted successfully")

            # Wait a moment for service to start
            time.sleep(3)

            # Check service status
            result = subprocess.run(["systemctl", "is-active", "nomad"], capture_output=True, text=True)
            if result.stdout.strip() == "active":
                logging.info("✅ Nomad service is running")
            else:
                logging.warning("⚠️ Nomad service may not be running properly")

        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to restart Nomad service: {e}") from e

    def update_job_id_content(self, config_content: str, new_job_id: str) -> str:
        """Update the job_id in the Nomad configuration content."""
        # Pattern to match the job_id line in the meta block
        pattern = r'(\s*"job_id"\s*=\s*")[^"]*(".*)'
        replacement = f"\\g<1>{new_job_id}\\g<2>"

        # Check if job_id exists
        if re.search(pattern, config_content):
            logging.info(f"Found existing job_id, updating to: {new_job_id}")
            updated_content = re.sub(pattern, replacement, config_content)
        else:
            # Need to add job_id to meta block
            logging.info(f"Adding job_id to meta block: {new_job_id}")

            # Find the meta block and add job_id
            meta_pattern = r"(\s*meta\s*\{[^}]*?)(\s*\})"
            meta_replacement = f'\\g<1>\\n    "job_id" = "{new_job_id}"\\g<2>'

            if re.search(meta_pattern, config_content, re.DOTALL):
                updated_content = re.sub(meta_pattern, meta_replacement, config_content, flags=re.DOTALL)
            else:
                raise Exception("Could not find meta block in Nomad configuration")

        return updated_content

    def update_status(self, new_status: str, new_job_id: str = None):
        """Update Nomad device status and optionally job ID configuration."""
        # Find config file
        config_path = self.find_nomad_config()
        logging.info(f"Using Nomad config: {config_path}")

        # Read current config
        current_content = self.read_config_file(config_path)

        # Check current values
        current_status_match = re.search(r'"device_status"\s*=\s*"([^"]*)"', current_content)
        current_status = current_status_match.group(1) if current_status_match else "NOT_SET"

        current_job_id_match = re.search(r'"job_id"\s*=\s*"([^"]*)"', current_content)
        current_job_id = current_job_id_match.group(1) if current_job_id_match else "NOT_SET"

        # Check if any changes are needed
        status_changed = current_status != new_status
        job_id_changed = new_job_id and current_job_id != new_job_id

        if not status_changed and not job_id_changed:
            logging.info(f"✅ No changes needed - status: '{new_status}', job_id: '{current_job_id}'")
            return

        # Log what's changing
        if status_changed:
            logging.info(f"Changing device status from '{current_status}' to '{new_status}'")
        if job_id_changed:
            logging.info(f"Changing job ID from '{current_job_id}' to '{new_job_id}'")

        updated_content = current_content

        # Update device status if needed
        if status_changed:
            updated_content = self.update_device_status_content(updated_content, new_status)

        # Update job ID if needed
        if job_id_changed:
            updated_content = self.update_job_id_content(updated_content, new_job_id)

        # Write updated config
        self.write_config_file(config_path, updated_content)

        # Restart Nomad service
        self.restart_nomad_service()

        changes = []
        if status_changed:
            changes.append(f"status: {new_status}")
        if job_id_changed:
            changes.append(f"job_id: {new_job_id}")

        logging.info(f"✅ Successfully updated {', '.join(changes)}")

    def migrate_from_public_zone(
        self, config_content: str, tenant_id: str, site_id: str, location_id: str, device_id: str
    ) -> str:
        """Migrate from 0/0/0 public zone to actual tenant/site/location."""
        logging.info(f"Migrating from public zone (0/0/0) to zone {tenant_id}/{site_id}/{location_id}")

        # Update datacenter
        zone_slash = f"{tenant_id}/{site_id}/{location_id}"
        updated_content = self.update_datacenter_content(config_content, zone_slash)

        # Update client name
        updated_content = self.update_client_name_content(updated_content, tenant_id, site_id, location_id, device_id)

        # Update metadata fields
        updated_content = self.update_meta_field_content(updated_content, "tenant_id", tenant_id)
        updated_content = self.update_meta_field_content(updated_content, "site_id", site_id)
        updated_content = self.update_meta_field_content(updated_content, "location_id", location_id)

        # Fetch bridge_api_client_id from Vault API and update create_from_role
        try:
            import requests

            vault_addr = os.environ.get("VAULT_ADDR")
            vault_token = os.environ.get("VAULT_TOKEN")

            if not vault_addr or not vault_token:
                logging.warning("VAULT_ADDR or VAULT_TOKEN not set, skipping vault create_from_role update")
            else:
                vault_path = f"brokkr/data/{tenant_id}/{site_id}/{location_id}/application/container-bridge-setup"
                vault_url = f"{vault_addr}/v1/{vault_path}"
                logging.info(f"Fetching bridge_api_client_id from Vault API: {vault_url}")

                headers = {"X-Vault-Request": "true", "X-Vault-Token": vault_token}

                response = requests.get(vault_url, headers=headers, verify=False, timeout=10)
                response.raise_for_status()

                vault_data = response.json()
                bridge_api_client_id = vault_data.get("data", {}).get("data", {}).get("bridge_api_client_id")

                if bridge_api_client_id:
                    logging.info(f"Retrieved bridge_api_client_id: {bridge_api_client_id}")
                    updated_content = self.update_vault_create_from_role_content(updated_content, bridge_api_client_id)
                else:
                    logging.warning("bridge_api_client_id not found in Vault response")

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch bridge_api_client_id from Vault API: {e}")
        except Exception as e:
            logging.error(f"Error fetching from Vault: {e}")

        return updated_content

    def update_device_info(
        self,
        device_id: str = None,
        status: str = None,
        platform: str = None,
        job_id: str = None,
        primary_ip: str = None,
        tenant_id: str = None,
        site_id: str = None,
        location_id: str = None,
    ):
        """Update device information in Nomad configuration."""
        # Find config file
        config_path = self.find_nomad_config()
        logging.info(f"Using Nomad config: {config_path}")

        # Read current config
        current_content = self.read_config_file(config_path)

        # Check if we need to migrate from public zone (0/0/0)
        current_datacenter_match = re.search(r'datacenter\s*=\s*"([^"]*)"', current_content)
        current_datacenter = current_datacenter_match.group(1) if current_datacenter_match else None

        needs_migration = (
            current_datacenter == "0/0/0"
            and tenant_id
            and site_id
            and location_id
            and device_id
            and (tenant_id != "0" or site_id != "0" or location_id != "0")
        )

        if needs_migration:
            logging.info("Public zone migration detected - updating datacenter and tenancy information")
            current_content = self.migrate_from_public_zone(current_content, tenant_id, site_id, location_id, device_id)

        # Check current values
        current_device_id_match = re.search(r'"device_id"\s*=\s*"([^"]*)"', current_content)
        current_device_id = current_device_id_match.group(1) if current_device_id_match else "NOT_SET"

        current_status_match = re.search(r'"device_status"\s*=\s*"([^"]*)"', current_content)
        current_status = current_status_match.group(1) if current_status_match else "NOT_SET"

        current_platform_match = re.search(r'"platform"\s*=\s*"([^"]*)"', current_content)
        current_platform = current_platform_match.group(1) if current_platform_match else "NOT_SET"

        current_job_id_match = re.search(r'"job_id"\s*=\s*"([^"]*)"', current_content)
        current_job_id = current_job_id_match.group(1) if current_job_id_match else "NOT_SET"

        # Check what needs to be updated
        device_id_changed = device_id and current_device_id != device_id
        status_changed = status and current_status != status
        platform_changed = platform and current_platform != platform
        job_id_changed = job_id and current_job_id != job_id

        if not any([device_id_changed, status_changed, platform_changed, job_id_changed]):
            logging.info("✅ No changes needed - all values are current")
            return

        # Log what's changing
        changes = []
        if device_id_changed:
            logging.info(f"Changing device_id from '{current_device_id}' to '{device_id}'")
            changes.append(f"device_id: {device_id}")
        if status_changed:
            logging.info(f"Changing device_status from '{current_status}' to '{status}'")
            changes.append(f"status: {status}")
        if platform_changed:
            logging.info(f"Changing platform from '{current_platform}' to '{platform}'")
            changes.append(f"platform: {platform}")
        if job_id_changed:
            logging.info(f"Changing job_id from '{current_job_id}' to '{job_id}'")
            changes.append(f"job_id: {job_id}")

        updated_content = current_content

        # Apply updates
        if device_id_changed:
            updated_content = self.update_device_id_content(updated_content, device_id)
        if status_changed:
            updated_content = self.update_device_status_content(updated_content, status)
        if platform_changed:
            updated_content = self.update_platform_content(updated_content, platform)
        if job_id_changed:
            updated_content = self.update_job_id_content(updated_content, job_id)

        # Always update advertise block if primary_ip is provided
        if primary_ip is not None:
            updated_content = self.update_advertise_block_content(updated_content, primary_ip)

        # Update client name if we have all tenancy data
        if (
            all([device_id, current_content])
            and "tenant_id" in current_content
            and "site_id" in current_content
            and "location_id" in current_content
        ):
            # Extract tenant_id, site_id, location_id from existing meta block
            tenant_match = re.search(r'"tenant_id"\s*=\s*"([^"]*)"', current_content)
            site_match = re.search(r'"site_id"\s*=\s*"([^"]*)"', current_content)
            location_match = re.search(r'"location_id"\s*=\s*"([^"]*)"', current_content)

            if tenant_match and site_match and location_match:
                tenant_id_val = tenant_match.group(1)
                site_id_val = site_match.group(1)
                location_id_val = location_match.group(1)
                updated_content = self.update_client_name_content(
                    updated_content, tenant_id_val, site_id_val, location_id_val, device_id
                )

        # Write updated config
        self.write_config_file(config_path, updated_content)

        # Restart Nomad service
        self.restart_nomad_service()

        logging.info(f"✅ Successfully updated {', '.join(changes)}")


def clear_console():
    """Clear the console screen."""
    print("\033[2J\033[H", end="", flush=True)


def stop_current_allocation():
    """Stop the current Nomad allocation to force constraint re-evaluation."""
    import os

    import requests

    try:
        allocation_id = os.getenv("NOMAD_ALLOC_ID")
        nomad_token = os.getenv("NOMAD_TOKEN")
        nomad_addr = os.getenv("NOMAD_ADDR")

        if not allocation_id:
            logging.warning("NOMAD_ALLOC_ID not found, cannot stop allocation")
            return

        if not nomad_token or not nomad_addr:
            logging.error("NOMAD_TOKEN or NOMAD_ADDR not set!")
            return

        logging.info(f"Stopping allocation {allocation_id} via API...")

        # Use requests to call Nomad API
        headers = {"X-Nomad-Token": nomad_token, "Content-Type": "application/json"}

        url = f"{nomad_addr}/v1/allocation/{allocation_id}/stop"
        params = {"namespace": "brokkr-bridge"}

        response = requests.post(url, headers=headers, params=params, verify=False, timeout=30)
        response.raise_for_status()

        logging.info("✅ Allocation stopped successfully via API")

    except requests.HTTPError as e:
        logging.error(f"HTTP error stopping allocation: {e}")
        logging.error(f"Response: {e.response.text}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error stopping allocation: {e}")
        raise


# Convenience functions for easy importing
def update_nomad_status(new_status: str, new_job_id: str = None):
    """Convenience function to update Nomad device status and optionally job ID."""
    updater = NomadStatusUpdater()
    updater.update_status(new_status, new_job_id)


def update_status_and_stop(new_status: str, new_job_id: str = None):
    """Update device status, optionally job ID, and stop current allocation."""
    update_nomad_status(new_status, new_job_id)
    stop_current_allocation()


def update_device_information(
    device_id: str = None,
    status: str = None,
    platform: str = None,
    job_id: str = None,
    primary_ip: str = None,
    tenant_id: str = None,
    site_id: str = None,
    location_id: str = None,
):
    """Convenience function to update device information in Nomad config."""
    updater = NomadStatusUpdater()
    updater.update_device_info(
        device_id=device_id,
        status=status,
        platform=platform,
        job_id=job_id,
        primary_ip=primary_ip,
        tenant_id=tenant_id,
        site_id=site_id,
        location_id=location_id,
    )


def update_device_info_and_stop(
    device_id: str = None,
    status: str = None,
    platform: str = None,
    job_id: str = None,
    primary_ip: str = None,
    tenant_id: str = None,
    site_id: str = None,
    location_id: str = None,
):
    """Update device information and stop current allocation."""
    update_device_information(
        device_id=device_id,
        status=status,
        platform=platform,
        job_id=job_id,
        primary_ip=primary_ip,
        tenant_id=tenant_id,
        site_id=site_id,
        location_id=location_id,
    )
    stop_current_allocation()
