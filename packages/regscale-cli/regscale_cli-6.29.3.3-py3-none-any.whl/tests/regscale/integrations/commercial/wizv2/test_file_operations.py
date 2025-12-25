#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for FileOperations module.

Tests cover:
- JSON file loading and saving
- Cache validation by file age
- Load cache or fetch pattern
- Multi-file search operations
"""

import datetime
import json
import os
import tempfile
import pytest
from pathlib import Path

from regscale.integrations.commercial.wizv2.core.file_operations import FileOperations


class TestFileOperationsBasics:
    """Test basic file I/O operations."""

    def test_save_and_load_json_file(self):
        """Test saving and loading JSON data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")
            test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}

            # Save data
            success = FileOperations.save_json_file(test_data, file_path)
            assert success is True
            assert os.path.exists(file_path)

            # Load data
            loaded_data = FileOperations.load_json_file(file_path)
            assert loaded_data == test_data

    def test_load_json_file_nonexistent(self):
        """Test loading nonexistent file returns None."""
        result = FileOperations.load_json_file("/nonexistent/path/file.json")
        assert result is None

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


class TestFileOperationsCaching:
    """Test cache-related operations."""

    def test_get_file_age_existing_file(self):
        """Test getting age of existing file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            age = FileOperations.get_file_age(temp_path)
            assert age is not None
            assert isinstance(age, datetime.timedelta)
            assert age.total_seconds() < 5  # Just created, should be very recent
        finally:
            os.unlink(temp_path)

    def test_get_file_age_nonexistent(self):
        """Test getting age of nonexistent file returns None."""
        age = FileOperations.get_file_age("/nonexistent/file.json")
        assert age is None

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

    def test_load_cache_or_fetch_uses_cache(self):
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
            assert fetch_called is False  # Should not fetch when cache is valid
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
            assert os.path.exists(cache_path)  # Should save cache

            # Verify cache was saved correctly
            cached_data = FileOperations.load_json_file(cache_path)
            assert cached_data == {"fetched": True}


class TestFileOperationsSearch:
    """Test file search operations."""

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

    def test_search_json_files_multiple_files(self):
        """Test searching across multiple JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple files
            file1 = os.path.join(tmpdir, "file1.json")
            file2 = os.path.join(tmpdir, "file2.json")
            file3 = os.path.join(tmpdir, "file3.json")

            with open(file1, "w") as f:
                json.dump([{"id": "1", "name": "File1Item"}], f)

            with open(file2, "w") as f:
                json.dump([{"id": "2", "name": "File2Item"}], f)

            with open(file3, "w") as f:
                json.dump([{"id": "3", "name": "File3Item"}], f)

            def match_fn(item, identifier):
                return item.get("id") == identifier

            # Search across all files - should find in file2
            result, source_file = FileOperations.search_json_files("2", [file1, file2, file3], match_fn)

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


class TestFileOperationsEdgeCases:
    """Test edge cases and error handling."""

    def test_save_json_file_invalid_data(self):
        """Test saving non-serializable data returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")

            # Try to save non-serializable data
            class NonSerializable:
                pass

            success = FileOperations.save_json_file({"obj": NonSerializable()}, file_path)
            assert success is False

    def test_load_json_file_invalid_json(self):
        """Test loading invalid JSON returns None."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("not valid json{[")
            temp_path = f.name

        try:
            result = FileOperations.load_json_file(temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)

    def test_search_json_files_with_nonexistent_files(self):
        """Test search gracefully handles nonexistent files."""

        def match_fn(item, identifier):
            return item.get("id") == identifier

        result, source = FileOperations.search_json_files("1", ["/nonexistent1.json", "/nonexistent2.json"], match_fn)

        assert result is None
        assert source is None
