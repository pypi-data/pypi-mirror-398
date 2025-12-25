#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for WizDataMixin module.

Tests cover:
- fetch_data_if_needed with various file states (exists/not exists, fresh/stale)
- write_to_file functionality
- load_file functionality
- fetch_data with GraphQL client mocking
- Error handling and edge cases
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, mock_open

import pytest

from regscale.integrations.commercial.wizv2.WizDataMixin import WizMixin


class TestWizMixinFetchDataIfNeeded:
    """Test fetch_data_if_needed method with various scenarios."""

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.load_file")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_fetch_data_if_needed_uses_fresh_cache(self, mock_getmtime, mock_exists, mock_load_file):
        """Test that fetch_data_if_needed uses cache when file is fresh."""
        # Setup
        wiz = WizMixin()
        file_path = "artifacts/test_data.json"
        cached_data = [{"id": "1", "name": "cached"}]

        # Mock file exists and is fresh (modified 1 hour ago, interval is 2 hours)
        mock_exists.return_value = True
        current_time = datetime.now()
        file_mod_time = current_time - timedelta(hours=1)
        mock_getmtime.return_value = file_mod_time.timestamp()
        mock_load_file.return_value = cached_data

        # Execute
        result = wiz.fetch_data_if_needed(
            file_path=file_path, query="query {}", topic_key="test", interval_hours=2, variables=None
        )

        # Verify
        assert result == cached_data
        mock_load_file.assert_called_once_with(file_path)

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.write_to_file")
    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.fetch_data")
    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.load_file")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_fetch_data_if_needed_fetches_when_cache_stale(
        self, mock_getmtime, mock_exists, mock_load_file, mock_fetch_data, mock_write_to_file
    ):
        """Test that fetch_data_if_needed fetches new data when cache is stale."""
        # Setup
        wiz = WizMixin()
        file_path = "artifacts/test_data.json"
        fresh_data = [{"id": "2", "name": "fresh"}]

        # Mock file exists but is stale (modified 3 hours ago, interval is 2 hours)
        mock_exists.return_value = True
        current_time = datetime.now()
        file_mod_time = current_time - timedelta(hours=3)
        mock_getmtime.return_value = file_mod_time.timestamp()
        mock_fetch_data.return_value = fresh_data

        # Execute
        result = wiz.fetch_data_if_needed(
            file_path=file_path, query="query {}", topic_key="test", interval_hours=2, variables=None
        )

        # Verify
        assert result == fresh_data
        mock_fetch_data.assert_called_once_with("query {}", "test", None)
        mock_write_to_file.assert_called_once_with(file_path, fresh_data)
        # Should not load the stale file
        mock_load_file.assert_not_called()

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.write_to_file")
    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.fetch_data")
    @patch("os.path.exists")
    def test_fetch_data_if_needed_fetches_when_no_cache(self, mock_exists, mock_fetch_data, mock_write_to_file):
        """Test that fetch_data_if_needed fetches data when cache doesn't exist."""
        # Setup
        wiz = WizMixin()
        file_path = "artifacts/test_data.json"
        fresh_data = [{"id": "3", "name": "new"}]

        # Mock file doesn't exist
        mock_exists.return_value = False
        mock_fetch_data.return_value = fresh_data

        # Execute
        result = wiz.fetch_data_if_needed(
            file_path=file_path, query="query {}", topic_key="test", interval_hours=2, variables={"key": "value"}
        )

        # Verify
        assert result == fresh_data
        mock_fetch_data.assert_called_once_with("query {}", "test", {"key": "value"})
        mock_write_to_file.assert_called_once_with(file_path, fresh_data)

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.load_file")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_fetch_data_if_needed_with_custom_interval(self, mock_getmtime, mock_exists, mock_load_file):
        """Test fetch_data_if_needed respects custom interval hours."""
        # Setup
        wiz = WizMixin()
        file_path = "artifacts/test_data.json"
        cached_data = [{"id": "4", "name": "cached"}]

        # Mock file exists and is fresh with custom 24 hour interval
        mock_exists.return_value = True
        current_time = datetime.now()
        file_mod_time = current_time - timedelta(hours=12)
        mock_getmtime.return_value = file_mod_time.timestamp()
        mock_load_file.return_value = cached_data

        # Execute with 24 hour interval - should use cache
        result = wiz.fetch_data_if_needed(
            file_path=file_path, query="query {}", topic_key="test", interval_hours=24, variables=None
        )

        # Verify
        assert result == cached_data
        mock_load_file.assert_called_once_with(file_path)


