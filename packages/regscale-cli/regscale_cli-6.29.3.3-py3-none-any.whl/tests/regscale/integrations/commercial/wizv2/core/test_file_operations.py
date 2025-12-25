#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for FileOperations module.

Tests cover:
- JSON file loading and saving with all edge cases
- Cache validation by file age
- Load cache or fetch pattern with various scenarios
- Multi-file search operations
- Error handling and boundary conditions
- load_cached_findings with progress callbacks
"""

import datetime
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open
from enum import Enum

import pytest

from regscale.integrations.commercial.wizv2.core.file_operations import FileOperations


PATH = "regscale.integrations.commercial.wizv2.core.file_operations"


class TestFileOperationsJSONLoading:
    """Test JSON file loading operations."""

    def test_load_json_file_success(self):
        """Test successful loading of JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
            json.dump(test_data, f)
            temp_path = f.name

        try:
            loaded_data = FileOperations.load_json_file(temp_path)
            assert loaded_data == test_data
        finally:
            os.unlink(temp_path)

    def test_load_json_file_nonexistent(self):
        """Test loading nonexistent file returns None."""
        result = FileOperations.load_json_file("/nonexistent/path/file.json")
        assert result is None

    def test_load_json_file_invalid_json(self):
        """Test loading invalid JSON returns None."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            f.write("not valid json{[")
            temp_path = f.name

        try:
            result = FileOperations.load_json_file(temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)

    def test_load_json_file_empty_file(self):
        """Test loading empty file returns None."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            f.write("")
            temp_path = f.name

        try:
            result = FileOperations.load_json_file(temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)

    @patch(f"{PATH}.open", side_effect=OSError("Permission denied"))
    @patch(f"{PATH}.os.path.exists", return_value=True)
    def test_load_json_file_oserror(self, mock_exists, mock_file_open):
        """Test OSError during file loading returns None."""
        result = FileOperations.load_json_file("/test/path.json")
        assert result is None

    def test_load_json_file_complex_data(self):
        """Test loading complex nested JSON structures."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            test_data = {
                "nested": {"deeply": {"nested": {"data": [1, 2, 3]}}},
                "list_of_dicts": [{"a": 1}, {"b": 2}, {"c": 3}],
                "null_value": None,
                "boolean": True,
            }
            json.dump(test_data, f)
            temp_path = f.name

        try:
            loaded_data = FileOperations.load_json_file(temp_path)
            assert loaded_data == test_data
        finally:
            os.unlink(temp_path)


class TestFileOperationsJSONSaving:
    """Test JSON file saving operations."""

    def test_save_json_file_success(self):
        """Test successful saving of JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")
            test_data = {"key": "value", "number": 42}

            success = FileOperations.save_json_file(test_data, file_path)
            assert success is True
            assert os.path.exists(file_path)

            loaded = FileOperations.load_json_file(file_path)
            assert loaded == test_data

    def test_save_json_file_creates_directory(self):
        """Test that save_json_file creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "level1", "level2", "test.json")
            test_data = {"nested": True}

            success = FileOperations.save_json_file(test_data, nested_path, create_dir=True)
            assert success is True
            assert os.path.exists(nested_path)

            loaded = FileOperations.load_json_file(nested_path)
            assert loaded == test_data

    def test_save_json_file_without_creating_directory(self):
        """Test save_json_file with create_dir=False on nonexistent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "nonexistent", "test.json")
            test_data = {"test": "data"}

            success = FileOperations.save_json_file(test_data, nested_path, create_dir=False)
            assert success is False
            assert not os.path.exists(nested_path)

    def test_save_json_file_invalid_data(self):
        """Test saving non-serializable data returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")

            class NonSerializable:
                pass

            success = FileOperations.save_json_file({"obj": NonSerializable()}, file_path)
            assert success is False

    def test_save_json_file_empty_data(self):
        """Test saving empty dict and list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Empty dict
            file_path = os.path.join(tmpdir, "empty_dict.json")
            success = FileOperations.save_json_file({}, file_path)
            assert success is True
            loaded = FileOperations.load_json_file(file_path)
            assert loaded == {}

            # Empty list
            file_path = os.path.join(tmpdir, "empty_list.json")
            success = FileOperations.save_json_file([], file_path)
            assert success is True
            loaded = FileOperations.load_json_file(file_path)
            assert loaded == []

    @patch(f"{PATH}.open", side_effect=PermissionError("Permission denied"))
    @patch(f"{PATH}.check_file_path")
    def test_save_json_file_permission_error(self, mock_check_path, mock_file_open):
        """Test permission error during file saving."""
        success = FileOperations.save_json_file({"test": "data"}, "/test/path.json")
        assert success is False

    def test_save_json_file_complex_unicode(self):
        """Test saving data with Unicode characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "unicode.json")
            test_data = {
                "english": "Hello",
                "japanese": "こんにちは",
                "emoji": "🚀🔥",
                "special": "Ñoño",
            }

            success = FileOperations.save_json_file(test_data, file_path)
            assert success is True

            loaded = FileOperations.load_json_file(file_path)
            assert loaded == test_data


class TestFileOperationsFileAge:
    """Test file age calculation operations."""

    def test_get_file_age_existing_file(self):
        """Test getting age of existing file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            age = FileOperations.get_file_age(temp_path)
            assert age is not None
            assert isinstance(age, datetime.timedelta)
            assert age.total_seconds() < 5
        finally:
            os.unlink(temp_path)

    def test_get_file_age_nonexistent(self):
        """Test getting age of nonexistent file returns None."""
        age = FileOperations.get_file_age("/nonexistent/file.json")
        assert age is None

    @patch(f"{PATH}.os.path.exists", return_value=True)
    @patch(f"{PATH}.os.path.getmtime", side_effect=OSError("Permission denied"))
    def test_get_file_age_oserror(self, mock_getmtime, mock_exists):
        """Test OSError during file age calculation returns None."""
        age = FileOperations.get_file_age("/test/path.json")
        assert age is None

    def test_get_file_age_old_file(self):
        """Test getting age of an older file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            # Modify file timestamp to be 2 hours old
            two_hours_ago = time.time() - (2 * 3600)
            os.utime(temp_path, (two_hours_ago, two_hours_ago))

            age = FileOperations.get_file_age(temp_path)
            assert age is not None
            assert age.total_seconds() >= 7000  # At least ~2 hours
        finally:
            os.unlink(temp_path)


class TestFileOperationsCacheValidation:
    """Test cache validation operations."""

    def test_is_cache_valid_fresh_file(self):
        """Test cache validation for fresh file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('{"fresh": true}')
            temp_path = f.name

        try:
            is_valid = FileOperations.is_cache_valid(temp_path, max_age_hours=1)
            assert is_valid is True
        finally:
            os.unlink(temp_path)

    def test_is_cache_valid_nonexistent(self):
        """Test cache validation for nonexistent file."""
        is_valid = FileOperations.is_cache_valid("/nonexistent/cache.json", max_age_hours=1)
        assert is_valid is False

    def test_is_cache_valid_old_file(self):
        """Test cache validation for file older than max age."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('{"old": true}')
            temp_path = f.name

        try:
            # Modify file timestamp to be 10 hours old
            ten_hours_ago = time.time() - (10 * 3600)
            os.utime(temp_path, (ten_hours_ago, ten_hours_ago))

            is_valid = FileOperations.is_cache_valid(temp_path, max_age_hours=1)
            assert is_valid is False
        finally:
            os.unlink(temp_path)

    def test_is_cache_valid_exact_boundary(self):
        """Test cache validation at exact boundary condition."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('{"boundary": true}')
            temp_path = f.name

        try:
            # Set file to be just under 1 hour old
            almost_one_hour_ago = time.time() - (3599)  # 59 minutes 59 seconds
            os.utime(temp_path, (almost_one_hour_ago, almost_one_hour_ago))

            is_valid = FileOperations.is_cache_valid(temp_path, max_age_hours=1)
            assert is_valid is True
        finally:
            os.unlink(temp_path)

    def test_is_cache_valid_custom_max_age(self):
        """Test cache validation with custom max age."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('{"custom": true}')
            temp_path = f.name

        try:
            # File is fresh, should be valid for any reasonable max age
            assert FileOperations.is_cache_valid(temp_path, max_age_hours=0.001) is True
            assert FileOperations.is_cache_valid(temp_path, max_age_hours=24) is True
            assert FileOperations.is_cache_valid(temp_path, max_age_hours=168) is True  # 1 week
        finally:
            os.unlink(temp_path)


class TestFileOperationsLoadCacheOrFetch:
    """Test load_cache_or_fetch pattern."""

    def test_load_cache_or_fetch_uses_valid_cache(self):
        """Test that load_cache_or_fetch uses valid cache."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({"cached": True}, f)
            temp_path = f.name

        try:
            fetch_called = False

            def fetch_fn():
                nonlocal fetch_called
                fetch_called = True
                return {"fetched": True}

            result = FileOperations.load_cache_or_fetch(
                file_path=temp_path, fetch_fn=fetch_fn, max_age_hours=1, save_cache=False
            )

            assert result == {"cached": True}
            assert fetch_called is False
        finally:
            os.unlink(temp_path)

    def test_load_cache_or_fetch_fetches_when_no_cache(self):
        """Test that load_cache_or_fetch fetches when cache doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.json")

            def fetch_fn():
                return {"fetched": True}

            result = FileOperations.load_cache_or_fetch(
                file_path=cache_path, fetch_fn=fetch_fn, max_age_hours=1, save_cache=True
            )

            assert result == {"fetched": True}
            assert os.path.exists(cache_path)

            cached_data = FileOperations.load_json_file(cache_path)
            assert cached_data == {"fetched": True}

    def test_load_cache_or_fetch_invalid_cache(self):
        """Test fetch when cache is invalid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "old_cache.json")

            # Create old cache file
            with open(cache_path, "w") as f:
                json.dump({"old": True}, f)

            # Make it old
            ten_hours_ago = time.time() - (10 * 3600)
            os.utime(cache_path, (ten_hours_ago, ten_hours_ago))

            def fetch_fn():
                return {"fresh": True}

            result = FileOperations.load_cache_or_fetch(
                file_path=cache_path, fetch_fn=fetch_fn, max_age_hours=1, save_cache=True
            )

            assert result == {"fresh": True}

            # Verify cache was updated
            cached_data = FileOperations.load_json_file(cache_path)
            assert cached_data == {"fresh": True}

    def test_load_cache_or_fetch_without_saving(self):
        """Test fetch without saving to cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "no_save.json")

            def fetch_fn():
                return {"not_saved": True}

            result = FileOperations.load_cache_or_fetch(
                file_path=cache_path, fetch_fn=fetch_fn, max_age_hours=1, save_cache=False
            )

            assert result == {"not_saved": True}
            assert not os.path.exists(cache_path)

    def test_load_cache_or_fetch_corrupted_cache_refetches(self):
        """Test that corrupted cache triggers refetch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "corrupted.json")

            # Create corrupted cache
            with open(cache_path, "w") as f:
                f.write("invalid json{[")

            def fetch_fn():
                return {"fetched_after_corruption": True}

            result = FileOperations.load_cache_or_fetch(
                file_path=cache_path, fetch_fn=fetch_fn, max_age_hours=1, save_cache=True
            )

            assert result == {"fetched_after_corruption": True}

    def test_load_cache_or_fetch_returns_none_from_load(self):
        """Test when cached file loads but returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "test.json")

            # Create a valid cache file
            with open(cache_path, "w") as f:
                json.dump({"test": "data"}, f)

            fetch_called = False

            def fetch_fn():
                nonlocal fetch_called
                fetch_called = True
                return {"fetched": True}

            # Mock load_json_file to return None even though file is valid
            with patch(f"{PATH}.FileOperations.load_json_file", return_value=None):
                result = FileOperations.load_cache_or_fetch(
                    file_path=cache_path, fetch_fn=fetch_fn, max_age_hours=1, save_cache=True
                )

            assert result == {"fetched": True}
            assert fetch_called is True


class TestFileOperationsSearchSingleFile:
    """Test search_single_json_file operations."""

    def test_search_single_json_file_found(self):
        """Test searching for item in single JSON file - found."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            test_data = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}, {"id": "3", "name": "Charlie"}]
            json.dump(test_data, f)
            temp_path = f.name

        try:

            def match_fn(item, identifier):
                return item.get("id") == identifier

            result = FileOperations.search_single_json_file("2", temp_path, match_fn)
            assert result is not None
            assert result["name"] == "Bob"
        finally:
            os.unlink(temp_path)

    def test_search_single_json_file_not_found(self):
        """Test searching for item in single JSON file - not found."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            test_data = [{"id": "1", "name": "Alice"}]
            json.dump(test_data, f)
            temp_path = f.name

        try:

            def match_fn(item, identifier):
                return item.get("id") == identifier

            result = FileOperations.search_single_json_file("999", temp_path, match_fn)
            assert result is None
        finally:
            os.unlink(temp_path)

    def test_search_single_json_file_empty_list(self):
        """Test searching in empty list returns None."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump([], f)
            temp_path = f.name

        try:

            def match_fn(item, identifier):
                return item.get("id") == identifier

            result = FileOperations.search_single_json_file("1", temp_path, match_fn)
            assert result is None
        finally:
            os.unlink(temp_path)

    def test_search_single_json_file_non_list_data(self):
        """Test searching in non-list data returns None."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({"id": "1", "name": "Not a list"}, f)
            temp_path = f.name

        try:

            def match_fn(item, identifier):
                return item.get("id") == identifier

            result = FileOperations.search_single_json_file("1", temp_path, match_fn)
            assert result is None
        finally:
            os.unlink(temp_path)

    def test_search_single_json_file_nonexistent(self):
        """Test searching nonexistent file returns None."""

        def match_fn(item, identifier):
            return item.get("id") == identifier

        result = FileOperations.search_single_json_file("1", "/nonexistent.json", match_fn)
        assert result is None

    def test_search_single_json_file_first_match(self):
        """Test that search returns first matching item."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            test_data = [
                {"id": "duplicate", "name": "First"},
                {"id": "duplicate", "name": "Second"},
            ]
            json.dump(test_data, f)
            temp_path = f.name

        try:

            def match_fn(item, identifier):
                return item.get("id") == identifier

            result = FileOperations.search_single_json_file("duplicate", temp_path, match_fn)
            assert result is not None
            assert result["name"] == "First"
        finally:
            os.unlink(temp_path)


