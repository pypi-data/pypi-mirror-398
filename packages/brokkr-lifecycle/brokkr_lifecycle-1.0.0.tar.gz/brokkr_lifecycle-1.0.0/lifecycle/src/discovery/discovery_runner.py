import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
"""
Discovery Package Runner
Handles running the brokkr-collector Python package and managing collection files
"""


class DiscoveryRunner:
    """
    Manages running the brokkr-collector Python package and processing collection files
    """

    def __init__(self, output_dir: str = "/tmp", shared_dir: str = "/opt/brokkr"):
        self.output_dir = output_dir
        self.shared_dir = shared_dir
        self.collection_file: str | None = None
        self.collection_data: dict[str, Any] | None = None

        # Package installation paths (set by lifecycle-download.sh)
        self.package_dir = Path("/tmp/discovery-processor")
        self.collector_module_path = self.package_dir / "collector"

    async def run_discovery_collection(
        self, dry_run: bool = False, install_packages: bool = False, check_dependencies: bool = False
    ) -> bool:
        """
        Run the brokkr-collector Python package and capture the collection file

        Args:
            dry_run: If True, simulate the discovery run
            install_packages: If True, install required system packages before running
            check_dependencies: If True, check if all dependencies are installed

        Returns:
            bool: True if successful, False otherwise
        """
        if dry_run:
            logger.info("🔍 DRY RUN: Simulating brokkr-collector execution")
            return await self._simulate_discovery()

        try:
            logger.info("=== Starting discovery collection ===")
            logger.info(f"Output directory: {self.output_dir}")

            # Ensure package is available
            package_available = await self._ensure_package_available()
            if not package_available:
                logger.error("Failed to ensure brokkr-collector package is available")
                return False

            # Handle dependency checking or installation if requested
            if check_dependencies or install_packages:
                if check_dependencies:
                    logger.info("Checking dependencies...")
                    check_cmd = ["brokkr-collector", "--check-dependencies"]
                    check_process = await asyncio.create_subprocess_exec(
                        *check_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                    )
                    check_output, _ = await check_process.communicate()
                    output_str = check_output.decode() if check_output else ""
                    logger.info(f"Dependency check result:\n{output_str}")

                    if check_process.returncode != 0:
                        logger.warning("Some dependencies are missing")
                        if not install_packages:
                            logger.warning("Consider running with install_packages=True or set INSTALL_PACKAGES=true")

                if install_packages:
                    # Check if we're running as root (required for package installation)
                    if os.geteuid() != 0:
                        # Try to run with sudo
                        logger.info("Package installation requires root privileges, attempting with sudo...")
                        install_cmd = ["sudo", "brokkr-collector", "--install-packages"]
                    else:
                        logger.info("Installing required packages as root...")
                        install_cmd = ["brokkr-collector", "--install-packages"]

                    logger.info(f"Running command: {' '.join(install_cmd)}")
                    install_process = await asyncio.create_subprocess_exec(
                        *install_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                    )
                    install_output, _ = await install_process.communicate()
                    output_str = install_output.decode() if install_output else ""

                    # Log the output for debugging
                    if output_str:
                        logger.info(f"Package installation output:\n{output_str}")

                    # Always continue regardless of return code
                    if install_process.returncode != 0:
                        logger.warning("Some packages may have failed to install, but continuing anyway...")
                    else:
                        logger.info("✅ Package installation completed")

                    # Re-check if brokkr-collector is available after installation
                    collector_path = shutil.which("brokkr-collector")
                    if not collector_path:
                        logger.error("brokkr-collector command still not found after package installation")
                        logger.info("Checking PATH and pip installation...")
                        logger.info(f"Current PATH: {os.environ.get('PATH', 'NOT_SET')}")
                        # Check pip installation
                        try:
                            pip_result = subprocess.run(
                                ["pip", "show", "brokkr-collector"], capture_output=True, text=True, timeout=5
                            )
                            if pip_result.returncode == 0:
                                logger.info(f"Pip package info:\n{pip_result.stdout}")
                            else:
                                logger.error("brokkr-collector not installed via pip")
                        except Exception as e:
                            logger.error(f"Could not check pip installation: {e}")

                        return False  # Fail if command not available

            # Run brokkr-collector using the installed pip package
            logger.info("Running brokkr-collector Python package...")

            try:
                # Use environment as-is (Nomad job sets PYTHONPATH to dist-packages)
                env = os.environ.copy()
                logger.info(f"Using PYTHONPATH: {env.get('PYTHONPATH', 'NOT_SET')}")

                # Use the brokkr-collector command that was installed by pip
                logger.info(f"Executing: brokkr-collector --output-dir {self.output_dir}")
                process = await asyncio.create_subprocess_exec(
                    "brokkr-collector",
                    "--output-dir",
                    self.output_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    env=env,
                )

                stdout, _ = await process.communicate()
                output = stdout.decode() if stdout else ""

                logger.info(f"brokkr-collector output: {output}")
                logger.info(f"Exit code: {process.returncode}")

                success = process.returncode == 0

            except Exception as e:
                logger.error(f"Failed to run brokkr-collector command: {e}")
                return False

            if not success:
                logger.error("brokkr-collector package execution failed")
                return False

            # Find the collection file in output directory
            collection_file = await self._find_collection_file()
            if not collection_file:
                logger.error("Could not find collection file after execution")
                return False

            self.collection_file = collection_file
            logger.info(f"Collection found at: {self.collection_file}")

            # Copy to shared location and save filename
            await self._save_collection_info()

            return True

        except Exception as e:
            logger.error(f"Error running brokkr-collector package: {e}")
            return False

    async def run_discovery_binary(self, dry_run: bool = False) -> bool:
        """
        Backward compatibility alias for run_discovery_collection

        Args:
            dry_run: If True, simulate the discovery run

        Returns:
            bool: True if successful, False otherwise
        """
        return await self.run_discovery_collection(dry_run)

    async def _simulate_discovery(self) -> bool:
        """Simulate discovery for dry run mode"""
        logger.info("🔍 DRY RUN: Creating mock collection file")

        # Create a mock collection file
        timestamp = int(time.time())
        mock_filename = f"{self.output_dir}/collection_{timestamp}_mock.json"

        mock_data = {
            "bdi": {
                "device_id": os.environ.get("DEVICE_ID", "999"),
                "role_id": os.environ.get("DEVICE_ROLE", "6"),
                "tenant_id": 1,
                "site_id": 76,
                "location_id": 14,
                "station_mac": "00:11:22:33:44:55",
                "station_ip": "192.168.1.100",
            },
            "ghw_baseboard": {"vendor": "Mock Vendor"},
            "lsblk": [{"name": "sda", "size": "1TB"}],
            "version": {"kernel": "6.1.0"},
        }

        with open(mock_filename, "w") as f:
            json.dump(mock_data, f, indent=2)

        self.collection_file = mock_filename
        logger.info(f"🔍 DRY RUN: Mock collection file created: {mock_filename}")

        await self._save_collection_info()
        return True

    async def _find_collection_file(self) -> str | None:
        """
        Find the collection file in output directory

        Returns:
            str: Collection filename or None if not found
        """
        try:
            # Look for the standard collection file only
            standard_file = Path(self.output_dir) / "collection-results.json"
            if standard_file.exists():
                logger.info(f"Found collection file: {standard_file}")
                return str(standard_file)
            else:
                logger.error(f"Collection file not found: {standard_file}")
                return None

        except Exception as e:
            logger.error(f"Error looking for collection file: {e}")
            return None

    async def _save_collection_info(self):
        """Save collection file info to shared location"""
        try:
            # Ensure shared directory exists
            os.makedirs(self.shared_dir, exist_ok=True)

            # Copy collection file to shared location
            shared_collection_path = f"{self.shared_dir}/latest-collection.json"

            # Remove existing file if it exists
            if os.path.exists(shared_collection_path):
                os.remove(shared_collection_path)

            # Copy the file
            shutil.copy2(self.collection_file, shared_collection_path)

            # Save the original filename for reference
            filename_path = f"{self.shared_dir}/collection-filename.txt"
            with open(filename_path, "w") as f:
                f.write(self.collection_file)

            logger.info(f"Collection file copied to: {shared_collection_path}")
            logger.info(f"Original filename saved to: {filename_path}")

        except Exception as e:
            logger.error(f"Error saving collection info: {e}")
            raise

    async def load_collection_data(self) -> dict[str, Any] | None:
        """
        Load the collection data from the most recent collection file

        Returns:
            dict: Collection data or None if not available
        """
        if not self.collection_file or not os.path.isfile(self.collection_file):
            logger.error("No valid collection file available")
            return None

        try:
            with open(self.collection_file) as f:
                self.collection_data = json.load(f)

            logger.info(f"Loaded collection data from: {self.collection_file}")
            return self.collection_data

        except Exception as e:
            logger.error(f"Error loading collection data: {e}")
            return None

    def get_collection_file_path(self) -> str | None:
        """Get the path to the collection file"""
        return self.collection_file

    def get_collection_data(self) -> dict[str, Any] | None:
        """Get the loaded collection data"""
        return self.collection_data

    async def _ensure_package_available(self) -> bool:
        """
        Ensure brokkr-collector Python package is available.

        Returns:
            bool: True if package is available, False otherwise
        """
        try:
            # Check if brokkr-collector command is available (installed via pip)
            import shutil
            import subprocess

            collector_path = shutil.which("brokkr-collector")

            if collector_path:
                logger.info(f"brokkr-collector command found at: {collector_path}")

                # Try to get the version
                try:
                    process = await asyncio.create_subprocess_exec(
                        "brokkr-collector",
                        "--version",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await process.communicate()
                    version_output = stdout.decode().strip() if stdout else stderr.decode().strip()
                    if version_output:
                        logger.info(f"brokkr-collector version: {version_output}")
                except Exception as e:
                    logger.warning(f"Could not get version: {e}")

                return True
            else:
                logger.error("brokkr-collector command not found in PATH")
                logger.info("Make sure brokkr-collector package has been installed via pip")

                # Try to check if the package is installed via pip
                try:
                    result = subprocess.run(
                        ["pip", "show", "brokkr-collector"], capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        logger.info("brokkr-collector package is installed but command not in PATH")
                        logger.info(result.stdout)
                    else:
                        logger.error("brokkr-collector package is not installed")
                        logger.info("Run: pip install brokkr-collector")
                except Exception as e:
                    logger.error(f"Could not check pip installation: {e}")

                # Also check if the old package directory structure exists
                if self.package_dir.exists():
                    logger.info(f"Legacy package directory found at: {self.package_dir}")
                    # Check version file to see what was installed
                    version_file = self.package_dir / ".version"
                    if version_file.exists():
                        version = version_file.read_text().strip()
                        logger.info(f"Legacy package version: {version}")
                        logger.info("The package should have been installed via pip by lifecycle-download.sh")

                return False

        except Exception as e:
            logger.error(f"Error checking package availability: {e}")
            return False
