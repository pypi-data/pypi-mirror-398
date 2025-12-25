import logging
from collections import defaultdict
from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.models.regscale_models.issue import Issue, IssueSeverity, IssueStatus, OpenIssueDict


def test_bad_issue_instance():
    issue = Issue(
        id=1,
        title="Test Issue",
        severityLevel=IssueSeverity.NotAssigned,
        status=IssueStatus.Draft,
        description="This is a test issue",
        parentId=1,
        parentModule="securityplans",
        pluginId=1,
        dateCreated=get_current_datetime(),
    )
    # Assert issue.model_fields_set raises an AttributeError
    with pytest.raises(AttributeError):
        issue.model_fields_set


def test_good_issue_instance():
    issue = Issue(
        id=1,
        title="Test Issue",
        severityLevel=IssueSeverity.NotAssigned,
        status=IssueStatus.Draft,
        description="This is a test issue",
        parentId=1,
        parentModule="securityplans",
        pluginId=str(1),
        dateCreated=get_current_datetime(),
    )
    assert isinstance(issue, Issue)


class TestOpenIssuesRefactoredMethods:
    """Test suite for refactored get_open_issues_ids_by_implementation_id methods"""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger"""
        return MagicMock(spec=logging.Logger)

    @pytest.fixture
    def sample_open_issues(self) -> Dict[int, List[OpenIssueDict]]:
        """Create sample open issues data"""
        return {
            1: [
                OpenIssueDict(id=101, otherIdentifier="ISS-101", integrationFindingId="FIND-101"),
                OpenIssueDict(id=102, otherIdentifier="ISS-102", integrationFindingId="FIND-102"),
            ],
            2: [
                OpenIssueDict(id=103, otherIdentifier="ISS-103", integrationFindingId="FIND-103"),
            ],
        }

    @pytest.fixture
    def mock_api_response_single_control(self):
        """Mock API response for single control support"""
        return {
            "issues": {
                "items": [
                    {"id": 101, "controlId": 1, "otherIdentifier": "ISS-101", "integrationFindingId": "FIND-101"},
                    {"id": 102, "controlId": 1, "otherIdentifier": "ISS-102", "integrationFindingId": "FIND-102"},
                    {"id": 103, "controlId": 2, "otherIdentifier": "ISS-103", "integrationFindingId": "FIND-103"},
                ],
                "pageInfo": {"hasNextPage": False},
                "totalCount": 3,
            }
        }

    @pytest.fixture
    def mock_api_response_multiple_controls(self):
        """Mock API response for multiple control support"""
        return {
            "issues": {
                "items": [
                    {
                        "id": 101,
                        "otherIdentifier": "ISS-101",
                        "integrationFindingId": "FIND-101",
                        "controlImplementations": [{"id": 1}, {"id": 2}],
                    },
                    {
                        "id": 102,
                        "otherIdentifier": "ISS-102",
                        "integrationFindingId": "FIND-102",
                        "controlImplementations": [{"id": 1}],
                    },
                ],
                "pageInfo": {"hasNextPage": False},
                "totalCount": 2,
            }
        }

    def test_check_cache_with_cache_disabled(self, mock_logger):
        """Test _check_cache when cache is disabled"""
        with patch.object(Issue, "_is_cache_disabled", return_value=True):
            result = Issue._check_cache(123, mock_logger)
            assert result is None
            mock_logger.info.assert_not_called()

    def test_check_cache_with_valid_cache(self, mock_logger, sample_open_issues):
        """Test _check_cache when valid cache exists"""
        with patch.object(Issue, "_is_cache_disabled", return_value=False), patch.object(
            Issue, "_get_from_cache", return_value=sample_open_issues
        ):
            result = Issue._check_cache(123, mock_logger)
            assert result == sample_open_issues
            mock_logger.info.assert_called_once()

    def test_check_cache_with_no_cache(self, mock_logger):
        """Test _check_cache when no cache exists"""
        with patch.object(Issue, "_is_cache_disabled", return_value=False), patch.object(
            Issue, "_get_from_cache", return_value=None
        ):
            result = Issue._check_cache(123, mock_logger)
            assert result is None

    def test_get_query_fields_with_multiple_controls(self):
        """Test _get_query_fields for multiple control support"""
        result = Issue._get_query_fields(supports_multiple_controls=True)
        assert "controlImplementations" in result
        assert "id" in result
        assert "otherIdentifier" in result
        assert "integrationFindingId" in result

    def test_get_query_fields_with_single_control(self):
        """Test _get_query_fields for single control support"""
        result = Issue._get_query_fields(supports_multiple_controls=False)
        assert "controlId" in result
        assert "id" in result
        assert "otherIdentifier" in result
        assert "integrationFindingId" in result
        assert "controlImplementations" not in result

    def test_build_query_for_security_plan(self):
        """Test _build_query for security plan"""
        with patch.object(Issue, "get_module_string", return_value="issues"):
            query = Issue._build_query(plan_id=123, is_component=False, skip=0, take=50, fields="id, title")
            assert "securityPlanId" in query
            assert "eq: 123" in query
            assert 'status: {eq: "Open"}' in query
            assert "componentId" not in query

    def test_build_query_for_component(self):
        """Test _build_query for component"""
        with patch.object(Issue, "get_module_string", return_value="issues"):
            query = Issue._build_query(plan_id=456, is_component=True, skip=10, take=25, fields="id, title")
            assert "componentId" in query
            assert "eq: 456" in query
            assert 'status: {eq: "Open"}' in query
            assert "securityPlanId" not in query

    def test_log_progress_with_large_dataset(self, mock_logger):
        """Test _log_progress logs for large datasets"""
        Issue._log_progress(skip=100, take=50, items_count=50, total_count=2000, logger=mock_logger)
        mock_logger.info.assert_called_once()
        assert "Processing batch 3" in mock_logger.info.call_args[0][0]

    def test_log_progress_with_small_dataset(self, mock_logger):
        """Test _log_progress does not log for small datasets"""
        Issue._log_progress(skip=0, take=50, items_count=50, total_count=100, logger=mock_logger)
        mock_logger.info.assert_not_called()

    def test_add_issue_to_single_control(self):
        """Test _add_issue_to_single_control"""
        control_issues = defaultdict(list)
        issue_dict = OpenIssueDict(id=101, otherIdentifier="ISS-101", integrationFindingId="FIND-101")
        item = {"id": 101, "controlId": 5}

        Issue._add_issue_to_single_control(item, issue_dict, control_issues)

        assert len(control_issues) == 1
        assert 5 in control_issues
        assert control_issues[5][0] == issue_dict

    def test_add_issue_to_single_control_no_control_id(self):
        """Test _add_issue_to_single_control when no controlId"""
        control_issues = defaultdict(list)
        issue_dict = OpenIssueDict(id=101, otherIdentifier="ISS-101", integrationFindingId="FIND-101")
        item = {"id": 101}

        Issue._add_issue_to_single_control(item, issue_dict, control_issues)

        assert len(control_issues) == 0

    def test_add_issue_to_multiple_controls(self):
        """Test _add_issue_to_multiple_controls"""
        control_issues = defaultdict(list)
        issue_dict = OpenIssueDict(id=101, otherIdentifier="ISS-101", integrationFindingId="FIND-101")
        item = {"id": 101, "controlImplementations": [{"id": 1}, {"id": 2}, {"id": 3}]}

        Issue._add_issue_to_multiple_controls(item, issue_dict, control_issues)

        assert len(control_issues) == 3
        assert 1 in control_issues
        assert 2 in control_issues
        assert 3 in control_issues
        assert control_issues[1][0] == issue_dict

    def test_add_issue_to_multiple_controls_no_implementations(self):
        """Test _add_issue_to_multiple_controls when no implementations"""
        control_issues = defaultdict(list)
        issue_dict = OpenIssueDict(id=101, otherIdentifier="ISS-101", integrationFindingId="FIND-101")
        item = {"id": 101}

        Issue._add_issue_to_multiple_controls(item, issue_dict, control_issues)

        assert len(control_issues) == 0

    def test_process_issue_items_single_control(self):
        """Test _process_issue_items with single control support"""
        items = [
            {"id": 101, "controlId": 1, "otherIdentifier": "ISS-101", "integrationFindingId": "FIND-101"},
            {"id": 102, "controlId": 2, "otherIdentifier": "ISS-102", "integrationFindingId": "FIND-102"},
        ]
        control_issues = defaultdict(list)

        Issue._process_issue_items(items, supports_multiple_controls=False, control_issues=control_issues)

        assert len(control_issues) == 2
        assert len(control_issues[1]) == 1
        assert len(control_issues[2]) == 1
        assert control_issues[1][0]["id"] == 101
        assert control_issues[2][0]["id"] == 102

    def test_process_issue_items_multiple_controls(self):
        """Test _process_issue_items with multiple control support"""
        items = [
            {
                "id": 101,
                "otherIdentifier": "ISS-101",
                "integrationFindingId": "FIND-101",
                "controlImplementations": [{"id": 1}, {"id": 2}],
            },
            {
                "id": 102,
                "otherIdentifier": "ISS-102",
                "integrationFindingId": "FIND-102",
                "controlImplementations": [{"id": 1}],
            },
        ]
        control_issues = defaultdict(list)

        Issue._process_issue_items(items, supports_multiple_controls=True, control_issues=control_issues)

        assert len(control_issues) == 2
        assert len(control_issues[1]) == 2
        assert len(control_issues[2]) == 1
        assert control_issues[1][0]["id"] == 101
        assert control_issues[1][1]["id"] == 102

    def test_log_completion(self, mock_logger):
        """Test _log_completion logs completion message"""
        import time

        start_time = time.time() - 5.5  # 5.5 seconds ago

        Issue._log_completion(
            plan_id=123, total_fetched=150, control_count=25, start_time=start_time, logger=mock_logger
        )

        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "150 open issue(s)" in log_message
        assert "25 control(s)" in log_message
        assert "123" in log_message
        assert "5.5" in log_message

    @patch.object(Issue, "_get_api_handler")
    @patch.object(Issue, "get_module_string", return_value="issues")
    @patch.object(Issue, "is_multiple_controls_supported", return_value=False)
    def test_paginate_and_process_issues_single_page(
        self, mock_supports, mock_module_string, mock_api_handler, mock_logger
    ):
        """Test _paginate_and_process_issues with single page response"""
        mock_api = MagicMock()
        mock_api.graph.return_value = {
            "issues": {
                "items": [
                    {"id": 101, "controlId": 1, "otherIdentifier": "ISS-101", "integrationFindingId": "FIND-101"},
                ],
                "pageInfo": {"hasNextPage": False},
                "totalCount": 1,
            }
        }
        mock_api_handler.return_value = mock_api
        control_issues = defaultdict(list)

        total_fetched = Issue._paginate_and_process_issues(
            plan_id=123, is_component=False, control_issues=control_issues, logger=mock_logger
        )

        assert total_fetched == 1
        assert len(control_issues) == 1
        assert len(control_issues[1]) == 1

    @patch.object(Issue, "_get_api_handler")
    @patch.object(Issue, "get_module_string", return_value="issues")
    @patch.object(Issue, "is_multiple_controls_supported", return_value=False)
    def test_paginate_and_process_issues_multiple_pages(
        self, mock_supports, mock_module_string, mock_api_handler, mock_logger
    ):
        """Test _paginate_and_process_issues with single page (totalCount <= take)"""
        mock_api = MagicMock()
        # Simulate single page with 2 items (totalCount: 2 <= take: 50)
        mock_api.graph.return_value = {
            "issues": {
                "items": [
                    {"id": 101, "controlId": 1, "otherIdentifier": "ISS-101", "integrationFindingId": "FIND-101"},
                    {"id": 102, "controlId": 2, "otherIdentifier": "ISS-102", "integrationFindingId": "FIND-102"},
                ],
                "pageInfo": {"hasNextPage": False},
                "totalCount": 2,
            }
        }
        mock_api_handler.return_value = mock_api
        control_issues = defaultdict(list)

        total_fetched = Issue._paginate_and_process_issues(
            plan_id=123, is_component=False, control_issues=control_issues, logger=mock_logger
        )

        assert total_fetched == 2
        assert len(control_issues) == 2
        assert mock_api.graph.call_count == 1  # Only one call since totalCount <= take

    @patch.object(Issue, "_paginate_and_process_issues")
    def test_fetch_open_issues_from_api_success(self, mock_paginate, mock_logger):
        """Test _fetch_open_issues_from_api successful execution"""
        mock_paginate.return_value = 150
        control_issues = Issue._fetch_open_issues_from_api(plan_id=123, is_component=False, logger=mock_logger)

        assert isinstance(control_issues, defaultdict)
        mock_logger.info.assert_called()

    @patch.object(Issue, "_paginate_and_process_issues")
    def test_fetch_open_issues_from_api_exception(self, mock_paginate, mock_logger):
        """Test _fetch_open_issues_from_api handles exceptions"""
        mock_paginate.side_effect = Exception("API Error")

        control_issues = Issue._fetch_open_issues_from_api(plan_id=123, is_component=False, logger=mock_logger)

        assert isinstance(control_issues, defaultdict)
        assert len(control_issues) == 0
        mock_logger.error.assert_called_once()

    @patch.object(Issue, "_check_cache")
    @patch.object(Issue, "_fetch_open_issues_from_api")
    @patch.object(Issue, "_is_cache_disabled", return_value=False)
    @patch.object(Issue, "_cache_data")
    def test_get_open_issues_ids_by_implementation_id_with_cache(
        self, mock_cache_data, mock_disabled, mock_fetch, mock_check_cache, sample_open_issues
    ):
        """Test get_open_issues_ids_by_implementation_id returns cached data"""
        mock_check_cache.return_value = sample_open_issues

        result = Issue.get_open_issues_ids_by_implementation_id(plan_id=123)

        assert result == sample_open_issues
        mock_fetch.assert_not_called()
        mock_cache_data.assert_not_called()

    @patch.object(Issue, "_check_cache", return_value=None)
    @patch.object(Issue, "_fetch_open_issues_from_api")
    @patch.object(Issue, "_is_cache_disabled", return_value=False)
    @patch.object(Issue, "_cache_data")
    def test_get_open_issues_ids_by_implementation_id_without_cache(
        self, mock_cache_data, mock_disabled, mock_fetch, mock_check_cache, sample_open_issues
    ):
        """Test get_open_issues_ids_by_implementation_id fetches and caches data"""
        mock_fetch.return_value = sample_open_issues

        result = Issue.get_open_issues_ids_by_implementation_id(plan_id=123)

        assert result == sample_open_issues
        mock_fetch.assert_called_once()
        mock_cache_data.assert_called_once_with(123, sample_open_issues)

    @patch.object(Issue, "_check_cache", return_value=None)
    @patch.object(Issue, "_fetch_open_issues_from_api")
    @patch.object(Issue, "_is_cache_disabled", return_value=True)
    @patch.object(Issue, "_cache_data")
    def test_get_open_issues_ids_by_implementation_id_cache_disabled(
        self, mock_cache_data, mock_disabled, mock_fetch, mock_check_cache, sample_open_issues
    ):
        """Test get_open_issues_ids_by_implementation_id with cache disabled"""
        mock_fetch.return_value = sample_open_issues

        result = Issue.get_open_issues_ids_by_implementation_id(plan_id=123)

        assert result == sample_open_issues
        mock_fetch.assert_called_once()
        mock_cache_data.assert_not_called()
