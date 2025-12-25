#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive unit tests for Wiz AsyncGraphQLClient Module"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import anyio
import httpx
import pytest

from regscale.integrations.commercial.wizv2.core.client import (
    AsyncWizGraphQLClient,
    run_async_queries,
)
from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

PATH = "regscale.integrations.commercial.wizv2.core.client"

logger = logging.getLogger("regscale")


class TestAsyncWizGraphQLClientInit:
    """Test AsyncWizGraphQLClient initialization"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        assert client.endpoint == "https://api.wiz.io/graphql"
        assert client.headers == {}
        assert client.timeout == 30.0
        assert client.max_concurrent == 5
        assert client._semaphore is not None

    def test_init_with_custom_parameters(self):
        """Test initialization with custom parameters"""
        headers = {"Authorization": "Bearer test-token"}
        client = AsyncWizGraphQLClient(
            endpoint="https://custom.wiz.io/graphql",
            headers=headers,
            timeout=60.0,
            max_concurrent=10,
        )

        assert client.endpoint == "https://custom.wiz.io/graphql"
        assert client.headers == headers
        assert client.timeout == 60.0
        assert client.max_concurrent == 10

    def test_init_with_none_headers(self):
        """Test initialization with None headers defaults to empty dict"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql", headers=None)

        assert client.headers == {}


