import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Lifecycle:
    device: object
    bdi: dict

    def __post_init__(self):
        logger.info(f"Entering {os.path.basename(__file__)} class")

        if self.device:
            if self.device.status.value in ["decommissioning", "inventory", "offline"]:
                self.new_status = "inventory"
            else:
                self.new_status = self.device.status.value
        else:
            self.new_status = "planned"

        if self.new_status == "planned" and "status" in self.bdi:
            self.new_status = self.bdi["status"]
