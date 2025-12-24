import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MemoryInfo:
    ghwd_memory: dict = None
    dmidecode_memory: list[dict] = None

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        self.field_data = {}

        if self.ghwd_memory:
            self.memory_size()

        if self.dmidecode_memory:
            self.memory_config()

    def memory_size(self):
        if "memory" in self.ghwd_memory and "total_physical_bytes" in self.ghwd_memory["memory"]:
            memory_size = int(self.ghwd_memory["memory"]["total_physical_bytes"] / 1024 / 1024 / 1024)
            self.field_data["memory"] = memory_size
            logger.info(f"Memory Size: {memory_size}")

    def memory_config(self):
        ram_count = 0
        ram_speed = ""
        ram_type = ""
        ram_type_detail = ""
        ram_size = ""

        # logger.warning(self.dmidecode_memory)
        for bank in self.dmidecode_memory:
            bank = bank["values"]
            if "speed" in bank and bank["speed"] != "Unknown":
                if "size" in bank and bank["size"] != "No Module Installed":
                    if "type" in bank and "type_detail" in bank:
                        if ram_speed == "":
                            ram_speed = bank["speed"]
                        if ram_type == "":
                            ram_type = bank["type"]
                        if ram_type_detail == "":
                            ram_type_detail = bank["type_detail"]
                        if ram_size == "":
                            ram_size = bank["size"]
                        if (
                            ram_speed == bank["speed"]
                            and ram_type == bank["type"]
                            and ram_type_detail == bank["type_detail"]
                            and ram_size == bank["size"]
                        ):
                            ram_count += 1

        # if ram_speed and ram_type and ram_type_detail and ram_size:
        memory_config = f"{ram_count}X {ram_size.replace(' ', '')} {ram_type} {ram_type_detail} {ram_speed}"
        self.field_data["memory_config"] = memory_config
        logger.info(f"Memory Config: {memory_config}")
