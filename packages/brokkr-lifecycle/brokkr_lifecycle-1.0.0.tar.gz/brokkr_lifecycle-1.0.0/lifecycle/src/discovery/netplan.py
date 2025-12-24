import difflib
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import requests
import yaml

logger = logging.getLogger(__name__)


@dataclass
class Netplan:
    device: object

    def __post_init__(self):
        self.set_config_template()
        self.apply_netplan()

    def set_config_template(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        # Get NetBox netplan template ID from environment
        netplan_template_id = os.environ.get("NB_NETPLAN_TEMPLATE")

        if not netplan_template_id:
            logger.info("NB_NETPLAN_TEMPLATE not set, skipping config template update")
            return

        try:
            template_id = int(netplan_template_id)
        except ValueError:
            logger.error(f"Invalid NB_NETPLAN_TEMPLATE value: '{netplan_template_id}', must be integer")
            return

        # Check current device config_template
        current_template = getattr(self.device, "config_template", None)

        # Update config_template if it's null or empty
        if current_template is None or current_template == "":
            logger.info(f"Device has no config template, setting to {template_id}")
            self.device.config_template = template_id
            logger.info(f"✅ Updated device config template to {template_id}")
        elif hasattr(current_template, "id") and current_template.id == template_id:
            logger.info(f"Device already has correct config template {template_id}")
        else:
            current_id = current_template.id if hasattr(current_template, "id") else current_template
            logger.info(f"Device has different config template {current_id}, not updating")

    def _validate_netplan_yaml(self, netplan_content: str) -> bool:
        """Validate that netplan content is properly formatted YAML.

        Args:
            netplan_content: YAML content to validate

        Returns:
            True if valid YAML, False otherwise
        """
        try:
            yaml.safe_load(netplan_content)
            return True
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in netplan config: {e}")
            return False

    def _has_static_ip(self, netplan_content: str) -> bool:
        """Check if netplan configuration has a static IP assignment.

        Args:
            netplan_content: YAML content to check

        Returns:
            True if static IP found, False otherwise
        """
        try:
            config = yaml.safe_load(netplan_content)
            network = config.get("network", {})

            # Check all possible network device types for static IPs
            device_types = ["ethernets", "bonds", "bridges", "vlans"]

            for device_type in device_types:
                devices = network.get(device_type, {})

                for interface_name, interface_config in devices.items():
                    # Check if addresses field exists and is not empty
                    addresses = interface_config.get("addresses", [])
                    if addresses and len(addresses) > 0:
                        logger.info(f"Found static IP configuration in {device_type}.{interface_name}: {addresses}")
                        return True

            logger.warning("No static IP addresses found in netplan configuration")
            return False

        except Exception as e:
            logger.error(f"Error checking for static IP in netplan: {e}")
            return False

    def _log_config_diff(self, current_config: str, new_config: str, file_path: str) -> None:
        """Log the differences between current and new netplan configurations.

        Args:
            current_config: Current configuration content
            new_config: New configuration content
            file_path: Path to the configuration file
        """
        current_lines = current_config.splitlines(keepends=True)
        new_lines = new_config.splitlines(keepends=True)

        diff = list(
            difflib.unified_diff(
                current_lines, new_lines, fromfile=f"{file_path} (current)", tofile=f"{file_path} (new)", lineterm=""
            )
        )

        if diff:
            logger.info("Netplan configuration changes:")
            for line in diff:
                # Log only the actual diff lines (skip header)
                if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
                    continue
                elif line.startswith("-"):
                    logger.info(f"  REMOVED: {line[1:].rstrip()}")
                elif line.startswith("+"):
                    logger.info(f"  ADDED:   {line[1:].rstrip()}")
        else:
            logger.info("No differences found in netplan configuration")

    def apply_netplan(self):
        """Apply netplan configuration from NetBox config template"""

        # Get NetBox configuration
        netbox_url = os.environ.get("NETBOX_URL", "").rstrip("/")
        netbox_token = os.environ.get("NETBOX_TOKEN")

        if not all([netbox_url, netbox_token]):
            logger.warning("NetBox configuration not available, skipping netplan apply")
            return

        render_config_url = f"{netbox_url}/api/dcim/devices/{self.device.id}/render-config/"
        netplan_file_path = Path("/run/netplan/zz-brokkr.yaml")

        headers = {"Authorization": f"Token {netbox_token}", "Content-Type": "application/json"}

        try:
            # Render config from NetBox (using POST like bridge-api)
            logger.info("Rendering netplan config from NetBox...")
            response = requests.post(render_config_url, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"Failed to render config: {response.status_code} - {response.text}")
                return

            # Extract content from JSON response like bridge-api does
            try:
                data = response.json()
                rendered_config = data.get("content", "").strip()
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response.text}")
                return

            if not rendered_config:
                logger.warning("Rendered config is empty, skipping netplan apply")
                return

            # Validate YAML before proceeding
            if not self._validate_netplan_yaml(rendered_config):
                logger.error("Rendered config contains invalid YAML, skipping netplan apply")
                return

            # Check if netplan has static IP assignment
            if not self._has_static_ip(rendered_config):
                logger.info("Netplan has no static IP assignment, skipping netplan apply")
                return

            # Check if netplan file exists and read current content
            current_config = ""
            if netplan_file_path.exists():
                try:
                    current_config = netplan_file_path.read_text().strip()
                    logger.info("Found existing netplan configuration")
                except Exception as e:
                    logger.warning(f"Could not read existing netplan file: {e}")
            else:
                logger.info("No existing netplan configuration found")

            # Compare configs
            if rendered_config == current_config:
                logger.info("Netplan configuration unchanged, no action needed")
                return

            # Log the differences between current and new config
            self._log_config_diff(current_config, rendered_config, str(netplan_file_path))

            # Ensure netplan directory exists
            netplan_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write new configuration
            logger.info("Writing new netplan configuration...")
            netplan_file_path.write_text(rendered_config)
            logger.info(f"✅ Updated netplan config: {netplan_file_path}")

            # Apply netplan configuration
            logger.info("Applying netplan configuration...")
            result = subprocess.run(["netplan", "apply"], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                logger.info("✅ Netplan configuration applied successfully")
            else:
                logger.error(f"Failed to apply netplan: {result.stderr}")

        except requests.RequestException as e:
            logger.error(f"Network error rendering config: {e}")
        except subprocess.TimeoutExpired:
            logger.error("Netplan apply timed out after 60 seconds")
        except Exception as e:
            logger.error(f"Error applying netplan: {e}")
