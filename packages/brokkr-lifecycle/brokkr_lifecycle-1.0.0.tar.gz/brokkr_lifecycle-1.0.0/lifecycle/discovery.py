#!/usr/bin/env python3
"""
Discovery Processor Entry Point

Processes marketplace host discovery data, optionally on a timer.
Configuration via environment variables.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from lifecycle.src.discovery import (
    AvailableOs,
    BmcInfo,
    CpuInfo,
    CustomFields,
    Device,
    DeviceAssociatedBridges,
    DiscoveryRunner,
    DiskInfo,
    EcoMode,
    GpuInfo,
    InterfaceData,
    Lifecycle,
    MemoryInfo,
    Netplan,
    OemInfo,
    PrimaryIps,
    StorageLayouts,
    Tags,
    Version,
    VrfInfo,
    ZabbixManager,
)

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO"):
    """Set up logging configuration"""
    # Remove any existing handlers to ensure clean setup
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure logging to stdout
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,  # Force logs to stdout instead of stderr
        force=True,  # Force reconfiguration even if already configured
    )


async def run_marketplace_hosts(message_file: str):
    """Run marketplace hosts processing"""
    import pynetbox

    # Check for dry run mode
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No actual changes will be made to external services")

    # Get device_id and role_id from environment variables
    device_id = os.environ.get("DEVICE_ID")
    role_id = os.environ.get("DEVICE_ROLE")

    if not device_id:
        logger.error("DEVICE_ID environment variable is required")
        return False
    if not role_id:
        logger.error("DEVICE_ROLE environment variable is required")
        return False

    try:
        device_id = int(device_id)
        role_id = int(role_id)
        logger.info(f"Using device_id={device_id}, role_id={role_id} from environment variables")
    except ValueError as e:
        logger.error(f"DEVICE_ID and DEVICE_ROLE must be valid integers: {e}")
        return False

    # Load discovery message (if provided)
    message = {}
    if message_file:
        try:
            with open(message_file) as f:
                message = json.load(f)
            logger.info(f"Loaded discovery message from {message_file}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading message file: {e}")
            return False
    else:
        logger.info("No message file provided, using empty discovery message")

    # Set up NetBox connection
    if dry_run:
        logger.info("🔍 DRY RUN: Skipping NetBox connection")

        # Create mock NetBox object for dry run
        class MockNetbox:
            class dcim:
                class devices:
                    @staticmethod
                    def get(id=None, **kwargs):
                        logger.info(f"🔍 DRY RUN: Would get device {id}")
                        # Return mock device object
                        from types import SimpleNamespace

                        return SimpleNamespace(
                            id=id,
                            name=f"mock-device-{id}",
                            tenant=SimpleNamespace(id=1),
                            custom_fields={},
                            role=SimpleNamespace(name="Mock Role"),
                        )

                    @staticmethod
                    def update(data):
                        logger.info(f"🔍 DRY RUN: Would update devices: {data}")
                        return data

                class device_roles:
                    @staticmethod
                    def get(id=None, **kwargs):
                        logger.info(f"🔍 DRY RUN: Would get device role {id}")
                        from types import SimpleNamespace

                        return SimpleNamespace(id=id, name="Mock Role")

        netbox = MockNetbox()
    else:
        netbox_url = os.environ.get("NETBOX_URL")
        netbox_token = os.environ.get("NETBOX_TOKEN")

        if not netbox_url or not netbox_token:
            logger.error("NetBox URL and token are required")
            return False

        try:
            netbox = pynetbox.api(url=netbox_url, token=netbox_token)
            logger.info(f"Connected to NetBox at {netbox_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NetBox: {e}")
            return False

    # Get device from NetBox (role_id is provided, no lookup needed)
    try:
        device = netbox.dcim.devices.get(id=device_id)
        initial_device_oob_ip = getattr(device, "oob_ip", None)
        if not device:
            logger.error(f"Device with ID {device_id} not found in NetBox")
            return False

        # Use role_id directly without NetBox lookup
        device_role_id = role_id
        logger.info(f"Processing device: {device.name} (ID: {device.id}) with role_id: {device_role_id}")

        # Create a simple object to maintain compatibility with existing code
        from types import SimpleNamespace

        device_role = SimpleNamespace(id=role_id, name="marketplace-hosts")

    except Exception as e:
        logger.error(f"Error getting device from NetBox: {e}")
        return False

    # Process the discovery data
    try:
        # Discovery processing logic
        tenant = device.tenant
        site = device.site
        location = device.location
        vrf = VrfInfo(netbox=netbox, tenant=tenant, location=location).vrf

        associated_bridges = DeviceAssociatedBridges(
            netbox=netbox,
            tenant_id=tenant.id,
            site_id=site.id,
            location_id=location.id,
        )

        # Get associated Bridge IDs
        associated_bridges_ids = associated_bridges.get_associated_bridges_ids()
        logger.info(f"Resolved associated bridge IDs: {associated_bridges_ids}")

        # Get OEM data
        device_type = None
        host_serial = None
        if "ghw_baseboard" in message and "ghw_chassis" in message and "ghw_product" in message and "bdi" in message:
            oem_info = OemInfo(
                netbox=netbox,
                baseboard=message["ghw_baseboard"],
                chassis=message["ghw_chassis"],
                product=message["ghw_product"],
                fallback_mac=message["bdi"].get("station_mac", None),
            )
            device_type = oem_info.device_type
            host_serial = oem_info.serial

        # Set new lifecycle status
        new_status = Lifecycle(device=device, bdi=message.get("bdi", None)).new_status

        # Get tag IDs
        tag_ids = Tags(netbox=netbox, device=device).ids

        # Update device
        device = Device(
            netbox=netbox,
            device=device,
            device_name=device.name,
            tenant=tenant,
            new_status=new_status,
            device_role=device_role,
            device_type=device_type,
            site=site,
            location=location,
            host_serial=host_serial,
            tag_ids=tag_ids,
            discovery_doc=message,
        ).updated_device

        # Update netplan config
        Netplan(device=device)

        custom_fields = {}

        # Manage IPMI interface and IPs
        discovered_interfaces = []
        bmc_info = BmcInfo(
            netbox=netbox,
            device=device,
            tenant=tenant,
            site=site,
            vrf=vrf,
            bmc_data=message.get("bmc", None),
            associated_bridges_ids=associated_bridges_ids,
        )

        # Initialize BMC processing async
        await bmc_info.initialize_async()

        if bmc_info.ipmi_enabled:
            discovered_interfaces.extend(bmc_info.interfaces)
            custom_fields.update(bmc_info.field_data)

        # Manage interface and IPs
        InterfaceData(
            netbox=netbox,
            ip_a=message.get("ip_a", None),
            bdi=message.get("bdi", None),
            device=device,
            tenant=tenant,
            site=site,
            vrf=vrf,
            discovered_interfaces=discovered_interfaces,
            network=message.get("ghw_net", None),
        )

        # Set public IPs as primary IPs
        if (
            str(device_role.name) in ["marketplace-hosts", "discovered-hosts"]
            and "public_ip" in message
            and "ip_a" in message
        ):
            PrimaryIps(
                netbox=netbox,
                public_ips=message["public_ip"],
                tenant=tenant,
                vrf=vrf,
                site=site,
                device=device,
                primary_interface_mac=message.get("bdi", {}).get("station_mac", None),
                ip_data=message["ip_a"],
            )

        # Collect custom fields
        custom_fields.update(
            CustomFields(
                organization=tenant.name,
                bmc=message.get("bmc", None),
                bdi=message.get("bdi", None),
                is_virtual=message.get("is_virtual", None),
                firmware_type=message.get("firmware_type", "uefi"),
                serial_ports=message.get("serial_ports", None),
                architecture=message.get("architecture", None),
            ).field_data
        )

        # Memory fields
        custom_fields.update(
            MemoryInfo(
                ghwd_memory=message.get("ghw_memory", None),
                dmidecode_memory=message.get("dmidecode_memory", None),
            ).field_data
        )

        # GPU info
        custom_fields.update(GpuInfo(nvidia=message.get("nvidia", None)).field_data)

        # Disk info
        custom_fields.update(DiskInfo(lsblk=message.get("lsblk", None)).field_data)
        custom_fields.update(StorageLayouts(device_type=device_type, lsblk=message.get("lsblk", None)).field_data)

        # CPU info
        custom_fields.update(CpuInfo(lscpu=message.get("lscpu", None), ghw_cpu=message.get("ghw_cpu", None)).field_data)

        # Version info
        custom_fields.update(Version(versions=message.get("version", None)).field_data)

        # Associated bridge IDs
        custom_fields.update({"associated_brokkr_bridges": associated_bridges_ids})

        # Available OS
        custom_fields.update(
            AvailableOs(
                netbox=netbox,
                nvidia=message.get("nvidia", None),
                pci=message.get("pci", None),
                virtualization=message.get("virtualization", None),
                device=device,
                architecture=message.get("architecture", None),
            ).field_data
        )

        # Update device with custom fields using idempotent logic
        update_dict = {}
        if custom_fields:
            current_custom_fields = device.custom_fields or {}

            for field, new_value in custom_fields.items():
                current_value = current_custom_fields.get(field, None)
                if hasattr(current_value, "value"):
                    current_value = current_value.value
                if str(current_value).lower() != str(new_value).lower():
                    logger.info(f"Updating custom field '{field}' from '{current_value}' to '{new_value}'")
                    update_dict.setdefault("custom_fields", {})[field] = new_value

        if initial_device_oob_ip != device.oob_ip:
            logger.info(f"Updating device OOB IP from {initial_device_oob_ip} to {device.oob_ip}")
            update_dict["oob_ip"] = device.oob_ip

        # Apply updates if any
        if update_dict:
            netbox.dcim.devices.update([{"id": device.id, **update_dict}])
            logger.info("Device custom fields updated successfully")
        else:
            logger.info("No custom field updates needed")

        # Create/Update Zabbix host
        try:
            associated_bridges_wt0_ips = associated_bridges.get_wt0_interface_ips()

            ZabbixManager(
                device_id=str(device.id),
                job_id="discovery",
                device=device,
                discovery_doc=message,
                associated_bridges_ids=associated_bridges_ids,
                associated_bridges_wt0_ips=associated_bridges_wt0_ips,
                netbox=netbox,
                vrf=vrf,
                mode="discovery",
            )
            logger.info(f"Finished processing Zabbix host: {device.name}")
        except Exception as e:
            logger.error(f"Failed to process Zabbix host for device {device.name}: {str(e)}")
            logger.warning("Continuing discovery process despite Zabbix failure")

        # # Apply Redfish settings
        # try:
        #     bmc_mac = None
        #     if message.get("bmc") and "mac" in message["bmc"]:
        #         bmc_mac = message["bmc"]["mac"]

        #     redfish_instance = Redfish(
        #         netbox=netbox,
        #         tenant_id=tenant.id,
        #         site_id=site.id,
        #         location_id=location.id,
        #         associated_bridges_ids=associated_bridges_ids,
        #         device_id=device.id,
        #         bmc_mac=bmc_mac,
        #     )
        #     await redfish_instance.apply_ideal_settings()
        # except Exception as e:
        #     logger.error(f"Failed to apply Redfish settings: {e}")

        # Check for ECO mode as final step
        logger.info("Checking ECO mode configuration...")
        try:
            EcoMode(device=device)
        except Exception as e:
            logger.warning(f"ECO mode check failed: {e}")

        logger.info(f"Discovery complete: {device.name}")
        return True

    except Exception as e:
        logger.error(f"Error during discovery processing: {e}")
        return False


def validate_environment():
    """Validate required environment variables (when not using command line args)"""
    # When using command line arguments, only validate variables that aren't passed as args
    required_vars = []

    # In dry run mode, skip validation for external services
    if os.environ.get("DRY_RUN", "false").lower() == "true":
        logger.info("Dry run mode enabled - skipping external service validation")
        required_vars = []

    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False

    return True


async def run_complete_discovery(discovery_runner: DiscoveryRunner, message_file: str | None, dry_run: bool) -> bool:
    """
    Run the complete discovery pipeline: binary collection + processing

    Args:
        discovery_runner: DiscoveryRunner instance
        message_file: Optional pre-existing message file
        dry_run: Whether this is a dry run

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Step 1: Run discovery collection if requested
        logger.info("Step 1: Running brokkr-collector package")

        # Check if we should install packages (defaults to True for production use)
        install_packages = os.environ.get("INSTALL_PACKAGES", "true").lower() == "true"
        check_dependencies = os.environ.get("CHECK_DEPENDENCIES", "true").lower() == "true"

        if install_packages:
            logger.info("Package installation is enabled (set INSTALL_PACKAGES=false to disable)")

        success = await discovery_runner.run_discovery_collection(
            dry_run=dry_run, install_packages=install_packages, check_dependencies=check_dependencies
        )
        if not success:
            logger.error("Failed to run discovery collection")
            return False

        # Use the collection file from the binary
        actual_message_file = discovery_runner.get_collection_file_path()
        if not actual_message_file:
            logger.error("No collection file generated by discovery binary")
            return False

        logger.info(f"Using collection file from binary: {actual_message_file}")

        # Step 2: Process the discovery data
        logger.info("Step 2: Processing discovery data")
        success = await run_marketplace_hosts(actual_message_file)

        if success:
            logger.info("✅ Complete discovery pipeline completed successfully")
        else:
            logger.error("❌ Discovery processing failed")

        return success

    except Exception as e:
        logger.error(f"Error in complete discovery pipeline: {e}")
        return False


