import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def get_secret(path: str, mount_point: str = "brokkr") -> dict[str, Any] | None:
    """
    Read a secret from Vault KV v2 engine using environment variables

    Args:
        path: The path to the secret within the mount point
        mount_point: The mount path for the KV v2 engine (default: "brokkr")

    Returns:
        dict: The secret data if successful, None if failed

    Environment Variables Required:
        VAULT_ADDR: Vault server address (e.g., https://vault.example.com)
        VAULT_TOKEN: Vault authentication token
    """
    vault_addr = os.environ.get("VAULT_ADDR")
    vault_token = os.environ.get("VAULT_TOKEN")

    if not vault_addr:
        logger.error("VAULT_ADDR environment variable is required")
        return None

    if not vault_token:
        logger.error("VAULT_TOKEN environment variable is required")
        return None

    # Remove trailing slash and build API path
    vault_addr = vault_addr.rstrip("/")
    api_path = f"{mount_point}/data/{path.lstrip('/')}"
    url = f"{vault_addr}/v1/{api_path}"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Vault-Token": vault_token,
        "X-Vault-Request": "true",
    }

    logger.debug(f"Reading secret from {api_path}")

    try:
        # Skip SSL verification for development (can be made configurable)
        verify_ssl = os.environ.get("VAULT_SKIP_VERIFY", "true").lower() != "true"

        async with httpx.AsyncClient(verify=verify_ssl, timeout=30.0) as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 404:
                logger.warning(f"Secret not found at {api_path}")
                return None
            elif response.status_code != 200:
                logger.error(f"Vault request failed with status {response.status_code}: {response.text}")
                return None

            data = response.json()

            # Validate KV v2 response structure
            if "data" not in data or "data" not in data["data"]:
                logger.error(f"Invalid KV v2 response structure for secret at {path}")
                return None

            secret_data = data["data"]["data"]
            logger.info(f"Successfully retrieved secret from {path}")
            return secret_data

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during Vault request: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Vault request: {e}")
        return None


async def set_secret(path: str, secret_data: dict[str, Any], mount_point: str = "brokkr") -> bool:
    """
    Write a secret to Vault KV v2 engine

    Args:
        path: The path where the secret should be stored
        secret_data: Dictionary containing the secret data
        mount_point: The mount path for the KV v2 engine (default: "brokkr")

    Returns:
        bool: True if successful, False if failed
    """
    vault_addr = os.environ.get("VAULT_ADDR")
    vault_token = os.environ.get("VAULT_TOKEN")

    if not vault_addr or not vault_token:
        logger.error("VAULT_ADDR and VAULT_TOKEN environment variables are required")
        return False

    # Remove trailing slash and build API path
    vault_addr = vault_addr.rstrip("/")
    api_path = f"{mount_point}/data/{path.lstrip('/')}"
    url = f"{vault_addr}/v1/{api_path}"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Vault-Token": vault_token,
        "X-Vault-Request": "true",
    }

    payload = {"data": secret_data}

    logger.debug(f"Writing secret to {api_path}")

    try:
        verify_ssl = os.environ.get("VAULT_SKIP_VERIFY", "true").lower() != "true"

        async with httpx.AsyncClient(verify=verify_ssl, timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)

            if response.status_code not in [200, 204]:
                logger.error(f"Vault write failed with status {response.status_code}: {response.text}")
                return False

            logger.info(f"Successfully wrote secret to {path}")
            return True

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during Vault write request: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Vault write request: {e}")
        return False
