import logging
import os
from dataclasses import dataclass

import pynetbox

logger = logging.getLogger(__name__)


@dataclass
class AvailableOs:
    netbox: pynetbox
    nvidia: dict
    pci: dict
    virtualization: dict
    device: object | None = None
    architecture: dict | None = None

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        self.platform_ids = []
        self.field_data = {}
        self.is_device_tee = False
        self.device_arch = None

        # Extract architecture from discovery data
        if self.architecture and "machine" in self.architecture:
            if self.architecture["machine"] == "aarch64":
                self.device_arch = "arm64"
            elif self.architecture["machine"] == "x86_64":
                self.device_arch = "amd64"
        logger.info(f"Device architecture: {self.device_arch}")

        self.get_platforms()
        logger.info(f"Platforms defined in Netbox: {self.retrieved_platforms}")
        if self.retrieved_platforms:
            self.hypervisor_check()
            self.mellanox_check()
            self.nvidia_gpu_check()
            self.tee_check()
            self.determine_platforms()
            self.set_platforms()

    def _list_platforms(self, tag_slug):
        """List platforms by tag (extracted from HydraNetbox)"""
        platforms = self.netbox.dcim.platforms.filter(tag=tag_slug)
        if platforms:
            platforms = list(platforms)
            return platforms
        return None

    def get_platforms(self):
        self.retrieved_platforms = self._list_platforms(tag_slug="bmc")

    def _truthy(self, value) -> bool:
        """Convert various truthy values to boolean, including NetBox select field values"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            # Handle NetBox TEE select field: TRUE/true/True = enabled, FALSE/UNVERIFIED = disabled
            return value.strip().upper() == "TRUE"
        return False

    def tee_check(self) -> None:
        """
        Determine if this device should be eligible for TEE-enabled OS variants.
        Uses the NetBox device custom field, falling back to False when unavailable.
        """
        try:
            if self.device and getattr(self.device, "custom_fields", None):
                cf = self.device.custom_fields or {}
                # Accept multiple possible field names/casing
                for key in ("tee", "TEE", "Tee"):
                    if key in cf:
                        self.is_device_tee = self._truthy(cf.get(key))
                        break
        except Exception as e:
            logger.warning(f"TEE check failed: {e}")
            self.is_device_tee = False
        logger.info(f"Device TEE enabled: {self.is_device_tee}")

    def _platform_is_tee(self, platform) -> bool:
        """
        Identify whether a platform is a TEE-enabled variant by either:
        - custom field 'variant' = 'TEE'
        - custom field flag (tee / TEE / tee_enabled)
        - or by slug containing 'tee'
        """
        try:
            cf = platform.get("custom_fields", {})  # pynetbox Record behaves like dict

            # Check variant field (NetBox standard)
            variant = cf.get("variant", "")
            if isinstance(variant, str) and variant.upper() == "TEE":
                return True

            # Check explicit tee flags
            for key in ("tee", "TEE", "tee_enabled"):
                if key in cf:
                    return self._truthy(cf.get(key))

            # Fallback to slug check
            slug = str(platform.get("slug", "")).lower()
            return "tee" in slug
        except Exception:
            # Best-effort fallback based on slug text
            slug = str(getattr(platform, "slug", "")).lower()
            return "tee" in slug

    def _platform_matches_architecture(self, platform) -> bool:
        """
        Check if platform architecture matches device architecture via tags.
        Returns True if:
        - Device arch is unknown (allow all)
        - Platform has no arch tags (universal - allow all)
        - Platform has both amd64 and arm64 tags (universal - allow all)
        - Platform has one arch tag and it matches device arch
        """
        if not self.device_arch:
            # Unknown device arch - allow all platforms
            return True

        try:
            tags = platform.get("tags", []) if isinstance(platform, dict) else platform.tags
            # Extract tag slugs (tags can be dicts or strings)
            tag_slugs = []
            for t in tags:
                if isinstance(t, dict):
                    tag_slugs.append(t.get("slug", ""))
                else:
                    tag_slugs.append(str(t))

            # Check for architecture tags
            has_amd64 = "amd64" in tag_slugs or "x86_64" in tag_slugs
            has_arm64 = "arm64" in tag_slugs or "aarch64" in tag_slugs

            # No arch tags = universal platform (allow all)
            if not has_amd64 and not has_arm64:
                return True

            # Both arch tags = universal platform (allow all)
            if has_amd64 and has_arm64:
                return True

            # Single arch tag - must match device
            if self.device_arch == "amd64":
                return has_amd64
            elif self.device_arch == "arm64":
                return has_arm64

            return False
        except Exception as e:
            logger.warning(f"Architecture tag check failed for platform {platform.get('slug', 'unknown')}: {e}")
            # On error, allow the platform (fail open)
            return True

    def determine_platforms(self):
        for platform in self.retrieved_platforms:
            if platform["custom_fields"]["enabled"]:
                # Check architecture compatibility first
                if not self._platform_matches_architecture(platform):
                    logger.info(
                        f"Skipping platform {platform['slug']} - architecture mismatch "
                        f"(device: {self.device_arch}, platform: {platform.get('custom_fields', {}).get('architecture', 'any')})"
                    )
                    continue

                # Skip TEE platforms unless the device is explicitly marked as TEE-capable
                if self._platform_is_tee(platform) and not self.is_device_tee:
                    logger.info(f"Skipping TEE platform {platform['slug']} - device not TEE-capable")
                    continue

                # Explicitly allow pure TEE variants when device is TEE-capable
                if self.is_device_tee and "tee" in str(platform["slug"]).lower():
                    self.platform_ids.append(platform["id"])

                if self.is_hypervisor and "proxmox" in platform["slug"]:
                    self.platform_ids.append(platform["id"])

                if (self.has_mellanox or self.has_nvidia) and "hpc" in platform["slug"]:
                    self.platform_ids.append(platform["id"])

                if "vanilla" in platform["slug"]:
                    self.platform_ids.append(platform["id"])

                if "ipxe-custom" in platform["slug"]:
                    self.platform_ids.append(platform["id"])

        self.platform_ids = list(set(self.platform_ids))
        self.platform_ids.sort()
        logger.info(f"Available platforms: {self.platform_ids}")

    def set_platforms(self):
        self.field_data["available_operating_systems"] = self.platform_ids

    def hypervisor_check(self) -> bool:
        if self.virtualization is not None:
            if "hypervisor_enabled" in self.virtualization:
                if self.virtualization["hypervisor_enabled"] is True:
                    self.is_hypervisor = True
                    return
        self.is_hypervisor = False
        logger.info(f"Hypervisor enabled: {self.is_hypervisor}")

    def mellanox_check(self) -> None:
        if self.pci is not None:
            if "Devices" in self.pci:
                for pci_device in self.pci["Devices"]:
                    if "vendor" in pci_device:
                        if "name" in pci_device["vendor"]:
                            if "mellanox" in pci_device["vendor"]["name"].lower():
                                self.has_mellanox = True
                                return
        self.has_mellanox = False
        logger.info(f"Mellanox enabled: {self.has_mellanox}")

    def nvidia_gpu_check(self) -> bool:
        if self.nvidia is not None:
            if "count" in self.nvidia:
                if self.nvidia["count"] > 0:
                    self.has_nvidia = True
                    return
        self.has_nvidia = False
        logger.info(f"Nvidia GPU enabled: {self.has_nvidia}")
