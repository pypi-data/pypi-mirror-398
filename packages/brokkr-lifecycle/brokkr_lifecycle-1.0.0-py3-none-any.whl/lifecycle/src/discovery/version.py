import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Version:
    versions: dict

    def __post_init__(self):
        self.field_data = {}

        if self.versions:
            if "iso_version" in self.versions:
                iso_version = self.versions["iso_version"]
                logger.info(f"Brokkr Live ISO Version: {iso_version}")
                self.field_data["brokkr_live_running_version"] = iso_version

            if "collector_version" in self.versions:
                collector_version = self.versions["collector_version"]
                logger.info(f"Discovery Collector Version: {collector_version}")
                self.field_data["discovery_collector_version"] = collector_version
