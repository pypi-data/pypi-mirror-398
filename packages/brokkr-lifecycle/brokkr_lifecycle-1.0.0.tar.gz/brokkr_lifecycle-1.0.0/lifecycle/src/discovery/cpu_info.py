import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CpuInfo:
    lscpu: dict = None
    ghw_cpu: dict = None

    def __post_init__(self):
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        self.field_data = {}

        if self.lscpu:
            self.lscpu_data()

        if self.ghw_cpu:
            self.ghw_cpu_data()

        if self.field_data != {}:
            logger.info(f"CPU Data: {self.field_data}")

    def lscpu_data(self):
        # Total CPU count
        if self.lscpu.get("total_cpu_sockets") and self.lscpu["total_cpu_sockets"] is not None:
            self.field_data["cpu_physical_count"] = self.lscpu["total_cpu_sockets"]

        # Total core count
        if self.lscpu.get("total_cpu_cores") and self.lscpu["total_cpu_cores"] is not None:
            self.field_data["cpu_core_count"] = self.lscpu["total_cpu_cores"]

        # Total CPU threads
        if self.lscpu.get("total_cpu_threads") and self.lscpu["total_cpu_threads"] is not None:
            self.field_data["cpu_thread_count"] = self.lscpu["total_cpu_threads"]

        # Cores per CPU count
        if self.lscpu.get("per_cpu_cores") and self.lscpu["per_cpu_cores"] is not None:
            self.field_data["cores_per_cpu"] = self.lscpu["per_cpu_cores"]

        # Threads per CPU count
        if self.lscpu.get("per_cpu_threads") and self.lscpu["per_cpu_threads"] is not None:
            self.field_data["threads_per_cpu"] = self.lscpu["per_cpu_threads"]

        # Threads per core count
        if self.lscpu.get("per_core_threads") and self.lscpu["per_core_threads"] is not None:
            self.field_data["threads_per_core"] = self.lscpu["per_core_threads"]

    def ghw_cpu_data(self):
        if "cpu" in self.ghw_cpu and "processors" in self.ghw_cpu["cpu"] and len(self.ghw_cpu["cpu"]["processors"]) > 0:
            self.field_data["cpu_model"] = self.ghw_cpu["cpu"]["processors"][0]["model"]
            logger.info(f"CPU Model: {self.field_data['cpu_model']}")
