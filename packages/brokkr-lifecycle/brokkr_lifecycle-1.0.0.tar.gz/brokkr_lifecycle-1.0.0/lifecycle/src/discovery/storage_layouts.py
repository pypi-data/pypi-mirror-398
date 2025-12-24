import logging
import os
from collections import defaultdict
from dataclasses import dataclass

import yaml
from pynetbox.models.dcim import DeviceTypes

logger = logging.getLogger(__name__)


@dataclass
class StorageLayouts:
    device_type: DeviceTypes
    lsblk: dict = None

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        # For whatever reason, these machines do not seem to play nice with XFS.
        # For the time being these will only be allowed ext4 until we can figure this out.
        self.asrock_piece_of_shit = self.device_type and "rome" in getattr(self.device_type, "slug", "")

        logger.info("Determining disk capabilities")
        try:
            if self.lsblk:
                self.field_data = {"storage_layouts": self.check_disk_configuration()}
            else:
                self.field_data = {"storage_layouts": None}
        except Exception as e:
            logger.error(f"Error determining storage layouts: {str(e)}")
            self.field_data = {"storage_layouts": None}

    def format_disk_space(self, bytes_value: int) -> str:
        tb = bytes_value / (1000**4)
        if tb >= 1:
            return f"{round(tb, 2)} TB"
        else:
            gb = bytes_value / (1000**3)
            return f"{round(gb, 2)} GB"

    def calculate_raid_space(self, num_disks: int, disk_sizes: list[int], raid_type: str) -> dict:
        """
        Calculate the total usable disk space, fault tolerance, and redundancy for a given RAID configuration.

        Args:
        num_disks (int): The number of disks in the array.
        disk_sizes (list): A list of disk sizes in bytes.
        raid_type (str): The type of RAID or storage configuration.

        Returns:
        dict: A dictionary containing fault tolerance, number of RAID groups, redundancy, and total usable disk space.
        """
        total_disk_space = sum(disk_sizes)

        num_raid_groups_map = {
            "direct": 0,
            "lvm": 0,
            "raid0": 1,
            "raid1": num_disks // 2,
            "raid5": 1,
            "raid6": 1,
            "raid10": num_disks // 2 if num_disks >= 4 else 0,
            "raid50": num_disks // 5 if num_disks >= 6 else 0,
            "raid60": num_disks // 6 if num_disks >= 8 else 0,
            "zfs_stripe": 1,
            "zfs_mirror": num_disks // 2,
            "raidz1": 1,
            "raidz2": 1,
            "raidz3": 1,
        }

        utilization_map = {
            "direct": 1.0,
            "lvm": 1.0,
            "raid0": 1.0,
            "raid1": 0.5,
            "raid5": (num_disks - 1) / num_disks,
            "raid6": (num_disks - 2) / num_disks,
            "raid10": 0.5,
            "raid50": ((num_disks - num_raid_groups_map.get("raid50", 0)) / num_disks) if num_disks >= 6 else 0,
            "raid60": ((num_disks - num_raid_groups_map.get("raid60", 0) * 2) / num_disks) if num_disks >= 8 else 0,
            "zfs_stripe": 1.0,
            "zfs_mirror": 0.5,
            "raidz1": (num_disks - 1) / num_disks,
            "raidz2": (num_disks - 2) / num_disks,
            "raidz3": (num_disks - 3) / num_disks,
        }

        utilization = utilization_map.get(raid_type, 0.0)
        available_disk_space_map = {
            "direct": total_disk_space * utilization,
            "lvm": total_disk_space * utilization,
            "raid0": total_disk_space * utilization,
            "raid1": total_disk_space * utilization,
            "raid5": (num_disks - 1) * min(disk_sizes),
            "raid6": (num_disks - 2) * min(disk_sizes),
            "raid10": total_disk_space * utilization,
            "raid50": (total_disk_space // 5) * 4 * num_raid_groups_map.get("raid50", 0),
            "raid60": (total_disk_space // 6) * 4 * num_raid_groups_map.get("raid60", 0),
            "zfs_stripe": total_disk_space * utilization,
            "zfs_mirror": total_disk_space * utilization,
            "raidz1": (num_disks - 1) * min(disk_sizes),
            "raidz2": (num_disks - 2) * min(disk_sizes),
            "raidz3": (num_disks - 3) * min(disk_sizes),
        }

        formatted_disk_space = self.format_disk_space(available_disk_space_map.get(raid_type, 0))

        return {
            "available_disk_space_friendly": formatted_disk_space,
        }

    def build_capabilities_list(self, num_disks: int, disks: list[dict]) -> tuple[list[str], dict]:
        """
        Generate a list of possible RAID and storage configurations based on the number and sizes of available disks.

        Args:
        num_disks (int): The number of available disks.
        disks (list): A list of disk objects.

        Returns:
        tuple: A list of possible configurations and a dictionary with detailed information for each configuration.
        """
        capabilities = []

        if num_disks == 1 or num_disks > 0:
            capabilities.extend(["lvm"])

        if num_disks == 1:
            capabilities.extend(["direct"])

        if num_disks >= 2:
            # capabilities.extend(["raid0", "lvm_striped", "lvm_mirrored", "zfs_stripe", "zfs_mirror"])
            capabilities.extend(["raid0"])

            if num_disks % 2 == 0:
                capabilities.extend(["raid1"])

        if num_disks >= 3:
            # capabilities.extend(["raid5", "raidz1"])
            capabilities.extend(["raid5"])

        if num_disks >= 4:
            # capabilities.extend(["raid6", "raidz2"])
            capabilities.extend(["raid6"])

            if num_disks % 2 == 0:
                capabilities.extend(["raid10"])

        if num_disks >= 6:
            capabilities.append("raid50")

        if num_disks >= 8:
            #     # capabilities.extend(["raid60", "raidz3"])
            capabilities.extend(["raid60"])

        capabilities.sort()

        # Calculate RAID info for each capability
        raid_info = {}
        disk_sizes = [disk["size"] for disk in disks]
        for cap in capabilities:
            if cap is not None:
                raid_space_info = self.calculate_raid_space(num_disks, disk_sizes, cap)
                raid_info[cap] = {
                    **raid_space_info,
                    # "performance":            self.get_storage_config_data(cap, "performance"),
                    # "use_case":               self.get_storage_config_data(cap, "use_cases"),
                    # "expandability":          self.get_storage_config_data(cap, "expandability"),
                    # "rebuild_time":           self.get_storage_config_data(cap, "rebuild_time"),
                    # "data_safety":            self.get_storage_config_data(cap, "data_safety"),
                    # "pros":                   self.get_storage_config_data(cap, "pros"),
                    # "cons":                   self.get_storage_config_data(cap, "cons"),
                    # "backup_recommendations": self.get_storage_config_data(cap, "backup_recommendations"),
                    # "special_notes":          self.get_storage_config_data(cap, "special_notes"),
                    "file_systems": self.get_storage_config_data(cap, "file_systems"),
                }

        return capabilities, raid_info

    # Helper functions
    def get_storage_config_data(self, parent_key: str = None, child_key: str = None) -> dict | str:
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            yaml_path = os.path.join(script_dir, "storage_layout_data.yml")

            with open(yaml_path) as file:
                data = yaml.safe_load(file)

            if parent_key is None:
                return data
            elif parent_key in data:
                if child_key is None:
                    return data[parent_key]
                elif child_key in data[parent_key]:
                    return data[parent_key][child_key]
                else:
                    raise KeyError(f"Child key '{child_key}' not found in configuration data.")
            else:
                raise KeyError(f"Parent key '{parent_key}' not found in configuration data.")

        except FileNotFoundError as e:
            raise FileNotFoundError("Configuration file not found: storage_layout_data.yml") from e
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file: {e}") from e

    def enrich_with_raid_info(self, capabilities: list[str], raid_info: dict) -> dict:
        """
        Combine capability information with detailed RAID information.

        Args:
        capabilities (list): List of possible RAID configurations.
        raid_info (dict): Detailed information for each RAID configuration.

        Returns:
        dict: Enriched information combining capabilities and RAID details.
        """
        enriched_info = {}
        for capability in capabilities:
            enriched_info[capability] = raid_info.get(capability, {})
        return enriched_info

    def default_disk_layout(self, disk_groups: dict) -> dict:
        """
        Default disk layout based on the available SSD, NVMe, and HDD disks.

        Args:
        disk_groups (dict): A dictionary containing grouped disks by type and size.

        Returns:
        dict: A dictionary with default OS, data, and cold storage disks by group names.
        """
        os_disks_group = None
        data_disks_groups = []
        cold_storage_disks_groups = []

        smallest_hdd_size = None

        # Get the smallest SSD/NVMe for OS and the largest for data
        if "nvme" in disk_groups or "ssd" in disk_groups:
            # Combine NVMe and SSD groups
            ssd_nvme_group = {**disk_groups.get("nvme", {}), **disk_groups.get("ssd", {})}
            # Sort sizes to get the smallest and largest groups
            sorted_sizes = sorted(ssd_nvme_group.keys())

            if sorted_sizes:
                # Use the smallest SSD/NVMe for OS
                smallest_size = sorted_sizes[0]
                if smallest_size in disk_groups.get("nvme", {}):
                    os_disks_group = {
                        "config": "lvm",
                        "file_system": "ext4",
                        "group": f"NVME_{smallest_size // (1000**3)}GB",
                        "mountpoint": "/",
                    }
                elif smallest_size in disk_groups.get("ssd", {}):
                    os_disks_group = {
                        "config": "lvm",
                        "file_system": "ext4",
                        "group": f"SSD_{smallest_size // (1000**3)}GB",
                        "mountpoint": "/",
                    }

                # Use remaining SSD/NVMe groups for data, starting from the next smallest
                for size in sorted_sizes[1:]:
                    if size in disk_groups.get("nvme", {}):
                        data_disks_groups.append(
                            {
                                "config": "lvm",
                                "file_system": "ext4",
                                "group": f"NVME_{size // (1000**3)}GB",
                                "mountpoint": f"/data{len(data_disks_groups)}",
                            }
                        )
                    elif size in disk_groups.get("ssd", {}):
                        data_disks_groups.append(
                            {
                                "config": "lvm",
                                "file_system": "ext4",
                                "group": f"SSD_{size // (1000**3)}GB",
                                "mountpoint": f"/data{len(data_disks_groups)}",
                            }
                        )

        # Track which HDD size is used for OS
        hdd_used_for_os = None

        # If no SSD/NVMe, use the smallest HDD for OS
        if not os_disks_group and "hdd" in disk_groups:
            sorted_hdd_sizes = sorted(disk_groups["hdd"].keys())
            smallest_hdd_size = sorted_hdd_sizes[0]
            hdd_used_for_os = smallest_hdd_size
            os_disks_group = {
                "config": "lvm",
                "file_system": "ext4",
                "group": f"HDD_{smallest_hdd_size // (1000**3)}GB",
                "mountpoint": "/",
            }

        # Use HDDs for data/cold storage
        if "hdd" in disk_groups:
            sorted_hdd_sizes = sorted(disk_groups["hdd"].keys())

            # Use HDDs for data (skip the one used for OS)
            for size in sorted_hdd_sizes:
                if size != hdd_used_for_os:
                    data_disks_groups.append(
                        {
                            "config": "lvm",
                            "file_system": "ext4",
                            "group": f"HDD_{size // (1000**3)}GB",
                            "mountpoint": f"/data{len(data_disks_groups)}",
                        }
                    )

            # Use remaining HDDs for cold storage (skip the one used for OS and any used for data)
            for size in sorted_hdd_sizes:
                if size != hdd_used_for_os and size not in [hdd_used_for_os]:
                    cold_storage_disks_groups.append(
                        {
                            "config": "lvm",
                            "file_system": "ext4",
                            "group": f"HDD_{size // (1000**3)}GB",
                            "mountpoint": f"/cold{len(cold_storage_disks_groups)}",
                        }
                    )

        return {
            "os_disks_group": os_disks_group,
            "data_disks_groups": data_disks_groups,
            "cold_storage_disks_groups": cold_storage_disks_groups,
        }

    def check_disk_configuration(self) -> dict:
        """
        Analyze the disk configuration to determine possible RAID setups for OS and data disks.

        Args:
        disks (list): A list of disk information dictionaries.

        Returns:
        dict: A dictionary containing possible storage layouts for OS and data disks.
        """
        # Group disks by type (HDD, SSD, NVMe) and size
        disk_groups = defaultdict(lambda: defaultdict(list))

        for disk in self.lsblk:
            disk_size = disk["size"]
            if disk_size > 0 and "virtual" not in disk["serial"].lower():
                disk_type = "nvme" if "nvme" in disk["name"] else "ssd" if not disk["rota"] else "hdd"
                del disk["model"]
                del disk["rota"]
                disk_groups[disk_type][disk_size].append(disk)

        def get_capabilities_and_raid_info(disks):
            """Helper function to determine RAID capabilities and info."""
            return self.build_capabilities_list(len(disks), disks) if disks else (None, None)

        # Prepare all possible groupings for user selection
        disk_layouts = []
        for disk_type, sizes in disk_groups.items():
            for size, grouped_disks in sizes.items():
                if size > 0:
                    capabilities, raid_info = get_capabilities_and_raid_info(grouped_disks)
                    disks_in_group = [{k: v for k, v in disk.items() if k != "size"} for disk in grouped_disks]

                    available_filesystems = ["ext4"]
                    if not self.asrock_piece_of_shit:
                        available_filesystems += ["xfs"]

                    # Set thresholds to remove ext4 from the list of available file systems. 5 TB or 8 disks is the cut off for ext4
                    if (size // (1000**3) > 5120 or len(disks_in_group) > 8) and not self.asrock_piece_of_shit:
                        available_filesystems.remove("ext4")

                    disk_layout = {
                        "disk_group_name": f"{disk_type.upper()}_{size // (1000**3)}GB",
                        "disk_type": disk_type,
                        "disks": disks_in_group,
                        "capabilities": capabilities,
                        "size_per_disk": size,
                        "file_systems": available_filesystems,
                        "num_disks": len(disks_in_group),
                        # **self.enrich_with_raid_info(capabilities, raid_info)
                    }
                    disk_layouts.append(disk_layout)

        # Build the field_data dictionary with all possible layouts
        disk_default = self.default_disk_layout(disk_groups)
        field_data = {"configs": disk_layouts, "default": disk_default}

        return field_data