class TestFileOperationsSearchMultipleFiles:
    """Test search_json_files operations."""

    def test_search_json_files_found_in_first_file(self):
        """Test searching across multiple files - found in first."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "file1.json")
            file2 = os.path.join(tmpdir, "file2.json")

            with open(file1, "w") as f:
                json.dump([{"id": "1", "name": "File1Item"}], f)

            with open(file2, "w") as f:
                json.dump([{"id": "2", "name": "File2Item"}], f)

            def match_fn(item, identifier):
                return item.get("id") == identifier

            result, source_file = FileOperations.search_json_files("1", [file1, file2], match_fn)

            assert result is not None
            assert result["name"] == "File1Item"
            assert source_file == file1

    def test_search_json_files_found_in_second_file(self):
        """Test searching across multiple files - found in second."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "file1.json")
            file2 = os.path.join(tmpdir, "file2.json")

            with open(file1, "w") as f:
                json.dump([{"id": "1", "name": "File1Item"}], f)

            with open(file2, "w") as f:
                json.dump([{"id": "2", "name": "File2Item"}], f)

            def match_fn(item, identifier):
                return item.get("id") == identifier

            result, source_file = FileOperations.search_json_files("2", [file1, file2], match_fn)

            assert result is not None
            assert result["name"] == "File2Item"
            assert source_file == file2

    def test_search_json_files_not_found(self):
        """Test searching across files when item doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "file1.json")

            with open(file1, "w") as f:
                json.dump([{"id": "1"}], f)

            def match_fn(item, identifier):
                return item.get("id") == identifier

            result, source_file = FileOperations.search_json_files("999", [file1], match_fn)

            assert result is None
            assert source_file is None

    def test_search_json_files_with_nonexistent_files(self):
        """Test search gracefully handles nonexistent files."""

        def match_fn(item, identifier):
            return item.get("id") == identifier

        result, source = FileOperations.search_json_files("1", ["/nonexistent1.json", "/nonexistent2.json"], match_fn)

        assert result is None
        assert source is None

    def test_search_json_files_mixed_existing_nonexisting(self):
        """Test search with mix of existing and non-existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "exists.json")

            with open(file1, "w") as f:
                json.dump([{"id": "found", "name": "FoundItem"}], f)

            def match_fn(item, identifier):
                return item.get("id") == identifier

            files = ["/nonexistent.json", file1, "/another_nonexistent.json"]
            result, source_file = FileOperations.search_json_files("found", files, match_fn)

            assert result is not None
            assert result["name"] == "FoundItem"
            assert source_file == file1

    def test_search_json_files_stops_at_first_match(self):
        """Test that search stops at first match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "file1.json")
            file2 = os.path.join(tmpdir, "file2.json")

            # Both files have the same ID but different names
            with open(file1, "w") as f:
                json.dump([{"id": "duplicate", "name": "FirstFile"}], f)

            with open(file2, "w") as f:
                json.dump([{"id": "duplicate", "name": "SecondFile"}], f)

            def match_fn(item, identifier):
                return item.get("id") == identifier

            result, source_file = FileOperations.search_json_files("duplicate", [file1, file2], match_fn)

            assert result is not None
            assert result["name"] == "FirstFile"
            assert source_file == file1

    def test_search_json_files_with_exception_in_file(self):
        """Test search handles exception in one file and continues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "corrupted.json")
            file2 = os.path.join(tmpdir, "valid.json")

            # Create corrupted file
            with open(file1, "w") as f:
                f.write("invalid json{[")

            # Create valid file
            with open(file2, "w") as f:
                json.dump([{"id": "found", "name": "ValidItem"}], f)

            def match_fn(item, identifier):
                return item.get("id") == identifier

            result, source_file = FileOperations.search_json_files("found", [file1, file2], match_fn)

            assert result is not None
            assert result["name"] == "ValidItem"
            assert source_file == file2

    def test_search_json_files_with_exception_during_search(self):
        """Test search handles general exception during search_single_json_file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "test.json")

            # Create valid file
            with open(file1, "w") as f:
                json.dump([{"id": "test"}], f)

            def match_fn(item, identifier):
                return item.get("id") == identifier

            # Mock search_single_json_file to raise exception
            with patch(f"{PATH}.FileOperations.search_single_json_file", side_effect=Exception("Search error")):
                result, source_file = FileOperations.search_json_files("test", [file1], match_fn)

                # Should return None when exception occurs
                assert result is None
                assert source_file is None


class TestFileOperationsLoadCachedFindings:
    """Test load_cached_findings operations."""

    def test_load_cached_findings_success(self):
        """Test successfully loading cached findings from multiple files."""

        class QueryType(Enum):
            ISSUES = "issues"
            VULNERABILITIES = "vulnerabilities"

        with tempfile.TemporaryDirectory() as tmpdir:
            issues_path = os.path.join(tmpdir, "issues.json")
            vulns_path = os.path.join(tmpdir, "vulns.json")

            # Create test files
            with open(issues_path, "w") as f:
                json.dump([{"id": "issue1"}, {"id": "issue2"}], f)

            with open(vulns_path, "w") as f:
                json.dump([{"id": "vuln1"}, {"id": "vuln2"}, {"id": "vuln3"}], f)

            query_configs = [
                {"type": QueryType.ISSUES, "file_path": issues_path},
                {"type": QueryType.VULNERABILITIES, "file_path": vulns_path},
            ]

            results = FileOperations.load_cached_findings(query_configs)

            assert len(results) == 2
            assert results[0][0] == "issues"
            assert len(results[0][1]) == 2
            assert results[0][2] is None
            assert results[1][0] == "vulnerabilities"
            assert len(results[1][1]) == 3
            assert results[1][2] is None

    def test_load_cached_findings_with_progress_callback(self):
        """Test load_cached_findings with progress callback."""

        class QueryType(Enum):
            ISSUES = "issues"

        with tempfile.TemporaryDirectory() as tmpdir:
            issues_path = os.path.join(tmpdir, "issues.json")

            with open(issues_path, "w") as f:
                json.dump([{"id": "issue1"}], f)

            query_configs = [{"type": QueryType.ISSUES, "file_path": issues_path}]

            callback_calls = []

            def progress_callback(query_type, status):
                callback_calls.append((query_type, status))

            results = FileOperations.load_cached_findings(query_configs, progress_callback=progress_callback)

            assert len(results) == 1
            assert len(callback_calls) == 2
            assert callback_calls[0] == ("issues", "loading")
            assert callback_calls[1] == ("issues", "loaded")

    def test_load_cached_findings_file_not_exists(self):
        """Test load_cached_findings when file doesn't exist."""

        class QueryType(Enum):
            ISSUES = "issues"

        query_configs = [{"type": QueryType.ISSUES, "file_path": "/nonexistent/issues.json"}]

        results = FileOperations.load_cached_findings(query_configs)

        assert len(results) == 1
        assert results[0][0] == "issues"
        assert results[0][1] == []
        assert results[0][2] is None

    def test_load_cached_findings_missing_file_path(self):
        """Test load_cached_findings with missing file_path in config."""

        class QueryType(Enum):
            ISSUES = "issues"

        query_configs = [{"type": QueryType.ISSUES}]

        results = FileOperations.load_cached_findings(query_configs)

        assert len(results) == 1
        assert results[0][0] == "issues"
        assert results[0][1] == []
        assert results[0][2] is None

    def test_load_cached_findings_none_file_path(self):
        """Test load_cached_findings with None file_path."""

        class QueryType(Enum):
            ISSUES = "issues"

        query_configs = [{"type": QueryType.ISSUES, "file_path": None}]

        results = FileOperations.load_cached_findings(query_configs)

        assert len(results) == 1
        assert results[0][0] == "issues"
        assert results[0][1] == []
        assert results[0][2] is None

    def test_load_cached_findings_load_returns_none(self):
        """Test load_cached_findings when load_json_file returns None."""

        class QueryType(Enum):
            ISSUES = "issues"

        with tempfile.TemporaryDirectory() as tmpdir:
            issues_path = os.path.join(tmpdir, "corrupted.json")

            # Create corrupted file
            with open(issues_path, "w") as f:
                f.write("invalid json{[")

            query_configs = [{"type": QueryType.ISSUES, "file_path": issues_path}]

            results = FileOperations.load_cached_findings(query_configs)

            assert len(results) == 1
            assert results[0][0] == "issues"
            assert results[0][1] == []
            assert isinstance(results[0][2], Exception)

    def test_load_cached_findings_exception_handling(self):
        """Test load_cached_findings handles exceptions during loading."""

        class QueryType(Enum):
            ISSUES = "issues"

        query_configs = [{"type": QueryType.ISSUES, "file_path": "/some/path.json"}]

        with patch(f"{PATH}.os.path.exists", side_effect=Exception("Unexpected error")):
            results = FileOperations.load_cached_findings(query_configs)

            assert len(results) == 1
            assert results[0][0] == "issues"
            assert results[0][1] == []
            assert isinstance(results[0][2], Exception)
            assert "Unexpected error" in str(results[0][2])

    def test_load_cached_findings_multiple_mixed_results(self):
        """Test load_cached_findings with mix of success, missing, and error."""

        class QueryType(Enum):
            ISSUES = "issues"
            VULNERABILITIES = "vulnerabilities"
            ASSETS = "assets"

        with tempfile.TemporaryDirectory() as tmpdir:
            issues_path = os.path.join(tmpdir, "issues.json")
            corrupted_path = os.path.join(tmpdir, "corrupted.json")

            # Valid file
            with open(issues_path, "w") as f:
                json.dump([{"id": "issue1"}], f)

            # Corrupted file
            with open(corrupted_path, "w") as f:
                f.write("invalid json")

            query_configs = [
                {"type": QueryType.ISSUES, "file_path": issues_path},
                {"type": QueryType.VULNERABILITIES, "file_path": "/nonexistent.json"},
                {"type": QueryType.ASSETS, "file_path": corrupted_path},
            ]

            results = FileOperations.load_cached_findings(query_configs)

            assert len(results) == 3

            # First should succeed
            assert results[0][0] == "issues"
            assert len(results[0][1]) == 1
            assert results[0][2] is None

            # Second should have empty results (file doesn't exist)
            assert results[1][0] == "vulnerabilities"
            assert results[1][1] == []
            assert results[1][2] is None

            # Third should have error (corrupted file)
            assert results[2][0] == "assets"
            assert results[2][1] == []
            assert isinstance(results[2][2], Exception)


class TestFileOperationsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_file_operations_with_symlinks(self):
        """Test file operations work with symbolic links."""
        with tempfile.TemporaryDirectory() as tmpdir:
            real_file = os.path.join(tmpdir, "real.json")
            symlink_file = os.path.join(tmpdir, "symlink.json")

            # Create real file
            test_data = {"symlink": "test"}
            with open(real_file, "w") as f:
                json.dump(test_data, f)

            # Create symlink
            os.symlink(real_file, symlink_file)

            # Test loading through symlink
            loaded = FileOperations.load_json_file(symlink_file)
            assert loaded == test_data

            # Test file age through symlink
            age = FileOperations.get_file_age(symlink_file)
            assert age is not None

    def test_file_operations_with_very_large_json(self):
        """Test file operations with large JSON data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "large.json")

            # Create large dataset
            large_data = [{"id": i, "data": "x" * 100} for i in range(1000)]

            success = FileOperations.save_json_file(large_data, file_path)
            assert success is True

            loaded = FileOperations.load_json_file(file_path)
            assert len(loaded) == 1000
            assert loaded[0]["id"] == 0
            assert loaded[999]["id"] == 999

    def test_file_operations_with_special_characters_in_path(self):
        """Test file operations with special characters in path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory with special chars
            special_dir = os.path.join(tmpdir, "test-dir_with.special")
            os.makedirs(special_dir)

            file_path = os.path.join(special_dir, "test.json")
            test_data = {"special": "chars"}

            success = FileOperations.save_json_file(test_data, file_path)
            assert success is True

            loaded = FileOperations.load_json_file(file_path)
            assert loaded == test_data

    def test_cache_validation_with_zero_max_age(self):
        """Test cache validation with zero max age."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('{"test": true}')
            temp_path = f.name

        try:
            # Even fresh file should be invalid with 0 max age
            is_valid = FileOperations.is_cache_valid(temp_path, max_age_hours=0)
            assert is_valid is False
        finally:
            os.unlink(temp_path)

    def test_search_with_complex_match_function(self):
        """Test search with complex matching logic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "complex.json")
            test_data = [
                {"id": 1, "tags": ["python", "testing"]},
                {"id": 2, "tags": ["javascript", "frontend"]},
                {"id": 3, "tags": ["python", "backend"]},
            ]

            with open(file_path, "w") as f:
                json.dump(test_data, f)

            def match_fn(item, identifier):
                return identifier in item.get("tags", [])

            result = FileOperations.search_single_json_file("python", file_path, match_fn)
            assert result is not None
            assert result["id"] == 1

    def test_load_cache_or_fetch_with_none_return(self):
        """Test load_cache_or_fetch when fetch_fn returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.json")

            def fetch_fn():
                return None

            result = FileOperations.load_cache_or_fetch(
                file_path=cache_path, fetch_fn=fetch_fn, max_age_hours=1, save_cache=True
            )

            assert result is None
