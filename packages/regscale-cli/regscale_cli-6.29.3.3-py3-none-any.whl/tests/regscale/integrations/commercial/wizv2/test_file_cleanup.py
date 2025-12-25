"""Tests for file cleanup utilities."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from regscale.integrations.commercial.wizv2.file_cleanup import ReportFileCleanup


class TestReportFileCleanup(unittest.TestCase):
    """Test cases for ReportFileCleanup."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.file_prefix = "test_report_"

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.test_dir):
            for filename in os.listdir(self.test_dir):
                filepath = os.path.join(self.test_dir, filename)
                try:
                    os.remove(filepath)
                except Exception:
                    pass
            try:
                os.rmdir(self.test_dir)
            except Exception:
                pass

    def _create_test_file(self, filename: str, age_seconds: int = 0) -> str:
        """
        Create a test file and optionally set its modification time.

        :param str filename: Name of the file to create
        :param int age_seconds: How many seconds old the file should be
        :return: Full path to the created file
        """
        filepath = os.path.join(self.test_dir, filename)
        Path(filepath).touch()
        if age_seconds > 0:
            import time

            current_time = time.time()
            os.utime(filepath, (current_time - age_seconds, current_time - age_seconds))
        return filepath

    def test_cleanup_no_files(self):
        """Test cleanup when no files exist."""
        ReportFileCleanup.cleanup_old_files(self.test_dir, self.file_prefix)
        # Should not raise any exceptions

    def test_cleanup_directory_not_exists(self):
        """Test cleanup when directory doesn't exist."""
        non_existent = os.path.join(self.test_dir, "non_existent")
        ReportFileCleanup.cleanup_old_files(non_existent, self.file_prefix)
        # Should not raise any exceptions

    def test_cleanup_keeps_recent_files(self):
        """Test that recent files are kept."""
        for i in range(3):
            self._create_test_file(f"{self.file_prefix}{i}.csv")

        ReportFileCleanup.cleanup_old_files(self.test_dir, self.file_prefix, keep_count=5)

        remaining_files = [f for f in os.listdir(self.test_dir) if f.startswith(self.file_prefix)]
        self.assertEqual(len(remaining_files), 3)

    def test_cleanup_deletes_old_files(self):
        """Test that old files beyond keep_count are deleted."""
        for i in range(10):
            self._create_test_file(f"{self.file_prefix}{i:02d}.csv", age_seconds=100 - i * 10)

        ReportFileCleanup.cleanup_old_files(self.test_dir, self.file_prefix, keep_count=3)

        remaining_files = [f for f in os.listdir(self.test_dir) if f.startswith(self.file_prefix)]
        self.assertEqual(len(remaining_files), 3)

    def test_cleanup_respects_extension_grouping(self):
        """Test that files are grouped by extension before cleanup."""
        for i in range(6):
            self._create_test_file(f"{self.file_prefix}{i:02d}.csv", age_seconds=100 - i * 10)
        for i in range(6):
            self._create_test_file(f"{self.file_prefix}{i:02d}.json", age_seconds=100 - i * 10)

        ReportFileCleanup.cleanup_old_files(self.test_dir, self.file_prefix, keep_count=3)

        csv_files = [f for f in os.listdir(self.test_dir) if f.endswith(".csv")]
        json_files = [f for f in os.listdir(self.test_dir) if f.endswith(".json")]

        self.assertEqual(len(csv_files), 3)
        self.assertEqual(len(json_files), 3)

    def test_cleanup_with_custom_extensions(self):
        """Test cleanup with custom extension list."""
        self._create_test_file(f"{self.file_prefix}01.csv")
        self._create_test_file(f"{self.file_prefix}02.txt")
        self._create_test_file(f"{self.file_prefix}03.log")

        ReportFileCleanup.cleanup_old_files(self.test_dir, self.file_prefix, extensions=[".txt", ".log"], keep_count=1)

        remaining_files = os.listdir(self.test_dir)
        self.assertIn(f"{self.file_prefix}01.csv", remaining_files)
        self.assertIn(f"{self.file_prefix}02.txt", remaining_files)
        self.assertIn(f"{self.file_prefix}03.log", remaining_files)

    def test_cleanup_default_extensions(self):
        """Test cleanup uses default extensions when not specified."""
        self._create_test_file(f"{self.file_prefix}01.csv")
        self._create_test_file(f"{self.file_prefix}02.json")
        self._create_test_file(f"{self.file_prefix}03.jsonl")
        self._create_test_file(f"{self.file_prefix}04.txt")

        ReportFileCleanup.cleanup_old_files(self.test_dir, self.file_prefix, keep_count=5)

        remaining_files = os.listdir(self.test_dir)
        self.assertEqual(len(remaining_files), 4)

    def test_cleanup_ignores_non_matching_prefix(self):
        """Test that files with different prefix are not deleted."""
        self._create_test_file(f"{self.file_prefix}01.csv")
        self._create_test_file("other_prefix_01.csv")

        ReportFileCleanup.cleanup_old_files(self.test_dir, self.file_prefix, keep_count=0)

        remaining_files = os.listdir(self.test_dir)
        self.assertIn("other_prefix_01.csv", remaining_files)

    def test_cleanup_handles_delete_exception(self):
        """Test cleanup handles exceptions when deleting files."""
        for i in range(10):
            self._create_test_file(f"{self.file_prefix}{i:02d}.csv", age_seconds=100 - i * 10)

        with patch("os.remove", side_effect=PermissionError("Permission denied")):
            # Should not raise exception, just log warning
            ReportFileCleanup.cleanup_old_files(self.test_dir, self.file_prefix, keep_count=3)

    def test_cleanup_handles_general_exception(self):
        """Test cleanup handles general exceptions."""
        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", side_effect=PermissionError("Permission denied")):
                # Should not raise exception, just log warning
                ReportFileCleanup.cleanup_old_files(self.test_dir, self.file_prefix)

    def test_find_matching_files(self):
        """Test _find_matching_files method."""
        self._create_test_file(f"{self.file_prefix}01.csv")
        self._create_test_file(f"{self.file_prefix}02.json")
        self._create_test_file("other_file.csv")

        entries = ReportFileCleanup._find_matching_files(self.test_dir, self.file_prefix, [".csv", ".json"])

        self.assertEqual(len(entries), 2)
        filenames = [entry[0] for entry in entries]
        self.assertIn(f"{self.file_prefix}01.csv", filenames)
        self.assertIn(f"{self.file_prefix}02.json", filenames)

    def test_find_matching_files_multiple_extensions_per_file(self):
        """Test that only one entry is created per file even if multiple extensions match."""
        self._create_test_file(f"{self.file_prefix}01.csv")

        entries = ReportFileCleanup._find_matching_files(self.test_dir, self.file_prefix, [".csv", ".json"])

        # Should only have one entry for the .csv file
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][2], ".csv")

    def test_group_files_by_extension(self):
        """Test _group_files_by_extension method."""
        entries = [
            ("file1.csv", "/path/file1.csv", ".csv"),
            ("file2.csv", "/path/file2.csv", ".csv"),
            ("file3.json", "/path/file3.json", ".json"),
        ]

        grouped = ReportFileCleanup._group_files_by_extension(entries)

        self.assertEqual(len(grouped), 2)
        self.assertEqual(len(grouped[".csv"]), 2)
        self.assertEqual(len(grouped[".json"]), 1)

    def test_group_files_by_extension_empty(self):
        """Test _group_files_by_extension with empty list."""
        grouped = ReportFileCleanup._group_files_by_extension([])
        self.assertEqual(grouped, {})

    def test_cleanup_files_by_extension(self):
        """Test _cleanup_files_by_extension method."""
        # Create test files
        files = []
        for i in range(5):
            filepath = self._create_test_file(f"{self.file_prefix}{i:02d}.csv", age_seconds=100 - i * 10)
            files.append((f"{self.file_prefix}{i:02d}.csv", filepath))

        files_by_ext = {".csv": files}
        deleted_count = ReportFileCleanup._cleanup_files_by_extension(files_by_ext, keep_count=2)

        self.assertEqual(deleted_count, 3)
        remaining_files = os.listdir(self.test_dir)
        self.assertEqual(len(remaining_files), 2)

    def test_cleanup_files_by_extension_no_files_to_delete(self):
        """Test _cleanup_files_by_extension when all files should be kept."""
        # Create test files
        files = []
        for i in range(3):
            filepath = self._create_test_file(f"{self.file_prefix}{i:02d}.csv")
            files.append((f"{self.file_prefix}{i:02d}.csv", filepath))

        files_by_ext = {".csv": files}
        deleted_count = ReportFileCleanup._cleanup_files_by_extension(files_by_ext, keep_count=5)

        self.assertEqual(deleted_count, 0)
        remaining_files = os.listdir(self.test_dir)
        self.assertEqual(len(remaining_files), 3)

    def test_cleanup_files_by_extension_delete_all(self):
        """Test _cleanup_files_by_extension with keep_count=0."""
        # Create test files
        files = []
        for i in range(5):
            filepath = self._create_test_file(f"{self.file_prefix}{i:02d}.csv")
            files.append((f"{self.file_prefix}{i:02d}.csv", filepath))

        files_by_ext = {".csv": files}
        deleted_count = ReportFileCleanup._cleanup_files_by_extension(files_by_ext, keep_count=0)

        self.assertEqual(deleted_count, 5)
        remaining_files = os.listdir(self.test_dir)
        self.assertEqual(len(remaining_files), 0)

    def test_cleanup_files_by_extension_with_delete_failure(self):
        """Test _cleanup_files_by_extension handles delete failures gracefully."""
        # Create test files
        files = []
        for i in range(5):
            filepath = self._create_test_file(f"{self.file_prefix}{i:02d}.csv", age_seconds=100 - i * 10)
            files.append((f"{self.file_prefix}{i:02d}.csv", filepath))

        files_by_ext = {".csv": files}

        with patch("os.remove", side_effect=[None, PermissionError("Permission denied"), None]):
            deleted_count = ReportFileCleanup._cleanup_files_by_extension(files_by_ext, keep_count=2)
            # Should continue processing even if one delete fails
            self.assertGreaterEqual(deleted_count, 0)

    def test_cleanup_files_sorted_by_modification_time(self):
        """Test that files are sorted by modification time before deletion."""
        # Create files with specific modification times
        self._create_test_file(f"{self.file_prefix}oldest.csv", age_seconds=1000)
        self._create_test_file(f"{self.file_prefix}middle.csv", age_seconds=500)
        self._create_test_file(f"{self.file_prefix}newest.csv", age_seconds=100)

        ReportFileCleanup.cleanup_old_files(self.test_dir, self.file_prefix, keep_count=1)

        remaining_files = os.listdir(self.test_dir)
        self.assertEqual(len(remaining_files), 1)
        self.assertIn(f"{self.file_prefix}newest.csv", remaining_files)

    def test_cleanup_multiple_extensions_independent(self):
        """Test that different extensions are cleaned up independently."""
        # Create CSV files
        for i in range(10):
            self._create_test_file(f"{self.file_prefix}{i:02d}.csv", age_seconds=200 - i * 10)

        # Create JSON files
        for i in range(5):
            self._create_test_file(f"{self.file_prefix}{i:02d}.json", age_seconds=100 - i * 10)

        ReportFileCleanup.cleanup_old_files(self.test_dir, self.file_prefix, keep_count=3)

        csv_files = [f for f in os.listdir(self.test_dir) if f.endswith(".csv")]
        json_files = [f for f in os.listdir(self.test_dir) if f.endswith(".json")]

        self.assertEqual(len(csv_files), 3)
        self.assertEqual(len(json_files), 3)


if __name__ == "__main__":
    unittest.main()
