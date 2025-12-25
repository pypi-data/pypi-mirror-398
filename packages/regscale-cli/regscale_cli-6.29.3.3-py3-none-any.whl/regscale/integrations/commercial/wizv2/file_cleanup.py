#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""File cleanup utilities for Wiz integrations."""

import logging
import os
from typing import List, Tuple

logger = logging.getLogger("regscale")


class ReportFileCleanup:
    """Utility class for cleaning up old report files."""

    @staticmethod
    def cleanup_old_files(directory: str, file_prefix: str, extensions: List[str] = None, keep_count: int = 5) -> None:
        """
        Keep the most recent files matching the pattern, delete older ones.

        :param str directory: Directory containing files to clean
        :param str file_prefix: File name prefix to match (e.g., 'compliance_report_')
        :param List[str] extensions: List of extensions to clean (e.g., ['.csv', '.json']), defaults to None
        :param int keep_count: Number of most recent files per extension to keep, defaults to 5
        :return: None
        :rtype: None
        """
        if extensions is None:
            extensions = [".csv", ".json", ".jsonl"]

        try:
            if not os.path.exists(directory):
                return

            matching_entries = ReportFileCleanup._find_matching_files(directory, file_prefix, extensions)
            files_by_extension = ReportFileCleanup._group_files_by_extension(matching_entries)
            files_deleted = ReportFileCleanup._cleanup_files_by_extension(files_by_extension, keep_count)

            if files_deleted > 0:
                logger.info(f"Cleaned up {files_deleted} old report files from {directory}")

        except Exception as e:
            logger.warning(f"Error during file cleanup in {directory}: {e}")

    @staticmethod
    def _find_matching_files(directory: str, file_prefix: str, extensions: List[str]) -> List[Tuple[str, str, str]]:
        """
        Find all files matching the prefix and extensions.

        :param str directory: Directory to search for files
        :param str file_prefix: File name prefix to match
        :param List[str] extensions: List of file extensions to match
        :return: List of tuples containing (filename, file_path, extension)
        :rtype: List[Tuple[str, str, str]]
        """
        entries = []
        for filename in os.listdir(directory):
            if filename.startswith(file_prefix):
                for ext in extensions:
                    if filename.endswith(ext):
                        file_path = os.path.join(directory, filename)
                        entries.append((filename, file_path, ext))
                        break
        return entries

    @staticmethod
    def _group_files_by_extension(entries: List[Tuple[str, str, str]]) -> dict:
        """
        Group files by their extensions.

        :param List[Tuple[str, str, str]] entries: List of file entries (filename, file_path, extension)
        :return: Dictionary mapping extensions to lists of (filename, file_path) tuples
        :rtype: dict
        """
        by_extension = {}
        for filename, file_path, ext in entries:
            if ext not in by_extension:
                by_extension[ext] = []
            by_extension[ext].append((filename, file_path))
        return by_extension

    @staticmethod
    def _cleanup_files_by_extension(files_by_extension: dict, keep_count: int) -> int:
        """
        Clean up files for each extension, keeping the most recent ones.

        :param dict files_by_extension: Dictionary mapping extensions to lists of (filename, file_path) tuples
        :param int keep_count: Number of most recent files to keep for each extension
        :return: Total number of files deleted
        :rtype: int
        """
        files_deleted = 0

        for ext, files in files_by_extension.items():
            files.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)

            for filename, file_path in files[keep_count:]:
                try:
                    os.remove(file_path)
                    files_deleted += 1
                    logger.debug(f"Deleted old report file: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {filename}: {e}")

        return files_deleted
