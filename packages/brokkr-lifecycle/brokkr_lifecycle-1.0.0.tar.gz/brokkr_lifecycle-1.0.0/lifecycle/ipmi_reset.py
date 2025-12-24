#!/usr/bin/env python3
"""
IPMI Reset and Health Check Tool

Detects bad/wedged IPMI KCS state and performs cold reset via Bridge API.
Enhanced for Nomad job execution with comprehensive logging and monitoring.

Environment Variables:
  Required for Bridge API calls:
    BRIDGE_URL      - Bridge API endpoint (e.g. "https://bridge.example.com")
    IPMI_MAC        - BMC MAC address (e.g. "00:11:22:33:44:55")
    BMC_USER        - BMC username
    BMC_PASS        - BMC password

  Optional:
    BMC_PORT        - IPMI port (default: 623)
    UEFI            - UEFI mode (true/false, default: false)
    JOB_ID          - Job ID for tracking (sent as x-brokkr-job-id header)
    LOG_LEVEL       - Logging level (DEBUG, INFO, WARNING, ERROR)
    RESET_WAIT_TIME - Wait time after reset in seconds (default: 300)

Exit codes:
  0 = OK (IPMI present and healthy)
  2 = No local IPMI interface detected
  3 = Suspected bad KCS/IPMI state (Bridge API reset attempted)
  4 = Tools missing (neither FreeIPMI nor ipmitool available)
  1 = Unexpected error
"""

import glob
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# Setup logging
def setup_logging():
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
        force=True,
    )
    return logging.getLogger(__name__)


logger = setup_logging()

# --- Tooling config ---
BMC_INFO = shutil.which("bmc-info") or "bmc-info"
IPMITOOL = shutil.which("ipmitool") or "ipmitool"
IPMITOOL_TIMEOUT_SEC = 10

FREEIPMI_BAD_PATTERNS = [
    "driver busy",
    "invalid state",
    "command not supported in present state",
]

IPMITOOL_BAD_PATTERNS = [
    "bmc not responding",
    "timeout",
    "driver timeout",
    "ipmi response is null",
    "no valid response received",
    "could not open device",
    "command not supported in present state",
]

# --- Bridge API helpers ---


def _bridge_endpoint() -> str | None:
    base = os.environ.get("BRIDGE_URL", "").strip()
    if not base:
        return None
    return f"{base.rstrip('/')}/api/oob/ipmi"


def _bridge_body(operation: str) -> dict:
    """Create request body matching the API specification"""
    body = {
        "mac_address": os.environ.get("IPMI_MAC", ""),
        "username": os.environ.get("BMC_USER", ""),
        "password": os.environ.get("BMC_PASS", ""),
        "operation": operation,
    }

    # Add optional fields if environment variables are set
    if os.environ.get("BMC_PORT"):
        body["port"] = int(os.environ.get("BMC_PORT", "623"))

    if os.environ.get("UEFI"):
        body["uefi"] = os.environ.get("UEFI", "false").lower() == "true"

    return body


def bridge_post(operation: str, timeout: int = 15) -> tuple[bool, int | None, str]:
    """
    POST to {BRIDGE_URL}/api/oob/ipmi with JSON body and return (ok, status_code, response_text).
    Returns (False, None, reason) if env vars missing or request fails.
    """
    url = _bridge_endpoint()
    if not url:
        return (False, None, "BRIDGE_URL not set; skipping Bridge call")

    body = _bridge_body(operation)
    missing = [
        k
        for k, v in [("IPMI_MAC", body["mac_address"]), ("BMC_USER", body["username"]), ("BMC_PASS", body["password"])]
        if not v
    ]
    if missing:
        return (False, None, f"Missing env vars for Bridge call: {', '.join(missing)}")

    data = json.dumps(body).encode("utf-8")

    # Prepare headers
    headers = {"Content-Type": "application/json"}

    # Add optional job ID header if available
    job_id = os.environ.get("JOB_ID")
    if job_id:
        headers["x-brokkr-job-id"] = job_id

    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")

            # Parse JSON response if possible
            try:
                response_data = json.loads(text)
                if isinstance(response_data, dict):
                    result = response_data.get("result", "unknown")
                    response_text = response_data.get("response", text)
                    return (200 <= resp.status < 300 and result == "success", resp.status, response_text)
            except json.JSONDecodeError:
                pass

            return (200 <= resp.status < 300, resp.status, text)
    except HTTPError as e:
        try:
            text = e.read().decode("utf-8", errors="replace")
        except Exception:
            text = str(e)
        return (False, e.code, text)
    except URLError as e:
        return (False, None, f"URLError: {e.reason}")
    except Exception as e:
        return (False, None, f"Error: {e}")