class TestWizMixinWriteToFile:
    """Test write_to_file static method."""

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.check_file_path")
    def test_write_to_file_creates_json(self, mock_check_file_path):
        """Test write_to_file creates valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")
            test_data = [{"id": "1", "name": "test"}, {"id": "2", "name": "test2"}]

            # Execute
            WizMixin.write_to_file(file_path, test_data)

            # Verify
            mock_check_file_path.assert_called_once_with("artifacts")
            assert os.path.exists(file_path)
            with open(file_path, "r") as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.check_file_path")
    def test_write_to_file_empty_list(self, mock_check_file_path):
        """Test write_to_file handles empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "empty.json")
            test_data = []

            # Execute
            WizMixin.write_to_file(file_path, test_data)

            # Verify
            assert os.path.exists(file_path)
            with open(file_path, "r") as f:
                loaded_data = json.load(f)
            assert loaded_data == []

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.check_file_path")
    def test_write_to_file_complex_data(self, mock_check_file_path):
        """Test write_to_file handles complex nested data structures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "complex.json")
            test_data = [
                {"id": "1", "nested": {"key": "value"}, "list": [1, 2, 3]},
                {"id": "2", "nested": {"key2": "value2"}, "list": [4, 5, 6]},
            ]

            # Execute
            WizMixin.write_to_file(file_path, test_data)

            # Verify
            assert os.path.exists(file_path)
            with open(file_path, "r") as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data


class TestWizMixinLoadFile:
    """Test load_file static method."""

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.check_file_path")
    def test_load_file_loads_json(self, mock_check_file_path):
        """Test load_file successfully loads JSON data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")
            test_data = [{"id": "1", "name": "test"}]

            # Create test file
            with open(file_path, "w") as f:
                json.dump(test_data, f)

            # Execute
            result = WizMixin.load_file(file_path)

            # Verify
            mock_check_file_path.assert_called_once_with("artifacts")
            assert result == test_data

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.check_file_path")
    def test_load_file_empty_json(self, mock_check_file_path):
        """Test load_file handles empty JSON array."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "empty.json")

            # Create empty JSON file
            with open(file_path, "w") as f:
                json.dump([], f)

            # Execute
            result = WizMixin.load_file(file_path)

            # Verify
            assert result == []

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.check_file_path")
    def test_load_file_complex_data(self, mock_check_file_path):
        """Test load_file handles complex nested structures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "complex.json")
            test_data = [
                {"id": "1", "nested": {"deep": {"deeper": "value"}}, "list": [1, 2, {"key": "value"}]},
            ]

            # Create test file
            with open(file_path, "w") as f:
                json.dump(test_data, f)

            # Execute
            result = WizMixin.load_file(file_path)

            # Verify
            assert result == test_data


