#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for GitLab integration in RegScale CLI
"""
import unittest
from unittest.mock import MagicMock, Mock, patch

from regscale.integrations.commercial.gitlab import (
    # run_sync_issues,
    get_issues_from_gitlab,
    get_regscale_issues,
    save_or_update_issues,
    extract_links_with_labels,
    convert_issues,
)
from regscale.models.regscale_models.issue import Issue
from regscale.models.regscale_models.link import Link
from tests import CLITestFixture


class TestGitLabIntegration(CLITestFixture, unittest.TestCase):
    @patch("regscale.integrations.commercial.gitlab.check_license")
    @patch("regscale.integrations.commercial.gitlab.Issue")
    @patch("regscale.integrations.commercial.gitlab.logger")
    def test_get_regscale_issues_securityplans(self, mock_logger, mock_issue, mock_check_license):
        # Mocking the check_license function
        mock_app = MagicMock()
        mock_check_license.return_value = mock_app

        # Mocking the fetch_issues_by_ssp method and setting return value
        mock_issue.fetch_issues_by_ssp.return_value = ["issue1", "issue2"]

        # Mocking the job_progress object
        mock_job_progress = MagicMock()
        mock_task = MagicMock()
        mock_job_progress.add_task.return_value = mock_task

        # Call the method to test
        issues = get_regscale_issues(1, "securityplans", mock_job_progress)

        # Assertions to check if the results are as expected
        self.assertEqual(len(issues), 2)
        mock_logger.info.assert_called_with("Fetched 2 issues from RegScale by SSP.")
        mock_job_progress.add_task.assert_called_once()
        mock_job_progress.update.assert_called_with(mock_task, advance=1)

    @patch("regscale.integrations.commercial.gitlab.check_license")
    @patch("regscale.integrations.commercial.gitlab.Issue")
    @patch("regscale.integrations.commercial.gitlab.logger")
    def test_get_regscale_issues_not_securityplan(self, mock_logger, mock_issue, mock_check_license):
        # Mocking the check_license function
        mock_app = MagicMock()
        mock_check_license.return_value = mock_app

        # Mocking the fetch_issues_by_parent method and setting return value
        mock_issue.fetch_issues_by_parent.return_value = ["issue1", "issue2"]

        # Mocking the job_progress object
        mock_job_progress = MagicMock()
        mock_task = MagicMock()
        mock_job_progress.add_task.return_value = mock_task

        # Call the method to test
        issues = get_regscale_issues(1, "not_securityplans", mock_job_progress)

        # Assertions to check if the results are as expected
        self.assertEqual(len(issues), 2)
        mock_logger.info.assert_called_with("Fetched 2 issues from RegScale by issue parent.")
        mock_job_progress.add_task.assert_called_once()
        mock_job_progress.update.assert_called_with(mock_task, advance=1)

    @patch("regscale.integrations.commercial.gitlab.check_license")
    @patch("regscale.integrations.commercial.gitlab.Issue")
    def test_save_issues(self, mock_issue, mock_check_license):
        """Test save_or_update_issues function intended to save"""
        mock_app = MagicMock()
        mock_check_license.return_value = mock_app

        # Mocking the job_progress object
        mock_job_progress = MagicMock()
        mock_task = MagicMock()
        mock_job_progress.add_task.return_value = mock_task

        gitlab_issues = [
            {
                "issue": Issue(
                    id=1,
                    title="Issue 1",
                    description="Description 1",
                    status="Open",
                    severityLevel="Low",
                    dependabotId="1",
                ),
                "links": [],
            }
        ]

        regscale_issues = [
            Issue(
                id=1,
                title="Issue 2",
                description="Description 2",
                status="Open",
                severityLevel="Low",
                dependabotId="2",
            )
        ]

        # mock the api call
        mock_issue.insert_issue.return_value = gitlab_issues[0]["issue"]

        # gitlab dependabot id not in regscale, will save new issue
        save_or_update_issues(gitlab_issues, regscale_issues, mock_job_progress)

        # Verify the issue was inserted with correct parameters
        mock_issue.insert_issue.assert_called_once_with(app=mock_app, issue=gitlab_issues[0]["issue"])

        # Verify job progress was updated
        mock_job_progress.update.assert_called_with(mock_task, advance=1)

    @patch("regscale.integrations.commercial.gitlab.check_license")
    @patch("regscale.integrations.commercial.gitlab.Issue")
    @patch("regscale.integrations.commercial.gitlab.Link")
    def test_save_issues_with_links(self, mock_link, mock_issue, mock_check_license):
        """Test save_or_update_issues function intended to save with links in gitlab issue"""
        mock_app = MagicMock()
        mock_check_license.return_value = mock_app

        # Mocking the job_progress object
        mock_job_progress = MagicMock()
        mock_task = MagicMock()
        mock_job_progress.add_task.return_value = mock_task

        gitlab_issues = [
            {
                "issue": Issue(
                    id=1,
                    title="Issue 1",
                    description="Description 1",
                    status="Open",
                    severityLevel="Low",
                    dependabotId="1",
                ),
                "links": [
                    Link(
                        id=None,
                        title="Link to GitLab repo",
                        url="https://www.gitlab.com",
                        createdById=None,
                        lastUpdatedById=None,
                        dateLastUpdated=None,
                        isPublic=True,
                    ),
                ],
            }
        ]

        regscale_issues = [
            Issue(
                id=1,
                title="Issue 2",
                description="Description 2",
                status="Open",
                severityLevel="Low",
                dependabotId="2",
            )
        ]

        # mock the api calls
        mock_issue.insert_issue.return_value = gitlab_issues[0]["issue"]
        mock_link.insert_link.return_value = gitlab_issues[0]["links"][0]

        # gitlab dependabot id not in regscale, will save new issue
        save_or_update_issues(gitlab_issues, regscale_issues, mock_job_progress)

        # Verify the issue was inserted with correct parameters
        mock_issue.insert_issue.assert_called_once_with(app=mock_app, issue=gitlab_issues[0]["issue"])

        # verify the link was inserted with correct parameters
        mock_link.insert_link.assert_called_once_with(app=mock_app, link=gitlab_issues[0]["links"][0])

        # Verify job progress was updated
        mock_job_progress.update.assert_called_with(mock_task, advance=1)

    @patch("regscale.integrations.commercial.gitlab.check_license")
    @patch("regscale.integrations.commercial.gitlab.Issue")
    def test_update_issues(self, mock_issue, mock_check_license):
        """Test save_or_update_issues function intended to update"""
        mock_app = MagicMock()
        mock_check_license.return_value = mock_app

        # Mocking the job_progress object
        mock_job_progress = MagicMock()
        mock_task = MagicMock()
        mock_job_progress.add_task.return_value = mock_task

        gitlab_issues = [
            {
                "issue": Issue(
                    id=1,
                    title="Issue 1",
                    description="Description 1",
                    status="Closed",
                    severityLevel="High",
                    dependabotId="1",
                ),
                "links": [],
            }
        ]

        regscale_issues = [
            Issue(
                id=2,
                title="Issue 2",
                description="Description 2",
                status="Open",
                severityLevel="Low",
                dependabotId="1",
            )
        ]

        # Verify the issues are different
        self.assertNotEqual(
            gitlab_issues[0]["issue"], regscale_issues[0], "Issues should be different but __eq__ is returning True"
        )

        # mock api call
        mock_issue.update_issue.return_value = gitlab_issues[0]["issue"]

        save_or_update_issues(gitlab_issues, regscale_issues, mock_job_progress)

        # Verify the issue was updated with correct parameters
        mock_issue.update_issue.assert_called_once_with(app=mock_app, issue=gitlab_issues[0]["issue"])

        # Verify job progress was updated
        mock_job_progress.update.assert_called_with(mock_task, advance=1)

    @patch("regscale.integrations.commercial.gitlab.check_license")
    @patch("regscale.integrations.commercial.gitlab.Issue")
    @patch("regscale.integrations.commercial.gitlab.Link")
    def test_update_issues_with_links(self, mock_link, mock_issue, mock_check_license):
        """Test save_or_update_issues function intended to update with links in gitlab issue"""
        mock_app = MagicMock()
        mock_check_license.return_value = mock_app

        # Mocking the job_progress object
        mock_job_progress = MagicMock()
        mock_task = MagicMock()
        mock_job_progress.add_task.return_value = mock_task

        gitlab_issues = [
            {
                "issue": Issue(
                    id=1,
                    title="Issue 1",
                    description="Description 1",
                    status="Closed",
                    severityLevel="High",
                    dependabotId="1",
                ),
                "links": [
                    Link(
                        id=None,
                        title="Link to GitLab repo",
                        url="https://www.gitlab.com",
                        createdById=None,
                        lastUpdatedById=None,
                        dateLastUpdated=None,
                        isPublic=True,
                    ),
                ],
            }
        ]

        regscale_issues = [
            Issue(
                id=1,
                title="Issue 2",
                description="Description 2",
                status="Open",
                severityLevel="Low",
                dependabotId="1",
            )
        ]

        # mock api calls
        mock_issue.update_issue.return_value = gitlab_issues[0]["issue"]
        mock_link.insert_link.return_value = gitlab_issues[0]["links"][0]

        save_or_update_issues(gitlab_issues, regscale_issues, mock_job_progress)

        # Verify the issue was inserted with correct parameters
        mock_issue.update_issue.assert_called_once_with(app=mock_app, issue=gitlab_issues[0]["issue"])
        mock_link.insert_link.assert_called_once_with(app=mock_app, link=gitlab_issues[0]["links"][0])

        # Verify job progress was updated
        mock_job_progress.update.assert_called_with(mock_task, advance=1)

    def test_extract_links_with_labels(self):
        # Test data
        text = "Link to GitLab repo: https: https://www.gitlab.com <br>\nAnother link: https: https://example.com"
        parent_id = 1
        parent_module = "issues"
        # Expected result
        expected_links = [
            Link(
                id=None,
                title="Link to GitLab repo",
                url="https://www.gitlab.com",
                parentID=1,
                parentModule=parent_module,
                createdById=None,
                lastUpdatedById=None,
                dateLastUpdated=None,
                isPublic=True,
            ),
            Link(
                id=None,
                title="Another link",
                url="https://example.com",
                parentID=1,
                parentModule=parent_module,
                createdById=None,
                lastUpdatedById=None,
                dateLastUpdated=None,
                isPublic=True,
            ),
        ]

        # Call the function
        result = extract_links_with_labels(text, parent_id, parent_module)
        print(result)
        # Assert
        self.assertEqual(result, expected_links)

    def test_convert_issues_basic_properties(self):
        """Test basic issue property conversion"""
        gitlab_issues = [
            {
                "title": "Test issue",
                "description": "Test description",
                "state": "open",
                "weight": 3,
                "due_date": "2023-06-25",
                "id": 1,
                "created_at": "2023-06-24",
            }
        ]

        job_progress = Mock()
        job_progress.add_task.return_value = "task"

        result = convert_issues(gitlab_issues, 1, "securityplans", True, job_progress)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        issue = result[0]["issue"]
        self.assertIsInstance(issue, Issue)
        self.assertEqual(issue.title, "Test issue")
        self.assertEqual(issue.severityLevel, Issue.assign_severity(gitlab_issues[0]["weight"]))
        self.assertEqual(issue.securityPlanId, 1)
        self.assertIsNone(issue.componentId)

    def test_convert_issues_status_handling(self):
        """Test issue status conversion for different states"""
        gitlab_issues = [
            {
                "title": "Open issue",
                "description": "Test description",
                "state": "open",
                "weight": 3,
                "due_date": "2023-06-25",
                "id": 1,
                "created_at": "2023-06-24",
            },
            {
                "title": "Closed issue",
                "description": "Test description",
                "state": "closed",
                "weight": 3,
                "due_date": "2023-06-25",
                "id": 2,
                "created_at": "2023-06-24",
                "closed_at": "2023-06-25",
            },
        ]

        job_progress = Mock()
        job_progress.add_task.return_value = "task"

        result = convert_issues(gitlab_issues, 1, "securityplans", True, job_progress)

        self.assertEqual(result[0]["issue"].status, "Open")
        self.assertEqual(result[1]["issue"].status, "Closed")

    @patch("regscale.integrations.commercial.gitlab.get_current_datetime", return_value="2024-06-25")
    def test_convert_issues_date_handling(self, mock_get_current_datetime):
        """Test dateCompleted handling for closed issues"""
        gitlab_issues = [
            {
                "title": "Closed with date",
                "description": "Test description",
                "state": "closed",
                "weight": 3,
                "due_date": "2023-06-25",
                "id": 1,
                "created_at": "2023-06-24",
                "closed_at": "2023-06-25",
            },
            {
                "title": "Closed without date",
                "description": "Test description",
                "state": "closed",
                "weight": 3,
                "due_date": "2023-06-25",
                "id": 2,
                "created_at": "2023-06-24",
            },
        ]

        job_progress = Mock()
        job_progress.add_task.return_value = "task"

        result = convert_issues(gitlab_issues, 1, "securityplans", True, job_progress)

        self.assertEqual(result[0]["issue"].dateCompleted, "2023-06-25")  # Uses closed_at
        self.assertEqual(result[1]["issue"].dateCompleted, "2024-06-25")  # Uses current datetime

    def test_convert_issues_with_links(self):
        """Test link extraction and inclusion"""
        gitlab_issues = [
            {
                "title": "Test issue",
                "description": "This is a test issue with a link: https: https://example.com",
                "state": "open",
                "weight": 3,
                "due_date": "2023-06-25",
                "id": 1,
                "created_at": "2023-06-24",
            }
        ]

        job_progress = Mock()
        job_progress.add_task.return_value = "task"

        result = convert_issues(gitlab_issues, 1, "securityplans", True, job_progress)

        self.assertEqual(len(result[0]["links"]), 1)
        self.assertEqual(result[0]["links"][0].url, "https://example.com")
        job_progress.update.assert_called_with("task", advance=1)

    def test_convert_issues_no_links(self):
        """Test convert issues with include_links set to False"""
        gitlab_issues = [
            {
                "title": "Test issue",
                "description": "This is a test issue with a link: https: https://example.com",
                "state": "closed",
                "weight": 3,
                "due_date": "2023-06-25",
                "id": 1,
                "created_at": "2023-06-24",
                "closed_at": "2023-06-25",
            },
        ]

        job_progress = Mock()
        job_progress.add_task.return_value = "task"

        result = convert_issues(gitlab_issues, 1, "securityplans", False, job_progress)

        # Assertions
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["links"], [])

    def test_convert_issues_empty(self):
        """Test with empty issue list from gitlab"""
        job_progress = Mock()
        job_progress.add_task.return_value = "task"

        result = convert_issues([], 1, "securityplans", True, job_progress)
        assert result == []

    @patch("regscale.integrations.commercial.gitlab.requests.get")
    @patch("regscale.integrations.commercial.gitlab.job_progress.add_task")
    @patch("regscale.integrations.commercial.gitlab.job_progress.update")
    def test_get_issues_from_gitlab_success(self, mock_update, mock_add_task, mock_get):
        # Mock the response from the GitLab API
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = [
            {"id": 1, "title": "Issue 1"},
            {"id": 2, "title": "Issue 2"},
        ]
        mock_get.return_value = mock_response

        # Mock job_progress
        mock_job_progress = MagicMock()
        mock_add_task.return_value = "fetching_issues"

        # Call the function
        issues = get_issues_from_gitlab("https://gitlab.com", 1, "api_token", mock_job_progress)

        # Assertions
        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0]["id"], 1)
        self.assertEqual(issues[0]["title"], "Issue 1")
        self.assertEqual(issues[1]["id"], 2)
        self.assertEqual(issues[1]["title"], "Issue 2")

        # Assert that the mock methods were called
        # mock_add_task.assert_called_once()
        # mock_update.assert_called_once_with("fetching_issues", advance=1)
        mock_get.assert_called_once_with(
            "https://gitlab.com/api/v4/projects/1/issues",
            headers={"Private-Token": "api_token"},
        )

    @patch("regscale.integrations.commercial.gitlab.requests.get")
    @patch("regscale.integrations.commercial.gitlab.job_progress.add_task")
    @patch("regscale.integrations.commercial.gitlab.job_progress.update")
    def test_get_issues_from_gitlab_failure(self, mock_update, mock_add_task, mock_get):
        # Mock the response from the GitLab API
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        mock_get.return_value = mock_response

        # Mock job_progress
        mock_job_progress = MagicMock()
        mock_add_task.return_value = "fetching_issues"

        # Call the function and verify it raises SystemExit
        with self.assertRaises(SystemExit) as context:
            get_issues_from_gitlab("https://gitlab.com", 1, "api_token", mock_job_progress)

        # Verify the exit code
        self.assertEqual(context.exception.code, 1)

        # Verify the API call was made correctly
        mock_get.assert_called_once_with(
            "https://gitlab.com/api/v4/projects/1/issues",
            headers={"Private-Token": "api_token"},
        )
