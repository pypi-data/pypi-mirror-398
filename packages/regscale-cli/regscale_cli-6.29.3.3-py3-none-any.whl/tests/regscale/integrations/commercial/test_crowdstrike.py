#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the CrowdStrike integration"""
from falconpy import OAuth2

from regscale.integrations.commercial.crowdstrike import (
    incident_information,
    open_sdk,
    status_information,
)
from tests import CLITestFixture


class TestCrowdstring(CLITestFixture):
    """
    Test for CrowdStrike integration
    """

    AllowedResponses = [200, 401, 403, 429]

    @staticmethod
    def test_bad_creds():
        """Test bad credentials"""
        bad_falcon = OAuth2()
        result = bad_falcon.revoke("Will generate a 403")
        assert result["status_code"] == 403

    def test_incidents(self):
        """Test incidents"""
        assert open_sdk().QueryIncidents(parameters={"limit": 1})["status_code"] in self.AllowedResponses

    @staticmethod
    def test_status_information():
        inc_data = {"status": 30, "tags": ["tag1", "tag2"]}
        expected_output = "[deep_sky_blue1]InProgress[/]\n \n[magenta]tag1[/]\n[magenta]tag2[/]"
        assert status_information(inc_data) == expected_output

    @staticmethod
    def test_incident_information():
        inc_data = {
            "name": "Test Incident",
            "incident_id": "12345:67890:ABCDE",
            "start": "2022-01-01T00:00:00Z",
            "end": "2022-01-02T00:00:00Z",
            "assigned_to": None,
            "description": "This is a test incident description.",
        }
        expected_output = "Test Incident\n[bold]ABCDE[/]\nStart: 2022-01-01 00:00:00Z\n  End: 2022-01-02 00:00:00Z\n \nThis is a test incident description. "
        assert incident_information(inc_data) == expected_output
