import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
"""
IPMI Service for Discovery classes
Simplified version that makes direct API requests to a given server
"""


@dataclass
class IPMIService:
    """
    Simplified IPMI service that makes direct API requests to a server.

    This service handles IPMI operations through direct HTTP requests,
    providing power management, serial console, and virtual media capabilities.
    """

    server_url: str  # The server to make requests to (e.g., "https://bridge.example.com")
    mac_address: str
    bmc_user: str
    bmc_pass: str
    bmc_port: int = 623
    uefi: bool = True
    job_id: str | None = None
    timeout: int = 60

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def perform_ipmi_operation(self, operation: str) -> bool:
        """
        Perform an IPMI operation through direct API request.

        Args:
            operation: The IPMI operation to perform (e.g., "on", "off", "status", "reset", "cold")

        Returns:
            bool: True if operation successful, False otherwise

        Raises:
            Exception: If operation fails after retries
        """
        try:
            logger.warning(f"Performing IPMI operation: {operation}")

            payload = {
                "mac_address": self.mac_address,
                "username": self.bmc_user,
                "password": self.bmc_pass,
                "port": self.bmc_port,
                "operation": operation,
                "uefi": self.uefi,
                "job_id": self.job_id or "",
            }

            # Make direct API request
            response = await self._make_request(
                method="POST", endpoint="/api/oob/ipmi", json=payload, timeout=self.timeout
            )

            if not response:
                raise Exception(f"No response received for IPMI operation {operation}")

            logger.info(f"API response status: {response.status_code}")

            if response.status_code != 200:
                # Try to get JSON error details if available
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = f"code={response.status_code} json={error_json}"
                except Exception:
                    error_detail = f"code={response.status_code} text={response.text}"

                logger.error(f"API response error: {error_detail}")
                raise Exception(f"Failed to perform IPMI operation {operation}: {error_detail}")

            json_response = response.json()
            if json_response.get("result") == "failure":
                raise Exception(f"IPMI operation failed: {json_response.get('error', 'Unknown error')}")

            logger.warning(f"IPMI response: {json_response}")

            # For power operations, ensure the operation completes before moving on
            if operation in ["off", "on", "soft"]:
                return await self._perform_power_operation_with_retry(payload, operation)

            return True

        except Exception as e:
            logger.error(f"Exception during IPMI operation {operation}: {str(e)}")
            raise

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response | None:
        """
        Make HTTP request to the server.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx request

        Returns:
            httpx.Response or None if request failed
        """
        url = f"{self.server_url.rstrip('/')}{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            # Skip SSL verification for development (can be made configurable)
            verify_ssl = False  # Typically false for internal bridge APIs

            async with httpx.AsyncClient(verify=verify_ssl, timeout=self.timeout) as client:
                response = await client.request(method=method, url=url, headers=headers, **kwargs)
                return response

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during request to {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during request to {url}: {e}")
            return None

    async def _perform_power_operation_with_retry(self, base_payload: dict[str, Any], operation: str) -> bool:
        """
        Enhanced power operation with retry logic and detailed status checking.

        Args:
            base_payload: Base payload for the IPMI request
            operation: Power operation to perform ("on", "off", "soft")

        Returns:
            bool: True if operation successful

        Raises:
            Exception: If operation fails after all retries
        """
        max_operation_retries = 3
        status_checks_per_retry = 3
        status_check_interval = 5

        # Prepare status check payload
        status_payload = base_payload.copy()
        status_payload["operation"] = "status"

        for attempt in range(1, max_operation_retries + 1):
            logger.info(f"IPMI operation attempt {attempt}/{max_operation_retries}: {operation}")

            # The initial operation was already performed, so we skip it for the first attempt
            if attempt > 1:
                # Re-perform the operation for retry attempts
                operation_payload = base_payload.copy()
                operation_payload["operation"] = operation

                response = await self._make_request(
                    method="POST", endpoint="/api/oob/ipmi", json=operation_payload, timeout=self.timeout
                )

                if not response or response.status_code != 200:
                    if response:
                        # Try to get JSON error details if available
                        try:
                            error_json = response.json()
                            error_detail = f"code={response.status_code} json={error_json}"
                        except Exception:
                            error_detail = f"code={response.status_code} text={response.text}"
                        logger.warning(f"Retry attempt {attempt} failed: {error_detail}")
                    else:
                        logger.warning(f"Retry attempt {attempt} failed: No response")
                    if attempt == max_operation_retries:
                        raise Exception(f"IPMI operation {operation} failed after {max_operation_retries} attempts")
                    continue

                json_response = response.json()
                if json_response.get("result") == "failure":
                    logger.warning(f"Retry attempt {attempt} failed: {json_response.get('error', 'Unknown error')}")
                    if attempt == max_operation_retries:
                        raise Exception(f"IPMI operation {operation} failed after {max_operation_retries} attempts")
                    continue

                logger.info(f"Retry attempt {attempt} initiated successfully")

            # Status checking phase
            for status_check in range(1, status_checks_per_retry + 1):
                logger.info(f"Status check {status_check}/{status_checks_per_retry} for operation '{operation}'")

                response = await self._make_request(
                    method="POST", endpoint="/api/oob/ipmi", json=status_payload, timeout=self.timeout
                )

                if response:
                    json_response = response.json()
                    logger.info(f"Status response: {json_response}")

                    # Check if desired state is achieved
                    response_text = json_response.get("response", "").lower()
                    if operation in response_text or (operation == "soft" and "off" in response_text):
                        logger.info(
                            f"Machine successfully powered {operation} after attempt {attempt}, status check {status_check}"
                        )
                        return True

                # If not the last status check, wait before next check
                if status_check < status_checks_per_retry:
                    logger.info(f"Waiting {status_check_interval} seconds before next status check")
                    await asyncio.sleep(status_check_interval)

            # If we get here, all status checks failed for this attempt
            if attempt < max_operation_retries:
                logger.warning(f"Status checks failed for attempt {attempt}, will retry operation '{operation}'")
            else:
                logger.error(f"All {max_operation_retries} attempts failed for operation '{operation}'")

                # Special handling for soft reboot - don't fail completely
                if operation == "soft":
                    logger.warning("Soft reboot attempts completed, moving on")
                    return True
                else:
                    raise Exception(
                        f"IPMI operation '{operation}' failed after {max_operation_retries} attempts with {status_checks_per_retry} status checks each"
                    )

        return False

    async def activate_sol(self) -> bool:
        """
        Activate Serial Over LAN (SOL) console.

        Returns:
            bool: True if SOL activated successfully
        """
        payload = {
            "mac_address": self.mac_address,
            "username": self.bmc_user,
            "password": self.bmc_pass,
            "job_id": self.job_id or "",
        }

        response = await self._make_request(
            method="POST",
            endpoint="/api/oob/sol",
            json=payload,
            timeout=548400,  # Long timeout for SOL session
        )

        if response:
            json_response = response.json()
            logger.info(f"SOL response: {json_response}")

            if response.status_code == 202:
                logger.info("SOL activated")
                return True

        logger.error("SOL activation failed")
        return False

    # Convenience methods for common operations
    async def power_on(self) -> bool:
        """Power on the server."""
        return await self.perform_ipmi_operation("on")

    async def power_off(self) -> bool:
        """Power off the server."""
        return await self.perform_ipmi_operation("off")

    async def power_cycle(self) -> bool:
        """Power cycle the server."""
        return await self.perform_ipmi_operation("reset")

    async def soft_reboot(self) -> bool:
        """Perform a soft reboot."""
        return await self.perform_ipmi_operation("soft")

    async def cold_reset(self) -> bool:
        """Perform a cold reset (BMC reset)."""
        return await self.perform_ipmi_operation("cold")

    async def get_power_status(self) -> dict[str, Any]:
        """
        Get the current power status.

        Returns:
            Dict containing power status information
        """
        response = await self._make_request(
            method="POST",
            endpoint="/api/oob/ipmi",
            json={
                "mac_address": self.mac_address,
                "username": self.bmc_user,
                "password": self.bmc_pass,
                "port": self.bmc_port,
                "operation": "status",
                "job_id": self.job_id or "",
            },
            timeout=self.timeout,
        )

        if response and response.status_code == 200:
            return response.json()

        return {"status": "unknown", "error": "Failed to get power status"}
