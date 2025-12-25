#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""File operations module for Wiz integration - handles caching and file I/O."""

import datetime
import json
import logging
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

from regscale.core.app.utils.app_utils import check_file_path

logger = logging.getLogger("regscale")


class FileOperations:
    """Handles file operations for Wiz integration including caching and data persistence."""

    @staticmethod
    def load_json_file(file_path: str) -> Optional[Any]:
        """
        Load data from a JSON file.

        :param str file_path: Path to JSON file
        :return: Loaded data or None if file doesn't exist or is invalid
        :rtype: Optional[Any]
        """
        if not os.path.exists(file_path):
            logger.debug(f"File does not exist: {file_path}")
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
            return None

    @staticmethod
    def save_json_file(data: Any, file_path: str, create_dir: bool = True) -> bool:
        """
        Save data to a JSON file.

        :param Any data: Data to save
        :param str file_path: Path to save file
        :param bool create_dir: Whether to create parent directory if needed
        :return: True if successful, False otherwise
        :rtype: bool
        """
        try:
            if create_dir:
                check_file_path(os.path.dirname(file_path))

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

            logger.debug(f"Saved data to {file_path}")
            return True

        except Exception as e:
            logger.warning(f"Failed to save data to {file_path}: {e}")
            return False

    @staticmethod
    def get_file_age(file_path: str) -> Optional[datetime.timedelta]:
        """
        Get the age of a file as a timedelta.

        :param str file_path: Path to file
        :return: File age or None if file doesn't exist
        :rtype: Optional[datetime.timedelta]
        """
        if not os.path.exists(file_path):
            return None

        try:
            file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            current_time = datetime.datetime.now()
            return current_time - file_mod_time
        except OSError as e:
            logger.warning(f"Error getting file age for {file_path}: {e}")
            return None

    @staticmethod
    def is_cache_valid(file_path: str, max_age_hours: float = 8) -> bool:
        """
        Check if a cache file is valid (exists and not too old).

        :param str file_path: Path to cache file
        :param float max_age_hours: Maximum age in hours before cache is invalid
        :return: True if cache is valid, False otherwise
        :rtype: bool
        """
        file_age = FileOperations.get_file_age(file_path)
        if file_age is None:
            return False

        max_age = datetime.timedelta(hours=max_age_hours)
        return file_age < max_age

    @staticmethod
    def load_cache_or_fetch(
        file_path: str,
        fetch_fn: Callable[[], Any],
        max_age_hours: float = 8,
        save_cache: bool = True,
    ) -> Any:
        """
        Load data from cache if valid, otherwise fetch and optionally cache.

        :param str file_path: Path to cache file
        :param Callable fetch_fn: Function to call to fetch fresh data
        :param float max_age_hours: Maximum cache age in hours
        :param bool save_cache: Whether to save fetched data to cache
        :return: Data from cache or freshly fetched
        :rtype: Any
        """
        # Try to load from cache if valid
        if FileOperations.is_cache_valid(file_path, max_age_hours):
            logger.info(f"Using cached data from {file_path} (newer than {max_age_hours} hours)")
            cached_data = FileOperations.load_json_file(file_path)
            if cached_data is not None:
                return cached_data

        # Cache invalid or doesn't exist - fetch fresh data
        file_age = FileOperations.get_file_age(file_path)
        if file_age:
            logger.info(
                f"Cache file {file_path} is {file_age.total_seconds() / 3600:.1f} hours old - fetching new data"
            )
        else:
            logger.info(f"Cache file {file_path} does not exist - fetching new data")

        data = fetch_fn()

        # Save to cache if requested
        if save_cache:
            FileOperations.save_json_file(data, file_path)

        return data

    @staticmethod
    def search_json_files(
        identifier: str,
        file_paths: List[str],
        match_fn: Callable[[Dict, str], bool],
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Search for an item across multiple JSON files.

        :param str identifier: Identifier to search for
        :param List[str] file_paths: List of file paths to search
        :param Callable match_fn: Function to determine if an item matches (takes item and identifier)
        :return: Tuple of (found_item, source_file) or (None, None)
        :rtype: Tuple[Optional[Dict], Optional[str]]
        """
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue

            try:
                result = FileOperations.search_single_json_file(identifier, file_path, match_fn)
                if result:
                    return result, file_path
            except Exception as e:
                logger.debug(f"Error searching {file_path}: {e}")
                continue

        return None, None

    @staticmethod
    def search_single_json_file(
        identifier: str,
        file_path: str,
        match_fn: Callable[[Dict, str], bool],
    ) -> Optional[Dict]:
        """
        Search for an item in a single JSON file.

        :param str identifier: Identifier to search for
        :param str file_path: Path to JSON file
        :param Callable match_fn: Function to determine if an item matches
        :return: Matched item or None
        :rtype: Optional[Dict]
        """
        logger.debug(f"Searching for {identifier} in {file_path}")

        data = FileOperations.load_json_file(file_path)
        if not isinstance(data, list):
            return None

        # Use generator for memory efficiency
        return next((item for item in data if match_fn(item, identifier)), None)

    @staticmethod
    def load_cached_findings(
        query_configs: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None,
    ) -> List[Tuple[str, List[Dict], Optional[Exception]]]:
        """
        Load cached findings from multiple files.

        :param List[Dict[str, Any]] query_configs: Query configurations with file paths
        :param Optional[Callable] progress_callback: Optional progress callback
        :return: List of (query_type, nodes, error) tuples
        :rtype: List[Tuple[str, List[Dict], Optional[Exception]]]
        """
        results = []

        for config in query_configs:
            query_type = config["type"].value
            file_path = config.get("file_path")

            if progress_callback:
                progress_callback(query_type, "loading")

            try:
                if file_path and os.path.exists(file_path):
                    nodes = FileOperations.load_json_file(file_path)
                    if nodes is not None:
                        logger.info(f"Loaded {len(nodes)} cached {query_type} findings from {file_path}")
                        results.append((query_type, nodes, None))
                    else:
                        logger.warning(f"Failed to load cached data for {query_type}")
                        results.append((query_type, [], Exception(f"Failed to load {file_path}")))
                else:
                    logger.warning(f"No cached data found for {query_type} at {file_path}")
                    results.append((query_type, [], None))

            except Exception as e:
                logger.error(f"Error loading cached data for {query_type}: {e}")
                results.append((query_type, [], e))

            if progress_callback:
                progress_callback(query_type, "loaded")

        return results
