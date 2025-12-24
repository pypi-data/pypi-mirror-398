"""
Disk operations and wipe management utilities.

This module handles disk wiping operations and status tracking for the
Brokkr discovery and lifecycle management system.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any


def perform_disk_wipe(
    device_id: str,
    status: str,
    bridge_client,
    wipe_tracker=None,
    retry_delay: int = 60,
    max_retries: int = 5,
) -> None:
    """
    Perform a disk wipe operation based on the device status with a retry limit.

    Args:
        device_id: Device identifier
        status: Device status
        bridge_client: BridgeClient instance for API communication
        wipe_tracker: WipeStatusTracker instance for status updates
        retry_delay: Time in seconds between API polling attempts
        max_retries: Maximum number of retries before giving up
    """
    wipe_url = f"{bridge_client.bridge_url}/api/lifecycle/wipe"
    retry_count = 0
    wipe_successful = False

    logging.info(f"Device ID: {device_id}")
    logging.info(f"Device Status: {status}")

    if not status:
        logging.error("Device status is empty.")
        if wipe_tracker:
            wipe_tracker.set_status("failed")
        return

    if status not in ["decommissioning"]:
        logging.info(f"Status '{status}' does not require wiping - marking as skipped.")
        if wipe_tracker:
            wipe_tracker.set_status("skipped")
        return

    # Status requires wiping
    logging.info("Status requires wiping. Proceeding with wipe.")

    while retry_count < max_retries:
        try:
            payload = _build_payload(device_id)
            logging.info(f"Attempting wipe for device: {device_id}")
            success, wipe_response = _perform_wipe(wipe_url, payload, bridge_client)

            if success:
                logging.info("Wipe completed successfully.")
                if wipe_tracker:
                    wipe_tracker.set_status("complete")
                wipe_successful = True
                return

            # If wipe failed, retry
            logging.error("Wipe failed.")

        except ValueError as e:
            logging.error(f"Error: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {str(e)}")

        retry_count += 1
        if retry_count < max_retries:
            logging.info(f"Retrying in {retry_delay} seconds... (Attempt {retry_count}/{max_retries})")
            time.sleep(retry_delay)
        else:
            logging.error(f"Disk wipe operation failed after {max_retries} attempts.")

    # Final status check outside the retry loop
    if not wipe_successful:
        logging.error("Disk wipe operation ultimately failed.")
        if wipe_tracker:
            wipe_tracker.set_status("failed")


def _build_payload(device_id: str) -> dict[str, Any]:
    """
    Build a payload dictionary for wipe API requests.

    Args:
        device_id: The NetBox device ID

    Returns:
        Dictionary containing the payload information
    """
    # Get job ID from environment variables
    import os

    job_id = os.getenv("JOB_ID")

    # Use job_id from environment, fallback to device-based ID
    if job_id and job_id.strip():
        job_id_clean = job_id.strip()
    else:
        job_id_clean = f"wipe-{device_id}"

    return {
        "device_id": device_id,
        "target_ssh_username": "root",
        "target_ssh_port": 22,
        "job_id": job_id_clean,
    }


def _perform_wipe(wipe_url: str, payload: dict[str, Any], bridge_client) -> tuple[bool, dict[str, Any]]:
    """
    Initiate and monitor a wipe operation by sending requests to the wipe URL.

    Args:
        wipe_url: The URL to send the wipe request to
        payload: The payload to send with the wipe request
        bridge_client: BridgeClient instance for making authenticated requests

    Returns:
        Tuple of (success status, wipe response data)
    """

    logging.info("Initiating wipe process...")

    try:
        # Get job ID from environment and prepare headers
        import os

        job_id = os.getenv("JOB_ID")
        job_id_clean = job_id.strip() if job_id else f"wipe-{int(time.time())}"

        headers = {"x-brokkr-job-id": job_id_clean}
        headers["Content-Type"] = "application/json"

        # Send wipe request - will return immediately with job info
        response = bridge_client.session.post(
            wipe_url,
            json=payload,
            headers=headers,
            timeout=30,  # Short timeout for job start
        )

        # Check if job was accepted (202) or completed immediately (200 for legacy)
        if response.status_code == 202:
            # Async job started - poll for completion
            job_data = response.json()
            job_id = job_data.get("job_id")
            status_url = (
                f"{bridge_client.bridge_url}{job_data.get('status_url', f'/api/lifecycle/wipe/status/{job_id}')}"
            )

            logging.info(f"Wipe job {job_id} started, polling for completion...")

            # Poll for job completion
            max_wait_time = 3600  # 60 minutes max
            poll_interval = 5  # Check every 5 seconds
            elapsed = 0

            while elapsed < max_wait_time:
                time.sleep(poll_interval)
                elapsed += poll_interval

                # Get job status
                status_response = bridge_client.session.get(status_url, headers=headers, timeout=30)

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status")

                    if status == "complete":
                        logging.info("Wipe job completed successfully.")
                        return True, status_data.get("result", {})
                    elif status == "failed":
                        error = status_data.get("error", "Unknown error")
                        logging.error(f"Wipe job failed: {error}")
                        return False, {"error": error}
                    elif status == "running":
                        progress = status_data.get("progress", {})
                        stage = progress.get("stage", "unknown")
                        message = progress.get("message", "")
                        logging.info(f"Wipe job in progress: {stage} - {message}")
                else:
                    logging.warning(f"Failed to get job status: {status_response.status_code}")

            logging.error(f"Wipe job timed out after {max_wait_time} seconds")
            return False, {"error": "Job timed out"}

        elif response.status_code == 200:
            logging.info("Wipe request successful.")
            return True, response.json()
        else:
            logging.error(f"Wipe request failed with status code {response.status_code}.")
            try:
                error_data = response.json()
                error_message = error_data.get("error", "No error message provided.")
            except Exception:
                error_message = "No response body or invalid JSON."
            logging.error(f"Error: {error_message}")
            return False, {}

    except Exception as e:
        logging.error(f"Wipe request failed: {e}")
        return False, {}


class WipeStatusTracker:
    """
    Track disk wipe operations and maintain status counts.
    """

    def __init__(self, output_file: str):
        """
        Initialize wipe status tracker.

        Args:
            output_file: Path to output JSON status file
        """
        self.output_file = output_file
        self.status = {
            "num_of_disk_wipes": 0,
            "secure_wipes": 0,
            "insecure_wipes": 0,
            "failed_wipes": 0,
            "nvme_wipes": 0,
            "sshd_wipes": 0,
            "hdd_wipes": 0,
            "wipe_status": "pending",
        }
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Ensure output directory exists."""
        Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)

    def set_status(self, status: str):
        """Set the overall wipe status."""
        self.status["wipe_status"] = status
        self._save_status()

    def increment_wipe_count(self, wipe_type: str):
        """Increment a specific wipe counter."""
        if wipe_type in self.status:
            self.status[wipe_type] += 1
            self.status["num_of_disk_wipes"] += 1
        self._save_status()

    def _save_status(self):
        """Save current status to file."""
        try:
            with open(self.output_file, "w") as f:
                json.dump(self.status, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save wipe status: {e}")

    def get_status(self) -> dict[str, Any]:
        """Get current status."""
        return self.status.copy()
