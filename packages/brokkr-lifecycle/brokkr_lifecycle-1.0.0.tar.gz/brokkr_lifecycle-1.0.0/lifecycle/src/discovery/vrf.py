import logging
import os
from dataclasses import dataclass

import pynetbox

logger = logging.getLogger(__name__)


@dataclass
class VrfInfo:
    netbox: pynetbox.api
    location: object
    tenant: object

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        if self.tenant and self.location:
            # Look up VRF by name using pynetbox API
            vrfs = list(self.netbox.ipam.vrfs.filter(name=str(self.location.id), tenant_id=int(self.tenant.id)))
            self.vrf = vrfs[0] if vrfs else None
            logger.info(f"VRF Name: {self.vrf.name}")
            logger.info(f"VRF ID: {self.vrf.id}")

        else:
            logger.info("Missing tenant or location, no VRF available")
            self.vrf = None
