#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Base classes for GCP resource collection.

This module provides the BaseCollector class that all GCP resource collectors
inherit from. It follows the pattern established by the AWS integration.
"""

import logging
import re
from typing import Any, Callable, Dict, Iterator, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from google.cloud import asset_v1  # noqa: F401

logger = logging.getLogger("regscale")


class BaseCollector:
    """Base class for GCP resource collectors with universal filtering support.

    This class provides common functionality for GCP resource collection including:
    - Parent resource path parsing (organizations/folders/projects)
    - Label-based resource filtering
    - Project-based resource filtering
    - Error handling for GCP API errors
    - Pagination helpers

    Attributes:
        parent: GCP parent resource path (e.g., 'projects/my-proj', 'organizations/123').
        credentials_path: Optional path to service account JSON key file.
        project_id: Optional project ID for filtering resources.
        labels: Dictionary of label key-value pairs for filtering resources.
        supported_asset_types: Class attribute listing supported GCP asset types.
    """

    # Supported asset types for this collector - subclasses should override
    supported_asset_types: List[str] = []

    def __init__(
        self,
        parent: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize the base collector with filtering support.

        :param str parent: GCP parent resource path (e.g., 'projects/my-proj',
                          'organizations/123456', 'folders/987654')
        :param Optional[str] credentials_path: Path to service account JSON key file
        :param Optional[str] project_id: GCP project ID for filtering resources
        :param Optional[Dict[str, str]] labels: Dictionary of label key-value pairs
                                                for filtering resources (AND logic)
        """
        self.parent = parent
        self.credentials_path = credentials_path
        self.project_id = project_id
        self.labels = labels or {}

    def _get_client(self, service_name: str) -> Any:
        """Get a GCP client for the specified service.

        This is a placeholder that subclasses can override for specific services.
        For most GCP services, clients are created differently than boto3.

        :param str service_name: Name of the GCP service
        :return: GCP client for the service
        :rtype: Any
        :raises NotImplementedError: If service client creation is not implemented
        """
        raise NotImplementedError(f"Client creation for {service_name} must be implemented in subclass")

    def _get_scope_type(self) -> str:
        """Get the scope type from the parent resource path.

        :return: Scope type ('project', 'organization', or 'folder')
        :rtype: str
        """
        if self.parent.startswith("projects/"):
            return "project"
        elif self.parent.startswith("organizations/"):
            return "organization"
        elif self.parent.startswith("folders/"):
            return "folder"
        return "unknown"

    def _get_scope_id(self) -> str:
        """Get the scope ID from the parent resource path.

        :return: Scope ID (project ID, organization ID, or folder ID)
        :rtype: str
        """
        if "/" in self.parent:
            return self.parent.split("/", 1)[1]
        return self.parent

    def _matches_labels(self, resource_labels: Optional[Dict[str, str]]) -> bool:
        """Check if all filter labels match resource labels (AND logic).

        :param Optional[Dict[str, str]] resource_labels: Labels from the resource
        :return: True if all filter labels match (or no filter), False otherwise
        :rtype: bool
        """
        if not self.labels:
            return True  # No filter, include all

        if not resource_labels:
            return False  # Filter set but resource has no labels

        # All filter labels must match (AND logic)
        for key, value in self.labels.items():
            if resource_labels.get(key) != value:
                logger.debug(
                    "Resource does not match label filter: expected %s=%s, got %s",
                    key,
                    value,
                    resource_labels.get(key),
                )
                return False

        return True

    def _matches_project(self, resource_name: str) -> bool:
        """Check if resource belongs to target project.

        GCP resource names follow the format:
        //service.googleapis.com/projects/PROJECT_ID/...

        :param str resource_name: GCP resource name (full resource path)
        :return: True if resource matches project filter or no filter specified
        :rtype: bool
        """
        if not self.project_id:
            return True  # No filter, include all

        # Extract project from resource name
        # Format: //compute.googleapis.com/projects/my-project/instances/vm1
        pattern = r"projects/([^/]+)"
        match = re.search(pattern, resource_name)

        if match:
            resource_project = match.group(1)
            matches = resource_project == self.project_id
            if not matches:
                logger.debug(
                    "Filtering out resource %s - project %s != %s",
                    resource_name,
                    resource_project,
                    self.project_id,
                )
            return matches

        # Could not extract project, include by default
        return True

    def _handle_error(self, error: Exception, resource_type: str) -> None:
        """Handle and log GCP API errors.

        :param Exception error: The error that occurred
        :param str resource_type: Type of resource being collected
        """
        # Import GCP exceptions lazily to avoid import errors when GCP SDK not installed
        try:
            from google.api_core.exceptions import PermissionDenied, NotFound

            if isinstance(error, PermissionDenied):
                logger.warning(
                    "Access denied to %s for parent %s: %s",
                    resource_type,
                    self.parent,
                    str(error),
                )
            elif isinstance(error, NotFound):
                logger.warning(
                    "Resource not found for %s in parent %s: %s",
                    resource_type,
                    self.parent,
                    str(error),
                )
            else:
                logger.error(
                    "Error collecting %s in parent %s: %s",
                    resource_type,
                    self.parent,
                    str(error),
                )
                logger.debug(error, exc_info=True)
        except ImportError:
            # GCP SDK not installed, just log the error
            logger.error(
                "Error collecting %s in parent %s: %s",
                resource_type,
                self.parent,
                str(error),
            )
            logger.debug(error, exc_info=True)

    def _paginate(
        self,
        method: Callable,
        items_key: str,
        page_token_key: str = "page_token",
        **kwargs: Any,
    ) -> Iterator[Any]:
        """Generic pagination helper for GCP API calls.

        Handles pagination for GCP APIs that use page tokens.

        :param Callable method: The API method to call
        :param str items_key: Key in response containing items
        :param str page_token_key: Key for page token parameter
        :param kwargs: Additional arguments to pass to the method
        :yield: Items from each page
        :rtype: Iterator[Any]
        """
        page_token = None

        while True:
            if page_token:
                kwargs[page_token_key] = page_token

            response = method(**kwargs)
            items = self._extract_items_from_response(response, items_key)

            for item in items:
                yield item

            page_token = self._extract_page_token(response)
            if not page_token:
                break

    def _extract_items_from_response(self, response: Any, items_key: str) -> List[Any]:
        """Extract items from a paginated response.

        :param Any response: The API response object
        :param str items_key: Key in response containing items
        :return: List of items from the response
        :rtype: List[Any]
        """
        if hasattr(response, items_key):
            return getattr(response, items_key)
        if isinstance(response, dict):
            return response.get(items_key, [])
        return []

    def _extract_page_token(self, response: Any) -> Optional[str]:
        """Extract the next page token from a paginated response.

        :param Any response: The API response object
        :return: The next page token if available, None otherwise
        :rtype: Optional[str]
        """
        if hasattr(response, "next_page_token"):
            return response.next_page_token
        if isinstance(response, dict):
            return response.get("nextPageToken") or response.get("next_page_token")
        return None

    def collect(self) -> Dict[str, Any]:
        """Collect resources. Must be implemented by subclasses.

        :return: Dictionary containing resource information
        :rtype: Dict[str, Any]
        :raises NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement collect()")