class TestWizMixinFetchData:
    """Test fetch_data method with GraphQL client mocking."""

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.PaginatedGraphQLClient")
    def test_fetch_data_success(self, mock_client_class):
        """Test fetch_data successfully fetches data from Wiz."""
        # Setup
        wiz = WizMixin()
        wiz.config = {"wizUrl": "https://api.wiz.io/graphql", "wizAccessToken": "test-token-123"}

        mock_client = MagicMock()
        mock_client.fetch_all.return_value = [
            {"id": "1", "name": "result1"},
            {"id": "2", "name": "result2"},
        ]
        mock_client_class.return_value = mock_client

        # Execute
        result = wiz.fetch_data(query="query {}", topic_key="test", variables={"key": "value"})

        # Verify
        assert len(result) == 2
        assert result[0]["name"] == "result1"
        assert result[1]["name"] == "result2"

        # Verify client was created with correct parameters
        mock_client_class.assert_called_once_with(
            endpoint="https://api.wiz.io/graphql",
            query="query {}",
            headers={"Content-Type": "application/json", "Authorization": "Bearer test-token-123"},
        )
        mock_client.fetch_all.assert_called_once_with(variables={"key": "value"}, topic_key="test")

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.error_and_exit")
    def test_fetch_data_missing_url_config(self, mock_error_and_exit):
        """Test fetch_data handles missing Wiz URL configuration."""
        # Setup
        wiz = WizMixin()
        wiz.config = {"wizAccessToken": "test-token"}  # Missing wizUrl

        mock_error_and_exit.side_effect = SystemExit(1)

        # Execute & Verify
        with pytest.raises(SystemExit):
            wiz.fetch_data(query="query {}", topic_key="test", variables=None)

        mock_error_and_exit.assert_called_once_with("Wiz API endpoint not configured")

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.error_and_exit")
    def test_fetch_data_empty_url_config(self, mock_error_and_exit):
        """Test fetch_data handles empty Wiz URL configuration."""
        # Setup
        wiz = WizMixin()
        wiz.config = {"wizUrl": "", "wizAccessToken": "test-token"}

        mock_error_and_exit.side_effect = SystemExit(1)

        # Execute & Verify
        with pytest.raises(SystemExit):
            wiz.fetch_data(query="query {}", topic_key="test", variables=None)

        mock_error_and_exit.assert_called_once_with("Wiz API endpoint not configured")

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.PaginatedGraphQLClient")
    def test_fetch_data_no_token_returns_empty(self, mock_client_class):
        """Test fetch_data returns empty list when no access token."""
        # Setup
        wiz = WizMixin()
        wiz.config = {"wizUrl": "https://api.wiz.io/graphql"}  # No token

        # Execute
        result = wiz.fetch_data(query="query {}", topic_key="test", variables=None)

        # Verify
        assert result == []
        mock_client_class.assert_not_called()

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.PaginatedGraphQLClient")
    def test_fetch_data_empty_token_returns_empty(self, mock_client_class):
        """Test fetch_data returns empty list when access token is empty."""
        # Setup
        wiz = WizMixin()
        wiz.config = {"wizUrl": "https://api.wiz.io/graphql", "wizAccessToken": ""}

        # Execute
        result = wiz.fetch_data(query="query {}", topic_key="test", variables=None)

        # Verify
        assert result == []
        mock_client_class.assert_not_called()

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.PaginatedGraphQLClient")
    def test_fetch_data_with_no_variables(self, mock_client_class):
        """Test fetch_data works without variables parameter."""
        # Setup
        wiz = WizMixin()
        wiz.config = {"wizUrl": "https://api.wiz.io/graphql", "wizAccessToken": "token"}

        mock_client = MagicMock()
        mock_client.fetch_all.return_value = [{"id": "1"}]
        mock_client_class.return_value = mock_client

        # Execute
        result = wiz.fetch_data(query="query {}", topic_key="test", variables=None)

        # Verify
        assert len(result) == 1
        mock_client.fetch_all.assert_called_once_with(variables=None, topic_key="test")

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.PaginatedGraphQLClient")
    def test_fetch_data_returns_empty_list_from_client(self, mock_client_class):
        """Test fetch_data handles empty results from GraphQL client."""
        # Setup
        wiz = WizMixin()
        wiz.config = {"wizUrl": "https://api.wiz.io/graphql", "wizAccessToken": "token"}

        mock_client = MagicMock()
        mock_client.fetch_all.return_value = []
        mock_client_class.return_value = mock_client

        # Execute
        result = wiz.fetch_data(query="query {}", topic_key="test", variables=None)

        # Verify
        assert result == []

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.PaginatedGraphQLClient")
    def test_fetch_data_bearer_token_format(self, mock_client_class):
        """Test fetch_data properly formats Bearer token in headers."""
        # Setup
        wiz = WizMixin()
        wiz.config = {"wizUrl": "https://api.wiz.io/graphql", "wizAccessToken": "my-access-token"}

        mock_client = MagicMock()
        mock_client.fetch_all.return_value = []
        mock_client_class.return_value = mock_client

        # Execute
        wiz.fetch_data(query="query {}", topic_key="test", variables=None)

        # Verify Bearer token format
        call_args = mock_client_class.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer my-access-token"

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.PaginatedGraphQLClient")
    def test_fetch_data_content_type_header(self, mock_client_class):
        """Test fetch_data includes correct Content-Type header."""
        # Setup
        wiz = WizMixin()
        wiz.config = {"wizUrl": "https://api.wiz.io/graphql", "wizAccessToken": "token"}

        mock_client = MagicMock()
        mock_client.fetch_all.return_value = []
        mock_client_class.return_value = mock_client

        # Execute
        wiz.fetch_data(query="query {}", topic_key="test", variables=None)

        # Verify Content-Type header
        call_args = mock_client_class.call_args
        assert call_args[1]["headers"]["Content-Type"] == "application/json"