async def main():
    """Main entry point"""
    # Get configuration from environment variables only
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    interval = int(os.environ.get("DISCOVERY_INTERVAL", "0"))

    # Set up logging
    setup_logging(log_level)

    logger.info("Discovery Processor starting")

    # Always run discovery binary to collect data
    logger.info("Will run brokkr-collector binary to collect data")
    message_file = "/tmp/collection-results.json"

    # Check for dry run mode
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

    logger.info("Discovery Processor starting")
    logger.info(f"Environment: {os.environ.get('HH_ENV', 'unknown')}")
    logger.info(f"Message file: {message_file}")
    logger.info(f"Dry run mode: {dry_run}")

    # Initialize discovery runner
    discovery_runner = DiscoveryRunner()

    if interval > 0:
        logger.info(f"Timer mode - running every {interval} seconds")

        # Timer mode - run continuously
        while True:
            try:
                logger.info("=== Starting scheduled discovery processing ===")
                start_time = time.time()

                success = await run_complete_discovery(discovery_runner, message_file, dry_run)

                end_time = time.time()
                duration = end_time - start_time

                if success:
                    logger.info(f"Scheduled processing completed successfully in {duration:.2f} seconds")
                else:
                    logger.error(f"Scheduled processing failed after {duration:.2f} seconds")

                logger.info(f"Waiting {interval} seconds until next run...")
                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                logger.info(f"Continuing scheduler - will retry in {interval} seconds")
                await asyncio.sleep(interval)
    else:
        # Single run mode
        logger.info("Single run mode")
        success = await run_complete_discovery(discovery_runner, message_file, dry_run)

        if success:
            logger.info("Discovery processing completed successfully")
            sys.exit(0)
        else:
            logger.error("Discovery processing failed")
            sys.exit(1)


def async_main():
    """Synchronous entry point for console script that runs the async main function."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    async_main()
