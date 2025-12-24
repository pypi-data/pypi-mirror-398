import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CustomFields:
    organization: str
    bmc: dict
    bdi: dict
    is_virtual: bool
    firmware_type: str
    serial_ports: dict = None
    architecture: dict = None

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        self.field_data = {}

        self.field_data["organization"] = self.organization

        if self.bdi and "station_netmask" in self.bdi:
            cidr = self._netmask_to_cidr(self.bdi["station_netmask"])
            self.field_data["machine_ip"] = f"{self.bdi['station_netmask']}/{cidr}"
        if self.bmc and self.bmc.get("mac", None):
            self.field_data["mgmt_mac"] = self.bmc["mac"].upper()
        else:
            if self.is_virtual:
                if "station_mac" in self.bdi:
                    self.field_data["mgmt_mac"] = self.bdi["station_mac"].upper()
        if "station_mac" in self.bdi:
            self.field_data["prov_mac"] = self.bdi["station_mac"].upper()
        if "bridge_group" in self.bdi:
            self.field_data["proxy_group"] = self.bdi["bridge_group"]
        self.field_data["uefi_boot"] = False if self.firmware_type == "bios" else True
        self.field_data["power_status"] = "Running"

        if self.architecture and "machine" in self.architecture:
            arch = None
            if self.architecture["machine"] == "aarch64":
                arch = "arm64"
            elif self.architecture["machine"] == "x86_64":
                arch = "amd64"
            self.field_data["architecture"] = arch

        # Process serial ports data
        self._process_serial_ports()

        logger.info(f"Misc Custom Field Data: {self.field_data}")

    def _process_serial_ports(self):
        """Extract and structure serial port information for NetBox custom field"""
        if not self.serial_ports:
            return

        serial_info = {}

        # Extract recommended port from hardware_recommendations.optimal_port
        if (
            "hardware_recommendations" in self.serial_ports
            and "optimal_port" in self.serial_ports["hardware_recommendations"]
        ):
            serial_info["recommended"] = self.serial_ports["hardware_recommendations"]["optimal_port"]

        # Extract all available ports from detected_ports keys
        if "detected_ports" in self.serial_ports:
            serial_info["available"] = list(self.serial_ports["detected_ports"].keys())

        # Only add to field_data if we have valid serial port information
        if serial_info:
            self.field_data["serial_ports"] = serial_info
            logger.info(f"Serial Ports Data: {serial_info}")

    def _netmask_to_cidr(self, netmask):
        # Split the netmask into octets
        octets = netmask.split(".")
        # Convert each octet to binary and concatenate them
        binary_str = "".join([bin(int(octet))[2:].zfill(8) for octet in octets])
        # Count the '1' bits
        cidr = binary_str.count("1")
        return cidr