class TestAsyncWizGraphQLClientExecuteQuery:
    """Test AsyncWizGraphQLClient.execute_query method"""

    @pytest.mark.asyncio
    async def test_execute_query_success(self):
        """Test successful query execution"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"data": {"result": "success"}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.execute_query(query="query { test }", variables={"key": "value"})

            assert result == {"result": "success"}
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_with_progress_callback(self):
        """Test query execution with progress callback"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"data": {"result": "success"}}

        progress_calls = []

        def progress_callback(task_name, status, extra_data=None):
            progress_calls.append((task_name, status))

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.execute_query(
                query="query { test }",
                variables={"key": "value"},
                progress_callback=progress_callback,
                task_name="Test Query",
            )

            assert result == {"result": "success"}
            assert ("Test Query", "starting") in progress_calls
            assert ("Test Query", "requesting") in progress_calls
            assert ("Test Query", "processing") in progress_calls
            assert ("Test Query", "completed") in progress_calls

    @pytest.mark.asyncio
    async def test_execute_query_non_success_response(self):
        """Test query execution with non-success HTTP response"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch(f"{PATH}.error_and_exit") as mock_error_exit:
                mock_error_exit.side_effect = SystemExit(1)

                with pytest.raises(SystemExit):
                    await client.execute_query(query="query { test }")

                mock_error_exit.assert_called_once()
                error_message = mock_error_exit.call_args[0][0]
                assert "500" in error_message

    @pytest.mark.asyncio
    async def test_execute_query_with_graphql_errors(self):
        """Test query execution with GraphQL errors in response"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"errors": [{"message": "GraphQL error occurred"}]}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch(f"{PATH}.error_and_exit") as mock_error_exit:
                mock_error_exit.side_effect = SystemExit(1)

                with pytest.raises(SystemExit):
                    await client.execute_query(query="query { test }")

                mock_error_exit.assert_called_once()
                error_message = mock_error_exit.call_args[0][0]
                assert "GraphQL errors" in error_message

    @pytest.mark.asyncio
    async def test_execute_query_http_error(self):
        """Test query execution with HTTP error"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Connection error"))
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch(f"{PATH}.error_and_exit") as mock_error_exit:
                mock_error_exit.side_effect = SystemExit(1)

                with pytest.raises(SystemExit):
                    await client.execute_query(query="query { test }")

                mock_error_exit.assert_called_once()
                error_message = mock_error_exit.call_args[0][0]
                assert "HTTP error" in error_message

    @pytest.mark.asyncio
    async def test_execute_query_general_exception(self):
        """Test query execution with general exception"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("Unexpected error"))
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch(f"{PATH}.error_and_exit") as mock_error_exit:
                mock_error_exit.side_effect = SystemExit(1)

                with pytest.raises(SystemExit):
                    await client.execute_query(query="query { test }")

                mock_error_exit.assert_called_once()
                error_message = mock_error_exit.call_args[0][0]
                assert "Error in" in error_message

    @pytest.mark.asyncio
    async def test_execute_query_with_ssl_verify_false(self):
        """Test query execution with SSL verification disabled"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"data": {"result": "success"}}

        with patch(f"{PATH}.ScannerVariables") as mock_scanner_vars:
            mock_scanner_vars.sslVerify = False

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client_class.return_value.__aenter__.return_value = mock_client

                result = await client.execute_query(query="query { test }")

                assert result == {"result": "success"}
                mock_client_class.assert_called_once()
                call_kwargs = mock_client_class.call_args[1]
                assert call_kwargs["verify"] is False

    @pytest.mark.asyncio
    async def test_execute_query_empty_response_data(self):
        """Test query execution with empty data in response"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.execute_query(query="query { test }")

            assert result == {}

    @pytest.mark.asyncio
    async def test_execute_query_with_empty_variables(self):
        """Test query execution with empty variables"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"data": {"result": "success"}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.execute_query(query="query { test }", variables=None)

            assert result == {"result": "success"}
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert payload["variables"] == {}


class TestAsyncWizGraphQLClientExecutePaginatedQuery:
    """Test AsyncWizGraphQLClient.execute_paginated_query method"""

    @pytest.mark.asyncio
    async def test_execute_paginated_query_single_page(self):
        """Test paginated query with single page"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "data": {
                "vulnerabilities": {
                    "nodes": [{"id": "1"}, {"id": "2"}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.execute_paginated_query(
                query="query { vulnerabilities }",
                variables={"first": 100},
                topic_key="vulnerabilities",
            )

            assert len(result) == 2
            assert result[0]["id"] == "1"
            assert result[1]["id"] == "2"

    @pytest.mark.asyncio
    async def test_execute_paginated_query_multiple_pages(self):
        """Test paginated query with multiple pages"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        # First page response
        mock_response_1 = Mock()
        mock_response_1.is_success = True
        mock_response_1.json.return_value = {
            "data": {
                "vulnerabilities": {
                    "nodes": [{"id": "1"}, {"id": "2"}],
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                }
            }
        }

        # Second page response
        mock_response_2 = Mock()
        mock_response_2.is_success = True
        mock_response_2.json.return_value = {
            "data": {
                "vulnerabilities": {
                    "nodes": [{"id": "3"}, {"id": "4"}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[mock_response_1, mock_response_2])
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.execute_paginated_query(
                query="query { vulnerabilities }",
                variables={"first": 100},
                topic_key="vulnerabilities",
            )

            assert len(result) == 4
            assert result[0]["id"] == "1"
            assert result[3]["id"] == "4"
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_paginated_query_with_progress_callback(self):
        """Test paginated query with progress callback"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "data": {
                "vulnerabilities": {
                    "nodes": [{"id": "1"}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }

        progress_calls = []

        def progress_callback(task_name, status, extra_data=None):
            progress_calls.append((task_name, status, extra_data))

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.execute_paginated_query(
                query="query { vulnerabilities }",
                variables={"first": 100},
                topic_key="vulnerabilities",
                progress_callback=progress_callback,
                task_name="Test Paginated Query",
            )

            assert len(result) == 1
            assert any("fetched_page_1" in str(call) for call in progress_calls)

    @pytest.mark.asyncio
    async def test_execute_paginated_query_with_null_nodes(self):
        """Test paginated query when nodes is None"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "data": {"vulnerabilities": {"nodes": None, "pageInfo": {"hasNextPage": False, "endCursor": None}}}
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.execute_paginated_query(
                query="query { vulnerabilities }",
                variables={"first": 100},
                topic_key="vulnerabilities",
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_execute_paginated_query_error_on_page(self):
        """Test paginated query with error on a page"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        # First page success
        mock_response_1 = Mock()
        mock_response_1.is_success = True
        mock_response_1.json.return_value = {
            "data": {
                "vulnerabilities": {
                    "nodes": [{"id": "1"}],
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                }
            }
        }

        # Second page fails
        mock_response_2 = Mock()
        mock_response_2.is_success = False
        mock_response_2.status_code = 500
        mock_response_2.text = "Server Error"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[mock_response_1, mock_response_2])
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch(f"{PATH}.error_and_exit") as mock_error_exit:
                mock_error_exit.side_effect = SystemExit(1)

                # Should return partial results before error
                with pytest.raises(SystemExit):
                    await client.execute_paginated_query(
                        query="query { vulnerabilities }",
                        variables={"first": 100},
                        topic_key="vulnerabilities",
                    )

    @pytest.mark.asyncio
    async def test_execute_paginated_query_empty_page_info(self):
        """Test paginated query with missing pageInfo"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"data": {"vulnerabilities": {"nodes": [{"id": "1"}], "pageInfo": {}}}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.execute_paginated_query(
                query="query { vulnerabilities }",
                variables={"first": 100},
                topic_key="vulnerabilities",
            )

            assert len(result) == 1
            assert result[0]["id"] == "1"


class TestAsyncWizGraphQLClientProgressCallback:
    """Test AsyncWizGraphQLClient._create_progress_callback method"""

    def test_create_progress_callback_starting(self):
        """Test progress callback for starting status"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_tracker = MagicMock()
        callback = client._create_progress_callback(mock_tracker, "task_1", "vulnerabilities")

        callback("test_task", "starting")

        mock_tracker.update.assert_called_once()
        call_args = mock_tracker.update.call_args
        assert "Starting vulnerabilities" in call_args[1]["description"]

    def test_create_progress_callback_requesting(self):
        """Test progress callback for requesting status"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_tracker = MagicMock()
        callback = client._create_progress_callback(mock_tracker, "task_1", "vulnerabilities")

        callback("test_task", "requesting")

        mock_tracker.update.assert_called_once()
        call_args = mock_tracker.update.call_args
        assert "Querying vulnerabilities" in call_args[1]["description"]

    def test_create_progress_callback_completed(self):
        """Test progress callback for completed status"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_tracker = MagicMock()
        callback = client._create_progress_callback(mock_tracker, "task_1", "vulnerabilities")

        callback("test_task", "completed")

        mock_tracker.update.assert_called_once()
        call_args = mock_tracker.update.call_args
        assert "Completed vulnerabilities" in call_args[1]["description"]

    def test_create_progress_callback_failed(self):
        """Test progress callback for failed status"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_tracker = MagicMock()
        callback = client._create_progress_callback(mock_tracker, "task_1", "vulnerabilities")

        callback("test_task", "failed")

        mock_tracker.update.assert_called_once()
        call_args = mock_tracker.update.call_args
        assert "Failed vulnerabilities" in call_args[1]["description"]

    def test_create_progress_callback_fetched_page(self):
        """Test progress callback for fetched_page status"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_tracker = MagicMock()
        callback = client._create_progress_callback(mock_tracker, "task_1", "vulnerabilities")

        callback("test_task", "fetched_page_1", {"nodes_count": 10, "total_nodes": 10})

        mock_tracker.update.assert_called_once()
        call_args = mock_tracker.update.call_args
        assert "10 nodes fetched" in call_args[1]["description"]

    def test_create_progress_callback_unknown_status(self):
        """Test progress callback with unknown status"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_tracker = MagicMock()
        callback = client._create_progress_callback(mock_tracker, "task_1", "vulnerabilities")

        callback("test_task", "unknown_status")

        # Should not crash, just not update
        assert mock_tracker.update.call_count == 0


class TestAsyncWizGraphQLClientExecuteSingleQueryConfig:
    """Test AsyncWizGraphQLClient._execute_single_query_config method"""

    @pytest.mark.asyncio
    async def test_execute_single_query_config_success(self):
        """Test successful single query config execution"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        config = {
            "type": WizVulnerabilityType.VULNERABILITY,
            "query": "query { test }",
            "variables": {"first": 100},
            "topic_key": "vulnerabilities",
        }

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "data": {"vulnerabilities": {"nodes": [{"id": "1"}], "pageInfo": {"hasNextPage": False}}}
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            query_type, results, error = await client._execute_single_query_config(config)

            assert query_type == "vulnerability"
            assert len(results) == 1
            assert error is None

    @pytest.mark.asyncio
    async def test_execute_single_query_config_with_progress_tracker(self):
        """Test single query config with progress tracker"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        config = {
            "type": WizVulnerabilityType.VULNERABILITY,
            "query": "query { test }",
            "variables": {"first": 100},
            "topic_key": "vulnerabilities",
        }

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "data": {"vulnerabilities": {"nodes": [{"id": "1"}], "pageInfo": {"hasNextPage": False}}}
        }

        mock_tracker = MagicMock()
        mock_tracker.add_task.return_value = "task_1"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            query_type, results, error = await client._execute_single_query_config(config, mock_tracker)

            assert query_type == "vulnerability"
            assert len(results) == 1
            assert error is None
            mock_tracker.add_task.assert_called_once()
            mock_tracker.update.assert_called()

    @pytest.mark.asyncio
    async def test_execute_single_query_config_with_exception(self):
        """Test single query config with exception"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        config = {
            "type": WizVulnerabilityType.VULNERABILITY,
            "query": "query { test }",
            "variables": {"first": 100},
            "topic_key": "vulnerabilities",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("Test error"))
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch(f"{PATH}.error_and_exit") as mock_error_exit:
                mock_error_exit.side_effect = SystemExit(1)

                with pytest.raises(SystemExit):
                    await client._execute_single_query_config(config)


