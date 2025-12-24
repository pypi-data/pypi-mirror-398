import logging
import os
from dataclasses import dataclass

import pynetbox

logger = logging.getLogger(__name__)


@dataclass
class OemInfo:
    netbox: pynetbox.api
    baseboard: dict = None
    product: dict = None
    chassis: dict = None
    fallback_mac: str = None

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        self.manufacturer = self.get_manufacturer()
        self.device_type = self.get_device_type(self.manufacturer)
        self.serial = self.get_serial()

    def get_manufacturer(self) -> object:
        manufacturer_name = None
        if self.product and "product" in self.product and "vendor" in self.product["product"]:
            manufacturer_name = self.product["product"]["vendor"]
        # Look up manufacturer using pynetbox API
        manufacturers = list(self.netbox.dcim.manufacturers.filter(name=manufacturer_name)) if manufacturer_name else []
        manufacturer = manufacturers[0] if manufacturers else None
        logger.info(f"Manufacturer: {manufacturer}")
        return manufacturer

    def get_device_type(self, manufacturer) -> object:
        device_type_name = None
        if self.product and "product" in self.product and "name" in self.product["product"]:
            device_type_name = self.product["product"]["name"]
        if not device_type_name or not manufacturer:
            return None

        # Look up device type using pynetbox API (get, not filter - like original HydraNetbox)
        try:
            device_type = self.netbox.dcim.device_types.get(model=device_type_name, manufacturer_id=manufacturer.id)
            logger.info(f"Device Type: {device_type}")
            return device_type
        except Exception as e:
            logger.error(f"Error looking up device type {device_type_name}: {e}")
            return None

    def get_serial(self) -> str:
        host_serial = ""
        reject_serials = ["", "0123456789", "to be filled by o.e.m.", "0", "01234567890123456789AB"]

        # Extract nested data from GHW structure
        chassis_data = self.chassis.get("chassis", {}) if self.chassis else {}
        baseboard_data = self.baseboard.get("baseboard", {}) if self.baseboard else {}
        product_data = self.product.get("product", {}) if self.product else {}

        for d, k in ((chassis_data, "serial_number"), (baseboard_data, "serial_number"), (product_data, "uuid")):
            host_serial = d.get(k, "") if d else ""
            if host_serial.lower() not in reject_serials:
                break

        if host_serial.lower() in reject_serials:
            if self.fallback_mac:
                host_serial = self.fallback_mac.replace(":", "")

        logger.info(f"Host Serial: {host_serial}")
        return host_serial
