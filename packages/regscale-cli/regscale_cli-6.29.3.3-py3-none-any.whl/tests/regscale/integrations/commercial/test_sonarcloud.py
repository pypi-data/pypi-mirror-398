#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for sonarcloud code scan integration in RegScale CLI
"""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from tests import CLITestFixture
from regscale.integrations.commercial.sonarcloud import (
    build_data,
    create_alert_assessment,
    create_alert_issues,
    get_sonarcloud_results,
    build_dataframes,
)


class TestSonarcloud(CLITestFixture):
    """
    Test for sonarcloud integration
    """

    @pytest.fixture
    def sample_vulnerability_data(self):
        """Fixture providing sample vulnerability data for multiple tests"""
        return [
            {
                "key": "test_issue_1",
                "severity": "HIGH",
                "component": "test_component_1",
                "status": "OPEN",
                "message": "Test message 1",
                "creationDate": "2021-01-01T00:00:00",
                "updateDate": "2021-01-01T00:00:00",
                "type": "Vulnerability",
                "days_elapsed": 5,
            },
            {
                "key": "test_issue_2",
                "severity": "LOW",
                "component": "test_component_2",
                "status": "OPEN",
                "message": "Test message 2",
                "creationDate": "2021-01-02T00:00:00",
                "updateDate": "2021-01-02T00:00:00",
                "type": "Vulnerability",
                "days_elapsed": 3,
            },
        ]

    @pytest.fixture
    def single_vulnerability_data(self):
        """Fixture providing single vulnerability data for specific tests"""
        return [
            {
                "key": "test_issue_1",
                "severity": "HIGH",
                "component": "test_component_1",
                "status": "OPEN",
                "message": "Test message 1",
                "creationDate": "2021-01-01T00:00:00",
                "updateDate": "2021-01-01T00:00:00",
                "type": "Vulnerability",
                "days_elapsed": 5,
            }
        ]

    @pytest.fixture
    def mock_api(self):
        """Fixture providing a mock API with common configuration"""
        mock_api = MagicMock()
        mock_api.config = {"sonarToken": "test_token_123", "sonarUrl": "https://sonarcloud.io", "userId": "1234"}
        mock_api.logger = MagicMock()
        mock_api.logger.info.return_value = None
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
    def mock_sonarcloud_issue(self):
        """Fixture providing a mock sonarcloud issue"""
        return {
            "key": "test_issue",
            "name": "Test Issue",
            "description": "This is a test issue",
            "type": "Vulnerability",
            "status": "OPEN",
            "severity": "HIGH",
            "component": "test_component",
            "message": "This is a test message",
            "creationDate": "2021-01-01T00:00:00Z",
            "updateDate": "2021-01-01T00:00:00Z",
            "days_elapsed": 0,
        }

    @pytest.fixture
    def mock_app(self):
        """Fixture providing a mock application"""
        mock_app = MagicMock()
        mock_app.config = {
            "userId": "1234",
            "domain": "https://test.regscale.com",
            "sonarToken": "test_token_123",
            "sonarUrl": "https://sonarcloud.io",
        }
        return mock_app

    @pytest.fixture
    def mock_issue_instance(self):
        """Fixture providing a mock issue instance"""
        mock_issue = MagicMock()
        mock_issue.dict.return_value = {"title": "Sonarcloud Code Scan", "description": "Test message"}
        return mock_issue

    def test_depend(self):
        """Make sure values are present"""
        self.verify_config("sonarToken", compare_template=False)

    def test_sonarcloud(self):
        """Get sonarcloud code scans"""
        url = "https://sonarcloud.io/api/"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                pytest.skip(f"Sonarcloud is down. {response.status_code}")
            assert response.status_code == 200
        except Exception:
            pytest.skip("Sonarcloud is down.")

    @patch("regscale.integrations.commercial.sonarcloud.requests.get")
    def test_get_sonarcloud_results_success(self, mock_get, mock_sonarcloud_issue):
        """Test sonarcloud results pull with a success"""
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.ok = True
        mock_response1.json.return_value = {"paging": {"total": 2, "pageSize": 1}, "issues": [mock_sonarcloud_issue]}

        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.ok = True
        mock_response2.json.return_value = {"issues": [mock_sonarcloud_issue]}

        mock_get.side_effect = [mock_response1, mock_response2]
        results = get_sonarcloud_results(self.config)
        test_results = [mock_sonarcloud_issue] * 2  # Expecting two issues, one from each page
        assert len(results) == 2
        assert results == test_results

    @patch("regscale.integrations.commercial.sonarcloud.requests.get")
    def test_get_sonarcloud_results_error(self, mock_get, mock_response_error):
        """Test sonarcloud results pull with an error"""
        mock_get.return_value = mock_response_error

        with pytest.raises(SystemExit) as e:
            get_sonarcloud_results(self.config)
        assert e.type == SystemExit

    @patch("regscale.integrations.commercial.sonarcloud.requests.get")
    def test_get_sonarcloud_results_empty(self, mock_get):
        """Test sonarcloud results when no issues are found"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "paging": {"total": 0, "pageSize": 500},
            "issues": [],
        }
        mock_get.return_value = mock_response

        results = get_sonarcloud_results(self.config)
        assert len(results) == 0

    @patch("regscale.integrations.commercial.sonarcloud.get_sonarcloud_results")
    def test_build_data(self, mock_get_sonarcloud_results, mock_api, mock_sonarcloud_issue):
        """Test the build_data function"""
        mock_get_sonarcloud_results.return_value = [mock_sonarcloud_issue]
        results = build_data(mock_api)
        assert len(results) == 1
        assert results[0]["key"] == "test_issue"

    @patch("regscale.integrations.commercial.sonarcloud.get_sonarcloud_results")
    def test_build_data_empty(self, mock_get_sonarcloud_results, mock_api):
        """Test the build_data function when no issues are found"""
        mock_get_sonarcloud_results.return_value = []
        results = build_data(mock_api)
        assert len(results) == 0
        assert results == []

    def test_build_dataframes(self, sample_vulnerability_data):
        """Test the build_dataframes function"""
        result = build_dataframes(sample_vulnerability_data)

        assert "<table" in result
        assert "test_issue_1" in result
        assert "test_issue_2" in result
        assert "HIGH" in result
        assert "LOW" in result

        # Should be sorted by severity (HIGH should come before LOW)
        high_index = result.find("HIGH")
        low_index = result.find("LOW")
        assert high_index < low_index

    @patch("regscale.integrations.commercial.sonarcloud.Assessment.create")
    def test_create_alert_assessment(self, mock_assessment_create, mock_api, sample_vulnerability_data):
        """Test the create_alert_assessment function"""
        mock_assessment_create.return_value = MagicMock(id=12345)

        result = create_alert_assessment(
            sample_vulnerability_data, mock_api, parent_id=123, parent_module="test_module"
        )

        assert result is not None
        mock_assessment_create.assert_called_once()

    @patch("regscale.integrations.commercial.sonarcloud.Assessment.create")
    def test_create_alert_assessment_failure(self, mock_assessment_create, mock_api, sample_vulnerability_data):
        """Test the create_alert_assessment function when assessment creation fails"""
        mock_assessment_create.return_value = None

        result = create_alert_assessment(sample_vulnerability_data, mock_api)

        assert result is None
        mock_assessment_create.assert_called_once()

    @patch("regscale.integrations.commercial.sonarcloud.Assessment")
    def test_create_alert_assessment_critical_vulnerability(self, mock_assessment_class, mock_api):
        """Test the create_alert_assessment function with CRITICAL vulnerability >= 10 days"""
        # Create critical vulnerability data
        critical_data = [
            {
                "key": "test_issue_1",
                "severity": "CRITICAL",
                "component": "test_component_1",
                "status": "OPEN",
                "message": "Test message 1",
                "creationDate": "2021-01-01T00:00:00",
                "updateDate": "2021-01-01T00:00:00",
                "type": "Vulnerability",
                "days_elapsed": 15,  # >= 10 days
            }
        ]

        # Create a mock assessment instance
        mock_assessment_instance = MagicMock()
        mock_assessment_instance.id = 12345
        mock_assessment_instance.create.return_value = mock_assessment_instance
        mock_assessment_class.return_value = mock_assessment_instance

        result = create_alert_assessment(critical_data, mock_api)

        assert result == 12345
        # Verify that the assessment was created with the correct status and result
        assert mock_assessment_instance.status == "Complete"
        assert mock_assessment_instance.assessmentResult == "Fail"
        assert mock_assessment_instance.actualFinish is not None

    @patch("regscale.integrations.commercial.sonarcloud.logger")
    @patch("regscale.integrations.commercial.sonarcloud.Issue")
    @patch("regscale.integrations.commercial.sonarcloud.build_data")
    @patch("regscale.integrations.commercial.sonarcloud.create_alert_assessment")
    @patch("regscale.integrations.commercial.sonarcloud.Api")
    @patch("regscale.integrations.commercial.sonarcloud.Application")
    def test_create_alert_issues(
        self,
        mock_app_class,
        mock_api_class,
        mock_create_assessment,
        mock_build_data,
        mock_issue_class,
        mock_logger,
        mock_app,
        mock_issue_instance,
        sample_vulnerability_data,
        mock_response_success,
    ):
        """Test the create_alert_issues function with mocked dependencies"""
        mock_app_class.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_create_assessment.return_value = 12345  # assessment_id
        mock_build_data.return_value = sample_vulnerability_data

        mock_issue_class.return_value = mock_issue_instance
        mock_api.post.return_value = mock_response_success

        create_alert_issues(parent_id=123, parent_module="test_module")

        mock_create_assessment.assert_called_once_with(
            sonar_data=sample_vulnerability_data, api=mock_api, parent_id=123, parent_module="test_module"
        )
        mock_build_data.assert_called_once_with(mock_api, None)

        # Verify Issue was created for each vulnerability
        assert mock_issue_class.call_count == 2

        # Verify API post was called for each issue
        assert mock_api.post.call_count == 2

        # Verify successful logging
        assert mock_logger.info.call_count == 2
        mock_logger.info.assert_any_call("Issue created successfully.")

    @patch("regscale.integrations.commercial.sonarcloud.logger")
    @patch("regscale.integrations.commercial.sonarcloud.Issue")
    @patch("regscale.integrations.commercial.sonarcloud.build_data")
    @patch("regscale.integrations.commercial.sonarcloud.create_alert_assessment")
    @patch("regscale.integrations.commercial.sonarcloud.Api")
    @patch("regscale.integrations.commercial.sonarcloud.Application")
    def test_create_alert_issues_api_failure(
        self,
        mock_app_class,
        mock_api_class,
        mock_create_assessment,
        mock_build_data,
        mock_issue_class,
        mock_logger,
        mock_app,
        mock_issue_instance,
        single_vulnerability_data,
        mock_response_error,
    ):
        """Test the create_alert_issues function when API calls fail"""
        mock_app_class.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_create_assessment.return_value = 12345  # assessment_id
        mock_build_data.return_value = single_vulnerability_data

        mock_issue_class.return_value = mock_issue_instance
        mock_api.post.return_value = mock_response_error

        create_alert_issues()

        # Verify API post was called
        mock_api.post.assert_called_once()

        # Verify failure logging
        mock_logger.info.assert_called_once_with("Issue was not created.")

    @patch("regscale.integrations.commercial.sonarcloud.logger")
    @patch("regscale.integrations.commercial.sonarcloud.build_data")
    @patch("regscale.integrations.commercial.sonarcloud.create_alert_assessment")
    @patch("regscale.integrations.commercial.sonarcloud.Api")
    @patch("regscale.integrations.commercial.sonarcloud.Application")
    def test_create_alert_issues_no_vulnerabilities(
        self, mock_app_class, mock_api_class, mock_create_assessment, mock_build_data, mock_logger, mock_app
    ):
        """Test the create_alert_issues function when no vulnerabilities are found"""
        mock_app_class.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_create_assessment.return_value = 12345  # assessment_id
        mock_build_data.return_value = []

        create_alert_issues()

        mock_create_assessment.assert_called_once_with(sonar_data=[], api=mock_api, parent_id=None, parent_module=None)
        mock_build_data.assert_called_once_with(mock_api, None)

        # Verify no API post calls were made (no vulnerabilities)
        mock_api.post.assert_not_called()