class TestWizMixinEdgeCases:
    """Test edge cases and error scenarios."""

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.write_to_file")
    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.fetch_data")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_fetch_data_if_needed_exactly_at_interval_boundary(
        self, mock_getmtime, mock_exists, mock_fetch_data, mock_write_to_file
    ):
        """Test behavior when file age exactly equals interval."""
        # Setup
        wiz = WizMixin()
        file_path = "artifacts/test.json"
        fresh_data = [{"id": "1"}]

        # Mock file modified exactly 2 hours ago with 2 hour interval
        mock_exists.return_value = True
        current_time = datetime.now()
        file_mod_time = current_time - timedelta(hours=2)
        mock_getmtime.return_value = file_mod_time.timestamp()
        mock_fetch_data.return_value = fresh_data

        # Execute
        result = wiz.fetch_data_if_needed(
            file_path=file_path, query="query {}", topic_key="test", interval_hours=2, variables=None
        )

        # Verify - at boundary, should fetch new data
        assert result == fresh_data
        mock_fetch_data.assert_called_once()
        mock_write_to_file.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.load_file")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_fetch_data_if_needed_very_fresh_file(self, mock_getmtime, mock_exists, mock_load_file):
        """Test with very recently modified file (seconds old)."""
        # Setup
        wiz = WizMixin()
        file_path = "artifacts/test.json"
        cached_data = [{"id": "1"}]

        # Mock file modified 30 seconds ago
        mock_exists.return_value = True
        current_time = datetime.now()
        file_mod_time = current_time - timedelta(seconds=30)
        mock_getmtime.return_value = file_mod_time.timestamp()
        mock_load_file.return_value = cached_data

        # Execute with 1 hour interval
        result = wiz.fetch_data_if_needed(
            file_path=file_path, query="query {}", topic_key="test", interval_hours=1, variables=None
        )

        # Verify - should use cache
        assert result == cached_data
        mock_load_file.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.write_to_file")
    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.WizMixin.fetch_data")
    @patch("os.path.exists")
    def test_fetch_data_if_needed_with_zero_interval(self, mock_exists, mock_fetch_data, mock_write_to_file):
        """Test with zero hour interval (always fetch)."""
        # Setup
        wiz = WizMixin()
        file_path = "artifacts/test.json"
        fresh_data = [{"id": "1"}]

        mock_exists.return_value = False
        mock_fetch_data.return_value = fresh_data

        # Execute with 0 hour interval
        result = wiz.fetch_data_if_needed(
            file_path=file_path, query="query {}", topic_key="test", interval_hours=0, variables=None
        )

        # Verify
        assert result == fresh_data
        mock_fetch_data.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.WizDataMixin.PaginatedGraphQLClient")
    def test_fetch_data_with_complex_variables(self, mock_client_class):
        """Test fetch_data with complex nested variables."""
        # Setup
        wiz = WizMixin()
        wiz.config = {"wizUrl": "https://api.wiz.io/graphql", "wizAccessToken": "token"}

        complex_variables = {
            "filterBy": {"status": ["OPEN", "IN_PROGRESS"], "severity": ["HIGH", "CRITICAL"]},
            "first": 100,
            "orderBy": {"field": "CREATED_AT", "direction": "DESC"},
        }

        mock_client = MagicMock()
        mock_client.fetch_all.return_value = [{"id": "1"}]
        mock_client_class.return_value = mock_client

        # Execute
        result = wiz.fetch_data(query="query {}", topic_key="test", variables=complex_variables)

        # Verify
        assert len(result) == 1
        mock_client.fetch_all.assert_called_once_with(variables=complex_variables, topic_key="test")

    @patch("regscale.core.app.utils.app_utils.check_file_path")
    def test_write_to_file_overwrites_existing(self, mock_check_file_path):
        """Test write_to_file overwrites existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")

            # Write initial data
            initial_data = [{"id": "1", "name": "old"}]
            WizMixin.write_to_file(file_path, initial_data)

            # Overwrite with new data
            new_data = [{"id": "2", "name": "new"}]
            WizMixin.write_to_file(file_path, new_data)

            # Verify only new data exists
            with open(file_path, "r") as f:
                loaded_data = json.load(f)
            assert loaded_data == new_data
            assert len(loaded_data) == 1
