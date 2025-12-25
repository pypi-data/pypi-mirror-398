#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Authentication, Session Management, and Client Factories.

This module provides:
- Session caching for GCP credentials
- Credential management (file-based and JSON content)
- Client factories for GCP APIs
- Scope resolution for organization/folder/project scanning
"""

import atexit
import base64
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional, Tuple

from regscale.core.app.utils.app_utils import error_and_exit
from regscale.integrations.commercial.gcp.variables import (
    GcpVariables,
    GCP_DEFAULT_CACHE_TTL_HOURS,
)

if TYPE_CHECKING:
    from google.cloud import asset_v1
    from google.cloud import securitycenter

logger = logging.getLogger("regscale")

# Track temp files for cleanup
_temp_credentials_files: list = []


class GCPSessionManager:
    """Manages GCP session credentials with local caching and automatic expiration.

    This class provides session caching for GCP service account credentials,
    following the pattern established by AWS session management.

    Attributes:
        cache_dir: Path to the directory where session files are cached.
    """

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        """Initialize the GCP session manager.

        :param Optional[str] cache_dir: Directory to store cached session data.
                                       Defaults to ~/.regscale/gcp_sessions/
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".regscale" / "gcp_sessions"

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions on the cache directory (owner read/write only)
        if os.name != "nt":  # Unix-like systems
            try:
                os.chmod(self.cache_dir, 0o700)
            except OSError:
                logger.debug("Could not set restrictive permissions on cache directory")

    def cache_session(
        self,
        session_name: str,
        credentials_path: str,
        project_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> None:
        """Cache session credentials to local file.

        :param str session_name: Name for this session (e.g., profile name or custom name)
        :param str credentials_path: Path to the service account JSON key file
        :param Optional[str] project_id: GCP project ID
        :param Optional[str] organization_id: GCP organization ID
        :param Optional[str] folder_id: GCP folder ID
        """
        cache_file = self.cache_dir / f"{session_name}.json"

        cache_data = {
            "session_name": session_name,
            "credentials_path": credentials_path,
            "project_id": project_id,
            "organization_id": organization_id,
            "folder_id": folder_id,
            "cached_at": datetime.now().isoformat(),
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

        # Set restrictive permissions on the cache file
        if os.name != "nt":
            try:
                os.chmod(cache_file, 0o600)
            except OSError:
                logger.debug("Could not set restrictive permissions on cache file")

        logger.debug(f"Cached GCP session: {session_name}")

    def get_cached_session(self, session_name: str) -> Optional[Dict[str, str]]:
        """Retrieve cached session credentials.

        :param str session_name: Name of the session to retrieve
        :return: Session data dictionary or None if not found
        :rtype: Optional[Dict[str, str]]
        """
        cache_file = self.cache_dir / f"{session_name}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read cached session {session_name}: {e}")
            return None

    def is_session_valid(
        self,
        session_name: str,
        ttl_hours: int = GCP_DEFAULT_CACHE_TTL_HOURS,
    ) -> bool:
        """Check if a cached session is still valid based on TTL.

        :param str session_name: Name of the session to check
        :param int ttl_hours: Time-to-live in hours (default from config)
        :return: True if session exists and is within TTL, False otherwise
        :rtype: bool
        """
        cached = self.get_cached_session(session_name)
        if cached is None:
            return False

        cached_at_str = cached.get("cached_at")
        if not cached_at_str:
            return False

        try:
            cached_at = datetime.fromisoformat(cached_at_str)
            expiration = cached_at + timedelta(hours=ttl_hours)
            return datetime.now() < expiration
        except (ValueError, TypeError):
            return False

    def clear_session(self, session_name: str) -> None:
        """Clear a cached session.

        :param str session_name: Name of the session to clear
        """
        cache_file = self.cache_dir / f"{session_name}.json"
        if cache_file.exists():
            cache_file.unlink()
            logger.debug(f"Cleared GCP session: {session_name}")


def _cleanup_temp_credentials() -> None:
    """Clean up temporary credentials files created during this session.

    This function is registered with atexit to ensure temp files are removed
    when the process exits.

    :rtype: None
    """
    for temp_file in _temp_credentials_files:
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                logger.debug("Cleaned up temporary credentials file: %s", temp_file)
        except OSError as e:
            logger.warning("Failed to clean up temporary credentials file %s: %s", temp_file, e)


# Register cleanup function
atexit.register(_cleanup_temp_credentials)


def decode_base64_credentials(base64_credentials: str) -> str:
    """Decode base64-encoded credentials JSON.

    :param str base64_credentials: Base64-encoded JSON string
    :return: Decoded JSON string
    :rtype: str
    :raises ValueError: If decoding fails
    """
    try:
        decoded_bytes = base64.b64decode(base64_credentials)
        return decoded_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decode base64 credentials: {e}")


def setup_credentials_from_json(credentials_json: str, is_base64: bool = False) -> str:
    """Write credentials JSON content to a temporary file and set environment variable.

    This function allows passing GCP service account credentials as JSON content
    (string or dict) instead of a file path. This is useful for:
    - Airflow DAGs where secrets are passed as parameters
    - Environments where file mounting is not available
    - Testing and CI/CD pipelines

    The temporary file is automatically cleaned up when the process exits.

    :param str credentials_json: JSON string, dict, or base64-encoded JSON containing service account credentials
    :param bool is_base64: If True, credentials_json is base64-encoded and will be decoded first
    :return: Path to the temporary credentials file
    :rtype: str
    :raises ValueError: If credentials_json is empty or invalid
    """
    if not credentials_json:
        raise ValueError("credentials_json cannot be empty")

    # Decode base64 if specified
    if is_base64:
        credentials_json = decode_base64_credentials(credentials_json)

    # Parse JSON if it's a string
    if isinstance(credentials_json, str):
        try:
            credentials_dict = json.loads(credentials_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in credentials_json: {e}")
    elif isinstance(credentials_json, dict):
        credentials_dict = credentials_json
    else:
        raise ValueError("credentials_json must be a JSON string or dictionary")

    # Validate required fields
    required_fields = ["type", "project_id", "private_key", "client_email"]
    missing_fields = [f for f in required_fields if f not in credentials_dict]
    if missing_fields:
        raise ValueError(f"credentials_json missing required fields: {missing_fields}")

    # Create temp file with secure permissions
    fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="gcp_creds_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(credentials_dict, f)

        # Set restrictive permissions (owner read/write only)
        if os.name != "nt":
            os.chmod(temp_path, 0o600)

        # Track for cleanup
        _temp_credentials_files.append(temp_path)

        # Set environment variable
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
        logger.info("Set up GCP credentials from JSON content (temp file: %s)", temp_path)

        return temp_path
    except Exception:
        # Clean up on error
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def ensure_gcp_credentials(credentials_json: Optional[str] = None, is_base64: bool = False) -> None:
    """Ensure that the GCP credentials are set in the environment.

    Sets GOOGLE_APPLICATION_CREDENTIALS environment variable. Credentials can be
    provided in multiple ways (in order of precedence):
    1. credentials_json parameter (JSON content as string, optionally base64-encoded)
    2. gcpCredentialsJsonBase64 from init.yaml configuration (base64-encoded JSON)
    3. gcpCredentialsJson from init.yaml configuration (raw JSON content)
    4. Existing GOOGLE_APPLICATION_CREDENTIALS environment variable
    5. gcpCredentials from init.yaml configuration (file path)

    :param Optional[str] credentials_json: JSON string containing service account credentials.
                                          If provided, writes to temp file and sets env var.
    :param bool is_base64: If True, credentials_json parameter is base64-encoded.
    :rtype: None
    """
    # If credentials JSON is provided as parameter, use it
    if credentials_json:
        setup_credentials_from_json(credentials_json, is_base64=is_base64)
        return

    # Check if GOOGLE_APPLICATION_CREDENTIALS is already set
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return

    # Check for gcpCredentialsJsonBase64 in init.yaml (base64-encoded JSON - recommended)
    try:
        config_json_b64 = GcpVariables.gcpCredentialsJsonBase64
        if config_json_b64 and config_json_b64.strip():
            logger.info("Using gcpCredentialsJsonBase64 from init.yaml")
            setup_credentials_from_json(config_json_b64, is_base64=True)
            return
    except (ValueError, AttributeError):
        # gcpCredentialsJsonBase64 not set or empty, continue
        pass

    # Check for gcpCredentialsJson in init.yaml (raw JSON content)
    try:
        config_json = GcpVariables.gcpCredentialsJson
        if config_json and config_json.strip():
            logger.info("Using gcpCredentialsJson from init.yaml")
            setup_credentials_from_json(config_json)
            return
    except (ValueError, AttributeError):
        # gcpCredentialsJson not set or empty, continue to file path
        pass

    # Fall back to gcpCredentials file path from init.yaml
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(GcpVariables.gcpCredentials)


def ensure_gcp_api_enabled(service_name: str) -> None:
    """Ensure that a GCP API is enabled.

    Checks if the specified API is enabled and raises an exception if it is not.

    :param str service_name: The name of the service to check (e.g., 'securitycenter.googleapis.com')
    :raises RuntimeError: If the API is not enabled or any other error occurs
    :rtype: None
    """
    from google.auth.exceptions import GoogleAuthError
    from googleapiclient.discovery import build

    ensure_gcp_credentials()
    project_id = GcpVariables.gcpProjectId

    try:
        service = build("serviceusage", "v1")
        request = service.services().get(name=f"projects/{project_id}/services/{service_name}")
        response = request.execute()

        if response and response.get("state") == "ENABLED":
            logger.info(f"{service_name} API is enabled for project {project_id}.")
        else:
            error_and_exit(
                f"{service_name} API is not enabled for project {project_id}. Please enable it.\n"
                f"Run the following command:\n"
                f"gcloud services enable {service_name} --project {project_id}"
            )
    except GoogleAuthError as e:
        raise RuntimeError(f"Authentication error: {e}")
    except Exception as e:
        raise RuntimeError(f"An error occurred checking API status: {e}")


def get_gcp_parent() -> str:
    """Get the GCP parent resource path based on configured scan type.

    Returns the appropriate parent path for organization, folder, or project
    level scanning based on gcpScanType configuration.

    :return: GCP parent resource path (e.g., 'organizations/123', 'folders/456', 'projects/my-proj')
    :rtype: str
    """
    scan_type = str(GcpVariables.gcpScanType).lower()

    if scan_type == "organization":
        return f"organizations/{GcpVariables.gcpOrganizationId}"
    elif scan_type == "folder":
        return f"folders/{GcpVariables.gcpFolderId}"
    else:  # Default to project
        return f"projects/{GcpVariables.gcpProjectId}"


def get_gcp_security_center_client() -> "securitycenter.SecurityCenterClient":
    """Get an authenticated GCP Security Center client.

    :return: Authenticated SecurityCenterClient instance
    :rtype: securitycenter.SecurityCenterClient
    """
    from google.cloud import securitycenter

    ensure_gcp_api_enabled("securitycenter.googleapis.com")
    return securitycenter.SecurityCenterClient()


def get_gcp_asset_service_client() -> "asset_v1.AssetServiceClient":
    """Get an authenticated GCP Asset Service client.

    :return: Authenticated AssetServiceClient instance
    :rtype: asset_v1.AssetServiceClient
    """
    from google.cloud import asset_v1

    ensure_gcp_api_enabled("cloudasset.googleapis.com")
    return asset_v1.AssetServiceClient()


def _test_gcp_connection() -> Tuple[bool, str]:
    """Test the GCP connection by validating credentials.

    Uses google.oauth2.service_account to load credentials from the service account
    JSON key file specified in GOOGLE_APPLICATION_CREDENTIALS.

    :return: Tuple of (success: bool, message: str)
    :rtype: Tuple[bool, str]
    """
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        # Get the credentials file path from environment
        credentials_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_file:
            return False, "GOOGLE_APPLICATION_CREDENTIALS environment variable not set"

        # Define scopes needed for Security Command Center and Cloud Asset APIs
        scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/cloud-platform.read-only",
        ]

        # Load credentials from service account file with scopes
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=scopes,
        )

        # Refresh credentials to validate they work
        credentials.refresh(Request())

        # Get project from credentials if available
        project = getattr(credentials, "project_id", None)
        project_info = f" (project: {project})" if project else ""
        return True, f"Successfully authenticated with GCP{project_info}"
    except FileNotFoundError as e:
        return False, f"Credentials file not found: {e}"
    except ValueError as e:
        return False, f"Invalid credentials file format: {e}"
    except Exception as e:
        return False, f"Failed to connect to GCP: {e}"


def authenticate(credentials_path: Optional[str] = None) -> Tuple[bool, str]:
    """Test GCP authentication and return status.

    Verifies that credentials are valid and can connect to GCP APIs.

    :param Optional[str] credentials_path: Path to service account JSON key file.
                                          If not provided, uses GcpVariables.gcpCredentials.
    :return: Tuple of (success: bool, message: str)
    :rtype: Tuple[bool, str]
    """
    # Use provided path or fall back to config
    if credentials_path is None:
        credentials_path = str(GcpVariables.gcpCredentials)

    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        return False, f"Credentials file not found: {credentials_path}"

    try:
        # Set the environment variable for Google libraries
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        return _test_gcp_connection()
    except Exception as e:
        return False, f"Authentication failed: {e}"