class TestGitLabSASTImport(CLITestFixture):
    """Tests for GitLab SAST report import functionality"""

    @pytest.fixture
    def sample_gitlab_sast_data(self):
        """Fixture providing sample GitLab SAST report data"""
        return {
            "scan": {
                "end_time": "2025-10-08T14:44:26",
                "analyzer": {"id": "CxOne-SAST", "name": "Checkmarx", "version": "2.3.35"},
                "scanner": {"id": "CxOne-SAST", "name": "Checkmarx", "version": "2.3.35"},
                "start_time": "2025-10-08T14:44:26",
                "status": "success",
                "type": "sast",
            },
            "schema": "https://gitlab.com/gitlab-org/security-products/security-report-schemas",
            "version": "15.0.0",
            "vulnerabilities": [
                {
                    "id": "Missing_HSTS_Header:/dotnet-sample/API/Startup.cs:42",
                    "category": "Checkmarx-sast",
                    "name": "Missing_HSTS_Header",
                    "message": "Missing_HSTS_Header@/dotnet-sample/API/Startup.cs:42",
                    "description": "The web-application does not define an HSTS header.",
                    "cve": "Missing_HSTS_Header:/dotnet-sample/API/Startup.cs:42",
                    "severity": "Medium",
                    "confidence": "Medium",
                    "solution": "",
                    "location": {
                        "file": "/dotnet-sample/API/Startup.cs",
                        "start_line": 42,
                        "end_line": 51,
                        "class": "",
                    },
                },
                {
                    "id": "Log_Forging:/dotnet-sample/WebApp1/Pages/Index.cshtml.cs:51",
                    "category": "Checkmarx-sast",
                    "name": "Log_Forging",
                    "message": "Log_Forging@/dotnet-sample/WebApp1/Pages/Index.cshtml.cs:51",
                    "description": "User input flows to audit log without sanitization.",
                    "cve": "Log_Forging:/dotnet-sample/WebApp1/Pages/Index.cshtml.cs:51",
                    "severity": "Low",
                    "confidence": "Low",
                    "solution": "Sanitize user input before logging.",
                    "location": {
                        "file": "/dotnet-sample/WebApp1/Pages/Index.cshtml.cs",
                        "start_line": 51,
                        "end_line": 59,
                        "class": "",
                    },
                },
            ],
        }

    @pytest.fixture
    def sample_gitlab_sast_vulnerability(self):
        """Single vulnerability in GitLab SAST format"""
        return {
            "id": "Test_Vuln:/test/file.cs:10",
            "category": "test-scanner",
            "name": "Test_Vulnerability",
            "message": "Test message",
            "description": "Detailed test description",
            "severity": "High",
            "solution": "Fix the issue",
            "location": {
                "file": "/test/file.cs",
                "start_line": 10,
                "end_line": 20,
            },
        }

    def test_parse_gitlab_sast_file_valid(self, tmp_path, sample_gitlab_sast_data):
        """Test parsing a valid GitLab SAST file"""
        from regscale.integrations.commercial.sonarcloud import (
            parse_gitlab_sast_file,
        )  # pylint: disable=import-outside-toplevel

        # Create temp file with sample data
        test_file = tmp_path / "gl-sast-report.json"
        test_file.write_text(json.dumps(sample_gitlab_sast_data))

        vulnerabilities, scan_info = parse_gitlab_sast_file(test_file)

        assert len(vulnerabilities) == 2
        assert scan_info["scanner"]["name"] == "Checkmarx"
        assert vulnerabilities[0]["name"] == "Missing_HSTS_Header"
        assert vulnerabilities[1]["severity"] == "Low"

    def test_parse_gitlab_sast_file_missing_vulnerabilities(self, tmp_path):
        """Test parsing file missing vulnerabilities field"""
        from regscale.integrations.commercial.sonarcloud import (
            parse_gitlab_sast_file,
        )  # pylint: disable=import-outside-toplevel

        test_file = tmp_path / "invalid.json"
        test_file.write_text(json.dumps({"scan": {}}))

        with pytest.raises(SystemExit):
            parse_gitlab_sast_file(test_file)

    def test_parse_gitlab_sast_file_missing_scan(self, tmp_path):
        """Test parsing file missing scan field"""
        from regscale.integrations.commercial.sonarcloud import (
            parse_gitlab_sast_file,
        )  # pylint: disable=import-outside-toplevel

        test_file = tmp_path / "invalid.json"
        test_file.write_text(json.dumps({"vulnerabilities": []}))

        with pytest.raises(SystemExit):
            parse_gitlab_sast_file(test_file)

    def test_parse_gitlab_sast_file_invalid_json(self, tmp_path):
        """Test parsing invalid JSON file"""
        from regscale.integrations.commercial.sonarcloud import (
            parse_gitlab_sast_file,
        )  # pylint: disable=import-outside-toplevel

        test_file = tmp_path / "invalid.json"
        test_file.write_text("not valid json")

        with pytest.raises(SystemExit):
            parse_gitlab_sast_file(test_file)

    def test_parse_gitlab_sast_file_not_found(self, tmp_path):
        """Test parsing non-existent file"""
        from regscale.integrations.commercial.sonarcloud import (
            parse_gitlab_sast_file,
        )  # pylint: disable=import-outside-toplevel

        with pytest.raises(SystemExit):
            parse_gitlab_sast_file(tmp_path / "nonexistent.json")

    def test_build_gitlab_sast_description(self, sample_gitlab_sast_vulnerability):
        """Test building description from vulnerability data"""
        from regscale.integrations.commercial.sonarcloud import (
            build_gitlab_sast_description,
        )  # pylint: disable=import-outside-toplevel

        description = build_gitlab_sast_description(sample_gitlab_sast_vulnerability)

        assert "Test message" in description
        assert "Detailed test description" in description
        assert "Location: /test/file.cs:10-20" in description
        assert "Solution: Fix the issue" in description

    def test_build_gitlab_sast_description_minimal(self):
        """Test building description with minimal data"""
        from regscale.integrations.commercial.sonarcloud import (
            build_gitlab_sast_description,
        )  # pylint: disable=import-outside-toplevel

        vuln = {"message": "Simple message"}
        description = build_gitlab_sast_description(vuln)

        assert description == "Simple message"

    def test_build_gitlab_sast_description_same_start_end_line(self):
        """Test description with same start and end line"""
        from regscale.integrations.commercial.sonarcloud import (
            build_gitlab_sast_description,
        )  # pylint: disable=import-outside-toplevel

        vuln = {
            "message": "Test",
            "location": {"file": "/test.cs", "start_line": 10, "end_line": 10},
        }
        description = build_gitlab_sast_description(vuln)

        assert "Location: /test.cs:10" in description
        assert "-" not in description.split("Location:")[1]

    def test_transform_gitlab_sast_to_internal(self, sample_gitlab_sast_data):
        """Test transforming GitLab SAST data to internal format"""
        from regscale.integrations.commercial.sonarcloud import (
            transform_gitlab_sast_to_internal,
        )  # pylint: disable=import-outside-toplevel

        vulnerabilities = sample_gitlab_sast_data["vulnerabilities"]
        scan_info = sample_gitlab_sast_data["scan"]

        internal_data = transform_gitlab_sast_to_internal(vulnerabilities, scan_info)

        assert len(internal_data) == 2

        # Check first vulnerability
        first = internal_data[0]
        assert first["key"] == "Missing_HSTS_Header:/dotnet-sample/API/Startup.cs:42"
        assert first["severity"] == "MEDIUM"  # Normalized to uppercase
        assert first["name"] == "Missing_HSTS_Header"
        assert first["scanner_name"] == "Checkmarx"
        assert first["status"] == "OPEN"
        assert first["type"] == "VULNERABILITY"

        # Check second vulnerability
        second = internal_data[1]
        assert second["severity"] == "LOW"  # Normalized to uppercase
        assert second["name"] == "Log_Forging"

    def test_transform_gitlab_sast_severity_normalization(self):
        """Test that severity values are normalized to uppercase"""
        from regscale.integrations.commercial.sonarcloud import (
            transform_gitlab_sast_to_internal,
        )  # pylint: disable=import-outside-toplevel

        vulnerabilities = [
            {"id": "1", "name": "V1", "severity": "Critical", "message": "m1", "location": {}},
            {"id": "2", "name": "V2", "severity": "high", "message": "m2", "location": {}},
            {"id": "3", "name": "V3", "severity": "MEDIUM", "message": "m3", "location": {}},
            {"id": "4", "name": "V4", "severity": "Low", "message": "m4", "location": {}},
        ]
        scan_info = {"end_time": "2025-01-01T00:00:00", "scanner": {"name": "Test"}}

        internal_data = transform_gitlab_sast_to_internal(vulnerabilities, scan_info)

        assert internal_data[0]["severity"] == "CRITICAL"
        assert internal_data[1]["severity"] == "HIGH"
        assert internal_data[2]["severity"] == "MEDIUM"
        assert internal_data[3]["severity"] == "LOW"

    def test_transform_gitlab_sast_missing_severity(self):
        """Test transformation handles missing severity"""
        from regscale.integrations.commercial.sonarcloud import (
            transform_gitlab_sast_to_internal,
        )  # pylint: disable=import-outside-toplevel

        vulnerabilities = [{"id": "1", "name": "V1", "message": "m1", "location": {}}]
        scan_info = {"end_time": "2025-01-01T00:00:00", "scanner": {"name": "Test"}}

        internal_data = transform_gitlab_sast_to_internal(vulnerabilities, scan_info)

        assert internal_data[0]["severity"] == "UNKNOWN"

    def test_transform_gitlab_sast_uses_analyzer_if_no_scanner(self):
        """Test transformation uses analyzer name if scanner not present"""
        from regscale.integrations.commercial.sonarcloud import (
            transform_gitlab_sast_to_internal,
        )  # pylint: disable=import-outside-toplevel

        vulnerabilities = [{"id": "1", "name": "V1", "severity": "High", "message": "m1", "location": {}}]
        scan_info = {"end_time": "2025-01-01T00:00:00", "analyzer": {"name": "AnalyzerTool"}}

        internal_data = transform_gitlab_sast_to_internal(vulnerabilities, scan_info)

        assert internal_data[0]["scanner_name"] == "AnalyzerTool"

    @patch("regscale.integrations.commercial.sonarcloud.Issue")
    @patch("regscale.integrations.commercial.sonarcloud.create_alert_assessment")
    @patch("regscale.integrations.commercial.sonarcloud.Api")
    @patch("regscale.integrations.commercial.sonarcloud.Application")
    def test_create_gitlab_sast_issues(
        self,
        mock_app_class,
        mock_api_class,
        mock_create_assessment,
        mock_issue_class,
        tmp_path,
        sample_gitlab_sast_data,
    ):
        """Test creating issues from GitLab SAST file"""
        from regscale.integrations.commercial.sonarcloud import (
            create_gitlab_sast_issues,
        )  # pylint: disable=import-outside-toplevel

        # Setup mocks
        mock_app = MagicMock()
        mock_app.config = self.config
        mock_app_class.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_create_assessment.return_value = 12345

        mock_issue_instance = MagicMock()
        mock_issue_instance.create_or_update.return_value = True
        mock_issue_class.return_value = mock_issue_instance

        # Create temp file
        test_file = tmp_path / "gl-sast-report.json"
        test_file.write_text(json.dumps(sample_gitlab_sast_data))

        # Execute
        create_gitlab_sast_issues(test_file, parent_id=123, parent_module="securityplans")

        # Verify assessment was created
        mock_create_assessment.assert_called_once()

        # Verify issues were created (2 vulnerabilities in sample data)
        assert mock_issue_class.call_count == 2

    @patch("regscale.integrations.commercial.sonarcloud.Api")
    @patch("regscale.integrations.commercial.sonarcloud.Application")
    def test_create_gitlab_sast_issues_empty_file(self, mock_app_class, mock_api_class, tmp_path):
        """Test handling of file with no vulnerabilities"""
        from regscale.integrations.commercial.sonarcloud import (
            create_gitlab_sast_issues,
        )  # pylint: disable=import-outside-toplevel

        mock_app_class.return_value = MagicMock(config=self.config)
        mock_api_class.return_value = MagicMock()

        # Create file with empty vulnerabilities
        test_file = tmp_path / "empty.json"
        test_file.write_text(json.dumps({"scan": {"end_time": "2025-01-01T00:00:00"}, "vulnerabilities": []}))

        # Should complete without error (just logs warning)
        create_gitlab_sast_issues(test_file)
