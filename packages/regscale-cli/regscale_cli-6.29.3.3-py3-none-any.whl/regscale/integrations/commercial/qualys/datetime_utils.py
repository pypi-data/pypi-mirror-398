"""
Centralized datetime parsing utilities for Qualys integration.

This module provides a single source of truth for parsing datetime values from various Qualys APIs
(VMDR, Total Cloud, WAS, Container Security) into ISO 8601 format expected by RegScale.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("regscale")

# Standard datetime formats used across Qualys APIs
QUALYS_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"  # Target format for RegScale
QUALYS_API_DATETIME_FORMAT = "%m/%d/%Y %H:%M"  # MM/DD/YYYY HH:MM (common in Total Cloud)
QUALYS_CONTAINER_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"  # ISO without Z (Container API)
QUALYS_ISO_WITH_Z = "%Y-%m-%dT%H:%M:%SZ"  # ISO with Z (some APIs)
QUALYS_ISO_NO_Z = "%Y-%m-%dT%H:%M:%S"  # ISO without Z (some APIs)


def parse_qualys_datetime(datetime_str: str, source_format: Optional[str] = None, fallback: str = "") -> str:
    """
    Parse any Qualys datetime format to ISO 8601 format expected by RegScale.

    This function automatically detects the format or uses source_format if provided.
    Handles all common Qualys date formats across VMDR, Total Cloud, WAS, and Container Security APIs.

    Args:
        datetime_str: Datetime string from Qualys API
        source_format: Optional format string to try first (auto-detect if None)
        fallback: Return value on parse error (default: empty string)

    Returns:
        ISO 8601 formatted datetime string (YYYY-MM-DDTHH:MM:SSZ)

    Examples:
        >>> parse_qualys_datetime("12/14/2025 10:09")
        "2025-12-14T10:09:00Z"

        >>> parse_qualys_datetime("2025-12-14T10:09:00")
        "2025-12-14T10:09:00Z"

        >>> parse_qualys_datetime("2025-12-14T10:09:00Z")
        "2025-12-14T10:09:00Z"

        >>> parse_qualys_datetime("invalid", fallback="N/A")
        "N/A"
    """
    if not datetime_str:
        return fallback

    # Try common Qualys formats in order of likelihood
    formats_to_try = [
        QUALYS_API_DATETIME_FORMAT,  # MM/DD/YYYY HH:MM
        QUALYS_CONTAINER_TIMESTAMP_FORMAT,  # YYYY-MM-DDTHH:MM:SS
        QUALYS_ISO_WITH_Z,  # YYYY-MM-DDTHH:MM:SSZ
        "%Y-%m-%d %H:%M:%S",  # YYYY-MM-DD HH:MM:SS
        "%Y-%m-%d",  # YYYY-MM-DD (date only)
    ]

    # If specific format provided, try it first
    if source_format:
        formats_to_try.insert(0, source_format)

    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(datetime_str, fmt)
            # Always return with Z suffix for consistency
            return dt.strftime(QUALYS_DATETIME_FORMAT)
        except ValueError:
            continue

    # If all parsing attempts fail, log warning and return fallback
    logger.warning(
        "Failed to parse datetime '%s' with any known Qualys format, using fallback: %s", datetime_str, fallback
    )
    return fallback or datetime_str


def normalize_qualys_datetime(datetime_str: str) -> str:
    """
    Convert Qualys API datetime format to ISO format expected by RegScale.

    This is a convenience wrapper around parse_qualys_datetime() for backwards compatibility
    with existing code in total_cloud_helpers.py.

    Args:
        datetime_str: Datetime string from Qualys API (e.g., "12/14/2025 10:09")

    Returns:
        ISO format datetime string (e.g., "2025-12-14T10:09:00Z")

    Example:
        >>> normalize_qualys_datetime("12/14/2025 10:09")
        "2025-12-14T10:09:00Z"
    """
    return parse_qualys_datetime(datetime_str, fallback="")


def convert_container_timestamp(timestamp) -> str:
    """
    Convert Qualys Container Security timestamp to RegScale format.

    This is a convenience wrapper around parse_qualys_datetime() for backwards compatibility
    with existing code in __init__.py.

    Handles various timestamp formats from Container Security API:
    - ISO 8601 with Z: "2025-12-14T10:09:00Z"
    - ISO 8601 without Z: "2025-12-14T10:09:00"
    - Unix timestamp (int/float): 1702553340
    - MM/DD/YYYY format: "12/14/2025 10:09"

    Args:
        timestamp: Timestamp from Container Security API (str, int, or float)

    Returns:
        ISO 8601 formatted datetime string, or empty string on error

    Example:
        >>> convert_container_timestamp("2025-12-14T10:09:00")
        "2025-12-14T10:09:00Z"

        >>> convert_container_timestamp(1702553340)
        "2023-12-14T10:09:00Z"
    """
    if not timestamp:
        return ""

    # Handle Unix timestamp (int or float)
    if isinstance(timestamp, (int, float)):
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime(QUALYS_DATETIME_FORMAT)
        except (ValueError, OSError) as e:
            logger.warning("Failed to convert Unix timestamp %s: %s", timestamp, e)
            return ""

    # Handle string timestamps
    if isinstance(timestamp, str):
        return parse_qualys_datetime(timestamp, fallback="")

    logger.warning("Unexpected timestamp type: %s (value: %s)", type(timestamp), timestamp)
    return ""
