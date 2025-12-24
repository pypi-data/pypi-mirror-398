import logging
import os
from dataclasses import dataclass

import pynetbox

from .documents import upload_device_doc

logger = logging.getLogger(__name__)


@dataclass
class Device:
    netbox: pynetbox.api
    device: object
    device_name: str
    tenant: object
    new_status: str
    device_role: object
    device_type: object
    site: object
    location: object
    host_serial: str
    tag_ids: list[int]
    discovery_doc: dict

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        # Update device using idempotent logic (extracted from HydraNetbox)
        update_dict = {}

        # Check each field and only update if changed
        # Note: role is NOT updated - only set during device creation
        fields_to_check = {
            "name": self.device_name,
            "status": self.new_status,
            "tenant": self.tenant.id if self.tenant else None,
            "device_type": self.device_type.id if self.device_type else None,
            "site": self.site.id if self.site else None,
            "location": self.location.id if self.location else None,
            "serial": self.host_serial,
            "tags": self.tag_ids,
        }

        for key, new_value in fields_to_check.items():
            if new_value is None:
                continue

            current_value = getattr(self.device, key, None)

            # Handle special cases
            if key == "tags":
                current_value = [tag.id for tag in current_value] if current_value else []
            elif hasattr(current_value, "value"):
                current_value = current_value.value
            elif hasattr(current_value, "id"):
                current_value = current_value.id

            # Only update if changed
            if str(current_value).lower() != str(new_value).lower():
                logger.info(f"Updating device {key} from {current_value} to {new_value}")
                update_dict[key] = new_value

        # Perform update only if there are changes
        if update_dict:
            self.updated_device = self.netbox.dcim.devices.update([{"id": self.device.id, **update_dict}])[0]
        else:
            logger.info("No device updates needed")
            self.updated_device = self.device
        logger.info(f"Device Name: {self.updated_device.name}")
        logger.info(f"Device ID: {self.updated_device.id}")

        # Upload discovery document to NetBox using documents plugin
        upload_device_doc(device_id=self.updated_device.id, doc_name="discovery.json", doc_content=self.discovery_doc)
