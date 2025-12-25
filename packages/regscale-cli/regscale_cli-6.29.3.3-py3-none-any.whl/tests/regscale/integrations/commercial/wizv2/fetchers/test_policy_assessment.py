"""
Comprehensive unit tests for policy_assessment.py module.

This test suite covers:
- WizDataCache: caching, TTL validation, file operations
- WizApiClient: async fetching, requests-based fetching, pagination, error handling
- PolicyAssessmentFetcher: main fetching logic, filtering, data cleaning
"""

import json
import logging
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch, call

import pytest
import requests

from regscale.integrations.commercial.wizv2.fetchers.policy_assessment import (
    WizDataCache,
    WizApiClient,
    PolicyAssessmentFetcher,
)
from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType, WIZ_POLICY_QUERY

logger = logging.getLogger("regscale")


class TestWizDataCache(unittest.TestCase):
    """Test cases for WizDataCache class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.wiz_project_id = "test-project-123"
        self.framework_id = "wf-id-4"

    def tearDown(self):
        """Clean up test artifacts."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_default_values(self):
        """Test WizDataCache initialization with default values."""
        cache = WizDataCache(self.temp_dir)
        self.assertEqual(cache.cache_dir, self.temp_dir)
        self.assertEqual(cache.cache_duration_minutes, 0)
        self.assertFalse(cache.force_refresh)

    def test_init_custom_values(self):
        """Test WizDataCache initialization with custom values."""
        cache = WizDataCache(self.temp_dir, cache_duration_minutes=60)
        self.assertEqual(cache.cache_dir, self.temp_dir)
        self.assertEqual(cache.cache_duration_minutes, 60)
        self.assertFalse(cache.force_refresh)

    def test_get_cache_file_path(self):
        """Test cache file path generation."""
        cache = WizDataCache(self.temp_dir)
        cache_path = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        expected_filename = f"policy_assessments_{self.wiz_project_id}_{self.framework_id}.json"
        expected_path = os.path.join(self.temp_dir, expected_filename)

        self.assertEqual(cache_path, expected_path)
        self.assertTrue(os.path.exists(self.temp_dir))

    def test_is_cache_valid_disabled(self):
        """Test cache validation when caching is disabled (duration = 0)."""
        cache = WizDataCache(self.temp_dir, cache_duration_minutes=0)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        self.assertFalse(cache.is_cache_valid(cache_file))

    def test_is_cache_valid_force_refresh(self):
        """Test cache validation when force_refresh is enabled."""
        cache = WizDataCache(self.temp_dir, cache_duration_minutes=60)
        cache.force_refresh = True
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        self.assertFalse(cache.is_cache_valid(cache_file))

    def test_is_cache_valid_file_not_exists(self):
        """Test cache validation when cache file does not exist."""
        cache = WizDataCache(self.temp_dir, cache_duration_minutes=60)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        self.assertFalse(cache.is_cache_valid(cache_file))

    def test_is_cache_valid_fresh_file(self):
        """Test cache validation with a fresh cache file."""
        cache = WizDataCache(self.temp_dir, cache_duration_minutes=60)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        # Create a fresh cache file
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "nodes": []}, f)

        self.assertTrue(cache.is_cache_valid(cache_file))

    def test_is_cache_valid_expired_file(self):
        """Test cache validation with an expired cache file."""
        cache = WizDataCache(self.temp_dir, cache_duration_minutes=1)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        # Create cache file and modify timestamp to be old
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "nodes": []}, f)

        # Modify file time to be 2 minutes old
        old_time = (datetime.now() - timedelta(minutes=2)).timestamp()
        os.utime(cache_file, (old_time, old_time))

        self.assertFalse(cache.is_cache_valid(cache_file))

    def test_is_cache_valid_exception_handling(self):
        """Test cache validation handles exceptions gracefully."""
        cache = WizDataCache(self.temp_dir, cache_duration_minutes=60)

        # Test with invalid path that will cause exception
        with patch("os.path.exists", return_value=True):
            with patch("os.path.getmtime", side_effect=OSError("Permission denied")):
                self.assertFalse(cache.is_cache_valid("/invalid/path/cache.json"))

    def test_load_from_cache_success_nodes_key(self):
        """Test loading cache with 'nodes' key."""
        cache = WizDataCache(self.temp_dir)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        test_nodes = [{"id": "1", "name": "test"}]
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "nodes": test_nodes}, f)

        loaded_nodes = cache.load_from_cache(cache_file)
        self.assertEqual(loaded_nodes, test_nodes)

    def test_load_from_cache_success_assessments_key(self):
        """Test loading cache with 'assessments' key."""
        cache = WizDataCache(self.temp_dir)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        test_nodes = [{"id": "2", "name": "assessment"}]
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "assessments": test_nodes}, f)

        loaded_nodes = cache.load_from_cache(cache_file)
        self.assertEqual(loaded_nodes, test_nodes)

    def test_load_from_cache_empty_nodes(self):
        """Test loading cache with empty nodes."""
        cache = WizDataCache(self.temp_dir)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "nodes": []}, f)

        loaded_nodes = cache.load_from_cache(cache_file)
        self.assertEqual(loaded_nodes, [])

    def test_load_from_cache_no_nodes_key(self):
        """Test loading cache without nodes or assessments key."""
        cache = WizDataCache(self.temp_dir)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now().isoformat()}, f)

        loaded_nodes = cache.load_from_cache(cache_file)
        self.assertEqual(loaded_nodes, [])

    def test_load_from_cache_invalid_json(self):
        """Test loading cache with invalid JSON."""
        cache = WizDataCache(self.temp_dir)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        with open(cache_file, "w", encoding="utf-8") as f:
            f.write("invalid json content")

        loaded_nodes = cache.load_from_cache(cache_file)
        self.assertIsNone(loaded_nodes)

    def test_load_from_cache_file_not_exists(self):
        """Test loading cache when file does not exist."""
        cache = WizDataCache(self.temp_dir)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        loaded_nodes = cache.load_from_cache(cache_file)
        self.assertIsNone(loaded_nodes)

    def test_load_from_cache_non_list_nodes(self):
        """Test loading cache when nodes is not a list."""
        cache = WizDataCache(self.temp_dir)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "nodes": "not a list"}, f)

        loaded_nodes = cache.load_from_cache(cache_file)
        self.assertIsNone(loaded_nodes)

    def test_save_to_cache_success(self):
        """Test saving data to cache."""
        cache = WizDataCache(self.temp_dir, cache_duration_minutes=60)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        test_nodes = [{"id": "3", "name": "save_test"}]
        cache.save_to_cache(cache_file, test_nodes, self.wiz_project_id, self.framework_id)

        self.assertTrue(os.path.exists(cache_file))

        with open(cache_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertIn("timestamp", saved_data)
        self.assertEqual(saved_data["wiz_project_id"], self.wiz_project_id)
        self.assertEqual(saved_data["framework_id"], self.framework_id)
        self.assertEqual(saved_data["nodes"], test_nodes)

    def test_save_to_cache_disabled(self):
        """Test saving to cache when caching is disabled."""
        cache = WizDataCache(self.temp_dir, cache_duration_minutes=0)
        cache_file = cache.get_cache_file_path(self.wiz_project_id, self.framework_id)

        test_nodes = [{"id": "4", "name": "no_save_test"}]
        cache.save_to_cache(cache_file, test_nodes, self.wiz_project_id, self.framework_id)

        self.assertFalse(os.path.exists(cache_file))

    def test_save_to_cache_exception_handling(self):
        """Test save to cache handles exceptions gracefully."""
        cache = WizDataCache(self.temp_dir, cache_duration_minutes=60)

        # Use invalid path to trigger exception
        with patch("builtins.open", side_effect=PermissionError("No permission")):
            # Should not raise exception
            cache.save_to_cache("/invalid/path/cache.json", [], self.wiz_project_id, self.framework_id)


class TestWizApiClient(unittest.TestCase):
    """Test cases for WizApiClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.endpoint = "https://api.wiz.io/graphql"
        self.access_token = "test_token_12345"
        self.client = WizApiClient(self.endpoint, self.access_token)

    def test_init(self):
        """Test WizApiClient initialization."""
        self.assertEqual(self.client.endpoint, self.endpoint)
        self.assertEqual(self.client.access_token, self.access_token)

    def test_get_headers(self):
        """Test header generation."""
        headers = self.client.get_headers()

        self.assertIn("Authorization", headers)
        self.assertIn("Content-Type", headers)
        self.assertEqual(headers["Authorization"], f"Bearer {self.access_token}")
        self.assertEqual(headers["Content-Type"], "application/json")

    @patch("regscale.integrations.commercial.wizv2.fetchers.policy_assessment.run_async_queries")
    @patch("regscale.integrations.commercial.wizv2.utils.compliance_job_progress")
    def test_fetch_policy_assessments_async_success(self, mock_progress, mock_run_async):
        """Test async policy assessment fetching - success case."""
        mock_progress.__enter__ = Mock(return_value=mock_progress)
        mock_progress.__exit__ = Mock(return_value=False)
        mock_progress.add_task = Mock(return_value="task_id")
        mock_progress.update = Mock()

        test_nodes = [{"id": "node1"}, {"id": "node2"}]
        mock_run_async.return_value = [(WizVulnerabilityType.CONFIGURATION.value, test_nodes, None)]

        result = self.client.fetch_policy_assessments_async()

        self.assertEqual(result, test_nodes)
        mock_run_async.assert_called_once()

        call_args = mock_run_async.call_args
        self.assertEqual(call_args.kwargs["endpoint"], self.endpoint)
        self.assertIn("Authorization", call_args.kwargs["headers"])

    @patch("regscale.integrations.commercial.wizv2.fetchers.policy_assessment.run_async_queries")
    @patch("regscale.integrations.commercial.wizv2.utils.compliance_job_progress")
    def test_fetch_policy_assessments_async_empty_results(self, mock_progress, mock_run_async):
        """Test async policy assessment fetching - empty results."""
        mock_progress.__enter__ = Mock(return_value=mock_progress)
        mock_progress.__exit__ = Mock(return_value=False)
        mock_progress.add_task = Mock(return_value="task_id")
        mock_progress.update = Mock()

        mock_run_async.return_value = []

        result = self.client.fetch_policy_assessments_async()

        self.assertEqual(result, [])

    @patch("regscale.integrations.commercial.wizv2.fetchers.policy_assessment.run_async_queries")
    @patch("regscale.integrations.commercial.wizv2.utils.compliance_job_progress")
    def test_fetch_policy_assessments_async_with_error(self, mock_progress, mock_run_async):
        """Test async policy assessment fetching - with error."""
        mock_progress.__enter__ = Mock(return_value=mock_progress)
        mock_progress.__exit__ = Mock(return_value=False)
        mock_progress.add_task = Mock(return_value="task_id")
        mock_progress.update = Mock()

        mock_run_async.return_value = [(WizVulnerabilityType.CONFIGURATION.value, [], Exception("API Error"))]

        result = self.client.fetch_policy_assessments_async()

        self.assertEqual(result, [])

    @patch("regscale.integrations.commercial.wizv2.fetchers.policy_assessment.run_async_queries")
    @patch("regscale.integrations.commercial.wizv2.utils.compliance_job_progress")
    def test_fetch_policy_assessments_async_exception(self, mock_progress, mock_run_async):
        """Test async policy assessment fetching - exception raised."""
        mock_progress.__enter__ = Mock(return_value=mock_progress)
        mock_progress.__exit__ = Mock(return_value=False)
        mock_progress.add_task = Mock(return_value="task_id")
        mock_progress.update = Mock()

        mock_run_async.side_effect = Exception("Async client error")

        with self.assertRaises(Exception) as context:
            self.client.fetch_policy_assessments_async()

        self.assertIn("Async client error", str(context.exception))

    def test_create_requests_session(self):
        """Test requests session creation with retry logic."""
        session = self.client._create_requests_session()

        self.assertIsInstance(session, requests.Session)
        # Verify retry adapter is configured
        adapter = session.get_adapter("https://")
        self.assertIsNotNone(adapter)

    @patch.object(WizApiClient, "_execute_paginated_query")
    def test_fetch_policy_assessments_requests_success_first_variant(self, mock_execute):
        """Test requests-based fetching - success with first filter variant."""
        test_nodes = [{"id": "req1"}, {"id": "req2"}]
        mock_execute.return_value = test_nodes

        base_variables = {"first": 100}
        filter_variants = [{"project": ["proj1"]}, {"projectId": ["proj1"]}, None]

        result = self.client.fetch_policy_assessments_requests(base_variables, filter_variants)

        self.assertEqual(result, test_nodes)
        mock_execute.assert_called_once()

    @patch.object(WizApiClient, "_execute_paginated_query")
    def test_fetch_policy_assessments_requests_fallback_to_second_variant(self, mock_execute):
        """Test requests-based fetching - fallback to second filter variant."""
        test_nodes = [{"id": "req3"}]

        def side_effect(*args, **kwargs):
            if mock_execute.call_count == 1:
                raise Exception("First variant failed")
            return test_nodes

        mock_execute.side_effect = side_effect

        base_variables = {"first": 100}
        filter_variants = [{"project": ["proj1"]}, {"projectId": ["proj1"]}, None]

        result = self.client.fetch_policy_assessments_requests(base_variables, filter_variants)

        self.assertEqual(result, test_nodes)
        self.assertEqual(mock_execute.call_count, 2)

    @patch.object(WizApiClient, "_execute_paginated_query")
    def test_fetch_policy_assessments_requests_all_variants_fail(self, mock_execute):
        """Test requests-based fetching - all filter variants fail."""
        mock_execute.side_effect = Exception("API Error")

        base_variables = {"first": 100}
        filter_variants = [{"project": ["proj1"]}, None]

        with self.assertRaises(RuntimeError) as context:
            self.client.fetch_policy_assessments_requests(base_variables, filter_variants)

        self.assertIn("All filter variants failed", str(context.exception))

    @patch.object(WizApiClient, "_execute_paginated_query")
    def test_fetch_policy_assessments_requests_with_callback(self, mock_execute):
        """Test requests-based fetching with progress callback."""
        test_nodes = [{"id": "req4"}]
        mock_execute.return_value = test_nodes

        mock_callback = Mock()
        base_variables = {"first": 100}
        filter_variants = [{"project": ["proj1"]}]

        result = self.client.fetch_policy_assessments_requests(base_variables, filter_variants, mock_callback)

        self.assertEqual(result, test_nodes)

    @patch("requests.Session.post")
    def test_execute_paginated_query_single_page(self, mock_post):
        """Test paginated query execution - single page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "policyAssessments": {
                    "nodes": [{"id": "page1_node1"}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }
        mock_post.return_value = mock_response

        session = self.client._create_requests_session()
        variables = {"first": 100}

        result = self.client._execute_paginated_query(session, variables)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "page1_node1")
        mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_execute_paginated_query_multiple_pages(self, mock_post):
        """Test paginated query execution - multiple pages."""
        # First page response
        response1 = Mock()
        response1.status_code = 200
        response1.json.return_value = {
            "data": {
                "policyAssessments": {
                    "nodes": [{"id": "page1_node1"}],
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                }
            }
        }

        # Second page response
        response2 = Mock()
        response2.status_code = 200
        response2.json.return_value = {
            "data": {
                "policyAssessments": {
                    "nodes": [{"id": "page2_node1"}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }

        mock_post.side_effect = [response1, response2]

        session = self.client._create_requests_session()
        variables = {"first": 100}

        result = self.client._execute_paginated_query(session, variables)

        self.assertEqual(len(result), 2)
        self.assertEqual(mock_post.call_count, 2)

    @patch("requests.Session.post")
    def test_execute_paginated_query_with_progress_callback(self, mock_post):
        """Test paginated query execution with progress callback."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "policyAssessments": {
                    "nodes": [{"id": "callback_node"}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }
        mock_post.return_value = mock_response

        mock_callback = Mock()
        session = self.client._create_requests_session()
        variables = {"first": 100}

        result = self.client._execute_paginated_query(session, variables, mock_callback)

        self.assertEqual(len(result), 1)
        mock_callback.assert_called()

    @patch("requests.Session.post")
    def test_execute_paginated_query_http_error(self, mock_post):
        """Test paginated query execution - HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        session = self.client._create_requests_session()
        variables = {"first": 100}

        with self.assertRaises(requests.HTTPError):
            self.client._execute_paginated_query(session, variables)

    @patch("requests.Session.post")
    def test_execute_paginated_query_graphql_errors(self, mock_post):
        """Test paginated query execution - GraphQL errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errors": [{"message": "GraphQL error"}]}
        mock_post.return_value = mock_response

        session = self.client._create_requests_session()
        variables = {"first": 100}

        with self.assertRaises(RuntimeError) as context:
            self.client._execute_paginated_query(session, variables)

        self.assertIn("GraphQL error", str(context.exception))

    @patch("requests.Session.post")
    def test_execute_paginated_query_callback_exception(self, mock_post):
        """Test paginated query execution - callback raises exception (should be caught)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "policyAssessments": {
                    "nodes": [{"id": "callback_error_node"}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }
        mock_post.return_value = mock_response

        mock_callback = Mock(side_effect=Exception("Callback error"))
        session = self.client._create_requests_session()
        variables = {"first": 100}

        # Should not raise exception despite callback error
        result = self.client._execute_paginated_query(session, variables, mock_callback)

        self.assertEqual(len(result), 1)


class TestPolicyAssessmentFetcher(unittest.TestCase):
    """Test cases for PolicyAssessmentFetcher class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.wiz_endpoint = "https://api.wiz.io/graphql"
        self.access_token = "test_token"
        self.wiz_project_id = "proj-123"
        self.framework_id = "wf-id-4"

        # Create fetcher without mocking cache
        self.fetcher = PolicyAssessmentFetcher(
            self.wiz_endpoint, self.access_token, self.wiz_project_id, self.framework_id, cache_duration_minutes=0
        )

    def tearDown(self):
        """Clean up test artifacts."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test PolicyAssessmentFetcher initialization."""
        self.assertIsNotNone(self.fetcher.api_client)
        self.assertEqual(self.fetcher.wiz_project_id, self.wiz_project_id)
        self.assertEqual(self.fetcher.framework_id, self.framework_id)
        self.assertIsNotNone(self.fetcher.cache)

    def test_fetch_policy_assessments_no_cache(self):
        """Test fetching policy assessments without cache."""
        test_nodes = [
            {
                "id": "assess1",
                "policy": {
                    "securitySubCategories": [
                        {"externalId": " AC-1 ", "category": {"framework": {"id": self.framework_id}}}
                    ]
                },
            }
        ]

        with patch.object(self.fetcher.cache, "is_cache_valid", return_value=False):
            with patch.object(self.fetcher.cache, "get_cache_file_path", return_value="/tmp/cache.json"):
                with patch.object(self.fetcher.cache, "save_to_cache") as mock_save:
                    with patch.object(
                        self.fetcher.api_client, "fetch_policy_assessments_async", return_value=test_nodes
                    ):
                        result = self.fetcher.fetch_policy_assessments()

        self.assertEqual(len(result), 1)
        mock_save.assert_called_once()

    def test_fetch_policy_assessments_with_valid_cache(self):
        """Test fetching policy assessments with valid cache."""
        cached_nodes = [{"id": "cached1"}]

        with patch.object(self.fetcher.cache, "is_cache_valid", return_value=True):
            with patch.object(self.fetcher.cache, "get_cache_file_path", return_value="/tmp/cache.json"):
                with patch.object(self.fetcher.cache, "load_from_cache", return_value=cached_nodes) as mock_load:
                    result = self.fetcher.fetch_policy_assessments()

        self.assertEqual(result, cached_nodes)
        mock_load.assert_called_once()

    def test_fetch_policy_assessments_async_fallback_to_requests(self):
        """Test fallback to requests when async fails."""
        test_nodes = [{"id": "fallback1"}]

        with patch.object(self.fetcher.cache, "is_cache_valid", return_value=False):
            with patch.object(self.fetcher.cache, "get_cache_file_path", return_value="/tmp/cache.json"):
                with patch.object(self.fetcher.cache, "save_to_cache"):
                    with patch.object(
                        self.fetcher.api_client, "fetch_policy_assessments_async", side_effect=Exception("Async failed")
                    ) as mock_async:
                        with patch.object(
                            self.fetcher.api_client, "fetch_policy_assessments_requests", return_value=test_nodes
                        ) as mock_requests:
                            result = self.fetcher.fetch_policy_assessments()

        self.assertEqual(len(result), 1)
        mock_async.assert_called_once()
        mock_requests.assert_called_once()

    def test_filter_nodes_to_framework_matching(self):
        """Test filtering nodes to framework - matching framework."""
        nodes = [
            {
                "id": "node1",
                "policy": {"securitySubCategories": [{"category": {"framework": {"id": self.framework_id}}}]},
            },
            {
                "id": "node2",
                "policy": {"securitySubCategories": [{"category": {"framework": {"id": "other-framework"}}}]},
            },
        ]

        filtered = self.fetcher._filter_nodes_to_framework(nodes)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], "node1")

    def test_filter_nodes_to_framework_no_subcategories(self):
        """Test filtering nodes to framework - no subcategories (should include)."""
        nodes = [{"id": "node1", "policy": {"securitySubCategories": []}}]

        filtered = self.fetcher._filter_nodes_to_framework(nodes)

        self.assertEqual(len(filtered), 1)

    def test_filter_nodes_to_framework_exception_handling(self):
        """Test filtering nodes to framework - exception handling."""
        nodes = [{"id": "node1", "policy": None}]

        filtered = self.fetcher._filter_nodes_to_framework(nodes)

        # Should include node on error (defensive)
        self.assertEqual(len(filtered), 1)

    def test_clean_node_data_trim_whitespace(self):
        """Test cleaning node data - trim whitespace from externalId."""
        nodes = [
            {
                "id": "node1",
                "policy": {
                    "securitySubCategories": [
                        {"externalId": " AC-1 ", "category": {"framework": {"id": "fw1"}}},
                        {"externalId": "AC-2", "category": {"framework": {"id": "fw1"}}},
                    ]
                },
            }
        ]

        cleaned = self.fetcher._clean_node_data(nodes)

        self.assertEqual(cleaned[0]["policy"]["securitySubCategories"][0]["externalId"], "AC-1")
        self.assertEqual(cleaned[0]["policy"]["securitySubCategories"][1]["externalId"], "AC-2")

    def test_clean_node_data_no_policy(self):
        """Test cleaning node data - no policy field."""
        nodes = [{"id": "node1"}]

        cleaned = self.fetcher._clean_node_data(nodes)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0]["id"], "node1")

    def test_clean_node_data_exception_handling(self):
        """Test cleaning node data - exception handling."""
        nodes = [{"id": "node1", "policy": {"securitySubCategories": "invalid"}}]

        cleaned = self.fetcher._clean_node_data(nodes)

        # Should include original node on error
        self.assertEqual(len(cleaned), 1)

    def test_clean_single_node(self):
        """Test cleaning a single node."""
        node = {
            "id": "node1",
            "policy": {"securitySubCategories": [{"externalId": " AC-1 "}]},
        }

        cleaned = self.fetcher._clean_single_node(node)

        self.assertEqual(cleaned["policy"]["securitySubCategories"][0]["externalId"], "AC-1")

    def test_should_clean_policy_true(self):
        """Test should_clean_policy returns True."""
        policy = {"securitySubCategories": []}

        result = self.fetcher._should_clean_policy(policy)

        self.assertTrue(result)

    def test_should_clean_policy_false_no_policy(self):
        """Test should_clean_policy returns False - no policy."""
        result = self.fetcher._should_clean_policy(None)

        self.assertFalse(result)

    def test_should_clean_policy_false_no_subcategories(self):
        """Test should_clean_policy returns False - no subcategories key."""
        policy = {"other_key": "value"}

        result = self.fetcher._should_clean_policy(policy)

        self.assertFalse(result)

    def test_clean_policy_subcategories(self):
        """Test cleaning policy subcategories."""
        policy = {
            "id": "policy1",
            "securitySubCategories": [
                {"externalId": " AC-1 "},
                {"externalId": " AC-2 "},
            ],
        }

        cleaned = self.fetcher._clean_policy_subcategories(policy)

        self.assertEqual(cleaned["securitySubCategories"][0]["externalId"], "AC-1")
        self.assertEqual(cleaned["securitySubCategories"][1]["externalId"], "AC-2")
        self.assertEqual(cleaned["id"], "policy1")

    def test_clean_subcategory(self):
        """Test cleaning a single subcategory."""
        subcat = {"externalId": " AC-1 ", "title": "Access Control"}

        cleaned = self.fetcher._clean_subcategory(subcat)

        self.assertEqual(cleaned["externalId"], "AC-1")
        self.assertEqual(cleaned["title"], "Access Control")

    def test_clean_subcategory_no_external_id(self):
        """Test cleaning subcategory without externalId."""
        subcat = {"title": "Access Control"}

        cleaned = self.fetcher._clean_subcategory(subcat)

        self.assertNotIn("externalId", cleaned)

    def test_clean_subcategory_non_string_external_id(self):
        """Test cleaning subcategory with non-string externalId."""
        subcat = {"externalId": 123, "title": "Test"}

        cleaned = self.fetcher._clean_subcategory(subcat)

        self.assertEqual(cleaned["externalId"], 123)

    @patch.object(WizApiClient, "fetch_policy_assessments_async")
    def test_fetch_with_async_client(self, mock_async):
        """Test _fetch_with_async_client."""
        test_nodes = [{"id": "async1"}]
        mock_async.return_value = test_nodes

        result = self.fetcher._fetch_with_async_client()

        self.assertEqual(result, test_nodes)
        mock_async.assert_called_once()

    @patch.object(WizApiClient, "fetch_policy_assessments_requests")
    def test_fetch_with_requests(self, mock_requests):
        """Test _fetch_with_requests with multiple filter variants."""
        test_nodes = [{"id": "req1"}]
        mock_requests.return_value = test_nodes

        result = self.fetcher._fetch_with_requests()

        self.assertEqual(result, test_nodes)
        mock_requests.assert_called_once()

        # Verify filter variants were passed
        call_args = mock_requests.call_args
        filter_variants = call_args[0][1]
        self.assertIn({"project": [self.wiz_project_id]}, filter_variants)
        self.assertIn({"projectId": [self.wiz_project_id]}, filter_variants)
        self.assertIn(None, filter_variants)


if __name__ == "__main__":
    unittest.main()
