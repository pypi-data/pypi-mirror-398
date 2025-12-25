#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test for jira integration in RegScale CLI"""
# standard python imports
import contextlib
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

import pytest
from rich.progress import Progress
from jira import JIRAError

from regscale.core.app.application import Application
from regscale.core.app.api import Api
from regscale.core.app.utils.app_utils import compute_hash, create_progress_object, get_current_datetime
from regscale.integrations.commercial.jira import (
    _generate_jira_comment,
    check_and_close_tasks,
    create_and_update_regscale_issues,
    create_issue_in_jira,
    create_jira_client,
    download_regscale_attachments_to_directory,
    fetch_jira_objects,
    get_regscale_data_and_attachments,
    map_jira_due_date,
    map_jira_to_regscale_issue,
    sync_regscale_and_jira,
    sync_regscale_objects_to_jira,
    sync_regscale_to_jira,
    task_and_attachments_sync,
    create_regscale_task_from_jira,
    create_and_update_regscale_tasks,
    process_tasks_for_sync,
    upload_files_to_jira,
    upload_files_to_regscale,
    validate_issue_type,
)
from regscale.models import File, Issue
from regscale.models.regscale_models.task import Task
from tests import CLITestFixture


class TestJira(CLITestFixture):
    JIRA_PROJECT = "SNES"
    PATH = "regscale.integrations.commercial.jira"
    security_plan = None

    @pytest.fixture(autouse=True)
    def setup_ssp(self, create_security_plan):
        self.security_plan = create_security_plan

    @property
    def PARENT_ID(self):
        """Get the parent ID from the existing SSP"""
        return self.security_plan.id

    @property
    def PARENT_MODULE(self):
        """Get the parent module from the existing SSP"""
        return self.security_plan.get_module_string()

    @pytest.fixture
    def jira_client(self):
        """Setup jira client"""
        # Mock the Jira client to avoid actual API calls during testing
        mock_client = MagicMock()
        mock_client.server_info.return_value = {"serverTitle": "Test Jira Server"}
        mock_client._options = {"server": "https://test.atlassian.net"}

        # Mock issue_types() for validate_issue_type function
        bug_type = MagicMock()
        bug_type.name = "Bug"
        task_type = MagicMock()
        task_type.name = "Task"
        story_type = MagicMock()
        story_type.name = "Story"
        mock_client.issue_types.return_value = [bug_type, task_type, story_type]

        # Mock the new /rest/api/3/search/jql endpoint
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "issues": [
                {"key": "TEST-1"},
                {"key": "TEST-2"},
            ],
            # No nextPageToken means no more results
        }
        mock_response.raise_for_status = MagicMock()
        mock_client._session.get.return_value = mock_response

        # Mock issue() to return mock issues
        def mock_issue(key):
            issue = MagicMock()
            issue.key = key
            issue.fields.summary = f"Test {key}"
            issue.fields.description = f"Description for {key}"
            issue.fields.attachment = [MagicMock()]  # At least one attachment
            return issue

        mock_client.issue.side_effect = mock_issue

        return mock_client

    @staticmethod
    @pytest.fixture(params=[True, False])
    def fetch_attachments(request):
        """Pytest fixture that will run twice:
        first time with a true value, second time with a false value"""
        return request.param

    @pytest.fixture
    def jira_issues(self, jira_client, fetch_attachments):
        """Fixture for fetching Jira issues and attachments"""
        return fetch_jira_objects(jira_client=jira_client, jira_project=self.JIRA_PROJECT, jira_issue_type="Bug")

    @pytest.fixture
    def jira_tasks(self, jira_client, fetch_attachments):
        """Fixture for fetching Jira tasks and attachments"""
        return fetch_jira_objects(
            jira_client=jira_client,
            jira_project=self.JIRA_PROJECT,
            jira_issue_type="Task",
            sync_tasks_only=True,
        )

    @pytest.fixture
    def get_jira_issue(self, jira_client):
        """Fixture for creating a test Issue in Jira"""
        jira_issue = jira_client.create_issue(
            fields={
                "project": {"key": self.JIRA_PROJECT},
                "summary": f"{self.title_prefix} Jira Integration Test",
                "description": "Test issue for integration testing",
                "issuetype": {"name": "Bug"},
            }
        )
        yield jira_issue
        jira_issue.delete()  # cleanup afterwards

    @pytest.fixture
    def get_jira_task(self, jira_client):
        """Fixture for creating a test Task in Jira"""
        jira_task = jira_client.create_issue(
            fields={
                "project": {"key": self.JIRA_PROJECT},
                "summary": f"{self.title_prefix} Jira Integration Test",
                "description": "Test task for integration testing",
                "issuetype": {"name": "Task"},
            }
        )
        yield jira_task
        jira_task.delete()  # cleanup afterwards

    @pytest.fixture
    def get_jira_issue_with_attachment(self, get_jira_issue, jira_client):
        """Fixture for creating a test Issue in Jira with an attachment"""
        issue = get_jira_issue
        file_path = os.path.join(self.get_tests_dir("tests"), "test_data", "jira_attachments", "attachment.txt")
        with open(file_path, "rb") as f:
            jira_client.add_attachment(issue=issue, filename="test_attachment.txt", attachment=f)
        yield jira_client.issue(issue.id)

    @pytest.fixture
    def get_jira_task_with_attachment(self, get_jira_task, jira_client):
        """Fixture for creating a test Task in Jira with an attachment"""
        task = get_jira_task
        file_path = os.path.join(self.get_tests_dir("tests"), "test_data", "jira_attachments", "attachment.txt")
        with open(file_path, "rb") as f:
            jira_client.add_attachment(issue=task, filename="test_attachment.txt", attachment=f)
        yield jira_client.issue(task.id)

    @pytest.fixture
    def regscale_issues_and_attachments(self, fetch_attachments, regscale_issue_and_attachment):
        """Fixture for fetching RegScale issues and attachments"""
        _ = regscale_issue_and_attachment

        if fetch_attachments:
            return Issue.get_objects_and_attachments_by_parent(
                parent_id=self.PARENT_ID,
                parent_module=self.PARENT_MODULE,
            )
        else:
            return (
                Issue.get_all_by_parent(
                    parent_id=self.PARENT_ID,
                    parent_module=self.PARENT_MODULE,
                ),
                [],
            )

    @pytest.fixture
    def regscale_tasks_and_attachments(self, fetch_attachments, regscale_task_and_attachment):
        """Fixture for fetching RegScale tasks and attachments"""
        _ = regscale_task_and_attachment
        if fetch_attachments:
            return Task.get_objects_and_attachments_by_parent(
                parent_id=self.PARENT_ID,
                parent_module=self.PARENT_MODULE,
            )
        else:
            return (
                Task.get_all_by_parent(
                    parent_id=self.PARENT_ID,
                    parent_module=self.PARENT_MODULE,
                ),
                [],
            )

    @pytest.fixture
    def regscale_issue_and_attachment(self, fetch_attachments):
        """Fixture for creating RegScale issue and attachment"""
        issue = Issue(
            title=f"{self.title_prefix} Jira Issue Integration Test",
            description="Security plan for Jira integration testing",
            parentId=self.PARENT_ID,
            parentModule=self.PARENT_MODULE,
            dueDate=get_current_datetime(),
            identification=f"{self.title_prefix} Jira Issue Integration Test",
            status="Open",
        ).create()
        if fetch_attachments:
            File.upload_file_to_regscale(
                file_name=os.path.join(self.get_tests_dir("tests"), "test_data", "jira_attachments", "attachment.txt"),
                parent_id=issue.id,
                parent_module=issue.get_module_string(),
                api=self.api,
            )
        return issue

    @pytest.fixture
    def regscale_task_and_attachment(self, fetch_attachments):
        """Fixture for creating RegScale task and attachment"""
        task = Task(
            status="Backlog",
            title=f"{self.title_prefix} Jira Task Integration Test",
            description="Task for Jira integration testing",
            parentId=self.PARENT_ID,
            parentModule=self.PARENT_MODULE,
            dueDate=get_current_datetime(),
        ).create()
        if fetch_attachments:
            File.upload_file_to_regscale(
                file_name=os.path.join(self.get_tests_dir("tests"), "test_data", "jira_attachments", "image.png"),
                parent_id=task.id,
                parent_module=task.get_module_string(),
                api=self.api,
            )
        return task

    @pytest.fixture
    def mock_job_progres_object(self):
        """Mock job_progress object"""
        with patch.object(self.PATH, "job_progress", new=create_progress_object()) as job_progress:
            yield job_progress

    def test_init(self):
        """Test init file and config"""
        self.verify_config(
            [
                "jiraUrl",
                "jiraApiToken",
                "jiraUserName",
            ]
        )

    @patch(f"{PATH}.Task.get_objects_and_attachments_by_parent")
    def test_get_regscale_data_and_attachments_sync_both(self, mock_get_objects_and_attachments_by_parent):
        """Test getting RegScale data and attachments"""
        mock_get_objects_and_attachments_by_parent.return_value = (["objects"], {"attachments": ["attachment"]})
        regscale_issues, regscale_attachments = get_regscale_data_and_attachments(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            sync_attachments=True,
            sync_tasks_only=True,
        )
        assert regscale_issues == ["objects"]
        assert regscale_attachments == {"attachments": ["attachment"]}

    @patch(f"{PATH}.Task.get_all_by_parent")
    def test_get_regscale_data_and_attachments_sync_tasks_only(self, mock_get_all_by_parent):
        """Test getting RegScale data and no attachments"""
        mock_get_all_by_parent.return_value = ["objects"]
        regscale_issues, regscale_attachments = get_regscale_data_and_attachments(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            sync_attachments=False,
            sync_tasks_only=True,
        )
        assert regscale_issues == ["objects"]
        assert regscale_attachments == []

    @patch(f"{PATH}.Issue.get_objects_and_attachments_by_parent")
    def test_get_regscale_data_and_attachments_sync_attachments_only(self, mock_get_objects_and_attachments_by_parent):
        """Test getting RegScale attachments only"""
        mock_get_objects_and_attachments_by_parent.return_value = (["objects"], {"attachments": ["attachment"]})
        regscale_issues, regscale_attachments = get_regscale_data_and_attachments(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            sync_attachments=True,
            sync_tasks_only=False,
        )
        assert regscale_issues == ["objects"]
        assert regscale_attachments == {"attachments": ["attachment"]}

    @patch(f"{PATH}.Issue.get_all_by_parent")
    def test_get_regscale_data_and_attachments_sync_issues_only(self, mock_get_all_by_parent):
        """Test getting RegScale issues only"""
        mock_get_all_by_parent.return_value = ["objects"]
        regscale_issues, regscale_attachments = get_regscale_data_and_attachments(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            sync_attachments=False,
            sync_tasks_only=False,
        )
        assert regscale_issues == ["objects"]
        assert regscale_attachments == []

    @patch(f"{PATH}.sync_regscale_objects_to_jira")
    @patch(f"{PATH}.sync_regscale_to_jira", return_value=[])
    @patch(f"{PATH}.create_jira_client")
    @patch(f"{PATH}.fetch_jira_objects", return_value=[])
    @patch(f"{PATH}.get_regscale_data_and_attachments", return_value=([], {}))
    @patch(f"{PATH}.Api", return_value=MagicMock(spec=Api))
    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_and_jira(
        self,
        mock_check_license,
        mock_api,
        mock_get_regscale_data_and_attachments,
        mock_fetch_jira_objects,
        mock_create_jira_client,
        mock_sync_regscale_to_jira,
        mock_sync_regscale_objects_to_jira,
        fetch_attachments,
    ):
        """Test the entire Jira & RegScale sync process"""
        mock_check_license.return_value.config = self.config
        # Add thread_manager to the mock Application
        mock_check_license.return_value.thread_manager = MagicMock()
        # mock jira client so we can check it was correctly used later
        mock_jira_client = MagicMock()
        mock_create_jira_client.return_value = mock_jira_client
        try:
            sync_regscale_and_jira(
                parent_id=self.PARENT_ID,
                parent_module=self.PARENT_MODULE,
                jira_project=self.JIRA_PROJECT,
                jira_issue_type="Bug",
                sync_attachments=fetch_attachments,
            )
        except Exception as e:
            pytest.fail("Jira & RegScale sync failed: {}".format(e))

    @patch(f"{PATH}.sync_regscale_objects_to_jira")
    @patch(f"{PATH}.sync_regscale_to_jira", return_value=[])
    @patch(f"{PATH}.create_jira_client")
    @patch(f"{PATH}.fetch_jira_objects", return_value=[])
    @patch(f"{PATH}.get_regscale_data_and_attachments", return_value=([], {}))
    @patch(f"{PATH}.Api", return_value=MagicMock(spec=Api))
    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_and_jira_tasks(
        self,
        mock_check_license,
        mock_api,
        mock_get_regscale_data_and_attachments,
        mock_fetch_jira_objects,
        mock_create_jira_client,
        mock_sync_regscale_to_jira,
        mock_sync_regscale_objects_to_jira,
        fetch_attachments,
    ):
        """Test the entire Jira & RegScale task sync process"""
        mock_check_license.return_value.config = self.config
        # Add thread_manager to the mock Application
        mock_check_license.return_value.thread_manager = MagicMock()
        # mock jira client so we can check it was correctly used later
        mock_jira_client = MagicMock()
        mock_create_jira_client.return_value = mock_jira_client
        try:
            sync_regscale_and_jira(
                parent_id=self.PARENT_ID,
                parent_module=self.PARENT_MODULE,
                jira_project=self.JIRA_PROJECT,
                jira_issue_type="Task",
                sync_attachments=fetch_attachments,
                sync_tasks_only=True,
            )
        except Exception as e:
            pytest.fail("Jira & RegScale task sync failed: {}".format(e))

    @patch(f"{PATH}.sync_regscale_objects_to_jira")
    @patch(f"{PATH}.sync_regscale_to_jira", return_value=[])
    @patch(f"{PATH}.create_jira_client")
    @patch(f"{PATH}.fetch_jira_objects", return_value=[])
    @patch(f"{PATH}.get_regscale_data_and_attachments", return_value=([], {}))
    @patch(f"{PATH}.Api", return_value=MagicMock(spec=Api))
    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_and_jira_no_updates(
        self,
        mock_check_license,
        mock_api,
        mock_get_regscale_data_and_attachments,
        mock_fetch_jira_objects,
        mock_create_jira_client,
        mock_sync_regscale_to_jira,
        mock_sync_regscale_objects_to_jira,
        fetch_attachments,
    ):
        """Test sync_regscale_and_jira without updates from either side"""
        # mock jira client so we can check it was correctly used later
        mock_jira_client = MagicMock()
        mock_create_jira_client.return_value = mock_jira_client

        sync_regscale_and_jira(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            jira_project=self.JIRA_PROJECT,
            jira_issue_type="Bug",
            sync_attachments=fetch_attachments,
        )

        # check that we get the jira client correctly
        mock_create_jira_client.assert_called_once()

        # check that we correctly fetch objects from jira and regscale
        mock_get_regscale_data_and_attachments.assert_called_once_with(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            sync_attachments=fetch_attachments,
            sync_tasks_only=False,
        )
        mock_fetch_jira_objects.assert_called_once_with(
            jira_client=mock_jira_client,
            jira_project=self.JIRA_PROJECT,
            jql_str="project = 'SNES'",
            jira_issue_type="Bug",
            sync_tasks_only=False,
        )

        # check that no updates were made because we did not find any objects from jira/regscale
        mock_sync_regscale_to_jira.assert_not_called()
        mock_sync_regscale_objects_to_jira.assert_not_called()

    @patch(f"{PATH}.sync_regscale_objects_to_jira")
    @patch(f"{PATH}.sync_regscale_to_jira", return_value=[])
    @patch(f"{PATH}.create_jira_client")
    @patch(f"{PATH}.fetch_jira_objects")
    @patch(f"{PATH}.get_regscale_data_and_attachments")
    @patch(f"{PATH}.Api", return_value=MagicMock(spec=Api))
    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_and_jira_updates(
        self,
        mock_check_license,
        mock_api,
        mock_get_regscale_data_and_attachments,
        mock_fetch_jira_objects,
        mock_create_jira_client,
        mock_sync_regscale_to_jira,
        mock_sync_regscale_objects_to_jira,
        fetch_attachments,
    ):
        """Test sync_regscale_and_jira with updates from both sides"""
        # mock jira client so we can check it was correctly used later
        mock_jira_client = MagicMock()
        mock_create_jira_client.return_value = mock_jira_client

        # Setup mock config with jiraCustomFields returning empty dict
        mock_config = MagicMock()
        mock_config.get.return_value = {}
        mock_check_license.return_value.config = mock_config

        # mock these so that we can control what objects were returned to check later
        mock_fetch_jira_objects.return_value = MagicMock()
        mock_get_regscale_data_and_attachments.return_value = (MagicMock(), MagicMock())

        sync_regscale_and_jira(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            jira_project=self.JIRA_PROJECT,
            jira_issue_type="Bug",
            sync_attachments=fetch_attachments,
        )

        # check that we get the jira client correctly
        mock_create_jira_client.assert_called_once()

        # check that we correctly fetch objects from jira and regscale
        mock_get_regscale_data_and_attachments.assert_called_once_with(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            sync_attachments=fetch_attachments,
            sync_tasks_only=False,
        )
        mock_fetch_jira_objects.assert_called_once_with(
            jira_client=mock_jira_client,
            jira_project=self.JIRA_PROJECT,
            jql_str="project = 'SNES'",
            jira_issue_type="Bug",
            sync_tasks_only=False,
        )

        # check that updates were made with correct objects
        mock_sync_regscale_to_jira.assert_called_once_with(
            regscale_objects=mock_get_regscale_data_and_attachments.return_value[0],
            jira_client=mock_jira_client,
            jira_project=self.JIRA_PROJECT,
            jira_issue_type="Bug",
            api=mock_api.return_value,
            sync_attachments=fetch_attachments,
            attachments=mock_get_regscale_data_and_attachments.return_value[1],
            custom_fields={},
        )
        mock_sync_regscale_objects_to_jira.assert_called_once_with(
            mock_fetch_jira_objects.return_value,
            mock_get_regscale_data_and_attachments.return_value[0],
            fetch_attachments,
            mock_check_license.return_value,
            self.PARENT_ID,
            self.PARENT_MODULE,
            False,
            False,
        )

    @patch(f"{PATH}.sync_regscale_objects_to_jira")
    @patch(f"{PATH}.sync_regscale_to_jira", return_value=[])
    @patch(f"{PATH}.create_jira_client")
    @patch(f"{PATH}.fetch_jira_objects")
    @patch(f"{PATH}.get_regscale_data_and_attachments")
    @patch(f"{PATH}.Api", return_value=MagicMock(spec=Api))
    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_and_jira_custom_jql(
        self,
        mock_check_license,
        mock_api,
        mock_get_regscale_data_and_attachments,
        mock_fetch_jira_objects,
        mock_create_jira_client,
        mock_sync_regscale_to_jira,
        mock_sync_regscale_objects_to_jira,
        fetch_attachments,
    ):
        """Test sync_regscale_and_jira with custom JQL query"""
        # mock jira client so we can check it was correctly used later
        mock_jira_client = MagicMock()
        mock_create_jira_client.return_value = mock_jira_client

        # mock these so that we can control what objects were returned to check later
        mock_fetch_jira_objects.return_value = []
        mock_get_regscale_data_and_attachments.return_value = ([], {})

        custom_jql = "project = SNES AND assignee = currentUser() AND status != Closed"

        sync_regscale_and_jira(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            jira_project=self.JIRA_PROJECT,
            jira_issue_type="Bug",
            sync_attachments=fetch_attachments,
            jql=custom_jql,
        )

        # check that we get the jira client correctly
        mock_create_jira_client.assert_called_once()

        # check that we correctly fetch objects from jira and regscale
        mock_get_regscale_data_and_attachments.assert_called_once_with(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            sync_attachments=fetch_attachments,
            sync_tasks_only=False,
        )
        # Verify that the custom JQL was used instead of the default
        mock_fetch_jira_objects.assert_called_once_with(
            jira_client=mock_jira_client,
            jira_project=self.JIRA_PROJECT,
            jql_str=custom_jql,
            jira_issue_type="Bug",
            sync_tasks_only=False,
        )

    @patch(f"{PATH}.sync_regscale_objects_to_jira")
    @patch(f"{PATH}.sync_regscale_to_jira", return_value=[])
    @patch(f"{PATH}.create_jira_client")
    @patch(f"{PATH}.fetch_jira_objects")
    @patch(f"{PATH}.get_regscale_data_and_attachments")
    @patch(f"{PATH}.Api", return_value=MagicMock(spec=Api))
    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_and_jira_custom_jql_tasks(
        self,
        mock_check_license,
        mock_api,
        mock_get_regscale_data_and_attachments,
        mock_fetch_jira_objects,
        mock_create_jira_client,
        mock_sync_regscale_to_jira,
        mock_sync_regscale_objects_to_jira,
        fetch_attachments,
    ):
        """Test sync_regscale_and_jira with custom JQL query for tasks"""
        # mock jira client so we can check it was correctly used later
        mock_jira_client = MagicMock()
        mock_create_jira_client.return_value = mock_jira_client

        # mock these so that we can control what objects were returned to check later
        mock_fetch_jira_objects.return_value = []
        mock_get_regscale_data_and_attachments.return_value = ([], {})

        custom_jql = "project = SNES AND assignee = currentUser() AND issueType = Task"

        sync_regscale_and_jira(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            jira_project=self.JIRA_PROJECT,
            jira_issue_type="Task",
            sync_attachments=fetch_attachments,
            sync_tasks_only=True,
            jql=custom_jql,
        )

        # check that we get the jira client correctly
        mock_create_jira_client.assert_called_once()

        # check that we correctly fetch objects from jira and regscale
        mock_get_regscale_data_and_attachments.assert_called_once_with(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            sync_attachments=fetch_attachments,
            sync_tasks_only=True,
        )
        # Verify that the custom JQL was used instead of the default task-specific JQL
        mock_fetch_jira_objects.assert_called_once_with(
            jira_client=mock_jira_client,
            jira_project=self.JIRA_PROJECT,
            jql_str=custom_jql,
            jira_issue_type="Task",
            sync_tasks_only=True,
        )

    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_objects_to_jira(
        self, mock_check_license, fetch_attachments, get_jira_issue, regscale_issues_and_attachments
    ):
        """Test syncing RegScale objects to Jira"""
        mock_check_license.return_value.config = self.config
        try:
            sync_regscale_objects_to_jira(
                jira_issues=[get_jira_issue],
                regscale_objects=regscale_issues_and_attachments[0],
                sync_attachments=fetch_attachments,
                app=self.app,
                parent_id=self.PARENT_ID,
                parent_module=self.PARENT_MODULE,
                sync_tasks_only=False,
            )
        except Exception as e:
            pytest.fail("Jira & RegScale task sync failed: {}".format(e))

    @patch(f"{PATH}.create_jira_client")
    @patch(f"{PATH}.create_and_update_regscale_issues")
    @patch(f"{PATH}.create_and_update_regscale_tasks")
    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_objects_to_jira_tasks_only(
        self,
        mock_check_license,
        mock_create_and_update_regscale_tasks,
        mock_create_and_update_regscale_issues,
        mock_create_jira_client,
        fetch_attachments,
    ):
        """Test syncing RegScale objects to Jira with sync_tasks_only=True"""
        mock_check_license.return_value.config = self.config
        mock_jira_client = MagicMock()
        mock_create_jira_client.return_value = mock_jira_client
        mock_create_and_update_regscale_tasks.return_value = (1, 0, 0)

        sync_regscale_objects_to_jira(
            MagicMock(),
            MagicMock(),
            fetch_attachments,
            MagicMock(spec=Application),
            self.PARENT_ID,
            self.PARENT_MODULE,
            True,
        )

        mock_create_and_update_regscale_tasks.assert_called_once()
        mock_create_and_update_regscale_issues.assert_not_called()

    @patch(f"{PATH}.create_jira_client")
    @patch(f"{PATH}.create_and_update_regscale_tasks")
    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_objects_to_jira_all(
        self,
        mock_check_license,
        mock_create_and_update_regscale_tasks,
        mock_create_jira_client,
        fetch_attachments,
    ):
        """Test syncing RegScale objects to Jira with sync_tasks_only=False"""
        mock_check_license.return_value.config = self.config
        mock_jira_client = MagicMock()
        mock_create_jira_client.return_value = mock_jira_client

        # Create mock application with ThreadManager
        mock_app = MagicMock(spec=Application)
        mock_app.config = self.config
        mock_thread_manager = MagicMock()
        mock_app.thread_manager = mock_thread_manager

        # Mock Jira issues
        mock_jira_issues = [MagicMock(), MagicMock()]

        sync_regscale_objects_to_jira(
            mock_jira_issues,
            MagicMock(),
            fetch_attachments,
            mock_app,
            self.PARENT_ID,
            self.PARENT_MODULE,
            False,
        )

        mock_create_and_update_regscale_tasks.assert_not_called()
        # Verify ThreadManager methods were called
        mock_thread_manager.submit_tasks_from_list.assert_called_once()
        mock_thread_manager.execute_and_verify.assert_called_once()

    @patch(f"{PATH}.JIRA")
    def test_create_jira_client_basic(self, mock_jira):
        """Test creating a Jira client"""
        conf = {
            "jiraUrl": "https://example.com",
            "jiraApiToken": "token",
            "jiraUserName": "user",
        }
        _ = create_jira_client(conf, token_auth=False)
        mock_jira.assert_called_once_with(basic_auth=("user", "token"), options={"server": "https://example.com"})

    @patch(f"{PATH}.JIRA")
    def test_create_jira_client_token(self, mock_jira):
        """Test creating a Jira client with token auth"""
        from regscale.integrations.variables import ScannerVariables

        conf = {
            "jiraUrl": "https://example.com",
            "jiraApiToken": "token",
            "jiraUserName": "user",
        }
        _ = create_jira_client(conf, token_auth=True)
        mock_jira.assert_called_once_with(
            token_auth="token", options={"server": "https://example.com", "verify": ScannerVariables.sslVerify}
        )

    @staticmethod
    def test_jira_issues(jira_issues, fetch_attachments):
        """Test fetching Jira issues and creating a Jira client"""
        has_attachments = None
        if fetch_attachments:
            assert jira_issues is not None
            assert True in [True if issue.fields.attachment else False for issue in jira_issues]
        else:
            assert jira_issues is not None
            try:
                # try to access the attachment attribute
                has_attachments = [True if issue.fields.attachment else False for issue in jira_issues]
                assert len(has_attachments) == len(jira_issues)
            except AttributeError:
                # if the attribute doesn't exist, then we know there are no attachments
                assert has_attachments is None

    @staticmethod
    def test_jira_tasks(jira_tasks, fetch_attachments):
        """Test fetching Jira tasks and creating a Jira client"""
        has_attachments = None
        if fetch_attachments:
            assert jira_tasks is not None
            assert True in [True if task.fields.attachment else False for task in jira_tasks]
        else:
            assert jira_tasks is not None
            try:
                # try to access the attachment attribute
                has_attachments = [True if task.fields.attachment else False for task in jira_tasks]
                assert len(has_attachments) == len(jira_tasks)
            except AttributeError:
                # if the attribute doesn't exist, then we know there are no attachments
                assert has_attachments is None

    @staticmethod
    def test_fetch_regscale_issues_and_attachments(regscale_issues_and_attachments, fetch_attachments):
        """Test fetching RegScale issues and attachments"""
        issues, attachments = regscale_issues_and_attachments
        assert issues is not None
        if fetch_attachments:
            assert attachments is not None
        else:
            assert attachments == []

    @staticmethod
    def test_fetch_regscale_tasks_and_attachments(regscale_tasks_and_attachments, fetch_attachments):
        """Test fetching RegScale tasks and attachments"""
        tasks, attachments = regscale_tasks_and_attachments
        assert tasks is not None
        if fetch_attachments:
            assert attachments != []
        else:
            assert attachments == []

    @pytest.mark.parametrize(
        "due_date,priority,expected_days",
        [
            ("2024-12-31", "High", 7),  # Has due date
            (None, "High", 7),  # No due date, high priority
            (None, "Medium", 14),  # No due date, medium priority
            (None, "Low", 30),  # No due date, low priority
            (None, None, 14),  # No due date, no priority (defaults to medium)
        ],
    )
    @patch(f"{PATH}.datetime")
    def test_map_jira_due_date(self, mock_datetime, due_date, priority, expected_days):
        """Test mapping Jira due dates to RegScale format"""
        # Set up mock datetime to return a fixed date
        fixed_date = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = fixed_date
        mock_datetime.timedelta = timedelta  # Allow timedelta to work normally

        # Create mock Jira issue
        mock_issue = MagicMock()
        mock_issue.fields.duedate = due_date
        if priority:
            mock_issue.fields.priority = MagicMock()
            mock_issue.fields.priority.name = priority
        else:
            mock_issue.fields.priority = None

        # Create mock config
        mock_config = {"issues": {"jira": {"high": 7, "medium": 14, "low": 30}}}

        result = map_jira_due_date(mock_issue, mock_config)

        if due_date:
            assert result == due_date
        else:
            # Calculate expected date using the same fixed date
            expected_date = fixed_date + timedelta(days=expected_days)
            result_date = datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
            assert result_date.date() == expected_date.date()

    @pytest.mark.parametrize(
        "status,expected_status",
        [
            ("Done", "Closed"),
            ("In Progress", "Open"),
            ("To Do", "Open"),
        ],
    )
    def test_map_jira_to_regscale_issue(self, status, expected_status):
        """Test mapping Jira issues to RegScale format"""
        # Create mock Jira issue
        issue_status = MagicMock()
        issue_status.name = status
        mock_issue = MagicMock(
            key="TEST-123",
            fields=MagicMock(
                summary="Skipped task",
                description="Skipped task description",
                status=issue_status,
                duedate=None,
                statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
            ),
        )
        mock_issue.fields.priority = MagicMock()
        mock_issue.fields.priority.name = "High"

        # Create mock config
        mock_config = {
            "userId": "1",  # Convert to string to match Optional[str] type
            "issues": {"jira": {"status": "Open", "high": 7, "medium": 14, "low": 30}},
        }

        result = map_jira_to_regscale_issue(mock_issue, mock_config, 1, "issues")

        # Verify the Issue object was created with correct attributes
        assert isinstance(result, Issue)
        assert result.title == "Skipped task"
        assert "Skipped task description" in result.description
        assert result.status == expected_status
        assert result.jiraId == "TEST-123"
        assert result.parentId == 1
        assert result.parentModule == "issues"
        assert result.dueDate is not None  # Due date will be calculated based on priority
        if status == "Done":
            assert result.dateCompleted is not None
        else:
            assert result.dateCompleted is None

    @pytest.mark.parametrize(
        "status,expected_status,expected_percent_complete,expected_date_closed",
        [
            ("Done", "Closed", 100, True),
            ("In Progress", "Open", None, False),
            ("To Do", "Backlog", None, False),
        ],
    )
    def test_create_regscale_task_from_jira(
        self, status, expected_status, expected_percent_complete, expected_date_closed
    ):
        """Test creating RegScale tasks from Jira issues"""
        # Create mock Jira issue
        mock_issue = MagicMock()
        mock_issue.fields.summary = "Test Task"
        mock_issue.fields.description = "Test Description"
        mock_issue.fields.status.name = status
        mock_issue.fields.duedate = "2024-12-31"
        mock_issue.fields.statuscategorychangedate = "2024-01-01T12:00:00.000Z"
        mock_issue.key = "TEST-123"

        # Create mock config
        mock_config = {"issues": {"jira": {"medium": 14}}}

        result = create_regscale_task_from_jira(mock_config, mock_issue, 1, "issues")

        assert result.title == "Test Task"
        assert result.description == "Test Description"
        assert result.status == expected_status
        assert result.dueDate == "2024-12-31"
        assert result.parentId == 1
        assert result.parentModule == "issues"
        assert result.otherIdentifier == "TEST-123"
        if expected_percent_complete:
            assert result.percentComplete == expected_percent_complete
        if expected_date_closed:
            assert result.dateClosed is not None
        else:
            assert result.dateClosed is None

    def test_check_and_close_tasks(self):
        """Test checking and closing tasks"""
        jira_titles = {"Testing1234"}
        tasks = [
            Task(
                id=3,
                title="Different Title",
                status="Backlog",
                dueDate=get_current_datetime(),
                dateClosed="",
                percentComplete=0,
            ),
            Task(
                id=4,
                title="Testing1234",
                status="Backlog",
                dueDate=get_current_datetime(),
                dateClosed="",
                percentComplete=0,
            ),
        ]

        closed_tasks = check_and_close_tasks(tasks, set(jira_titles))
        assert len(closed_tasks) == 1
        assert closed_tasks[0].status == "Closed"
        assert closed_tasks[0].percentComplete == 100

    def test_process_tasks_for_sync(self):
        """Test processing tasks for sync"""
        todo_status = MagicMock()
        todo_status.name = "to do"
        in_progress_status = MagicMock()
        in_progress_status.name = "in progress"
        done_status = MagicMock()
        done_status.name = "done"
        # Create mock Jira issues
        jira_tasks = [
            MagicMock(  # should be skipped (up to date - nothing happens)
                key="JIRA-1",
                fields=MagicMock(
                    summary="Skipped task",
                    description="Skipped task description",
                    status=todo_status,
                    duedate=None,
                    statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                    priority=None,
                ),
            ),
            MagicMock(  # should be inserted (task in jira but not regscale)
                key="JIRA-2",
                fields=MagicMock(
                    summary="New task",
                    description="New task description",
                    status=todo_status,
                    duedate=None,
                    statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                    priority=None,
                ),
            ),
            MagicMock(  # should be updated (task in both but out of sync)
                key="JIRA-3",
                fields=MagicMock(
                    summary="Existing task",
                    description="Existing task description",
                    status=in_progress_status,
                    duedate=None,
                    statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                    priority=None,
                ),
            ),
            MagicMock(  # should be updated
                key="JIRA-4",
                fields=MagicMock(
                    summary="Existing task",
                    description="Existing task description",
                    status=todo_status,
                    duedate=None,
                    statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                    priority=None,
                ),
            ),
            MagicMock(  # should be closed
                key="JIRA-5",
                fields=MagicMock(
                    summary="Existing task",
                    description="Existing task description",
                    status=done_status,
                    duedate=None,
                    statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                    priority=None,
                ),
            ),
            MagicMock(  # date to be updated
                key="JIRA-6",
                fields=MagicMock(
                    summary="Existing task",
                    description="Existing task description",
                    status=todo_status,
                    duedate="2024-12-31",
                    statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                    priority=None,
                ),
            ),
        ]
        regscale_tasks = [
            Task(  # matches JIRA-1 (should be skipped - up to date)
                id=1,
                title="Skipped task",
                status="Backlog",
                description="Skipped task description",
                otherIdentifier="JIRA-1",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
                dueDate=get_current_datetime(),
            ),
            Task(  # matches JIRA-3 (should be updated - task in both but out of sync)
                id=3,
                title="Existing task",
                status="Open",
                description="Different description",  # Different description to show sync needed
                otherIdentifier="JIRA-3",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
                dueDate=get_current_datetime(),
            ),
            Task(  # matches JIRA-4 (should be updated - regscale closed but jira open)
                id=4,
                title="Existing task",
                status="Closed",  # Closed in RegScale but open in Jira
                description="Existing task description",
                otherIdentifier="JIRA-4",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
                dueDate=get_current_datetime(),
            ),
            Task(  # matches JIRA-5 (should be closed - jira closed but regscale open)
                id=5,
                title="Existing task",
                status="Open",  # Open in RegScale but closed in Jira
                description="Existing task description",
                otherIdentifier="JIRA-5",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
                dueDate=get_current_datetime(),
            ),
            Task(
                id=6,
                title="New task",
                status="Backlog",
                description="Not in jira",
                otherIdentifier="JIRA-19",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
            ),
            Task(
                id=7,
                title="Existing task",
                status="Backlog",
                description="Existing task description",
                otherIdentifier="JIRA-6",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
                dueDate="2023-01-01",
            ),
        ]

        progress = MagicMock(spec=Progress)
        progress_task = MagicMock()

        insert_tasks, update_tasks, close_tasks = process_tasks_for_sync(
            config=self.config,
            jira_issues=jira_tasks,
            existing_tasks=regscale_tasks,
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            progress=progress,
            progress_task=progress_task,
        )

        # Assertions
        assert len(insert_tasks) == 1  # New task should be inserted
        assert len(update_tasks) == 3  # No updates needed
        assert len(close_tasks) == 1  # Existing task should be closed

    @patch(f"{PATH}.process_tasks_for_sync")
    @patch(f"{PATH}.task_and_attachments_sync")
    @patch("regscale.core.app.api.Api")
    @patch(f"{PATH}.ThreadPoolExecutor")
    @patch(f"{PATH}.as_completed")
    def test_create_and_update_regscale_tasks(
        self, mock_as_completed, mock_thread_pool, mock_api, mock_task_sync, mock_process_tasks_for_sync
    ):
        """Test creating and updating RegScale tasks from Jira tasks"""
        # Setup mock tasks
        insert_tasks = [
            Task(
                id=1,
                title="New task",
                status="Backlog",
                description="New task description",
                otherIdentifier="JIRA-19",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
            )
        ]
        update_tasks = [
            Task(
                id=2,
                title="Existing task",
                status="Open",
                description="Existing task description",
                otherIdentifier="JIRA-3",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
            )
        ]
        close_tasks = [
            Task(
                id=3,
                title="Existing task",
                status="Closed",
                description="Existing task description",
                otherIdentifier="JIRA-5",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
            )
        ]
        mock_process_tasks_for_sync.return_value = (insert_tasks, update_tasks, close_tasks)

        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance
        mock_api_instance.app.config = self.config

        # Setup mock thread pool
        mock_executor = MagicMock()
        mock_thread_pool.return_value.__enter__.return_value = mock_executor

        # Setup task_and_attachments_sync to return None
        mock_task_sync.return_value = None

        # Make as_completed return an empty iterator
        mock_as_completed.return_value = []

        inserted, updated, closed = create_and_update_regscale_tasks(
            jira_issues=[],
            existing_tasks=[],
            jira_client=MagicMock(),
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            progress=MagicMock(spec=Progress),
            progress_task=MagicMock(),
        )

        assert inserted == 1
        assert updated == 1
        assert closed == 1

        mock_thread_pool.assert_called_once_with(max_workers=10)
        assert mock_executor.submit.call_count == 3

    @patch(f"{PATH}.compare_files_for_dupes_and_upload")
    def test_tasks_and_attachments_sync_create(self, mock_compare_files_for_dupes_and_upload):
        """Test performing create operation on tasks in task_and_attachments_sync"""
        # check if operation fails
        mock_task = MagicMock()
        mock_task.create.return_value = None
        task_and_attachments_sync(
            operation="create",
            task=mock_task,
            jira_client=MagicMock(),
            api=MagicMock(),
        )
        mock_task.create.assert_called_once()
        mock_compare_files_for_dupes_and_upload.assert_not_called()

        # check if operation is successful
        mock_task.create.reset_mock()
        mock_task.create.return_value = MagicMock()
        task_and_attachments_sync(
            operation="create",
            task=mock_task,
            jira_client=MagicMock(),
            api=MagicMock(),
        )
        mock_task.create.assert_called_once()
        mock_compare_files_for_dupes_and_upload.assert_called_once()

    @pytest.mark.parametrize("operation", ["update", "close"])
    @patch(f"{PATH}.compare_files_for_dupes_and_upload")
    def test_tasks_and_attachments_sync_save(self, mock_compare_files_for_dupes_and_upload, operation):
        """Test performing save operation on tasks in task_and_attachments_sync"""
        # check if operation fails
        mock_task = MagicMock()
        mock_task.save.return_value = None
        task_and_attachments_sync(
            operation=operation,
            task=mock_task,
            jira_client=MagicMock(),
            api=MagicMock(),
        )
        mock_task.save.assert_called_once()
        mock_compare_files_for_dupes_and_upload.assert_not_called()

        # check if operation is successful
        mock_task.save.reset_mock()
        mock_task.save.return_value = MagicMock()
        task_and_attachments_sync(
            operation=operation,
            task=mock_task,
            jira_client=MagicMock(),
            api=MagicMock(),
        )
        mock_task.save.assert_called_once()
        mock_compare_files_for_dupes_and_upload.assert_called_once()

    @patch(f"{PATH}.compare_files_for_dupes_and_upload")
    @patch(f"{PATH}.map_jira_to_regscale_issue")
    @patch(f"{PATH}.Issue.save")
    @patch(f"{PATH}.job_progress", return_value=MagicMock(spec=Progress))
    def test_create_and_update_regscale_issues(
        self,
        mock_job_progress_object,
        mock_update_issue,
        mock_map_jira_to_regscale_issue,
        mock_compare_files_for_dupes_and_upload,
        fetch_attachments,
    ):
        """Test creating and updating RegScale issues from Jira issues"""
        open_status = MagicMock()
        open_status.name = "open"
        in_progress_status = MagicMock()
        in_progress_status.name = "in progress"
        closed_status = MagicMock()
        closed_status.name = "done"

        highest_priority = MagicMock()
        highest_priority.name = "highest"
        high_priority = MagicMock()
        high_priority.name = "high"
        medium_priority = MagicMock()
        medium_priority.name = "medium"
        low_priority = MagicMock()
        low_priority.name = "low"
        lowest_priority = MagicMock()
        lowest_priority.name = "lowest"

        # Create mock Jira issues
        jira_issue_1 = MagicMock(  # should be updated (existing issue)
            key="JIRA-1",
            fields=MagicMock(
                summary="Skipped issue",
                description="Skipped issue description",
                status=open_status,
                duedate=None,
                priority=highest_priority,
                statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                attachment=[MagicMock()],  # Has attachments
            ),
        )
        jira_issue_2 = MagicMock(  # should be inserted (issue in jira but not regscale)
            key="JIRA-2",
            fields=MagicMock(
                summary="New issue",
                description="New issue description",
                status=open_status,
                duedate=None,
                priority=medium_priority,
                statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                attachment=None,
            ),
        )
        jira_issue_3 = MagicMock(  # should be updated (issue in both but out of sync)
            key="JIRA-3",
            fields=MagicMock(
                summary="Existing issue",
                description="Existing issue description",
                status=in_progress_status,
                duedate=None,
                priority=low_priority,
                statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                attachment=None,  # No attachments
            ),
        )
        jira_issue_4 = MagicMock(  # should be closed - counts as updated
            key="JIRA-4",
            fields=MagicMock(
                summary="Existing issue",
                description="Existing issue description",
                status=closed_status,
                duedate=None,
                priority=lowest_priority,
                statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                attachment=None,  # No attachments
            ),
        )

        # Create RegScale issues
        regscale_issues = [
            Issue(  # matches JIRA-1 (should be updated)
                id=1,
                title="Skipped issue",
                status="Open",
                description="Skipped issue description",
                jiraId="JIRA-1",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
                dueDate=get_current_datetime(),
                identification=f"{self.title_prefix} Jira Issue Integration Test",
            ),
            Issue(  # matches JIRA-3 (should be updated - issue in both but out of sync)
                id=3,
                title="Existing issue",
                status="Open",
                description="Different description",  # Different description to show sync needed
                jiraId="JIRA-3",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
                dueDate=get_current_datetime(),
                identification=f"{self.title_prefix} Jira Issue Integration Test",
            ),
            Issue(  # matches JIRA-4 (should be closed - jira closed but regscale open)
                id=4,
                title="Existing issue",
                status="Open",  # Open in RegScale but closed in Jira
                description="Existing issue description",
                jiraId="JIRA-4",
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
                dueDate=get_current_datetime(),
                identification=f"{self.title_prefix} Jira Issue Integration Test",
            ),
        ]

        # Create mock config with priority mappings from init.yaml
        config = {
            "issues": {"jira": {"highest": 7, "high": 30, "medium": 90, "low": 180, "lowest": 365, "status": "Open"}},
            "maxThreads": 4,
            "userId": "123e4567-e89b-12d3-a456-426614174000",
        }
        app = MagicMock()
        app.config = config

        # Setup mock return values
        mock_update_issue.return_value = MagicMock()

        # Mock the creation of a new issue
        created_issue_mock = MagicMock()
        created_issue_mock.id = 2
        created_issue_mock.create.return_value = created_issue_mock
        mock_map_jira_to_regscale_issue.return_value = created_issue_mock

        with mock_job_progress_object as job_progress:
            test_task = job_progress.add_task(
                description="Processing issues",
                total=4,
                visible=False,
            )

            # Test the function with each Jira issue individually (as ThreadManager would call it)
            # JIRA-1: existing issue with matching jiraId and attachments
            create_and_update_regscale_issues(
                jira_issue_1,
                regscale_issues,
                False,
                fetch_attachments,
                MagicMock(),
                app,
                self.PARENT_ID,
                self.PARENT_MODULE,
                test_task,
                job_progress,
            )

            # JIRA-2: new issue (not in regscale_issues)
            create_and_update_regscale_issues(
                jira_issue_2,
                regscale_issues,
                False,
                fetch_attachments,
                MagicMock(),
                app,
                self.PARENT_ID,
                self.PARENT_MODULE,
                test_task,
                job_progress,
            )

            # JIRA-3: existing issue to be updated
            create_and_update_regscale_issues(
                jira_issue_3,
                regscale_issues,
                False,
                fetch_attachments,
                MagicMock(),
                app,
                self.PARENT_ID,
                self.PARENT_MODULE,
                test_task,
                job_progress,
            )

            # JIRA-4: existing issue to be closed
            create_and_update_regscale_issues(
                jira_issue_4,
                regscale_issues,
                False,
                fetch_attachments,
                MagicMock(),
                app,
                self.PARENT_ID,
                self.PARENT_MODULE,
                test_task,
                job_progress,
            )

            # Verify update_issue was called 3 times (JIRA-1, JIRA-3, JIRA-4)
            assert mock_update_issue.call_count == 3
            # Verify map_jira_to_regscale_issue was called once for JIRA-2 (new issue)
            assert mock_map_jira_to_regscale_issue.call_count == 1
            # Verify attachment handling
            if fetch_attachments:
                # Only JIRA-1 has attachments in fields.attachment
                assert mock_compare_files_for_dupes_and_upload.call_count == 1
            else:
                assert mock_compare_files_for_dupes_and_upload.call_count == 0

    @patch(f"{PATH}.create_issue_in_jira")
    def test_sync_regscale_issues_to_jira(self, mock_create_issue_in_jira, fetch_attachments):
        """Test inserting Regscale issues into jira if they do not exist"""

        # Create RegScale issues
        regscale_objects = [
            Issue(
                id=1,
                title="Test Issue",
                status="Open",
                description="This is a test issue",
                dueDate=get_current_datetime(),
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
                identification=f"{self.title_prefix} Jira Issue Integration Test",
            ),
            Issue(
                id=3,
                title="Test Issue with Jira ID",
                status="Open",
                description="This is a test issue with Jira ID",
                dueDate=get_current_datetime(),
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
                jiraId="JIRA-3",
                identification=f"{self.title_prefix} Jira Issue Integration Test",
            ),
        ]

        # Create mock Jira issues
        open_status = MagicMock()
        open_status.name = "open"

        returned_jira_issues = [
            MagicMock(
                key="JIRA-1",
                fields=MagicMock(
                    summary="Test Issue",
                    description="This is a test issue",
                    status=open_status,
                    duedate=None,
                    statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                    attachment=None,
                ),
            )
        ]

        mock_create_issue_in_jira.side_effect = returned_jira_issues

        new_regscale_objects = sync_regscale_to_jira(
            regscale_objects=regscale_objects,
            jira_client=MagicMock(),
            jira_project=self.JIRA_PROJECT,
            jira_issue_type="Issue",  # Using Issue type for issues
            sync_attachments=fetch_attachments,
            attachments={},
            api=MagicMock(),
        )

        assert len(new_regscale_objects) == 1  # Only one new issue should be created
        assert mock_create_issue_in_jira.call_count == 1  # Should only be called once for the issue without Jira ID
        assert new_regscale_objects[0].jiraId == "JIRA-1"

    @patch(f"{PATH}.create_issue_in_jira")
    def test_sync_regscale_tasks_to_jira(self, mock_create_issue_in_jira, fetch_attachments):
        """Test inserting Regscale tasks into jira if they do not exist"""

        # Create RegScale tasks
        regscale_objects = [
            Task(
                id=2,
                title="Test Task",
                status="Backlog",
                description="This is a test task",
                dueDate=get_current_datetime(),
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
            ),
            Task(
                id=4,
                title="Test Task with Other ID",
                status="Backlog",
                description="This is a test task with other ID",
                dueDate=get_current_datetime(),
                parentId=self.PARENT_ID,
                parentModule=self.PARENT_MODULE,
                otherIdentifier="JIRA-4",
            ),
        ]

        # Create mock Jira issues
        todo_status = MagicMock()
        todo_status.name = "to do"

        returned_jira_issues = [
            MagicMock(
                key="JIRA-2",
                fields=MagicMock(
                    summary="Test Task",
                    description="This is a test task",
                    status=todo_status,
                    duedate=None,
                    statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                    attachment=None,
                ),
            )
        ]

        mock_create_issue_in_jira.side_effect = returned_jira_issues

        new_regscale_objects = sync_regscale_to_jira(
            regscale_objects=regscale_objects,
            jira_client=MagicMock(),
            jira_project=self.JIRA_PROJECT,
            jira_issue_type="Task",  # Using Task type for tasks
            sync_attachments=fetch_attachments,
            attachments={},
            api=MagicMock(),
        )

        assert len(new_regscale_objects) == 1  # Only one new task should be created
        assert mock_create_issue_in_jira.call_count == 1  # Should only be called once for the task without Jira ID
        assert new_regscale_objects[0].otherIdentifier == "JIRA-2"

    def test_generate_jira_comment(self):
        """Test generating a Jira comment from a RegScale issue"""
        # Create issue with mix of included and excluded fields
        issue = Issue(
            id=1,
            title="Test Issue",
            status="Open",
            description="Test description",
            createdById="excluded-1",
            lastUpdatedById="excluded-2",
            issueOwnerId="excluded-3",
            assignedToId="excluded-4",
            uuid="excluded-5",
            jiraId="JIRA-123",
            severityLevel="High",
            dueDate="2023-12-31",
            identification=f"{self.title_prefix} Jira Issue Integration Test",
        )

        comment = _generate_jira_comment(issue)

        # Verify excluded fields are not in comment
        assert "createdById" not in comment
        assert "lastUpdatedById" not in comment
        assert "issueOwnerId" not in comment
        assert "assignedToId" not in comment
        assert "uuid" not in comment

        # Verify included fields are in comment
        assert "**jiraId:** JIRA-123" in comment
        assert "**severityLevel:** High" in comment
        assert "**dueDate:** 2023-12-31" in comment
        assert "**title:** Test Issue" in comment
        assert "**status:** Open" in comment
        assert "**description:** Test description" in comment

    def test_generate_jira_comment_task(self):
        """Test generating a Jira comment from a RegScale task"""
        # Create task with mix of included and excluded fields
        task = Task(
            id=1,
            title="Test Task",
            status="Backlog",
            description="Test task description",
            createdById="excluded-1",
            lastUpdatedById="excluded-2",
            assignedToId="excluded-3",
            uuid="excluded-4",
            otherIdentifier="JIRA-123",
            percentComplete=50,
            dueDate="2023-12-31",
            identification=f"{self.title_prefix} Jira Issue Integration Test",
        )

        comment = _generate_jira_comment(task)

        # Verify excluded fields are not in comment
        assert "createdById" not in comment
        assert "lastUpdatedById" not in comment
        assert "assignedToId" not in comment
        assert "uuid" not in comment

        # Verify included fields are in comment
        assert "**otherIdentifier:** JIRA-123" in comment
        assert "**percentComplete:** 50" in comment
        assert "**dueDate:** 2023-12-31" in comment
        assert "**title:** Test Task" in comment
        assert "**status:** Backlog" in comment
        assert "**description:** Test task description" in comment

    def test_create_issue_in_jira(self, regscale_issues_and_attachments, jira_client, fetch_attachments):
        """Test creating an issue in Jira"""
        issues, attachments = regscale_issues_and_attachments
        for issue in issues:
            jira_issue = create_issue_in_jira(
                regscale_object=issue,
                jira_client=jira_client,
                jira_project=self.JIRA_PROJECT,
                issue_type="Bug",
                add_attachments=fetch_attachments,
                attachments=attachments,
                api=self.api,
            )

            assert jira_issue is not None
            assert jira_issue.key is not None
            assert jira_issue.fields.summary == issue.title
            assert issue.description in jira_issue.fields.description

            jira_issue.delete()  # cleanup issue in jira

    def test_create_task_in_jira(self, regscale_tasks_and_attachments, jira_client, fetch_attachments):
        """Test creating a task in Jira"""
        tasks, attachments = regscale_tasks_and_attachments
        for task in tasks:
            jira_task = create_issue_in_jira(
                regscale_object=task,
                jira_client=jira_client,
                jira_project=self.JIRA_PROJECT,
                issue_type="Task",
                add_attachments=fetch_attachments,
                attachments=attachments,
                api=self.api,
            )

            assert jira_task is not None
            assert jira_task.key is not None
            assert jira_task.fields.summary == task.title
            assert task.description in jira_task.fields.description

            jira_task.delete()  # cleanup task in jira

    def test_create_issue_in_jira_error(self):
        """Test that we exit when Jira API call fails"""
        # Create a mock Jira client that will raise an error
        mock_jira_client = MagicMock()
        mock_jira_client.create_issue.side_effect = JIRAError("Test error")

        mock_regscale = MagicMock()
        mock_regscale.get_module_string.return_value = "issues"
        mock_regscale.id = 1

        mock_api = MagicMock()
        mock_api.config = {"domain": "https://test.regscale.com"}

        with pytest.raises(SystemExit) as e:
            create_issue_in_jira(
                regscale_object=mock_regscale,
                jira_client=mock_jira_client,
                jira_project=self.JIRA_PROJECT,
                issue_type="Bug",
                add_attachments=True,
                attachments={},
                api=mock_api,
            )
        assert e.value.code == 1
        assert e.type == SystemExit

    def test_upload_files_to_jira(self, jira_client):
        """Test uploading files to Jira"""
        # create a jira issue to upload attachment to
        jira_issue = jira_client.create_issue(
            project=self.JIRA_PROJECT,
            summary="Test Issue",
            description="Test Description",
            issuetype={"name": "Bug"},
        )

        # create regscale issue to link to
        reg_issue = Issue(
            id=1,
            title="Test Issue",
            description="Test Description",
            parentId=self.PARENT_ID,
            parentModule=self.PARENT_MODULE,
            identification=f"{self.title_prefix} Jira Issue Integration Test",
        )

        # setup file hashes for upload
        file_path = os.path.join(self.get_tests_dir("tests"), "test_data", "jira_attachments", "attachment.txt")
        with open(file_path, "rb") as file:
            reg_hashes = {compute_hash(file): file_path}
        jira_hashes = {}
        uploaded_attachments = []

        upload_files_to_jira(
            jira_hashes,
            reg_hashes,
            jira_issue,
            reg_issue,
            jira_client,
            uploaded_attachments,
        )
        assert uploaded_attachments == [file_path]
        check_issue = jira_client.issue(jira_issue.key)
        assert len(check_issue.fields.attachment) == 1
        assert check_issue.fields.attachment[0].size > 0
        assert check_issue.fields.attachment[0].created is not None

        # Clean up
        jira_issue.delete()

    def test_upload_files_to_jira_duplicates(self):
        """Test that we don't upload duplicates"""
        jira_hashes = {"dummyhash": "dummy/path/file.txt"}
        reg_hashes = {"dummyhash": "dummy/path/file.txt"}
        jira_issue = MagicMock()
        reg_issue = MagicMock()
        jira_client = MagicMock()
        uploaded_attachments = []

        upload_files_to_jira(jira_hashes, reg_hashes, jira_issue, reg_issue, jira_client, uploaded_attachments)

        assert uploaded_attachments == []
        jira_client.add_attachment.assert_not_called()

    @pytest.mark.parametrize("error_type", [JIRAError, TypeError])
    @patch(f"{PATH}.open")
    def test_upload_files_to_jira_error(self, mock_open, error_type):
        """Test that uploads aren't made when errors are encountered"""
        # Setup mock file
        mock_file = MagicMock()
        mock_file.read.return_value = b"test content"
        mock_open.return_value.__enter__.return_value = mock_file

        # Setup test data
        file_path = "dummy/path/file.txt"
        reg_hashes = {"dummyhash": file_path}
        jira_hashes = {}
        jira_issue = MagicMock()
        reg_issue = MagicMock()
        jira_client = MagicMock()
        jira_client.add_attachment.side_effect = error_type("Test error")
        uploaded_attachments = []

        upload_files_to_jira(jira_hashes, reg_hashes, jira_issue, reg_issue, jira_client, uploaded_attachments)

        assert uploaded_attachments == []
        jira_client.add_attachment.assert_called_once()
        mock_file.read.assert_called_once()

    def test_upload_files_to_regscale(self):
        """Test uploading files to RegScale"""
        tmp = Issue(
            id=1,
            title="Test Issue",
            description="Test Description",
            parentId=self.PARENT_ID,
            parentModule=self.PARENT_MODULE,
            dueDate=get_current_datetime(),
            status="Open",
            identification=f"{self.title_prefix} Jira Issue Integration Test",
        )
        reg_issue = tmp.create()

        file_path = os.path.join(self.get_tests_dir("tests"), "test_data", "jira_attachments", "attachment.txt")
        with open(file_path, "rb") as file:
            jira_hashes = {compute_hash(file): file_path}
        reg_hashes = {}
        uploaded_attachments = []

        upload_files_to_regscale(jira_hashes, reg_hashes, reg_issue, self.api, uploaded_attachments)

        assert uploaded_attachments == [file_path]
        check_issues, attachments = Issue.get_objects_and_attachments_by_parent(
            parent_id=self.PARENT_ID, parent_module=self.PARENT_MODULE
        )
        assert reg_issue in check_issues
        assert len(attachments[reg_issue.id]) == 1

    @patch(f"{PATH}.File.upload_file_to_regscale", return_value=None)
    def test_upload_files_to_regscale_duplicates(self, mock_upload_file_to_regscale):
        """Test that we don't upload duplicate attachments to regscale"""
        jira_hashes = {"dummyhash": "dummy/path/file.txt"}
        reg_hashes = {"dummyhash": "dummy/path/file.txt"}
        reg_issue = MagicMock()
        uploaded_attachments = []

        upload_files_to_regscale(jira_hashes, reg_hashes, reg_issue, MagicMock(), uploaded_attachments)

        assert uploaded_attachments == []
        mock_upload_file_to_regscale.assert_not_called()

    @patch(f"{PATH}.File.upload_file_to_regscale", return_value=None)
    @patch(f"{PATH}.open")
    def test_upload_files_to_regscale_error(self, mock_open, mock_upload_file_to_regscale):
        """Test when the uploads are unsuccessful"""
        mock_file = MagicMock()
        mock_file.read.return_value = b"test content"
        mock_open.return_value.__enter__.return_value = mock_file

        # Setup test data
        file_path = "dummy/path/file.txt"
        jira_hashes = {"dummyhash": file_path}
        reg_hashes = {}
        reg_issue = MagicMock()
        uploaded_attachments = []
        api = MagicMock()

        upload_files_to_regscale(jira_hashes, reg_hashes, reg_issue, api, uploaded_attachments)

        assert uploaded_attachments == []
        mock_upload_file_to_regscale.assert_called_once()

    def test_validate_issue_type(self):
        """Test validating the issue type"""
        jira_client = MagicMock()
        issue_type_bug = MagicMock()
        issue_type_bug.name = "Bug"
        issue_type_task = MagicMock()
        issue_type_task.name = "Task"
        jira_client.issue_types.return_value = [issue_type_bug, issue_type_task]
        assert validate_issue_type(jira_client, "Bug") is True
        assert validate_issue_type(jira_client, "Task") is True
        # Now returns False instead of raising SystemExit for invalid types
        assert validate_issue_type(jira_client, "Invalid") is False

    def test_download_issue_attachments(self, regscale_issues_and_attachments, get_jira_issue_with_attachment):
        """Test downloading attachments from Jira and RegScale issues"""
        issues, attachments = regscale_issues_and_attachments
        jira_issue = get_jira_issue_with_attachment
        if attachments:
            with tempfile.TemporaryDirectory() as tmpdir:
                download_regscale_attachments_to_directory(
                    directory=tmpdir,
                    jira_issue=jira_issue,
                    regscale_object=issues[0],
                    api=self.api,
                )
                assert os.path.exists(tmpdir) is True
        with tempfile.TemporaryDirectory() as tmpdir:
            download_regscale_attachments_to_directory(
                directory=tmpdir,
                jira_issue=jira_issue,
                regscale_object=issues[0],
                api=self.api,
            )
            assert os.path.exists(tmpdir) is True

    def test_download_task_attachments(self, regscale_tasks_and_attachments, get_jira_task_with_attachment):
        """Test downloading attachments from Jira and RegScale tasks"""
        tasks, attachments = regscale_tasks_and_attachments
        jira_task = get_jira_task_with_attachment
        if attachments:
            with tempfile.TemporaryDirectory() as tmpdir:
                download_regscale_attachments_to_directory(
                    directory=tmpdir,
                    jira_issue=jira_task,
                    regscale_object=tasks[0],
                    api=self.api,
                )
                assert os.path.exists(tmpdir) is True
        with tempfile.TemporaryDirectory() as tmpdir:
            download_regscale_attachments_to_directory(
                directory=tmpdir,
                jira_issue=jira_task,
                regscale_object=tasks[0],
                api=self.api,
            )
            assert os.path.exists(tmpdir) is True

    @patch(f"{PATH}.sync_regscale_objects_to_jira")
    @patch(f"{PATH}.sync_regscale_to_jira", return_value=[])
    @patch(f"{PATH}.create_jira_client")
    @patch(f"{PATH}.fetch_jira_objects")
    @patch(f"{PATH}.get_regscale_data_and_attachments")
    @patch(f"{PATH}.Api", return_value=MagicMock(spec=Api))
    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_and_jira_with_poams_true(
        self,
        mock_check_license,
        mock_api,
        mock_get_regscale_data_and_attachments,
        mock_fetch_jira_objects,
        mock_create_jira_client,
        mock_sync_regscale_to_jira,
        mock_sync_regscale_objects_to_jira,
        fetch_attachments,
    ):
        """Test sync_regscale_and_jira with use_poams=True"""
        # Setup mocks
        mock_jira_client = MagicMock()
        mock_create_jira_client.return_value = mock_jira_client
        mock_fetch_jira_objects.return_value = [MagicMock()]
        mock_get_regscale_data_and_attachments.return_value = ([MagicMock()], MagicMock())

        # Call function with use_poams=True
        sync_regscale_and_jira(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            jira_project=self.JIRA_PROJECT,
            jira_issue_type="Bug",
            sync_attachments=fetch_attachments,
            use_poams=True,
        )

        # Verify sync_regscale_objects_to_jira was called with use_poams=True
        mock_sync_regscale_objects_to_jira.assert_called_once()
        call_args = mock_sync_regscale_objects_to_jira.call_args
        assert call_args[0][7] is True  # use_poams is the 8th positional argument

    @patch(f"{PATH}.sync_regscale_objects_to_jira")
    @patch(f"{PATH}.sync_regscale_to_jira", return_value=[])
    @patch(f"{PATH}.create_jira_client")
    @patch(f"{PATH}.fetch_jira_objects")
    @patch(f"{PATH}.get_regscale_data_and_attachments")
    @patch(f"{PATH}.Api", return_value=MagicMock(spec=Api))
    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_and_jira_with_poams_false(
        self,
        mock_check_license,
        mock_api,
        mock_get_regscale_data_and_attachments,
        mock_fetch_jira_objects,
        mock_create_jira_client,
        mock_sync_regscale_to_jira,
        mock_sync_regscale_objects_to_jira,
        fetch_attachments,
    ):
        """Test sync_regscale_and_jira with use_poams=False (default)"""
        # Setup mocks
        mock_jira_client = MagicMock()
        mock_create_jira_client.return_value = mock_jira_client
        mock_fetch_jira_objects.return_value = [MagicMock()]
        mock_get_regscale_data_and_attachments.return_value = ([MagicMock()], MagicMock())

        # Call function with use_poams=False (default)
        sync_regscale_and_jira(
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            jira_project=self.JIRA_PROJECT,
            jira_issue_type="Bug",
            sync_attachments=fetch_attachments,
            use_poams=False,
        )

        # Verify sync_regscale_objects_to_jira was called with use_poams=False
        mock_sync_regscale_objects_to_jira.assert_called_once()
        call_args = mock_sync_regscale_objects_to_jira.call_args
        assert call_args[0][7] is False  # use_poams is the 8th positional argument

    @patch(f"{PATH}.create_jira_client")
    @patch(f"{PATH}.create_and_update_regscale_issues")
    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    def test_sync_regscale_objects_to_jira_with_poams(
        self,
        mock_check_license,
        mock_create_and_update_regscale_issues,
        mock_create_jira_client,
        fetch_attachments,
    ):
        """Test sync_regscale_objects_to_jira passes use_poams to create_and_update_regscale_issues"""
        mock_check_license.return_value.config = self.config
        mock_jira_client = MagicMock()
        mock_create_jira_client.return_value = mock_jira_client

        # Create mock application with ThreadManager
        mock_app = MagicMock(spec=Application)
        mock_app.config = self.config
        mock_thread_manager = MagicMock()
        mock_app.thread_manager = mock_thread_manager

        # Mock Jira issues
        mock_jira_issues = [MagicMock(), MagicMock()]
        mock_regscale_objects = [MagicMock()]

        # Test with use_poams=True
        sync_regscale_objects_to_jira(
            mock_jira_issues,
            mock_regscale_objects,
            fetch_attachments,
            mock_app,
            self.PARENT_ID,
            self.PARENT_MODULE,
            False,  # sync_tasks_only
            True,  # use_poams
        )

        # Verify ThreadManager was called with correct parameters
        mock_thread_manager.submit_tasks_from_list.assert_called_once()
        call_args = mock_thread_manager.submit_tasks_from_list.call_args[0]
        # use_poams is the 4th argument (index 3) after function, jira_issues, and regscale_objects
        assert call_args[3] is True

    @patch(f"{PATH}.map_jira_to_regscale_issue")
    def test_map_jira_to_regscale_issue_with_poam_true(self, mock_map_jira_to_regscale_issue):
        """Test map_jira_to_regscale_issue sets isPoam=True when is_poam=True"""
        # Create mock Jira issue
        mock_issue = MagicMock()
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = "Test Description"
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.priority.name = "High"
        mock_issue.fields.duedate = None
        mock_issue.key = "TEST-123"

        # Create mock config
        mock_config = {
            "userId": "1",
            "issues": {"jira": {"status": "Open", "high": 7, "medium": 14, "low": 30}},
        }

        # Call the actual function with is_poam=True
        result = map_jira_to_regscale_issue(
            jira_issue=mock_issue,
            config=mock_config,
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            is_poam=True,
        )

        # Verify the Issue object was created with isPoam=True
        assert isinstance(result, Issue)
        assert result.isPoam is True
        assert result.title == "Test Issue"
        assert result.jiraId == "TEST-123"

    @patch(f"{PATH}.map_jira_to_regscale_issue")
    def test_map_jira_to_regscale_issue_with_poam_false(self, mock_map_jira_to_regscale_issue):
        """Test map_jira_to_regscale_issue sets isPoam=False when is_poam=False"""
        # Create mock Jira issue
        mock_issue = MagicMock()
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = "Test Description"
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.priority.name = "High"
        mock_issue.fields.duedate = None
        mock_issue.key = "TEST-123"

        # Create mock config
        mock_config = {
            "userId": "1",
            "issues": {"jira": {"status": "Open", "high": 7, "medium": 14, "low": 30}},
        }

        # Call the actual function with is_poam=False
        result = map_jira_to_regscale_issue(
            jira_issue=mock_issue,
            config=mock_config,
            parent_id=self.PARENT_ID,
            parent_module=self.PARENT_MODULE,
            is_poam=False,
        )

        # Verify the Issue object was created with isPoam=False
        assert isinstance(result, Issue)
        assert result.isPoam is False
        assert result.title == "Test Issue"
        assert result.jiraId == "TEST-123"

    @patch(f"{PATH}.compare_files_for_dupes_and_upload")
    @patch(f"{PATH}.map_jira_to_regscale_issue")
    @patch(f"{PATH}.Issue.update_issue")
    @patch(f"{PATH}.job_progress", return_value=MagicMock(spec=Progress))
    def test_create_and_update_regscale_issues_sets_ispoam_on_new_issue(
        self,
        mock_job_progress_object,
        mock_update_issue,
        mock_map_jira_to_regscale_issue,
        mock_compare_files_for_dupes_and_upload,
    ):
        """Test that create_and_update_regscale_issues sets isPoam on newly created issues"""
        # Create mock Jira issue
        open_status = MagicMock()
        open_status.name = "open"
        high_priority = MagicMock()
        high_priority.name = "high"

        jira_issue = MagicMock(
            key="JIRA-NEW",
            fields=MagicMock(
                summary="New Issue",
                description="New issue description",
                status=open_status,
                duedate=None,
                priority=high_priority,
                statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                attachment=None,
            ),
        )

        # Create empty RegScale issues list (no existing issues)
        regscale_issues = []

        # Create mock config
        config = {
            "issues": {"jira": {"highest": 7, "high": 30, "medium": 90, "low": 180, "lowest": 365, "status": "Open"}},
            "maxThreads": 4,
            "userId": "123e4567-e89b-12d3-a456-426614174000",
        }
        app = MagicMock()
        app.config = config

        # Mock the creation of a new issue
        created_issue_mock = MagicMock()
        created_issue_mock.id = 999
        created_issue_mock.create.return_value = created_issue_mock
        mock_map_jira_to_regscale_issue.return_value = created_issue_mock

        with mock_job_progress_object as job_progress:
            test_task = job_progress.add_task(
                description="Processing issues",
                total=1,
                visible=False,
            )

            # Call with use_poams=True
            create_and_update_regscale_issues(
                jira_issue,
                regscale_issues,
                True,  # use_poams
                False,  # add_attachments
                MagicMock(),
                app,
                self.PARENT_ID,
                self.PARENT_MODULE,
                test_task,
                job_progress,
            )

            # Verify map_jira_to_regscale_issue was called with is_poam=True
            mock_map_jira_to_regscale_issue.assert_called_once()
            call_kwargs = mock_map_jira_to_regscale_issue.call_args[1]
            assert call_kwargs["is_poam"] is True

    @patch(f"{PATH}.compare_files_for_dupes_and_upload")
    @patch(f"{PATH}.map_jira_to_regscale_issue")
    @patch(f"{PATH}.Issue.save")
    @patch(f"{PATH}.job_progress", return_value=MagicMock(spec=Progress))
    def test_create_and_update_regscale_issues_sets_ispoam_on_existing_issue(
        self,
        mock_job_progress_object,
        mock_save,
        mock_map_jira_to_regscale_issue,
        mock_compare_files_for_dupes_and_upload,
    ):
        """Test that create_and_update_regscale_issues sets isPoam on existing issues"""
        # Create mock Jira issue
        open_status = MagicMock()
        open_status.name = "open"
        high_priority = MagicMock()
        high_priority.name = "high"

        jira_issue = MagicMock(
            key="JIRA-1",
            fields=MagicMock(
                summary="Existing Issue",
                description="Existing issue description",
                status=open_status,
                duedate=None,
                priority=high_priority,
                statuscategorychangedate="2025-06-12T12:46:34.755961+0000",
                attachment=None,
            ),
        )

        # Create existing RegScale issue (using MagicMock to avoid actual creation)
        existing_issue = MagicMock(spec=Issue)
        existing_issue.jiraId = "JIRA-1"
        existing_issue.isPoam = False  # Initially not a POAM
        existing_issue.id = 1
        existing_issue.title = "Existing Issue"
        regscale_issues = [existing_issue]

        # Create mock config
        config = {
            "issues": {"jira": {"highest": 7, "high": 30, "medium": 90, "low": 180, "lowest": 365, "status": "Open"}},
            "maxThreads": 4,
            "userId": "123e4567-e89b-12d3-a456-426614174000",
            "jiraCustomFields": {},
        }
        app = MagicMock()
        app.config = config

        # Setup mock return values
        mock_save.return_value = MagicMock()

        with mock_job_progress_object as job_progress:
            test_task = job_progress.add_task(
                description="Processing issues",
                total=1,
                visible=False,
            )

            # Call with use_poams=True
            create_and_update_regscale_issues(
                jira_issue,
                regscale_issues,
                True,  # use_poams
                False,  # add_attachments
                MagicMock(),
                app,
                self.PARENT_ID,
                self.PARENT_MODULE,
                test_task,
                job_progress,
            )

            # Verify the existing issue had isPoam set to True
            assert existing_issue.isPoam is True

    @staticmethod
    def teardown_class(cls):
        """Remove test data"""
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree("./artifacts")
            assert not os.path.exists("./artifacts")