class TestAsyncWizGraphQLClientProcessConcurrentResults:
    """Test AsyncWizGraphQLClient._process_concurrent_results method"""

    def test_process_concurrent_results_all_success(self):
        """Test processing concurrent results with all successes"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        results = [
            ("vulnerability", [{"id": "1"}], None),
            ("configuration_finding", [{"id": "2"}], None),
        ]

        query_configs = [
            {"type": WizVulnerabilityType.VULNERABILITY},
            {"type": WizVulnerabilityType.CONFIGURATION},
        ]

        processed = client._process_concurrent_results(results, query_configs)

        assert len(processed) == 2
        assert processed[0] == ("vulnerability", [{"id": "1"}], None)
        assert processed[1] == ("configuration_finding", [{"id": "2"}], None)

    def test_process_concurrent_results_with_exception(self):
        """Test processing concurrent results with exception"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        test_exception = Exception("Test error")
        results = [
            ("vulnerability", [{"id": "1"}], None),
            test_exception,
        ]

        query_configs = [
            {"type": WizVulnerabilityType.VULNERABILITY},
            {"type": WizVulnerabilityType.CONFIGURATION},
        ]

        processed = client._process_concurrent_results(results, query_configs)

        assert len(processed) == 2
        assert processed[0] == ("vulnerability", [{"id": "1"}], None)
        assert processed[1][0] == "configuration_finding"
        assert processed[1][1] == []
        assert isinstance(processed[1][2], Exception)


