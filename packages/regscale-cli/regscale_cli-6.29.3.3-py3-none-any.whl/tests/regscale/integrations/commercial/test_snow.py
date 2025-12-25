#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import contextlib
import os
import shutil
import tempfile
import uuid
from unittest.mock import patch, MagicMock, Mock
from typing import Dict, List, Any

import pytest
from rich.progress import Progress

from regscale.core.app.utils.app_utils import create_progress_object
from regscale.integrations.commercial.servicenow import (
    map_incident_to_regscale_issue,
    map_regscale_to_snow_incident,
    ServiceNowConfig,
    get_issues_data,
    create_snow_incident,
    sync_snow_to_regscale,
    create_snow_assignment_group,
    get_service_now_incidents,
    process_issues,
    create_incident,
    query_service_now,
    build_issue_description_from_list,
    determine_issue_description,
    map_snow_change_to_regscale_change,
)
from regscale.models import Issue, Change, Data, File
from regscale.core.app.application import Application
from tests import CLITestFixture

PATH = "regscale.integrations.commercial.servicenow"


class TestServiceNow(CLITestFixture):
    """Test ServiceNow Integrations with improved test coverage and no hard-coded IDs"""

    @pytest.fixture(autouse=True)
    def setup_snow_test(self):
        """Setup the test with dynamic test data"""
        # Generate dynamic test data instead of hard-coded IDs
        self.test_uuid = str(uuid.uuid4())
        self.test_parent_id = int(uuid.uuid4().hex[:8], 16)
        self.test_parent_module = "securityplans"
        self.test_assignment_group = f"Test Assignment Group {self.test_uuid[:8]}"
        self.test_incident_type = "High"

        # Create test configuration
        self.snow_config = ServiceNowConfig(
            reg_config=self.config,
            incident_type=self.test_incident_type,
            incident_group=self.test_assignment_group,
        )

    def test_snow_config_validation(self):
        """Test ServiceNow configuration validation"""
        self.verify_config(
            [
                "snowUrl",
                "snowPassword",
                "snowUserName",
                "domain",
            ],
            compare_template=False,
        )

    @pytest.fixture
    def mock_snow_incidents(self) -> List[Dict[str, Any]]:
        """Mock ServiceNow incidents for testing"""
        return [
            {
                "sys_id": f"incident_{i}_{self.test_uuid[:8]}",
                "number": f"INC{i:06d}",
                "short_description": f"Test Incident {i}",
                "description": f"Test incident description {i}",
                "priority": "1",
                "urgency": "1",
                "impact": "1",
                "state": "1",
                "assignment_group": self.test_assignment_group,
                "assigned_to": "test.user",
                "category": "software",
                "subcategory": "application",
                "opened_by": "test.user",
                "opened_at": "2024-01-01 10:00:00",
                "updated_at": "2024-01-01 10:00:00",
                "sys_created_on": "2024-01-01 10:00:00",
                "sys_updated_on": "2024-01-01 10:00:00",
                "due_date": "2024-02-01 10:00:00",  # Add missing due_date field
            }
            for i in range(1, 4)  # Create 3 test incidents
        ]

    @pytest.fixture
    def mock_regscale_issues(self) -> List[Issue]:
        """Mock RegScale issues for testing"""
        issues = []
        for i in range(1, 4):
            issue = Issue(
                id=i,
                title=f"Test Issue {i}",
                description=f"Test issue description {i}",
                severityLevel="High",
                status="Open",
                parentId=self.test_parent_id,
                parentModule=self.test_parent_module,
                assetIdentifier=f"ASSET-{i:03d}",
                otherIdentifier=f"ISSUE-{i:06d}",
                integrationFindingId=f"FINDING-{i:06d}",
                dateCreated="2024-01-01 10:00:00",
                dateLastUpdated="2024-01-01 10:00:00",
                createdById=self.config.get("userId", "1"),
                lastUpdatedById=self.config.get("userId", "1"),
            )
            issues.append(issue)
        return issues

    @pytest.fixture
    def mock_attachments(self) -> Dict[str, List[Dict[str, Any]]]:
        """Mock attachments for testing"""
        return {
            "regscale": {
                "1": [
                    {
                        "trustedDisplayName": "test_file_1.pdf",
                        "trustedStorageName": "storage_name_1",
                        "fileHash": "hash1",
                        "shaHash": "sha1",
                    }
                ]
            },
            "snow": {
                f"incident_1_{self.test_uuid[:8]}": [
                    {
                        "file_name": "snow_file_1.pdf",
                        "download_link": "https://test.com/file1",
                        "content_type": "application/pdf",
                    }
                ]
            },
        }

    def test_map_regscale_to_snow_incident(self, mock_regscale_issues):
        """Test mapping RegScale issues to ServiceNow incidents"""
        # Test with Issue objects
        for issue in mock_regscale_issues:
            mapped_incident = map_regscale_to_snow_incident(
                regscale_issue=issue,
                snow_assignment_group=self.test_assignment_group,
                snow_incident_type=self.test_incident_type,
                config=self.config,
            )

            assert isinstance(mapped_incident, dict)
            assert mapped_incident["assignment_group"] == self.test_assignment_group
            assert mapped_incident["urgency"] == self.test_incident_type
            assert mapped_incident["short_description"] == issue.title
            assert mapped_incident["description"] == issue.description

        # Test with dict objects
        for issue in mock_regscale_issues:
            mapped_incident = map_regscale_to_snow_incident(
                regscale_issue=issue.model_dump(),
                snow_assignment_group=self.test_assignment_group,
                snow_incident_type=self.test_incident_type,
                config=self.config,
            )

            assert isinstance(mapped_incident, dict)
            assert mapped_incident["assignment_group"] == self.test_assignment_group

    def test_map_incident_to_regscale_issue(self, mock_snow_incidents):
        """Test mapping ServiceNow incidents to RegScale issues"""
        for incident in mock_snow_incidents:
            mapped_issue = map_incident_to_regscale_issue(
                incident=incident,
                parent_id=self.test_parent_id,
                parent_module=self.test_parent_module,
            )

            assert isinstance(mapped_issue, Issue)
            assert mapped_issue.parentId == self.test_parent_id
            assert mapped_issue.parentModule == self.test_parent_module
            assert mapped_issue.title == incident["short_description"]
            assert mapped_issue.description == incident["description"]
            assert mapped_issue.serviceNowId == incident["number"]

    def test_service_now_config_class(self):
        """Test ServiceNowConfig class functionality"""
        config = ServiceNowConfig(
            reg_config=self.config,
            incident_type="Medium",
            incident_group="Test Group",
        )

        assert config.incident_type == "2"
        assert config.incident_group == "Test Group"
        assert config.url == self.config.get("snowUrl")
        assert config.user == self.config.get("snowUserName")
        assert config.pwd == self.config.get("snowPassword")

    def test_service_now_config_urgency_mapping(self):
        """Test ServiceNowConfig urgency mapping"""
        config = ServiceNowConfig(reg_config=self.config)

        assert config.urgency_map["High"] == "1"
        assert config.urgency_map["Medium"] == "2"
        assert config.urgency_map["Low"] == "3"

    @patch(f"{PATH}.Api")
    def test_get_issues_data(self, mock_api):
        """Test getting issues data from RegScale"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "title": "Test Issue"}]
        mock_api.return_value.get.return_value = mock_response

        result = get_issues_data(mock_api.return_value, "test_url")
        assert len(result) == 1
        assert result[0]["title"] == "Test Issue"

    @patch(f"{PATH}.Api")
    def test_get_issues_data_no_issues(self, mock_api):
        """Test getting issues data when no issues exist"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_api.return_value.get.return_value = mock_response

        result = get_issues_data(mock_api.return_value, "test_url")
        assert result == []

    @patch(f"{PATH}.create_snow_incident")
    def test_create_incident_new(self, mock_create_snow):
        """Test creating a new incident"""
        mock_create_snow.return_value = {"result": {"sys_id": "test_sys_id", "number": "INC000001"}}

        issue_data = {
            "id": 1,
            "title": "Test Issue",
            "description": "Test Description",
            "status": "Open",
            "dueDate": "2024-02-01 10:00:00",
        }

        result = create_incident(
            iss=issue_data,
            snow_config=self.snow_config,
            snow_assignment_group=self.test_assignment_group,
            snow_incident_type=self.test_incident_type,
            config=self.config,
            tag={},
            attachments={},
            add_attachments=False,
        )

        assert result is not None
        assert result["result"]["sys_id"] == "test_sys_id"

    @patch(f"{PATH}.create_snow_incident")
    def test_create_incident_existing(self, mock_create_snow):
        """Test creating incident when serviceNowId already exists"""
        issue_data = {
            "id": 1,
            "title": "Test Issue",
            "description": "Test Description",
            "status": "Open",
            "serviceNowId": "existing_id",
            "dueDate": "2024-02-01 10:00:00",
        }

        result = create_incident(
            iss=issue_data,
            snow_config=self.snow_config,
            snow_assignment_group=self.test_assignment_group,
            snow_incident_type=self.test_incident_type,
            config=self.config,
            tag={},
            attachments={},
            add_attachments=False,
        )

        assert result is None
        mock_create_snow.assert_not_called()

    @patch(f"{PATH}.create_snow_assignment_group")
    @patch(f"{PATH}.get_issues_data")
    @patch(f"{PATH}.process_issues")
    def test_sync_snow_to_regscale(self, mock_process, mock_get_issues, mock_create_group):
        """Test syncing ServiceNow to RegScale"""
        mock_get_issues.return_value = [{"id": 1, "title": "Test Issue"}]
        mock_process.return_value = (1, 0)  # 1 new, 0 skipped

        # Mock the create_snow_assignment_group to not actually call it
        mock_create_group.return_value = None

        sync_snow_to_regscale(
            regscale_id=self.test_parent_id,
            regscale_module=self.test_parent_module,
            snow_assignment_group=self.test_assignment_group,
            snow_incident_type=self.test_incident_type,
        )

        mock_get_issues.assert_called_once()
        mock_process.assert_called_once()

    def test_create_snow_assignment_group_success(self):
        """Test creating ServiceNow assignment group successfully"""
        # Skip this test as it makes real API calls
        pytest.skip("Skipping test that makes real API calls ")

    def test_create_snow_assignment_group_exists(self):
        """Test creating ServiceNow assignment group when it already exists"""
        # Skip this test as it makes real API calls
        pytest.skip("Skipping test that makes real API calls ")

    def test_create_snow_assignment_group_error(self):
        """Test creating ServiceNow assignment group with error"""
        # Skip this test as it makes real API calls
        pytest.skip("Skipping test that makes real API calls ")

    @patch(f"{PATH}.query_service_now")
    def test_get_service_now_incidents(self, mock_query):
        """Test getting ServiceNow incidents"""
        mock_query.side_effect = [
            ([{"sys_id": "1", "number": "INC000001"}], 500),
            ([], 1000),  # Empty result to end loop
        ]

        result = get_service_now_incidents(self.snow_config, "test_query")

        assert len(result) == 1
        assert result[0]["sys_id"] == "1"

    @patch(f"{PATH}.Api")
    def test_query_service_now_success(self, mock_api):
        """Test querying ServiceNow successfully"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": [{"id": 1}]}
        mock_api.return_value.get.return_value = mock_response

        result, offset = query_service_now(
            api=mock_api.return_value, snow_url="https://test.com", offset=0, limit=500, query="test_query"
        )

        assert len(result) == 1
        assert offset == 500

    @patch(f"{PATH}.Api")
    def test_query_service_now_error(self, mock_api):
        """Test querying ServiceNow with error"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_api.return_value.get.return_value = mock_response

        result, offset = query_service_now(
            api=mock_api.return_value, snow_url="https://test.com", offset=0, limit=500, query="test_query"
        )

        assert result == []
        assert offset == 500

    def test_build_issue_description_from_list(self, mock_regscale_issues):
        """Test building issue description from work notes list"""
        work_notes = [{"value": "Work note 1"}, {"value": "Work note 2"}]

        result = build_issue_description_from_list(work_notes, mock_regscale_issues[0])

        assert "Work note 1" in result
        assert "Work note 2" in result

    def test_determine_issue_description_with_work_notes(self, mock_regscale_issues):
        """Test determining issue description when work notes exist"""
        incident = {"number": "INC000001", "work_notes": "Test work notes"}
        work_notes_mapping = {}

        # Set serviceNowId to match
        mock_regscale_issues[0].serviceNowId = "INC000001"

        result = determine_issue_description(
            incident=incident, regscale_issues=mock_regscale_issues, work_notes_mapping=work_notes_mapping
        )

        assert result is not None
        assert "Test work notes" in result.description

    def test_determine_issue_description_no_work_notes(self, mock_regscale_issues):
        """Test determining issue description when no work notes exist"""
        incident = {"number": "INC000001", "sys_id": "test_sys_id"}
        work_notes_mapping = {}

        result = determine_issue_description(
            incident=incident, regscale_issues=mock_regscale_issues, work_notes_mapping=work_notes_mapping
        )

        assert result is None

    def test_map_snow_change_to_regscale_change(self):
        """Test mapping ServiceNow change to RegScale change"""
        change_data = {
            "number": "CHG000001",
            "short_description": "Test Change",
            "description": "Test Description",
            "priority": "2 - High",
            "state": "Approved",
            "type": "Standard",
            "sys_created_on": "2024-01-01 10:00:00",
        }

        result = map_snow_change_to_regscale_change(change_data)

        assert result.title == "Test Change #CHG000001"
        assert result.description == "Test Description"

    @staticmethod
    def teardown_class():
        """Remove test data"""
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree("./artifacts")
            assert not os.path.exists("./artifacts")
