#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for AlienVault OTX integration functions
"""

import unittest.mock as mock
from datetime import datetime
from unittest.mock import MagicMock

import pytest

import regscale.integrations.public.otx as otx
from regscale.integrations.public.otx import (
    create_url,
    extract_id,
    walkapi_iter,
    pulses,
    SUBSCRIBED,
)
from regscale.models.regscale_models import Threat
from tests import CLITestFixture


class TestAlienVaultOTX(CLITestFixture):
    """Test class for AlienVault OTX integration functions."""

    def setup_walkapi_mocks(self, app_config=None):
        """Helper to create consistent walkapi_iter test setup."""
        app = MagicMock()
        app.config = app_config or {"otx": "KEY"}
        app.logger = MagicMock()
        api = MagicMock()
        return app, api

    def get_common_pulse_mocks(self):
        """Get standard mock patches for pulses() tests."""
        return (
            mock.patch.object(Threat, "fetch_all_threats", classmethod(lambda cls: [])),
            mock.patch.object(Threat, "bulk_save", classmethod(lambda cls: None)),
            mock.patch.object(
                otx,
                "Application",
                side_effect=lambda: MagicMock(config={"otx": "KEY", "userId": "testuser"}, logger=MagicMock()),
            ),
            mock.patch.object(otx, "Api", side_effect=lambda: MagicMock()),
        )

    @pytest.mark.parametrize(
        "input_path,kwargs,expected_contains,param_checks",
        [
            ("/pulses", {}, "https://otx.alienvault.com/pulses", []),
            ("/pulses", {"a": 1, "b": "x"}, "https://otx.alienvault.com/pulses?", ["a=1", "b=x"]),
            ("http://example.com/data", {}, "http://example.com/data", []),
            ("http://example.com/data", {"foo": "bar"}, "http://example.com/data?", ["foo=bar"]),
        ],
    )
    def test_create_url(self, input_path, kwargs, expected_contains, param_checks):
        """Test URL creation with various inputs and parameters."""
        result = create_url(input_path, **kwargs)
        assert expected_contains in result
        for param in param_checks:
            assert param in result

    @pytest.mark.parametrize(
        "description,expected_result",
        [
            ("Info AlienVault ID: ABC123 ...", "ABC123 ..."),
            ("no id here", ""),
            ("AlienVault ID: AAA and AlienVault ID: BBB", "AAA and AlienVault ID: BBB"),
            ("AlienVault ID: 12345", "12345"),
        ],
    )
    def test_extract_id(self, description, expected_result):
        """Test ID extraction from various description formats."""
        result = extract_id(description)
        assert result == expected_result

    def test_walkapi_iter_pagination_and_errors(self):
        """Test that walkapi_iter paginates through results and handles authentication failures."""
        page1 = {"count": 3, "results": [{"id": 1}, {"id": 2}], "next": "url2"}
        page2 = {"count": 3, "results": [{"id": 3}], "next": None}
        app, api = self.setup_walkapi_mocks()
        api.get.side_effect = [
            mock.MagicMock(ok=True, json=mock.MagicMock(return_value=page1)),
            mock.MagicMock(ok=True, json=mock.MagicMock(return_value=page2)),
        ]
        items = list(walkapi_iter(app, api, SUBSCRIBED, {"limit": 2}))
        assert [i["id"] for i in items] == [1, 2, 3]
        assert api.get.call_count == 2
        auth_fail = mock.MagicMock(ok=True, json=mock.MagicMock(return_value={"detail": "Authentication required"}))
        api.get.side_effect = [auth_fail]
        with pytest.raises(ValueError):
            next(walkapi_iter(app, api, SUBSCRIBED, {}))

    def test_walkapi_iter_retries_on_error(self):
        """Test that walkapi_iter retries once if API.get raises UnboundLocalError."""
        page = {"count": 1, "results": [{"id": 10}], "next": None}
        app, api = self.setup_walkapi_mocks()
        api.get.side_effect = [
            UnboundLocalError("oops"),
            mock.MagicMock(ok=True, json=mock.MagicMock(return_value=page)),
        ]
        with mock.patch("time.sleep", return_value=None):
            items = list(walkapi_iter(app, api, SUBSCRIBED, {"limit": 1}))
        assert items == page["results"]

    @pytest.mark.parametrize(
        "modified_since,limit,expected_args",
        [
            (datetime(2022, 1, 2, 3, 4, 5), 8, {"limit": 8, "modified_since": "2022-01-02T03:04:05"}),
            (None, 12, {"limit": 12}),
        ],
    )
    def test_pulses_parameter_handling(self, modified_since, limit, expected_args):
        """Test that pulses() correctly handles modified_since parameter."""
        captured = {}

        def fake_walk(app, api, url, args):
            captured.update(args)
            return iter([])

        with mock.patch.object(otx, "walkapi_iter", side_effect=fake_walk), mock.patch.object(
            Threat, "fetch_all_threats", classmethod(lambda cls: [])
        ), mock.patch.object(Threat, "bulk_save", classmethod(lambda cls: None)), mock.patch.object(
            otx, "Application", side_effect=lambda: MagicMock(config={"otx": "KEY", "userId": "u"}, logger=MagicMock())
        ), mock.patch.object(
            otx, "Api", side_effect=lambda: MagicMock()
        ):
            pulses(modified_since, limit)
        assert captured == expected_args

    def run_pulses_test(self, pulse_data, existing_threats=None):
        """Helper to run pulses tests with common setup."""
        created_threats = []

        def mock_threat_create(self, bulk=False):
            created_threats.append(self)
            return self

        threat_patches = list(self.get_common_pulse_mocks())
        with threat_patches[0], threat_patches[1], threat_patches[2], threat_patches[3]:
            with mock.patch.object(otx, "walkapi_iter", return_value=[pulse_data]), mock.patch.object(
                Threat, "fetch_all_threats", classmethod(lambda cls: existing_threats or [])
            ), mock.patch.object(Threat, "create", mock_threat_create):
                pulses(None, 10)

        return created_threats

    def test_pulses_threat_creation(self):
        """Test that pulses() creates threats correctly from API data."""
        sample_pulse = {
            "id": "12345",
            "name": "Test Threat",
            "description": "Test description",
            "created": "2022-01-01T00:00:00",
            "tags": ["malware", "trojan"],
            "references": ["http://example.com"],
        }

        created_threats = self.run_pulses_test(sample_pulse)
        assert len(created_threats) == 1
        threat = created_threats[0]
        assert threat.title == "Test Threat"
        assert threat.description == "Test description\nhttps://otx.alienvault.com/pulse/12345"
        assert "malware, trojan" in threat.notes
        assert "AlienVault ID: 12345" in threat.notes
        assert threat.threatOwnerId == "testuser"

    def test_pulses_deduplication(self):
        """Test that pulses() avoids creating duplicate threats."""
        sample_pulse = {
            "id": "existing123",
            "name": "Test Threat",
            "description": "Test description",
            "created": "2022-01-01T00:00:00",
            "tags": ["malware"],
            "references": [],
        }

        existing_threat = MagicMock()
        existing_threat.notes = "Some notes\nAlienVault ID: existing123"

        created_threats = self.run_pulses_test(sample_pulse, [existing_threat])
        assert len(created_threats) == 0

    def test_walkapi_iter_empty_response(self):
        """Test that walkapi_iter handles empty API responses."""
        empty_page = {"count": 0, "results": [], "next": None}
        app, api = self.setup_walkapi_mocks()
        api.get.return_value = mock.MagicMock(ok=True, json=mock.MagicMock(return_value=empty_page))

        items = list(walkapi_iter(app, api, SUBSCRIBED, {"limit": 10}))
        assert items == []

    def test_walkapi_iter_malformed_response(self):
        """Test that walkapi_iter handles responses missing required fields."""
        malformed_page = {"results": [{"id": 1}]}  # Missing 'count' and 'next'
        app, api = self.setup_walkapi_mocks()
        api.get.return_value = mock.MagicMock(ok=True, json=mock.MagicMock(return_value=malformed_page))

        with pytest.raises(KeyError):
            list(walkapi_iter(app, api, SUBSCRIBED, {"limit": 10}))

    def test_pulses_handles_missing_references(self):
        """Test that pulses() handles API data missing optional references field."""
        minimal_pulse = {
            "id": "minimal123",
            "name": "Minimal Threat",
            "description": "Basic description",
            "created": "2022-01-01T00:00:00",
            "tags": ["minimal"],
            # Missing 'references' - this is actually optional
        }

        created_threats = self.run_pulses_test(minimal_pulse)
        assert len(created_threats) == 1
        threat = created_threats[0]
        assert "minimal \n" in threat.notes  # Tags present, empty references
        assert "AlienVault ID: minimal123" in threat.notes