def bridge_cold_reset_then_status():
    """
    Fire cold reset, wait for configured time, then status check.
    Uses enhanced logging and configurable wait time.
    """
    logger.info("Starting IPMI cold reset via Bridge API")

    # Perform cold reset
    ok, code, text = bridge_post("cold")
    if not ok:
        logger.error(f"Bridge cold reset failed (status={code}): {text}")
        return False

    logger.info(f"Bridge cold reset successful (status={code}): {text}")

    # Configure wait time
    wait_time = int(os.environ.get("RESET_WAIT_TIME", "300"))  # Default 5 minutes
    logger.info(f"Waiting {wait_time} seconds for BMC to complete reset...")

    # Wait with progress logging
    for i in range(wait_time // 60):
        time.sleep(60)
        remaining = wait_time - (i + 1) * 60
        if remaining > 0:
            logger.info(f"Reset in progress... {remaining} seconds remaining")

    # Sleep any remaining seconds
    remaining_seconds = wait_time % 60
    if remaining_seconds > 0:
        time.sleep(remaining_seconds)

    logger.info("Reset wait period complete, checking BMC status...")

    # Check status
    ok2, code2, text2 = bridge_post("status")
    if not ok2:
        logger.error(f"Bridge status check failed (status={code2}): {text2}")
        return False
    logger.info(f"Bridge status check successful (status={code2}): {text2}")
    return True


# --- Detection logic ---


def has_local_ipmi() -> bool:
    if any(os.path.exists(p) for p in glob.glob("/dev/ipmi*") + glob.glob("/dev/ipmidev/*")):
        return True
    if os.path.isdir("/sys/class/ipmi"):
        try:
            if any(e.startswith("ipmi") for e in os.listdir("/sys/class/ipmi")):
                return True
        except Exception:
            pass
    return False


def run(cmd: list[str], timeout: int | float | None = None) -> tuple[int, str, str, bool]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", e.stderr or "", True


def contains_any(s: str, needles: list[str]) -> bool:
    ls = s.lower()
    return any(n.lower() in ls for n in needles)


def detect_bad_kcs() -> tuple[bool, str]:
    """
    Detect bad IPMI/KCS state using available tools.
    Returns (is_bad, reason).
    """
    logger.debug("Checking for local IPMI interface...")
    if not has_local_ipmi():
        logger.info("No local IPMI/KCS interface detected")
        return False, "No local IPMI/KCS interface detected"

    # Check available tools
    freeipmi_found = shutil.which("bmc-info") is not None
    ipmitool_found = shutil.which("ipmitool") is not None

    logger.info(f"Tool availability: FreeIPMI={freeipmi_found}, ipmitool={ipmitool_found}")

    if not freeipmi_found and not ipmitool_found:
        logger.error("Neither FreeIPMI (bmc-info) nor ipmitool found in PATH")
        return False, "Neither FreeIPMI (bmc-info) nor ipmitool found in PATH"

    # Prefer FreeIPMI for better KCS state detection
    if freeipmi_found:
        logger.debug("Testing IPMI state with FreeIPMI (bmc-info)...")
        rc, out, err, to = run([BMC_INFO, "--driver-type=KCS"], timeout=10)
        combined = f"{out}\n{err}"

        logger.debug(f"bmc-info result: rc={rc}, timeout={to}")
        logger.debug(f"bmc-info output: {combined}")

        if to:
            logger.warning("bmc-info timed out after 10 seconds")
            return True, "bmc-info timed out (10s)"
        if rc != 0 and contains_any(combined, FREEIPMI_BAD_PATTERNS):
            logger.warning("bmc-info reported KCS busy/invalid state")
            return True, "bmc-info reported KCS busy/invalid state"
        if rc == 0 and contains_any(combined, FREEIPMI_BAD_PATTERNS):
            logger.warning("bmc-info indicates KCS busy/invalid state")
            return True, "bmc-info indicates KCS busy/invalid state"
        if rc == 0:
            logger.info("FreeIPMI test passed; KCS appears healthy")
            return False, "FreeIPMI succeeded; KCS appears healthy"

        logger.debug("FreeIPMI inconclusive, falling back to ipmitool...")

    # Fallback to ipmitool
    if ipmitool_found:
        logger.debug("Testing IPMI state with ipmitool...")
        rc, out, err, to = run([IPMITOOL, "lan", "print"], timeout=IPMITOOL_TIMEOUT_SEC)
        combined = f"{out}\n{err}"

        logger.debug(f"ipmitool result: rc={rc}, timeout={to}")
        logger.debug(f"ipmitool output: {combined}")

        if to:
            logger.warning(f"ipmitool timed out after {IPMITOOL_TIMEOUT_SEC} seconds")
            return True, f"ipmitool timed out after {IPMITOOL_TIMEOUT_SEC}s"
        if rc != 0 or contains_any(combined, IPMITOOL_BAD_PATTERNS):
            logger.warning(f"ipmitool indicates bad state (exit={rc})")
            return True, f"ipmitool indicates bad state (exit={rc})"

        logger.info("ipmitool test passed; KCS appears healthy")
        return False, "ipmitool succeeded; KCS appears healthy"

    logger.error("Unexpected detection path - no tools executed")
    return False, "Unexpected detection path"


def main() -> int:
    """
    Main execution function with enhanced logging and error handling
    """
    try:
        logger.info("IPMI Reset Tool starting")
        logger.info(f"Job ID: {os.environ.get('JOB_ID', 'not set')}")
        logger.info(f"Bridge URL: {os.environ.get('BRIDGE_URL', 'not set')}")
        logger.info(f"IPMI MAC: {os.environ.get('IPMI_MAC', 'not set')}")

        # Detect IPMI state
        logger.info("Detecting IPMI/KCS state...")
        bad, reason = detect_bad_kcs()

        if bad:
            logger.warning(f"Bad IPMI/KCS state detected: {reason}")

            # Check if Bridge API is configured
            bridge_url = _bridge_endpoint()
            if bridge_url:
                logger.info("Bridge API configured, attempting cold reset and status check")
                success = bridge_cold_reset_then_status()

                if success:
                    logger.info("✅ IPMI reset completed successfully")
                    return 0  # Success

                logger.error("❌ IPMI reset failed")
                return 3  # Reset attempted but failed

            logger.warning("Bridge API not configured (missing BRIDGE_URL/IPMI_MAC/BMC_USER/BMC_PASS)")
            logger.warning("IPMI issue detected but no reset action taken")
            return 3  # Bad state but no action

        logger.info(f"✅ IPMI state healthy: {reason}")
        return 0  # All good

    except Exception as e:
        logger.error(f"Unexpected error in IPMI reset tool: {e}")
        return 1


if __name__ == "__main__":
    main()
