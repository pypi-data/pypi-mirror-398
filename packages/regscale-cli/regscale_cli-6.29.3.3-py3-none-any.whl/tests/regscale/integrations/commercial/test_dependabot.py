#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for dependabot alerts integration in RegScale CLI
"""

import sys

import pytest
import requests
from unittest.mock import MagicMock, patch

from tests import CLITestFixture
from regscale.integrations.commercial.dependabot import (
    get_github_dependabot_alerts,
    build_data,
    build_dataframes,
    create_alert_assessment,
    create_alert_issues,
)


class TestDependabot(CLITestFixture):
    """
    Test for dependabot integration
    """

    @pytest.fixture
    def sample_dependabot_data(self):
        """Fixture providing sample dependabot data for multiple tests"""
        return [
            {
                "number": [1],
                "state": ["open"],
                "summary": ["Critical vulnerability in test-package-1"],
                "ecosystem": ["npm"],
                "name": ["test-package-1"],
                "severity": ["high"],
                "published": ["2021-01-01T00:00:00Z"],
                "days_elapsed": [5],
            },
            {
                "number": [2],
                "state": ["open"],
                "summary": ["Medium severity issue in another-package"],
                "ecosystem": ["pip"],
                "name": ["another-package"],
                "severity": ["medium"],
                "published": ["2021-01-02T00:00:00Z"],
                "days_elapsed": [3],
            },
        ]

    @pytest.fixture
    def single_dependabot_data(self):
        """Fixture providing single dependabot data for specific tests"""
        return [
            {
                "number": [1],
                "state": ["open"],
                "summary": ["Critical vulnerability in test-package-1"],
                "ecosystem": ["npm"],
                "name": ["test-package-1"],
                "severity": ["high"],
                "published": ["2021-01-01T00:00:00Z"],
                "days_elapsed": [5],
            }
        ]

    @pytest.fixture
    def mock_api(self):
        """Fixture providing a mock API with common configuration"""
        mock_api = MagicMock()
        mock_api.config = {"userId": "1234", "domain": "https://test.regscale.com"}
        mock_api.logger = MagicMock()
        mock_api.logger.info.return_value = None
        return mock_api

    @pytest.fixture
    def mock_dependabot_api(self):
        """Fixture providing a mock API with dependabot configuration"""
        mock_api = MagicMock()
        mock_api.config = {
            "githubDomain": "test-domain",
            "dependabotOwner": "test-owner",
            "dependabotRepo": "test-repo",
            "dependabotId": "test-id",
            "dependabotToken": "test-token",
        }
        return mock_api

    @pytest.fixture
    def mock_response_success(self):
        """Fixture providing a successful mock response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        return mock_response

    @pytest.fixture
    def mock_response_error(self):
        """Fixture providing an error mock response"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.ok = False
        return mock_response

    @pytest.fixture
    def mock_issue_instance(self):
        """Fixture providing a mock issue instance"""
        mock_issue = MagicMock()
        mock_issue.dict.return_value = {"title": "Dependabot Alert", "description": "Test vulnerability"}
        return mock_issue

    @pytest.fixture
    def mock_assessment_instance(self):
        """Fixture providing a mock assessment instance"""
        mock_assessment = MagicMock()
        mock_assessment.id = 12345
        mock_assessment.create.return_value = mock_assessment
        return mock_assessment

    def test_depend(self):
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
        """Get Dependabot scans"""
        url = "https://api.github.com"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                pytest.skip(f"Github is down. {response.status_code}")
        except Exception:
            pytest.skip("Github is down.")

    @patch("regscale.integrations.commercial.dependabot.requests.get")
    def test_get_github_dependabot_alerts(self, mock_get, mock_dependabot_api):
        """Test get request to dependabot alerts"""
        mock_get.return_value.status_code = 200
        mock_json = MagicMock()
        mock_get.return_value.json.return_value = mock_json

        result = get_github_dependabot_alerts(mock_dependabot_api)
        assert result == mock_json
        mock_get.assert_called_once()

    @patch("regscale.integrations.commercial.dependabot.get_github_dependabot_alerts")
    def test_build_data(self, mock_get_github_dependabot_alerts):
        """Test build data function"""
        mock_get_github_dependabot_alerts.return_value = [
            {
                "number": 1,
                "state": "open",
                "security_advisory": {
                    "summary": "Test Alert",
                    "published_at": "2021-01-01T00:00:00Z",
                },
                "security_vulnerability": {
                    "package": {"ecosystem": "test-ecosystem", "name": "test-name"},
                    "severity": "test-severity",
                },
            },
            {
                "state": "closed",
            },
        ]
        result = build_data(MagicMock())
        assert len(result) == 1

    @patch("regscale.integrations.commercial.dependabot.build_data")
    def test_build_dataframes(self, mock_build_data, sample_dependabot_data):
        """Test build_dataframes function"""
        mock_build_data.return_value = sample_dependabot_data

        mock_api = MagicMock()
        result = build_dataframes(mock_api)

        mock_build_data.assert_called_once_with(api=mock_api)

        # Verify the result is an HTML table
        assert "<table" in result
        assert "<thead>" in result
        assert "<tbody>" in result
        assert "<tr>" in result
        assert "<td>" in result

        # Verify the data is present in the HTML
        assert "test-package-1" in result
        assert "another-package" in result
        assert "high" in result
        assert "medium" in result
        assert "npm" in result
        assert "pip" in result
        assert "Critical vulnerability in test-package-1" in result
        assert "Medium severity issue in another-package" in result

    @patch("regscale.integrations.commercial.dependabot.Assessment.create")
    @patch("regscale.integrations.commercial.dependabot.build_data")
    def test_create_alert_assessment(
        self, mock_build_data, mock_assessment_create, mock_api, sample_dependabot_data, mock_assessment_instance
    ):
        """Test create alert assessment function"""
        mock_build_data.return_value = sample_dependabot_data
        mock_assessment_create.return_value = mock_assessment_instance

        result = create_alert_assessment(mock_api, parent_module="test_module", parent_id=123)

        assert result == 12345
        mock_assessment_create.assert_called_once()

    @patch("regscale.integrations.commercial.dependabot.build_data")
    @patch("regscale.integrations.commercial.dependabot.Assessment.create")
    def test_create_alert_assessment_failure(
        self, mock_assessment_create, mock_build_data, mock_api, sample_dependabot_data
    ):
        """Test the create_alert_assessment function when assessment creation fails"""
        mock_build_data.return_value = sample_dependabot_data
        mock_assessment_create.return_value = None

        result = create_alert_assessment(mock_api)

        assert result is None
        mock_assessment_create.assert_called_once()

    @patch("regscale.integrations.commercial.dependabot.build_data")
    @patch("regscale.integrations.commercial.dependabot.Assessment")
    def test_create_alert_assessment_high_vulnerability(
        self, mock_assessment_class, mock_build_data, mock_api, mock_assessment_instance
    ):
        """Test the create_alert_assessment function with HIGH vulnerability >= 10 days"""
        # Create high vulnerability data
        high_vulnerability_data = [
            {
                "number": [1],
                "state": ["open"],
                "summary": ["Critical vulnerability in test-package-1"],
                "ecosystem": ["npm"],
                "name": ["test-package-1"],
                "severity": ["high"],
                "published": ["2021-01-01T00:00:00Z"],
                "days_elapsed": [15],  # >= 10 days
            }
        ]
        mock_build_data.return_value = high_vulnerability_data
        mock_assessment_class.return_value = mock_assessment_instance

        result = create_alert_assessment(mock_api)

        assert result == 12345
        # Verify that the assessment was created with the correct status and result
        assert mock_assessment_instance.status == "Complete"
        assert mock_assessment_instance.assessmentResult == "Fail"
        assert mock_assessment_instance.actualFinish is not None

    @patch("regscale.integrations.commercial.dependabot.Issue")
    @patch("regscale.integrations.commercial.dependabot.build_data")
    @patch("regscale.integrations.commercial.dependabot.create_alert_assessment")
    def test_create_alert_issues(
        self,
        mock_create_assessment,
        mock_build_data,
        mock_issue_class,
        mock_api,
        mock_issue_instance,
        sample_dependabot_data,
        mock_response_success,
    ):
        """Test the create_alert_issues function with mocked dependencies"""
        mock_create_assessment.return_value = 12345  # assessment_id
        mock_build_data.return_value = sample_dependabot_data
        mock_issue_class.return_value = mock_issue_instance
        mock_api.post.return_value = mock_response_success

        create_alert_issues(mock_api, parent_id=123, parent_module="test_module")

        mock_create_assessment.assert_called_once_with(api=mock_api, parent_id=123, parent_module="test_module")
        mock_build_data.assert_called_once_with(api=mock_api)

        # Verify Issue was created for each vulnerability
        assert mock_issue_class.call_count == 2

        # Verify API post was called for each issue
        assert mock_api.post.call_count == 2

        # Verify the correct endpoint was called
        expected_endpoint = "https://test.regscale.com/api/issues"
        mock_api.post.assert_called_with(expected_endpoint, json=mock_issue_instance.dict())

    @patch("regscale.integrations.commercial.dependabot.Issue")
    @patch("regscale.integrations.commercial.dependabot.build_data")
    @patch("regscale.integrations.commercial.dependabot.create_alert_assessment")
    def test_create_alert_issues_api_failure(
        self,
        mock_create_assessment,
        mock_build_data,
        mock_issue_class,
        mock_api,
        mock_issue_instance,
        single_dependabot_data,
        mock_response_error,
    ):
        """Test the create_alert_issues function when API calls fail"""
        mock_create_assessment.return_value = 12345  # assessment_id
        mock_build_data.return_value = single_dependabot_data
        mock_issue_class.return_value = mock_issue_instance
        mock_api.post.return_value = mock_response_error

        create_alert_issues(mock_api)

        # Verify API post was called
        mock_api.post.assert_called_once()

        # Verify the correct endpoint was called
        expected_endpoint = "https://test.regscale.com/api/issues"
        mock_api.post.assert_called_with(expected_endpoint, json=mock_issue_instance.dict())

    @patch("regscale.integrations.commercial.dependabot.build_data")
    @patch("regscale.integrations.commercial.dependabot.create_alert_assessment")
    def test_create_alert_issues_no_vulnerabilities(self, mock_create_assessment, mock_build_data, mock_api):
        """Test the create_alert_issues function when no vulnerabilities are found"""
        mock_create_assessment.return_value = 12345  # assessment_id
        mock_build_data.return_value = []

        create_alert_issues(mock_api)

        mock_create_assessment.assert_called_once_with(api=mock_api, parent_id=None, parent_module=None)
        mock_build_data.assert_called_once_with(api=mock_api)

        # Verify no API post calls were made (no vulnerabilities)
        mock_api.post.assert_not_called()