class TestAsyncWizGraphQLClientExecuteConcurrentQueries:
    """Test AsyncWizGraphQLClient.execute_concurrent_queries method"""

    @pytest.mark.asyncio
    async def test_execute_concurrent_queries_success(self):
        """Test concurrent queries execution"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        query_configs = [
            {
                "type": WizVulnerabilityType.VULNERABILITY,
                "query": "query { vulnerabilities }",
                "variables": {"first": 100},
                "topic_key": "vulnerabilities",
            },
            {
                "type": WizVulnerabilityType.CONFIGURATION,
                "query": "query { configurationFindings }",
                "variables": {"first": 100},
                "topic_key": "configurationFindings",
            },
        ]

        mock_response_1 = Mock()
        mock_response_1.is_success = True
        mock_response_1.json.return_value = {
            "data": {"vulnerabilities": {"nodes": [{"id": "1"}], "pageInfo": {"hasNextPage": False}}}
        }

        mock_response_2 = Mock()
        mock_response_2.is_success = True
        mock_response_2.json.return_value = {
            "data": {"configurationFindings": {"nodes": [{"id": "2"}], "pageInfo": {"hasNextPage": False}}}
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[mock_response_1, mock_response_2])
            mock_client_class.return_value.__aenter__.return_value = mock_client

            results = await client.execute_concurrent_queries(query_configs)

            assert len(results) == 2
            assert results[0][0] == "vulnerability"
            assert len(results[0][1]) == 1
            assert results[1][0] == "configuration_finding"
            assert len(results[1][1]) == 1

    @pytest.mark.asyncio
    async def test_execute_concurrent_queries_with_progress_tracker(self):
        """Test concurrent queries with progress tracker"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        query_configs = [
            {
                "type": WizVulnerabilityType.VULNERABILITY,
                "query": "query { vulnerabilities }",
                "variables": {"first": 100},
                "topic_key": "vulnerabilities",
            }
        ]

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "data": {"vulnerabilities": {"nodes": [{"id": "1"}], "pageInfo": {"hasNextPage": False}}}
        }

        mock_tracker = MagicMock()
        mock_tracker.add_task.return_value = "task_1"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            results = await client.execute_concurrent_queries(query_configs, mock_tracker)

            assert len(results) == 1
            mock_tracker.add_task.assert_called_once()


