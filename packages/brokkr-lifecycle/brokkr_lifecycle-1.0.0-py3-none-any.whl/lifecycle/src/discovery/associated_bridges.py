import logging
from dataclasses import dataclass

import pynetbox

logger = logging.getLogger(__name__)


@dataclass
class DeviceAssociatedBridges:
    netbox: pynetbox
    tenant_id: int
    site_id: int
    location_id: int

    def __post_init__(self):
        self.bridges = list(
            self.netbox.dcim.devices.filter(
                tenant_id=self.tenant_id,
                site_id=self.site_id,
                location_id=self.location_id,
                role="brokkr-bridge",
            )
        )

        self.bridge_ids = [bridge.id for bridge in self.bridges]
        logger.info(f"Located associated bridge(s): {[f'{b.name} (ID: {b.id})' for b in self.bridges]}")

    def get_associated_bridges_ids(self) -> list[int]:
        return self.bridge_ids

    def update_device_bridge_ids(self, device_id: int):
        if device_id and len(self.bridge_ids) > 0:
            self.netbox.dcim.devices.update(
                objects=[{"id": device_id, "custom_fields": {"associated_brokkr_bridges": self.bridge_ids}}]
            )
        else:
            logger.error(f"No device ID or bridge IDs found for device {device_id}")
            raise ValueError("No device ID or bridge IDs found")

    def get_wt0_interface_ips(self) -> list[str]:
        """
        Return a list of IP addresses for the 'wt0' interface on all associated bridges.
        """
        ip_list = []

        logger.info(f"Starting IP collection for wt0 interfaces on {len(self.bridges)} bridge(s)")

        for bridge_id in self.bridge_ids:
            bridge = self.netbox.dcim.devices.get(id=bridge_id)
            logger.info(f"Processing bridge: {bridge.name} (ID: {bridge.id})")

            # Look up all interfaces for the bridge
            interfaces = list(self.netbox.dcim.interfaces.filter(device_id=bridge.id))
            interface_names = [iface.name for iface in interfaces]
            logger.info(f"Interfaces found for bridge {bridge.name}: {interface_names}")

            # Filter for the interface with name 'wt0'
            wt0_interfaces = [iface for iface in interfaces if iface.name == "wt0"]
            if not wt0_interfaces:
                logger.warning(f"No 'wt0' interface found on bridge {bridge.name} (ID: {bridge.id})")
                continue

            interface = wt0_interfaces[0]
            logger.info(f"wt0 interface ID: {interface.id} for bridge {bridge.name}")

            # Check IPs
            ip_addresses = list(self.netbox.ipam.ip_addresses.filter(interface_id=interface.id))
            logger.info(f"IP addresses found on wt0: {[ip.address for ip in ip_addresses]}")

            for ip in ip_addresses:
                logger.info(f" - IP: {ip.address}, family: {getattr(ip.family, 'value', 'unknown')}")

            selected_ip = None
            for ip in ip_addresses:
                if getattr(ip.family, "value", None) == 4:
                    selected_ip = ip_addresses[0].address
                    break

            if not selected_ip and ip_addresses:
                selected_ip = ip_addresses[0].address
                logger.info(f"Fallback to non-IPv4 IP: {selected_ip}")

            if selected_ip:
                ip_list.append(selected_ip)
                logger.info(f"Selected IP for bridge {bridge}: {selected_ip}")
            else:
                logger.warning(f"No usable IPs found for bridge {bridge}")

        logger.info(f"Finished wt0 IP collection. Total collected: {len(ip_list)}")
        return ip_list
