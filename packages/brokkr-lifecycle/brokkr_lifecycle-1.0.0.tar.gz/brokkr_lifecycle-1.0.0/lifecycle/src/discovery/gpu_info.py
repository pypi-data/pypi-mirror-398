import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GpuInfo:
    nvidia: dict = None

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        self.field_data = {}

        if self.nvidia is not None:
            self.field_data["gpu_model"] = self.nvidia["model"]
            self.field_data["gpu_count"] = self.nvidia["count"]
        else:
            self.field_data["gpu_model"] = None
            self.field_data["gpu_count"] = None

        logger.info(f"Nvidia present: {self.nvidia is not None}")
        if self.nvidia is not None:
            logger.info(f"GPU Model: {self.field_data['gpu_model']}")
            logger.info(f"GPU Count: {self.field_data['gpu_count']}")
