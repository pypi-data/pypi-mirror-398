#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QRadar API Client for RegScale Integration

This module provides a Python client for interacting with IBM QRadar SIEM via REST API.
It implements the Ariel Query Language (AQL) API pattern for querying events.

Based on client's Script for API.txt workflow:
1. POST to /api/ariel/searches with URL-encoded AQL query
2. Poll GET /api/ariel/searches/{search_id} until status = "COMPLETED"
3. GET /api/ariel/searches/{search_id}/results to retrieve CSV/JSON results

QRadar API Documentation: https://www.ibm.com/docs/en/qradar-common?topic=api-restful-overview
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("regscale")


class QRadarAPIException(Exception):
    """Exception raised for QRadar API errors."""

    pass


class QRadarAPIClient:
    """
    Python client for IBM QRadar SIEM REST API.

    Handles authentication, query execution, and result retrieval from QRadar.
    Uses the Ariel Query Language (AQL) API for searching events.

    Example usage:
        >>> client = QRadarAPIClient(
        ...     base_url="https://qradar.example.com",
        ...     api_key="your-api-key-here"
        ... )
        >>> events = client.get_events(
        ...     start_time="2025-01-01 00:00:00",
        ...     end_time="2025-01-01 23:59:59"
        ... )
    """

    # API version supported by QRadar CE 7.5.0
    API_VERSION = "19.0"

    # Default timeout for queries (15 minutes) - increased to handle large datasets
    # Customer queries can take 5-10 minutes on production QRadar instances
    DEFAULT_QUERY_TIMEOUT = 900

    # Poll interval for checking query status (seconds)
    POLL_INTERVAL = 5

    # Error message constants
    _UNEXPECTED_RESPONSE_TYPE_MSG = "Unexpected response type: {}"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        verify_ssl: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
        api_version: Optional[str] = None,
    ):
        """
        Initialize QRadar API client.

        Args:
            base_url: QRadar instance base URL (e.g., "https://qradar.example.com")
            api_key: QRadar API key (SEC token)
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            api_version: QRadar API version (defaults to 19.0 if not specified)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.qradar_api_version = api_version or self.API_VERSION

        # Create session with retry capability
        self.session = self._create_session(max_retries)

        # Set default headers
        self.session.headers.update(
            {
                "SEC": self.api_key,
                "Version": self.qradar_api_version,
                "Accept": "application/json",
            }
        )

        logger.info("QRadar API client initialized for %s (API version: %s)", self.base_url, self.qradar_api_version)

    def _create_session(self, max_retries: int) -> requests.Session:
        """
        Create a requests session with retry capability.

        Args:
            max_retries: Maximum number of retry attempts

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure retry strategy for transient errors
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)  # Support both HTTP and HTTPS

        if not self.verify_ssl:
            # Disable SSL warnings if verification is disabled
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning("SSL verification is disabled - not recommended for production")

        return session

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict[str, Any], str]:
        """
        Make an HTTP request to the QRadar API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            headers: Additional headers (overrides session headers)

        Returns:
            Response data (JSON dict or text)

        Raises:
            QRadarAPIException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"

        # Merge additional headers with session headers
        request_headers = dict(self.session.headers)
        if headers:
            request_headers.update(headers)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Return JSON if content-type is JSON, otherwise return text
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return response.json()
            else:
                return response.text

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error("QRadar API request failed: %s", error_msg)
            raise QRadarAPIException(error_msg) from e

        except requests.exceptions.RequestException as e:
            logger.error("QRadar API request failed: %s", str(e))
            raise QRadarAPIException(f"Request failed: {e!s}") from e

    def _url_encode_query(self, aql_query: str) -> str:
        """
        URL encode an AQL query string.

        Args:
            aql_query: Ariel Query Language query string

        Returns:
            URL-encoded query string
        """
        return quote(aql_query, safe="")

    def execute_aql_query(
        self,
        aql_query: str,
        query_timeout: int = DEFAULT_QUERY_TIMEOUT,
        return_format: str = "json",
    ) -> List[Dict[str, Any]]:
        """
        Execute an Ariel Query Language (AQL) query and return results.

        This method implements the QRadar API workflow:
        1. POST to /api/ariel/searches to initiate search
        2. Poll GET /api/ariel/searches/{id} until status = "COMPLETED"
        3. GET /api/ariel/searches/{id}/results to retrieve results

        Args:
            aql_query: AQL query string (e.g., "SELECT * FROM events LAST 24 HOURS")
            query_timeout: Maximum time to wait for query completion (seconds)
            return_format: Result format ("json" or "csv")

        Returns:
            List of result records as dictionaries

        Raises:
            QRadarAPIException: If query execution fails or times out

        Example:
            >>> client.execute_aql_query(
            ...     "SELECT sourceip, destinationip FROM events LAST 1 HOURS",
            ...     query_timeout=300
            ... )
        """
        logger.debug("Executing AQL query: %s...", aql_query[:100])

        # Step 1: Initiate the search
        search_id = self._initiate_search(aql_query)
        logger.info("Search initiated with ID: %s", search_id)

        # Step 2: Poll for completion
        start_time = time.time()
        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > query_timeout:
                raise QRadarAPIException(f"Query timed out after {query_timeout} seconds (search_id: {search_id})")

            # Check status
            status_response = self._get_search_status(search_id)
            status = status_response.get("status")
            progress = status_response.get("progress", 0)

            logger.debug("Search %s status: %s (%s%% complete)", search_id, status, progress)

            if status == "COMPLETED":
                logger.info("Search %s completed successfully", search_id)
                break
            elif status == "ERROR":
                error_messages = status_response.get("error_messages", [])
                error_msg = "; ".join(error_messages) if error_messages else "Unknown error"
                raise QRadarAPIException("Search failed: %s" % error_msg)
            elif status == "CANCELED":
                raise QRadarAPIException("Search was canceled")

            # Wait before next poll
            time.sleep(self.POLL_INTERVAL)

        # Step 3: Retrieve results
        results = self._get_search_results(search_id, return_format)
        logger.info("Retrieved %s results from search %s", len(results), search_id)

        return results

    def _initiate_search(self, aql_query: str) -> str:
        """
        Initiate an AQL search.

        Args:
            aql_query: AQL query string

        Returns:
            Search ID

        Raises:
            QRadarAPIException: If search initiation fails
        """
        encoded_query = self._url_encode_query(aql_query)
        endpoint = f"/api/ariel/searches?query_expression={encoded_query}"

        response = self._make_request("POST", endpoint)

        if not isinstance(response, dict):
            raise QRadarAPIException(self._UNEXPECTED_RESPONSE_TYPE_MSG.format(type(response).__name__))

        search_id = response.get("search_id")
        if not search_id:
            raise QRadarAPIException("No search_id in response")

        return search_id

    def _get_search_status(self, search_id: str) -> Dict[str, Any]:
        """
        Get the status of a search.

        Args:
            search_id: Search ID

        Returns:
            Status response dict

        Raises:
            QRadarAPIException: If status check fails
        """
        endpoint = f"/api/ariel/searches/{search_id}"
        response = self._make_request("GET", endpoint)

        if not isinstance(response, dict):
            raise QRadarAPIException(self._UNEXPECTED_RESPONSE_TYPE_MSG.format(type(response).__name__))

        return response

    def _get_search_results(
        self,
        search_id: str,
        return_format: str = "json",
    ) -> List[Dict[str, Any]]:
        """
        Get results from a completed search.

        Args:
            search_id: Search ID
            return_format: Result format ("json" or "csv")

        Returns:
            List of result records

        Raises:
            QRadarAPIException: If result retrieval fails
        """
        endpoint = f"/api/ariel/searches/{search_id}/results"

        if return_format.lower() == "csv":
            headers = {"Accept": "application/csv"}
            response = self._make_request("GET", endpoint, headers=headers)

            # Parse CSV to list of dicts
            import csv
            import io

            if not isinstance(response, str):
                raise QRadarAPIException("Expected CSV string response, got %s" % type(response))

            csv_reader = csv.DictReader(io.StringIO(response))
            return list(csv_reader)
        else:
            # JSON format
            response = self._make_request("GET", endpoint)

            if not isinstance(response, dict):
                raise QRadarAPIException(self._UNEXPECTED_RESPONSE_TYPE_MSG.format(type(response).__name__))

            # QRadar returns results in "events" key for event queries
            results = response.get("events", [])
            return results

    def get_events(
        self,
        start_time: str,
        end_time: str,
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Fetch events from QRadar within a time range.

        Args:
            start_time: Start time in format "YYYY-MM-DD HH:MM:SS"
            end_time: End time in format "YYYY-MM-DD HH:MM:SS"
            filters: Optional filters (e.g., {"severity": ">=5", "username": "!=admin"})
            fields: Optional list of fields to retrieve (defaults to all)
            limit: Maximum number of results to return

        Returns:
            List of event records

        Example:
            >>> client.get_events(
            ...     start_time="2025-01-01 00:00:00",
            ...     end_time="2025-01-01 23:59:59",
            ...     filters={"severity": ">=5"},
            ...     fields=["sourceip", "destinationip", "username"]
            ... )
        """
        # Build SELECT clause
        if fields:
            select_clause = ", ".join(fields)
        else:
            # Default fields matching client requirements - use raw field names for Pydantic model
            select_clause = """
                qid,
                QIDNAME(qid) as qidname,
                logsourceid,
                LOGSOURCENAME(logsourceid) as logsourcename,
                category,
                CATEGORYNAME(category) as categoryname,
                magnitude,
                severity,
                devicetime,
                starttime,
                sourceip,
                sourceport,
                destinationip,
                destinationport,
                username,
                COUNT(*) as eventcount,
                resourceid,
                accountid,
                accountname,
                awsaccesskeyid
            """

        # Build WHERE clause
        where_conditions = []

        # Add time range
        where_conditions.append(f"deviceTime >= '{start_time}'")
        where_conditions.append(f"deviceTime <= '{end_time}'")

        # Add custom filters
        if filters:
            for field, value in filters.items():
                where_conditions.append(f"{field} {value}")

        where_clause = " AND ".join(where_conditions)

        # Build complete query
        aql_query = f"""
            SELECT {select_clause}
            FROM events
            WHERE {where_clause}
            LIMIT {limit}
        """

        return self.execute_aql_query(aql_query)

    def get_log_sources(self) -> List[Dict[str, Any]]:
        """
        Fetch list of log sources from QRadar.

        Returns:
            List of log source records

        Raises:
            QRadarAPIException: If request fails
        """
        endpoint = "/api/config/event_sources/log_source_management/log_sources"
        response = self._make_request("GET", endpoint)

        if not isinstance(response, list):
            raise QRadarAPIException("Unexpected response type: %s" % type(response))

        return response

    def get_saved_search_results(
        self, saved_search_id: int, query_timeout: int = DEFAULT_QUERY_TIMEOUT
    ) -> Dict[str, Any]:
        """
        Fetch results from a saved search by ID.

        This method retrieves the results from a pre-configured saved search in QRadar.
        Saved searches are useful for recurring queries and assessments.

        For production QRadar instances with large datasets, the saved search may take
        several minutes to complete. This method polls until completion or timeout.

        Args:
            saved_search_id: The ID of the saved search to execute
            query_timeout: Maximum time to wait for query completion (seconds, default: 900/15min)

        Returns:
            Dict containing search results with structure:
                {
                    "search_id": str,
                    "status": str,
                    "filtered_events": [{"AWS Account ID (custom)": str, "Count": int}, ...],
                    "processed_record_count": int,
                    ...
                }

        Raises:
            QRadarAPIException: If request fails or times out

        Example:
            >>> client = QRadarAPIClient(...)
            >>> results = client.get_saved_search_results(7042, query_timeout=900)
            >>> for event in results.get("filtered_events", []):
            ...     account_id = event.get("AWS Account ID (custom)")
            ...     count = event.get("Count")
            ...     print(f"Account {account_id}: {count} events")
        """
        endpoint = f"/api/ariel/searches?saved_search_id={saved_search_id}"

        logger.info("Initiating saved search query for ID: %s (timeout: %ds)", saved_search_id, query_timeout)
        response = self._make_request("POST", endpoint)

        if not isinstance(response, dict):
            raise QRadarAPIException(self._UNEXPECTED_RESPONSE_TYPE_MSG.format(type(response).__name__))

        # Validate response structure
        if "search_id" not in response:
            raise QRadarAPIException("No search_id in saved search response")

        search_id = response.get("search_id")
        initial_status = response.get("status", "UNKNOWN")
        logger.info("Search initiated with ID: %s (initial status: %s)", search_id, initial_status)

        # If already completed (mock API or cached result), return immediately
        if initial_status == "COMPLETED":
            logger.info(
                "Saved search %s completed immediately (records: %s)",
                search_id,
                response.get("processed_record_count", 0),
            )
            return response

        # Poll for completion (production QRadar may take 5-10 minutes for large queries)
        start_time = time.time()
        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > query_timeout:
                raise QRadarAPIException(
                    f"Saved search query timed out after {query_timeout} seconds (search_id: {search_id}). "
                    f"Consider increasing query_timeout in init.yaml config."
                )

            # Check status
            status_response = self._get_search_status(search_id)
            status = status_response.get("status")
            progress = status_response.get("progress", 0)

            logger.info(
                "Saved search %s status: %s (%s%% complete, elapsed: %.1fs)",
                search_id,
                status,
                progress,
                elapsed,
            )

            if status == "COMPLETED":
                logger.info(
                    "Saved search %s completed successfully after %.1fs (records: %s)",
                    search_id,
                    elapsed,
                    status_response.get("processed_record_count", 0),
                )
                return status_response
            elif status == "ERROR":
                error_messages = status_response.get("error_messages", [])
                error_msg = "; ".join(error_messages) if error_messages else "Unknown error"
                raise QRadarAPIException(f"Saved search failed: {error_msg}")
            elif status == "CANCELED":
                raise QRadarAPIException("Saved search was canceled")

            # Wait before next poll
            time.sleep(self.POLL_INTERVAL)

    def test_connection(self) -> bool:
        """
        Test the connection to QRadar API.

        Returns:
            True if connection is successful

        Raises:
            QRadarAPIException: If connection test fails
        """
        try:
            # Try to fetch system info as a connection test
            endpoint = "/api/system/about"
            response = self._make_request("GET", endpoint)

            version = "Unknown version"
            if isinstance(response, dict):
                version = response.get("version", "Unknown version")

            logger.info("Successfully connected to QRadar: %s", version)
            return True
        except QRadarAPIException as exc:
            logger.error("Connection test failed: %s", str(exc))
            raise


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Example: Connect to QRadar and fetch events
    # NOTE: Replace with actual QRadar instance details
    client = QRadarAPIClient(
        base_url="https://qradar.example.com",
        api_key="your-api-key-here",
        verify_ssl=False,  # Set to True in production
    )

    # Test connection
    try:
        client.test_connection()
        print("Connection successful!")
    except QRadarAPIException as e:
        print(f"Connection failed: {e}")

    # Fetch recent events
    try:
        events = client.get_events(start_time="2025-01-01 00:00:00", end_time="2025-01-01 23:59:59", limit=10)
        print(f"Retrieved {len(events)} events")
        for event in events[:3]:
            print(json.dumps(event, indent=2))
    except QRadarAPIException as e:
        print(f"Query failed: {e}")
