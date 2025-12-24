import base64
import json
import logging
import os
import urllib.parse
from typing import Any

import requests

logger = logging.getLogger(__name__)
"""
NetBox Document and Interface Utilities
Handles document uploads and interface type mapping for NetBox
"""


def get_device_doc(device_id: int, doc_name: str) -> dict[str, Any]:
    """
    Retrieve a document from NetBox for a specific device

    Args:
        device_id: NetBox device ID
        doc_name: Name of the document to retrieve

    Returns:
        dict: API response with count and results
    """
    try:
        netbox_url = os.environ.get("NETBOX_URL", "").rstrip("/")
        netbox_token = os.environ.get("NETBOX_TOKEN", "")

        if not netbox_url or not netbox_token:
            logger.error("NETBOX_URL and NETBOX_TOKEN environment variables are required")
            return {"count": 0}

        url = f"{netbox_url}/api/plugins/documents/device-documents"
        params = {}
        if doc_name:
            params["name"] = doc_name
        if device_id:
            params["device"] = device_id
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}/?{query_string}"

        headers = {"Authorization": f"Token {netbox_token}", "Content-Type": "application/json"}
        response = requests.get(url, headers=headers)
        results = response.json() if response.status_code == 200 else {"count": 0}

        if "detail" in results:
            logger.warning(results["detail"])

        return results

    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        raise


def upload_device_doc(
    device_id: int, doc_name: str, doc_content: dict[str, Any], doc_type: str = "other"
) -> dict[str, Any]:
    """
    Upload a document to NetBox for a specific device

    Args:
        device_id: NetBox device ID
        doc_name: Name of the document (e.g., "discovery.json")
        doc_content: Document content as dictionary
        doc_type: Document type (default: "other")

    Returns:
        dict: API response
    """
    try:
        netbox_url = os.environ.get("NETBOX_URL", "").rstrip("/")
        netbox_token = os.environ.get("NETBOX_TOKEN", "")

        if not netbox_url or not netbox_token:
            logger.error("NETBOX_URL and NETBOX_TOKEN environment variables are required")
            return {}

        # Check if document already exists
        results = get_device_doc(device_id=device_id, doc_name=doc_name)

        # Encode document content to base64
        json_string_pretty = json.dumps(doc_content, indent=4)
        string_bytes = json_string_pretty.encode("ascii")
        base64_bytes = base64.b64encode(string_bytes)
        base64_string = base64_bytes.decode("ascii")

        # Create payload
        payload = {
            "name": doc_name,
            "document": base64_string,
            "document_type": doc_type,
            "device": device_id,
        }

        # Set base URL
        url = f"{netbox_url}/api/plugins/documents/device-documents/"
        headers = {"Authorization": f"Token {netbox_token}", "Content-Type": "application/json"}

        response = None

        # Update existing documents
        if results["count"] == 1:
            logger.info(f"Updating device {device_id} document: {doc_name}")
            doc_id = results["results"][0]["id"]
            url = f"{url}{doc_id}/"
            response = requests.patch(url, headers=headers, json=payload)

        # Create new documents
        elif results["count"] == 0:
            logger.info(f"Creating device {device_id} document: {doc_name}")
            response = requests.post(url, headers=headers, json=payload)
        else:
            logger.error(f"Unexpected document count ({results['count']}) for device {device_id} document: {doc_name}")
            raise ValueError(f"Expected 0 or 1 documents, found {results['count']}")

        if response is None:
            raise ValueError("No response received from document operation")

        return response.json()

    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise
