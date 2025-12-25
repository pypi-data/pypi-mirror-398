#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Field utility functions for scanner integrations.

This module provides utility functions extracted from scanner_integration.py
for reuse across the RegScale CLI codebase. These functions handle common
operations like thread worker configuration, retry logic with backoff,
due date calculation, configuration overrides, and string hashing.
"""
from __future__ import annotations

import hashlib
import logging
import time
from typing import Any, Callable, Dict, Optional

from regscale.integrations.due_date_handler import DueDateHandler
from regscale.integrations.variables import ScannerVariables
from regscale.models import regscale_models

logger = logging.getLogger("regscale")


def get_thread_workers_max() -> int:
    """
    Get the maximum number of thread workers.

    :return: The maximum number of thread workers
    :rtype: int
    """
    return ScannerVariables.threadMaxWorkers


def _create_config_override(
    config: Optional[Dict[str, Dict]],
    integration_name: str,
    critical: Optional[int],
    high: Optional[int],
    moderate: Optional[int],
    low: Optional[int],
) -> Dict[str, Dict]:
    """
    Create a config override for legacy parameter support.

    :param Optional[Dict[str, Dict]] config: Existing configuration dictionary
    :param str integration_name: Name of the integration
    :param Optional[int] critical: Days until due for critical severity issues
    :param Optional[int] high: Days until due for high severity issues
    :param Optional[int] moderate: Days until due for moderate severity issues
    :param Optional[int] low: Days until due for low severity issues
    :return: Updated configuration dictionary with overrides applied
    :rtype: Dict[str, Dict]
    """
    override_config = config.copy() if config else {}
    if "issues" not in override_config:
        override_config["issues"] = {}
    if integration_name not in override_config["issues"]:
        override_config["issues"][integration_name] = {}

    integration_config = override_config["issues"][integration_name]
    severity_params = {"critical": critical, "high": high, "moderate": moderate, "low": low}

    for param_name, param_value in severity_params.items():
        if param_value is not None:
            integration_config[param_name] = param_value

    return override_config


def _is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable based on error message patterns.

    :param Exception error: The exception to evaluate
    :return: True if the error is retryable, False otherwise
    :rtype: bool
    """
    error_str = str(error)
    has_status_code = "400" in error_str or "500" in error_str
    has_transient_pattern = "Object reference" in error_str or "interrupted" in error_str
    return has_status_code and has_transient_pattern


def _suppress_logger_temporarily(regscale_logger: logging.Logger, should_suppress: bool) -> None:
    """
    Temporarily suppress logger output by setting to CRITICAL level.

    :param logging.Logger regscale_logger: The logger to modify
    :param bool should_suppress: Whether to suppress (True) or not
    """
    if should_suppress:
        regscale_logger.setLevel(logging.CRITICAL)


def _handle_retry_attempt(attempt: int, max_retries: int, retry_delay: float, operation_name: str) -> float:
    """
    Handle retry logging and delay, returning the next delay value.

    :param int attempt: Current attempt number (0-indexed)
    :param int max_retries: Maximum number of retry attempts
    :param float retry_delay: Current delay in seconds
    :param str operation_name: Name of the operation for logging
    :return: Next retry delay (exponentially increased)
    :rtype: float
    """
    logger.debug(
        "Operation '%s' failed due to transient error (attempt %d/%d). Retrying in %.2fs...",
        operation_name,
        attempt + 1,
        max_retries,
        retry_delay,
    )
    time.sleep(retry_delay)
    return retry_delay * 2


def _retry_with_backoff(
    operation: Callable[[], Any],
    operation_name: str,
    max_retries: int = 3,
    initial_delay: float = 0.5,
    suppress_intermediate_logs: bool = True,
) -> Any:
    """
    Execute an operation with exponential backoff retry logic.

    This helper handles transient failures that occur due to eventual consistency
    issues where newly created resources may not be immediately visible to the database.

    :param Callable operation: The operation to execute (no-argument callable)
    :param str operation_name: Name of the operation for logging
    :param int max_retries: Maximum number of retry attempts, defaults to 3
    :param float initial_delay: Initial delay in seconds before first retry, defaults to 0.5
    :param bool suppress_intermediate_logs: Suppress error logs during retries, defaults to True
    :return: The result of the operation if successful
    :raises RuntimeError: If all retry attempts fail
    """
    retry_delay = initial_delay
    regscale_logger = logging.getLogger("regscale")
    original_level = regscale_logger.level

    for attempt in range(max_retries):
        try:
            should_suppress = suppress_intermediate_logs and attempt < max_retries - 1
            _suppress_logger_temporarily(regscale_logger, should_suppress)

            result = operation()
            regscale_logger.setLevel(original_level)

            if attempt > 0:
                logger.info("Operation '%s' succeeded on attempt %d", operation_name, attempt + 1)
            return result

        except Exception as error:
            regscale_logger.setLevel(original_level)

            is_last_attempt = attempt >= max_retries - 1
            if is_last_attempt:
                logger.error("Operation '%s' failed after %d attempts: %s", operation_name, max_retries, error)
                raise

            if _is_retryable_error(error):
                retry_delay = _handle_retry_attempt(attempt, max_retries, retry_delay, operation_name)
            else:
                raise


def issue_due_date(
    severity: regscale_models.IssueSeverity,
    created_date: str,
    critical: Optional[int] = None,
    high: Optional[int] = None,
    moderate: Optional[int] = None,
    low: Optional[int] = None,
    title: Optional[str] = "",
    config: Optional[Dict[str, Dict]] = None,
) -> str:
    """
    Calculate the due date for an issue based on its severity and creation date.

    DEPRECATED: This function is kept for backward compatibility. New code should use DueDateHandler directly.
    This function now uses DueDateHandler internally to ensure consistent behavior and proper validation.

    :param regscale_models.IssueSeverity severity: The severity of the issue.
    :param str created_date: The creation date of the issue.
    :param Optional[int] critical: Days until due for critical severity issues.
    :param Optional[int] high: Days until due for high severity issues.
    :param Optional[int] moderate: Days until due for moderate severity issues.
    :param Optional[int] low: Days until due for low severity issues.
    :param Optional[str] title: The title of the Integration.
    :param Optional[Dict[str, Dict]] config: Configuration options for the due date calculation.
    :return: The due date for the issue.
    :rtype: str
    """
    integration_name = title or "default"

    # Check if individual parameters need config override
    if any(param is not None for param in [critical, high, moderate, low]):
        config = _create_config_override(config, integration_name, critical, high, moderate, low)

    due_date_handler = DueDateHandler(integration_name, config=config)
    return due_date_handler.calculate_due_date(
        severity=severity,
        created_date=created_date,
        cve=None,  # Legacy function doesn't have CVE parameter
        title=title,
    )


def hash_string(input_string: str) -> str:
    """
    Hash a string using SHA-256.

    :param str input_string: The string to hash
    :return: The hashed string as a hexadecimal digest
    :rtype: str
    """
    return hashlib.sha256(input_string.encode()).hexdigest()
