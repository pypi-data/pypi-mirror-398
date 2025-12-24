"""
Bridge API communication utilities for Brokkr scripts.

This module provides functions for communicating with the Brokkr bridge API,
including mTLS session management, authentication headers, and data fetching.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BridgeClient:
    """
    Client for communicating with Brokkr bridge API.
    """

    def __init__(self, bridge_url: str = None, enable_mtls: bool = True):
        """
        Initialize bridge client with configuration.

        Args:
            bridge_url: Bridge API URL (overrides environment variable)
            enable_mtls: Enable mTLS (default: True)
        """

        # Use provided values or environment variables with defaults
        self.bridge_url = bridge_url or os.getenv("BRIDGE_URL", "")
        self.enable_mtls = enable_mtls
        self.bridge_api_version_path = "/opt/brokkr/bridge-api-version"

        # Debug bridge URL configuration
        logging.info(f"Bridge client initialized with URL: '{self.bridge_url}'")
        if not self.bridge_url:
            logging.error("Bridge URL is empty! Check BRIDGE_URL environment variable or config.yml")
        elif not self.bridge_url.startswith(("http://", "https://")):
            logging.error(f"Bridge URL '{self.bridge_url}' must start with http:// or https://")

        # SSL Certificate paths
        ssl_dir = Path("/opt/brokkr/ssl")

        if self.enable_mtls:
            self.ssl_cert_file = ssl_dir / "cert.crt"
            self.ssl_key_file = ssl_dir / "key.key"
            self.ssl_ca_file = ssl_dir / "ca.crt"
        else:
            self.ssl_cert_file = None
            self.ssl_key_file = None
            self.ssl_ca_file = None

        # Create SSL session
        self.session = self._create_ssl_session()

    def _create_ssl_session(self) -> requests.Session:
        """
        Create a requests session with proper SSL configuration for mTLS.

        Returns:
            Configured session with SSL settings and retry strategy
        """
        session = requests.Session()

        if self.enable_mtls and all([self.ssl_cert_file, self.ssl_key_file, self.ssl_ca_file]):
            if all(
                cert_file.exists()
                for cert_file in [
                    self.ssl_cert_file,
                    self.ssl_key_file,
                    self.ssl_ca_file,
                ]
            ):
                # Configure mutual TLS
                session.cert = (str(self.ssl_cert_file), str(self.ssl_key_file))
                session.verify = str(self.ssl_ca_file)
            else:
                missing_certs = [
                    cert
                    for cert in [
                        self.ssl_cert_file,
                        self.ssl_key_file,
                        self.ssl_ca_file,
                    ]
                    if not cert.exists()
                ]
                logging.warning(f"mTLS certificates not found: {missing_certs}")

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def fetch_device_info(self, mac_address: str, retry_interval: int = 10) -> dict[str, Any]:
        """
        Fetch device information from the bridge API.

        Args:
            mac_address: MAC address to query
            retry_interval: Time in seconds between retry attempts

        Returns:
            Device information as a dictionary
        """
        if not self.bridge_url:
            raise ValueError(
                "Bridge URL is not configured. Set BRIDGE_URL environment variable or add bridge_url to config.yml"
            )

        url = f"{self.bridge_url}/api/server/device-info?mac={mac_address}"
        logging.info(f"Attempting to fetch device info from: {url}")

        while True:
            try:
                # Get job ID from environment or create timestamp-based ID
                job_id = os.getenv("JOB_ID") or f"discovery-{int(time.time())}"

                headers = {"x-brokkr-job-id": job_id}
                response = self.session.get(url, timeout=30, headers=headers)
                response.raise_for_status()
                device_data = response.json()

                # Device data fetched successfully - no persistent storage needed
                logging.info("Device data fetched successfully")

                return device_data
            except requests.HTTPError as e:
                logging.error(f"HTTP error occurred while fetching data from {url}: {e}")
                logging.error(f"Response status: {e.response.status_code}")
                logging.error(f"Response content: {e.response.text}")
            except requests.RequestException as e:
                logging.error(f"Error occurred while fetching data from {url}: {e}")
                logging.error(f"Error type: {type(e).__name__}")
            except ValueError as e:
                logging.error(f"Invalid JSON received from {url}: {e}")
            except Exception as e:
                logging.error(f"Unexpected error occurred: {e}")
                logging.error(f"Error type: {type(e).__name__}")

            logging.info(f"Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
