#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test configuration for RegScale integrations."""
import socket
from unittest.mock import MagicMock, patch

import pytest

# Store original socket functions for tests that explicitly need network access
_original_socket_connect = socket.socket.connect
_original_socket_connect_ex = socket.socket.connect_ex


def _block_network_connect(self, address):
    """Block real network connections in tests."""
    host = address[0] if isinstance(address, tuple) else address
    # Allow localhost connections for local testing
    if host in ("localhost", "127.0.0.1", "::1"):
        return _original_socket_connect(self, address)
    raise ConnectionRefusedError(
        f"Network access blocked in tests. Attempted connection to: {address}. "
        "Use proper mocking (e.g., responses, moto, unittest.mock) instead of real network calls."
    )


def _block_network_connect_ex(self, address):
    """Block real network connections in tests (connect_ex variant)."""
    host = address[0] if isinstance(address, tuple) else address
    if host in ("localhost", "127.0.0.1", "::1"):
        return _original_socket_connect_ex(self, address)
    raise ConnectionRefusedError(
        f"Network access blocked in tests. Attempted connection to: {address}. "
        "Use proper mocking instead of real network calls."
    )


@pytest.fixture(scope="session", autouse=True)
def block_real_network_calls():
    """
    Block all real network calls during tests to prevent hanging.

    This fixture prevents tests from making real HTTP/HTTPS requests that could:
    - Hang indefinitely waiting for timeouts
    - Make tests flaky due to network issues
    - Accidentally hit production APIs

    Tests should use proper mocking libraries:
    - `moto` for AWS services
    - `responses` for HTTP requests
    - `unittest.mock.patch` for specific functions
    """
    socket.socket.connect = _block_network_connect
    socket.socket.connect_ex = _block_network_connect_ex
    yield
    # Restore original functions after all tests
    socket.socket.connect = _original_socket_connect
    socket.socket.connect_ex = _original_socket_connect_ex


@pytest.fixture(autouse=True)
def mock_scanner_api_calls():
    """
    Automatically mock all API calls during scanner initialization.

    This fixture runs automatically for all tests in this directory and subdirectories.
    It prevents slow HTTP requests to localhost:4200 and external APIs during test setup.
    """
    with patch("regscale.integrations.scanner_integration.Application") as mock_app:
        with patch("regscale.integrations.scanner_integration.APIHandler") as mock_api:
            with patch(
                "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_label_map_by_parent"
            ) as mock_control_label:
                with patch(
                    "regscale.integrations.scanner_integration.regscale_models.Issue.get_open_issues_ids_by_implementation_id"
                ) as mock_open_issues:
                    with patch(
                        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_id_map_by_parent"
                    ) as mock_control_id:
                        with patch("regscale.integrations.scanner_integration.pull_cisa_kev") as mock_kev:
                            # Configure mocks
                            mock_app.return_value = MagicMock()
                            mock_api_handler = MagicMock()
                            mock_api_handler.regscale_version = "1.0.0"
                            mock_api.return_value = mock_api_handler
                            mock_control_label.return_value = {}
                            mock_open_issues.return_value = {}
                            mock_control_id.return_value = {}
                            mock_kev.return_value = {}
                            yield


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "stress: mark test as a stress test (requires --stress flag to run)")
    # Note: Global timeout is now 90 seconds (1 min 30 sec) via pytest.ini
    # This prevents infinite loops and memory crashes during integration testing


def pytest_addoption(parser):
    """Add command line options to pytest."""
    parser.addoption(
        "--stress",
        action="store_true",
        default=False,
        help="Run stress tests (tests that generate and process large amounts of data)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip stress tests unless --stress option is specified."""
    if not config.getoption("--stress"):
        skip_stress = pytest.mark.skip(reason="Need --stress option to run")
        for item in items:
            if "stress" in item.keywords:
                item.add_marker(skip_stress)
