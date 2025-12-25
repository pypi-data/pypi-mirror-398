#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for npm audit scan integration in RegScale CLI
"""

import sys

import pytest
import requests

from tests import CLITestFixture


class TestNpmAudit(CLITestFixture):
    """
    Test for npm audit integration
    """

    def test_npm(self):
        """Make sure values are present"""
        self.verify_config(
            [
                "dependabotId",
                "dependabotOwner",
                "dependabotRepo",
                "dependabotToken",
                "domain",
                "githubDomain",
            ],
            compare_template=False,
        )

    def test_github(self):
        """Get NPM Audit scans"""
        url = "https://api.github.com"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                pytest.skip(f"Github is down. {response.status_code}")
        except Exception:
            pytest.skip("Github is down.")
