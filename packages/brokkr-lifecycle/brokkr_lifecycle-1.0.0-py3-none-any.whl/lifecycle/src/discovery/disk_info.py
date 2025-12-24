import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DiskInfo:
    lsblk: list

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")
        logger.info(f"Raw lsblk input: {self.lsblk}")

        # have to set prior to perhaps returning early
        self.field_data = {}

        if not self.lsblk:
            return

        nvme_count = 0
        nvme_size = 0
        ssd_count = 0
        ssd_size = 0
        hdd_count = 0
        hdd_size = 0

        disks_with_empty_wwn: list[int] = []

        # Filter out 0-sized disks and virtual disks
        # fmt: off
        self.disk_info = [
            disk for disk in self.lsblk
            if disk.get("size", 0) > 0 and "virtual" not in disk.get("serial", "").lower()
        ]

        for disk_index, disk in enumerate(self.disk_info):
            logger.info(f"Processing disk: {disk}")
            logger.info(f"Disk rotation value: {disk.get('rota')}")

            is_ssd = disk["rota"] in (0, "0")
            logger.info(f"Is SSD?: {is_ssd}")

            if disk["name"].startswith("nvme"):
                nvme_count += 1
                nvme_size += disk["size"]
                logger.info(f"Added NVME disk: {disk['name']}, size: {disk['size']}")
            elif is_ssd:
                ssd_count += 1
                ssd_size += disk["size"]
                logger.info(f"Added SSD disk: {disk['name']}, size: {disk['size']}")
            else:
                hdd_count += 1
                hdd_size += disk["size"]
                logger.info(f"Added HDD disk: {disk['name']}, size: {disk['size']}")

            # if the WWN is hex, convert it to int and check to confirm it is not 0
            wwn = disk.get("wwn")
            if wwn:
                try:
                    wwn = int(disk["wwn"], 16)
                    if wwn == 0:
                        wwn = None
                    elif str(wwn) != disk["wwn"]:
                        # a long numberic or hex wwn will convert to int
                        # but could be incorrect due to precision loss
                        # as long as it is not 0, use the original wwn
                        wwn = disk["wwn"]
                except ValueError:
                    pass

                if not wwn:
                    disks_with_empty_wwn.append(disk_index)

                disk["wwn"] = wwn

        serial_numbers_with_empty_wwn = {self.disk_info[index]["serial"] for index in disks_with_empty_wwn}
        if len(serial_numbers_with_empty_wwn) != len(disks_with_empty_wwn):
            logger.error("Disks with empty WWN have duplicate serial numbers")

        if ssd_count == 0 or ssd_size == 0:
            self.field_data["ssd_count"] = None
            self.field_data["ssd_size"] = None
            logger.info("No SSDs found or total size is 0")
        else:
            size = round(ssd_size / 1e9)
            logger.info(f"SSD Count: {ssd_count}")
            logger.info(f"Total SSD Size: {size}")
            self.field_data["ssd_count"] = ssd_count
            self.field_data["ssd_size"] = size

        if hdd_count == 0 or hdd_size == 0:
            self.field_data["hdd_count"] = None
            self.field_data["hdd_size"] = None
            logger.info("No HDDs found or total size is 0")
        else:
            size = round(hdd_size / 1e9)
            logger.info(f"HDD Count: {hdd_count}")
            logger.info(f"Total HDD Size: {size}")
            self.field_data["hdd_count"] = hdd_count
            self.field_data["hdd_size"] = size

        if nvme_count == 0 or nvme_size == 0:
            self.field_data["nvme_count"] = None
            self.field_data["nvme_size"] = None
            logger.info("No NVMEs found or total size is 0")
        else:
            size = round(nvme_size / 1e9)
            logger.info(f"NVME Count: {nvme_count}")
            logger.info(f"Total NVME Size: {size}")
            self.field_data["nvme_count"] = nvme_count
            self.field_data["nvme_size"] = size

        self.field_data["disk_info"] = self.disk_info
        logger.info(f"Setting disk_info in field_data: {self.disk_info}")

        # Legacy - to be deprecated (use filtered disk_info)
        self.field_data["disk_count"] = int(len(self.disk_info))
        self.field_data["disks_size"] = int(sum(disk["size"] for disk in self.disk_info) / 1073741824)
        logger.info(f"Combined Disk Count: {self.field_data['disk_count']}")
        logger.info(f"Combined Disk Size: {self.field_data['disks_size']}")

        logger.info(f"Final field_data payload: {self.field_data}")
