import logging
import os
import subprocess
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EcoMode:
    device: object

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        # Check if ECO mode is enabled in custom fields
        eco_mode_enabled = False
        if hasattr(self.device, "custom_fields") and self.device.custom_fields:
            eco_mode_enabled = self.device.custom_fields.get("eco_mode", False)

        if not eco_mode_enabled:
            logger.info("ECO mode not enabled, skipping")
            return

        status = getattr(self.device, "status", {})
        status_value = status.get("value") if isinstance(status, dict) else str(status)

        self.configure_eco_mode(status_value, eco_mode_enabled)

    def configure_eco_mode(self, status: str, eco_mode_enabled: bool) -> None:
        status = status.lower()
        if status in ["decommissioning", "inventory", "planned"] and eco_mode_enabled:
            logger.info("ECO mode enabled, waiting 5 minutes before shutdown")

            time.sleep(300)  # Wait 5 minutes

            # Fetch updated device info
            subprocess.run(["/sbin/shutdown", "-P", "now"], check=True)

        else:
            if status == "decommissioning":
                logger.info("Device is decommissioning but ECO mode not enabled")
            elif status == "inventory":
                logger.info("Device is inventory but ECO mode not enabled")
            elif status == "planned":
                logger.info("Device is planned but ECO mode not enabled")
            else:
                logger.info(f"Device status is '{status}', ECO mode not applicable")
