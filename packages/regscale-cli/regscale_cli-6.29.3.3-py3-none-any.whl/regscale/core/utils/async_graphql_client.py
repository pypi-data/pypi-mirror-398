#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generic async GraphQL client for concurrent query processing in RegScale CLI."""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

import anyio
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.aiohttp import log as aiohttp_logger

from regscale.core.app.application import Application

logger = logging.getLogger("regscale")


class GraphQLQueryError(Exception):
    """Exception raised when a GraphQL query fails."""

    pass


class GraphQLAuthenticationError(GraphQLQueryError):
    """Exception raised when GraphQL authentication fails."""

    pass


class AsyncRegScaleGraphQLClient:
    """
    Generic async GraphQL client optimized for concurrent RegScale API queries.

    This client can execute multiple GraphQL queries concurrently, significantly
    improving performance when fetching paginated data from RegScale.
    """

    def __init__(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        max_concurrent: int = 5,
        token_refresh_callback: Optional[Callable[[], str]] = None,
    ):
        """
        Initialize the async GraphQL client.

        :param str endpoint: GraphQL endpoint URL
        :param Optional[Dict[str, str]] headers: HTTP headers for requests
        :param float timeout: Request timeout in seconds
        :param int max_concurrent: Maximum concurrent requests
        :param Optional[Callable[[], str]] token_refresh_callback: Callback to refresh auth token
        """
        self.app = Application()
        self.ssl_verify = self.app.config.get("sslVerify", True)
        self.endpoint = endpoint
        # Ensure token is a string for the Authorization header
        token = self.app.config.get("token") or ""
        self.headers = headers or {"Authorization": token}
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.token_refresh_callback = token_refresh_callback
        self._semaphore = anyio.Semaphore(max_concurrent)
        self._ssl_warning_logged = False  # Track if SSL warning has been logged

        # Set logging level for aiohttp transport
        aiohttp_logger.setLevel(logging.CRITICAL)

    def _create_client(self) -> Client:
        """
        Create a new GQL client with transport.

        Each concurrent request needs its own transport and client to avoid
        "Transport is already connected" errors.

        :return: New GQL Client instance
        :rtype: Client
        """

        # Create the transport with authentication headers
        # Note: AIOHTTPTransport uses ssl parameter, not verify_ssl
        import ssl as ssl_module
        from typing import Union

        # Type-safe SSL parameter handling
        ssl_param: Union[ssl_module.SSLContext, bool]
        if not self.ssl_verify:
            # SECURITY WARNING: SSL verification is intentionally disabled
            # This is required for environments with self-signed certificates or corporate proxies
            # where SSL verification cannot be performed. This should only be used when:
            # 1. Working with internal/trusted networks with self-signed certificates
            # 2. Behind corporate proxies that intercept SSL/TLS traffic
            # 3. Development/testing environments
            # DO NOT use in production with untrusted networks
            if not self._ssl_warning_logged:
                logger.warning(
                    "SSL certificate verification is disabled. "
                    "This is insecure and should only be used in controlled environments "
                    "with self-signed certificates or corporate proxies."
                )
                self._ssl_warning_logged = True
            # Create a minimal SSL context without loading default CA bundle
            # This avoids potential issues with OpenSSL 3.x and corporate environments
            ssl_context = ssl_module.SSLContext(ssl_module.PROTOCOL_TLS_CLIENT)  # NOSONAR - Uses TLS 1.2+ by default
            ssl_context.check_hostname = False  # NOSONAR - Intentionally disabled when sslVerify=false is configured
            ssl_context.verify_mode = ssl_module.CERT_NONE  # NOSONAR - Required for self-signed certs/corporate proxies
            logger.debug("Created SSL context with verification disabled for GraphQL client")
            ssl_param = ssl_context
        else:
            # Use default SSL verification
            ssl_param = True

        transport = AIOHTTPTransport(
            url=self.endpoint,
            headers=self.headers,
            timeout=int(self.timeout),
            ssl=ssl_param,
        )

        # Create and return a new GQL client
        return Client(
            transport=transport,
            fetch_schema_from_transport=False,  # Skip schema introspection for performance
        )

    def _is_auth_error(self, error_msg: str) -> bool:
        """
        Check if an error message indicates an authentication issue.

        :param str error_msg: Error message to check
        :return: True if the error is authentication-related
        :rtype: bool
        """
        auth_indicators = ["AUTH_NOT_AUTHENTICATED", "UNAUTHENTICATED", "401", "403"]
        return any(indicator in error_msg for indicator in auth_indicators)

    async def _execute_single_attempt(
        self, query: str, variables: Optional[Dict[str, Any]], progress_callback: Optional[Callable], task_name: str
    ) -> Dict[str, Any]:
        """
        Execute a single query attempt.

        :param str query: GraphQL query string
        :param Optional[Dict[str, Any]] variables: Query variables
        :param Optional[callable] progress_callback: Callback for progress updates
        :param str task_name: Name for progress tracking
        :return: Query response data
        :rtype: Dict[str, Any]
        """
        if progress_callback:
            progress_callback(task_name, "requesting")

        # Parse the query string to a GraphQL document
        doc = gql(query)

        # Create a new client for this request to avoid connection conflicts
        client = self._create_client()

        # Execute the query using the GQL client
        async with client as session:
            result = await session.execute(doc, variable_values=variables or {})

        if progress_callback:
            progress_callback(task_name, "completed")

        return result

    async def execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None,
        task_name: str = "GraphQL Query",
    ) -> Dict[str, Any]:
        """
        Execute a single GraphQL query asynchronously.

        :param str query: GraphQL query string
        :param Optional[Dict[str, Any]] variables: Query variables
        :param Optional[callable] progress_callback: Callback for progress updates
        :param str task_name: Name for progress tracking
        :return: Query response data
        :rtype: Dict[str, Any]
        """
        async with self._semaphore:  # Limit concurrent requests
            if progress_callback:
                progress_callback(task_name, "starting")

            logger.debug("Async GraphQL request to %s", self.endpoint)

            # Try up to 2 times (initial + 1 retry with token refresh)
            max_attempts = 2
            for attempt in range(max_attempts):
                try:
                    result = await self._execute_single_attempt(query, variables, progress_callback, task_name)
                    return result

                except Exception as e:
                    error_msg = str(e)

                    # Check for authentication errors and retry if possible
                    if self._is_auth_error(error_msg):
                        if attempt < max_attempts - 1 and self.token_refresh_callback:
                            logger.warning("Authentication error, refreshing token and retrying")
                            new_token = self.token_refresh_callback()
                            self.headers["Authorization"] = f"Bearer {new_token}"
                            continue

                    # Log and re-raise other errors
                    # Use DEBUG level - errors during paginated queries are often expected (API limits)
                    # and are handled gracefully by the caller
                    error_msg = f"Error in {task_name}: {error_msg}"
                    logger.debug(error_msg)
                    if progress_callback:
                        progress_callback(task_name, "failed")
                    raise GraphQLQueryError(error_msg) from e

            # Should never reach here, but just in case
            raise GraphQLQueryError(f"Failed to execute query after {max_attempts} attempts")

    async def execute_paginated_query_concurrent(
        self,
        query_builder: Callable[[int, int], str],
        topic_key: str,
        total_count: int,
        page_size: int = 50,
        starting_skip: int = 0,
        progress_callback: Optional[Callable] = None,
        task_name: str = "Paginated Query",
    ) -> List[Dict[str, Any]]:
        """
        Execute a paginated GraphQL query with concurrent page fetching.

        :param Callable[[int, int], str] query_builder: Function that builds query with skip and take
        :param str topic_key: Key to extract nodes from response
        :param int total_count: Total number of items expected
        :param int page_size: Items per page (default: 50)
        :param int starting_skip: Starting skip value (default: 0)
        :param Optional[callable] progress_callback: Callback for progress updates
        :param str task_name: Name for progress tracking
        :return: All nodes from all pages
        :rtype: List[Dict[str, Any]]
        """
        # Calculate number of pages needed
        num_pages = (total_count + page_size - 1) // page_size

        logger.debug("Fetching %d pages concurrently for %s", num_pages, task_name)

        # Create tasks for all pages
        tasks = []
        for page_num in range(num_pages):
            skip = starting_skip + (page_num * page_size)
            query = query_builder(skip, page_size)

            page_task_name = f"{task_name} (Page {page_num + 1}/{num_pages})"
            tasks.append(
                self._fetch_single_page(
                    query=query,
                    variables={},
                    topic_key=topic_key,
                    page_num=page_num + 1,
                    progress_callback=progress_callback,
                    task_name=page_task_name,
                )
            )

        # Execute all page fetches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all nodes from successful pages
        all_nodes: List[Dict[str, Any]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Log at DEBUG level - these errors are often expected due to API limits
                # and are handled gracefully by continuing with successfully fetched pages
                logger.debug("Error fetching page %d: %s", i + 1, str(result))
            elif isinstance(result, list):
                all_nodes.extend(result)

        return all_nodes

    async def _fetch_single_page(
        self,
        query: str,
        variables: Dict[str, Any],
        topic_key: str,
        page_num: int,
        progress_callback: Optional[Callable] = None,
        task_name: str = "Page",
    ) -> List[Dict[str, Any]]:
        """
        Fetch a single page of results.

        :param str query: GraphQL query string
        :param Dict[str, Any] variables: Query variables
        :param str topic_key: Key to extract nodes from response
        :param int page_num: Page number for logging
        :param Optional[callable] progress_callback: Callback for progress updates
        :param str task_name: Name for progress tracking
        :return: Nodes from this page
        :rtype: List[Dict[str, Any]]
        """
        try:
            data = await self.execute_query(
                query=query, variables=variables, progress_callback=progress_callback, task_name=task_name
            )

            topic_data = data.get(topic_key, {})
            nodes = topic_data.get("items", [])

            # Handle case where nodes is explicitly None
            if nodes is None:
                nodes = []

            if progress_callback:
                progress_callback(task_name, f"fetched_{len(nodes)}_items")

            return nodes

        except Exception as e:
            # Log at DEBUG level - page fetch errors are handled gracefully by the caller
            # and are often expected when hitting API limits
            logger.debug("Error fetching page %d: %s", page_num, str(e))
            raise


def run_async_paginated_query(
    endpoint: str,
    headers: Dict[str, str],
    query_builder: Callable[[int, int], str],
    topic_key: str,
    total_count: int,
    page_size: int = 50,
    starting_skip: int = 0,
    max_concurrent: int = 5,
    timeout: int = 60,
    progress_callback: Optional[Callable] = None,
    task_name: str = "Paginated Query",
    token_refresh_callback: Optional[Callable[[], str]] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to run async paginated query from synchronous code.

    :param str endpoint: GraphQL endpoint URL
    :param Dict[str, str] headers: HTTP headers
    :param Callable[[int, int], str] query_builder: Function to build query with skip and take
    :param str topic_key: Key to extract data from response
    :param int total_count: Total number of items to fetch
    :param int page_size: Items per page
    :param int starting_skip: Starting skip value
    :param int max_concurrent: Maximum concurrent requests
    :param int timeout: Request timeout in seconds
    :param Optional[callable] progress_callback: Progress callback
    :param str task_name: Task name for progress tracking
    :param Optional[Callable[[], str]] token_refresh_callback: Callback to refresh auth token
    :return: Query results
    :rtype: List[Dict[str, Any]]
    """

    async def _run():
        client = AsyncRegScaleGraphQLClient(
            endpoint=endpoint,
            headers=headers,
            max_concurrent=max_concurrent,
            timeout=timeout,
            token_refresh_callback=token_refresh_callback,
        )
        return await client.execute_paginated_query_concurrent(
            query_builder=query_builder,
            topic_key=topic_key,
            total_count=total_count,
            page_size=page_size,
            starting_skip=starting_skip,
            progress_callback=progress_callback,
            task_name=task_name,
        )

    # Use anyio.run for better compatibility
    return anyio.run(_run)