class TestRunAsyncQueries:
    """Test run_async_queries function"""

    def test_run_async_queries_success(self):
        """Test run_async_queries with successful execution"""
        endpoint = "https://api.wiz.io/graphql"
        headers = {"Authorization": "Bearer test-token"}
        query_configs = [
            {
                "type": WizVulnerabilityType.VULNERABILITY,
                "query": "query { vulnerabilities }",
                "variables": {"first": 100},
                "topic_key": "vulnerabilities",
            }
        ]

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "data": {"vulnerabilities": {"nodes": [{"id": "1"}], "pageInfo": {"hasNextPage": False}}}
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            results = run_async_queries(endpoint, headers, query_configs)

            assert len(results) == 1
            assert results[0][0] == "vulnerability"
            assert len(results[0][1]) == 1

    def test_run_async_queries_with_custom_parameters(self):
        """Test run_async_queries with custom max_concurrent and timeout"""
        endpoint = "https://api.wiz.io/graphql"
        headers = {"Authorization": "Bearer test-token"}
        query_configs = [
            {
                "type": WizVulnerabilityType.VULNERABILITY,
                "query": "query { vulnerabilities }",
                "variables": {"first": 100},
                "topic_key": "vulnerabilities",
            }
        ]

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "data": {"vulnerabilities": {"nodes": [{"id": "1"}], "pageInfo": {"hasNextPage": False}}}
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            results = run_async_queries(endpoint, headers, query_configs, max_concurrent=10, timeout=120)

            assert len(results) == 1

    def test_run_async_queries_with_progress_tracker(self):
        """Test run_async_queries with progress tracker"""
        endpoint = "https://api.wiz.io/graphql"
        headers = {"Authorization": "Bearer test-token"}
        query_configs = [
            {
                "type": WizVulnerabilityType.VULNERABILITY,
                "query": "query { vulnerabilities }",
                "variables": {"first": 100},
                "topic_key": "vulnerabilities",
            }
        ]

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "data": {"vulnerabilities": {"nodes": [{"id": "1"}], "pageInfo": {"hasNextPage": False}}}
        }

        mock_tracker = MagicMock()
        mock_tracker.add_task.return_value = "task_1"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            results = run_async_queries(endpoint, headers, query_configs, progress_tracker=mock_tracker)

            assert len(results) == 1
            mock_tracker.add_task.assert_called_once()


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_concurrent_request_limiting(self):
        """Test that max_concurrent limits concurrent requests"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql", max_concurrent=2)

        assert client.max_concurrent == 2
        assert client._semaphore._value == 2

    @pytest.mark.asyncio
    async def test_timeout_configuration(self):
        """Test that timeout is properly configured"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql", timeout=90.0)

        assert client.timeout == 90.0

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"data": {"result": "success"}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await client.execute_query(query="query { test }")

            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["timeout"] == 90.0

    @pytest.mark.asyncio
    async def test_empty_query_configs(self):
        """Test execute_concurrent_queries with empty configs"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        results = await client.execute_concurrent_queries([])

        assert results == []

    @pytest.mark.asyncio
    async def test_query_with_null_topic_key_data(self):
        """Test paginated query when topic_key data is missing"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"data": {}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.execute_paginated_query(
                query="query { vulnerabilities }",
                variables={"first": 100},
                topic_key="vulnerabilities",
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_large_page_count(self):
        """Test paginated query with many pages"""
        client = AsyncWizGraphQLClient(endpoint="https://api.wiz.io/graphql")

        responses = []
        for i in range(10):
            mock_response = Mock()
            mock_response.is_success = True
            mock_response.json.return_value = {
                "data": {
                    "vulnerabilities": {
                        "nodes": [{"id": str(i)}],
                        "pageInfo": {"hasNextPage": i < 9, "endCursor": f"cursor{i}" if i < 9 else None},
                    }
                }
            }
            responses.append(mock_response)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=responses)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await client.execute_paginated_query(
                query="query { vulnerabilities }",
                variables={"first": 100},
                topic_key="vulnerabilities",
            )

            assert len(result) == 10
            assert mock_client.post.call_count == 10


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_full_query_workflow(self):
        """Test complete workflow from run_async_queries to results"""
        endpoint = "https://api.wiz.io/graphql"
        headers = {"Authorization": "Bearer test-token"}

        # Create multiple query configs
        query_configs = [
            {
                "type": WizVulnerabilityType.VULNERABILITY,
                "query": "query { vulnerabilities }",
                "variables": {"first": 100},
                "topic_key": "vulnerabilities",
            },
            {
                "type": WizVulnerabilityType.CONFIGURATION,
                "query": "query { configurationFindings }",
                "variables": {"first": 100},
                "topic_key": "configurationFindings",
            },
            {
                "type": WizVulnerabilityType.HOST_FINDING,
                "query": "query { hostFindings }",
                "variables": {"first": 100},
                "topic_key": "hostFindings",
            },
        ]

        # Mock responses for all queries
        mock_response_1 = Mock()
        mock_response_1.is_success = True
        mock_response_1.json.return_value = {
            "data": {"vulnerabilities": {"nodes": [{"id": "v1"}, {"id": "v2"}], "pageInfo": {"hasNextPage": False}}}
        }

        mock_response_2 = Mock()
        mock_response_2.is_success = True
        mock_response_2.json.return_value = {
            "data": {"configurationFindings": {"nodes": [{"id": "c1"}], "pageInfo": {"hasNextPage": False}}}
        }

        mock_response_3 = Mock()
        mock_response_3.is_success = True
        mock_response_3.json.return_value = {
            "data": {
                "hostFindings": {
                    "nodes": [{"id": "h1"}, {"id": "h2"}, {"id": "h3"}],
                    "pageInfo": {"hasNextPage": False},
                }
            }
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[mock_response_1, mock_response_2, mock_response_3])
            mock_client_class.return_value.__aenter__.return_value = mock_client

            results = run_async_queries(endpoint, headers, query_configs)

            # Verify results
            assert len(results) == 3

            # Check vulnerabilities
            assert results[0][0] == "vulnerability"
            assert len(results[0][1]) == 2
            assert results[0][2] is None

            # Check configuration findings
            assert results[1][0] == "configuration_finding"
            assert len(results[1][1]) == 1
            assert results[1][2] is None

            # Check host findings
            assert results[2][0] == "host_finding"
            assert len(results[2][1]) == 3
            assert results[2][2] is None
