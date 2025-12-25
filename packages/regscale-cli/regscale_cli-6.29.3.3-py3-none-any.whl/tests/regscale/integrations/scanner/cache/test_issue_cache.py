#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive unit tests for IssueCache class."""
import time
from unittest.mock import MagicMock, patch

import pytest

from regscale.integrations.scanner.cache.issue_cache import IssueCache
from regscale.models.regscale_models.issue import Issue, IssueStatus, OpenIssueDict
from regscale.utils.threading import ThreadSafeDict

PATH = "regscale.integrations.scanner.cache.issue_cache"


class MockIntegrationFinding:
    """Mock IntegrationFinding for testing."""

    def __init__(
        self,
        external_id: str = "test-external-id",
        due_date: str = "2024-12-31",
        title: str = "Test Finding",
    ):
        self.external_id = external_id
        self.due_date = due_date
        self.title = title
        self.severity = "High"
        self.status = IssueStatus.Open


def create_mock_issue(
    issue_id: int,
    integration_finding_id: str = None,
    status: IssueStatus = IssueStatus.Open,
    due_date: str = "2024-12-31",
    other_identifier: str = None,
    source_report: str = "Test Integration",
) -> MagicMock:
    """
    Create a mock Issue object for testing.

    :param int issue_id: The issue ID
    :param str integration_finding_id: The integration finding ID
    :param IssueStatus status: The issue status
    :param str due_date: The due date
    :param str other_identifier: The other identifier
    :param str source_report: The source report
    :return: Mock Issue object
    :rtype: MagicMock
    """
    mock_issue = MagicMock(spec=Issue)
    mock_issue.id = issue_id
    mock_issue.integrationFindingId = integration_finding_id
    mock_issue.status = status
    mock_issue.dueDate = due_date
    mock_issue.otherIdentifier = other_identifier
    mock_issue.sourceReport = source_report
    return mock_issue


class TestIssueCacheInitialization:
    """Test IssueCache initialization."""

    @patch(f"{PATH}.Application")
    def test_init_basic(self, mock_app_class):
        """Test basic initialization with required parameters."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")

        assert cache.plan_id == 123
        assert cache.parent_module == "securityplans"
        assert cache.is_component is False
        assert cache.title is None
        assert cache.issue_identifier_field is None
        assert cache._integration_finding_id_cache is None
        assert isinstance(cache._existing_issues_map, ThreadSafeDict)
        assert cache._open_issues_by_implementation == {}
        assert cache._cache_hit_count == 0
        assert cache._cache_miss_count == 0
        assert cache._cache_fallback_count == 0

    @patch(f"{PATH}.Application")
    def test_init_with_all_parameters(self, mock_app_class):
        """Test initialization with all optional parameters."""
        cache = IssueCache(
            plan_id=456,
            parent_module="components",
            is_component=True,
            title="Test Integration",
            issue_identifier_field="testField",
        )

        assert cache.plan_id == 456
        assert cache.parent_module == "components"
        assert cache.is_component is True
        assert cache.title == "Test Integration"
        assert cache.issue_identifier_field == "testField"

    @patch(f"{PATH}.Application")
    def test_init_cache_lock_created(self, mock_app_class):
        """Test that cache lock is created on initialization."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")

        assert cache._cache_lock is not None
        assert hasattr(cache._cache_lock, "acquire")
        assert hasattr(cache._cache_lock, "release")


class TestWarmCache:
    """Test cache warming functionality."""

    @patch(f"{PATH}.IssueCache._load_open_issues_by_implementation")
    @patch(f"{PATH}.IssueCache._populate_issue_lookup_cache")
    @patch(f"{PATH}.Application")
    def test_warm_cache_calls_both_methods(self, mock_app_class, mock_populate, mock_load_open):
        """Test that warm_cache calls both population methods."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache.warm_cache()

        mock_populate.assert_called_once()
        mock_load_open.assert_called_once()


class TestPopulateIssueLookupCache:
    """Test issue lookup cache population."""

    @patch(f"{PATH}.Issue.fetch_issues_by_ssp")
    @patch(f"{PATH}.Application")
    def test_populate_cache_success(self, mock_app_class, mock_fetch):
        """Test successful cache population with multiple issues."""
        mock_issue1 = create_mock_issue(1, "finding-1")
        mock_issue2 = create_mock_issue(2, "finding-2")
        mock_issue3 = create_mock_issue(3, "finding-1")  # Same finding ID
        mock_issue4 = create_mock_issue(4, None)  # No finding ID

        mock_fetch.return_value = [mock_issue1, mock_issue2, mock_issue3, mock_issue4]

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._populate_issue_lookup_cache()

        assert cache._integration_finding_id_cache is not None
        assert len(cache._integration_finding_id_cache) == 2
        assert "finding-1" in cache._integration_finding_id_cache
        assert "finding-2" in cache._integration_finding_id_cache
        assert len(cache._integration_finding_id_cache["finding-1"]) == 2
        assert len(cache._integration_finding_id_cache["finding-2"]) == 1

    @patch(f"{PATH}.Issue.fetch_issues_by_ssp")
    @patch(f"{PATH}.Application")
    def test_populate_cache_empty_issues(self, mock_app_class, mock_fetch):
        """Test cache population with no issues."""
        mock_fetch.return_value = []

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._populate_issue_lookup_cache()

        assert cache._integration_finding_id_cache is not None
        assert len(cache._integration_finding_id_cache) == 0

    @patch(f"{PATH}.Issue.fetch_issues_by_ssp")
    @patch(f"{PATH}.Application")
    def test_populate_cache_double_check_locking(self, mock_app_class, mock_fetch):
        """Test double-check locking pattern prevents re-population."""
        mock_fetch.return_value = []

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._populate_issue_lookup_cache()
        cache._populate_issue_lookup_cache()

        # Should only be called once due to double-check locking
        assert mock_fetch.call_count == 1

    @patch(f"{PATH}.Issue.fetch_issues_by_ssp")
    @patch(f"{PATH}.Application")
    def test_populate_cache_component_mode(self, mock_app_class, mock_fetch):
        """Test cache population for component integration."""
        mock_fetch.return_value = []

        cache = IssueCache(plan_id=456, parent_module="components", is_component=True)
        cache._populate_issue_lookup_cache()

        mock_fetch.assert_called_once()
        assert cache._integration_finding_id_cache is not None


class TestLoadOpenIssuesByImplementation:
    """Test loading open issues by implementation ID."""

    @patch(f"{PATH}.Issue.get_open_issues_ids_by_implementation_id")
    @patch(f"{PATH}.Application")
    def test_load_open_issues_success(self, mock_app_class, mock_get_open):
        """Test successful loading of open issues."""
        mock_open_issues = {
            101: [{"id": 1, "otherIdentifier": "oid1", "integrationFindingId": "fid1"}],
            102: [{"id": 2, "otherIdentifier": "oid2", "integrationFindingId": "fid2"}],
        }
        mock_get_open.return_value = mock_open_issues

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._load_open_issues_by_implementation()

        mock_get_open.assert_called_once_with(plan_id=123, is_component=False)
        assert cache._open_issues_by_implementation == mock_open_issues

    @patch(f"{PATH}.Issue.get_open_issues_ids_by_implementation_id")
    @patch(f"{PATH}.Application")
    def test_load_open_issues_component(self, mock_app_class, mock_get_open):
        """Test loading open issues for component integration."""
        mock_get_open.return_value = {}

        cache = IssueCache(plan_id=456, parent_module="components", is_component=True)
        cache._load_open_issues_by_implementation()

        mock_get_open.assert_called_once_with(plan_id=456, is_component=True)


class TestGetByFindingId:
    """Test getting issues by finding ID."""

    @patch(f"{PATH}.Issue.get_all_by_parent")
    @patch(f"{PATH}.Application")
    def test_get_by_finding_id_found(self, mock_app_class, mock_get_all):
        """Test retrieving an issue by finding ID when it exists."""
        mock_issue = create_mock_issue(1, "finding-123")
        mock_get_all.return_value = [mock_issue]

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        result = cache.get_by_finding_id("finding-123")

        assert result is not None
        assert result.id == 1

    @patch(f"{PATH}.Issue.get_all_by_parent")
    @patch(f"{PATH}.Application")
    def test_get_by_finding_id_not_found(self, mock_app_class, mock_get_all):
        """Test retrieving an issue by finding ID when it doesn't exist."""
        mock_get_all.return_value = []

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        result = cache.get_by_finding_id("nonexistent")

        assert result is None


class TestGetIssuesMap:
    """Test _get_issues_map functionality."""

    @patch(f"{PATH}.Issue.get_all_by_parent")
    @patch(f"{PATH}.Application")
    def test_get_issues_map_creates_mapping(self, mock_app_class, mock_get_all):
        """Test that _get_issues_map creates proper mapping."""
        mock_issue1 = create_mock_issue(1, "finding-1")
        mock_issue2 = create_mock_issue(2, "finding-2")
        mock_issue3 = create_mock_issue(3, None)  # No finding ID

        mock_get_all.return_value = [mock_issue1, mock_issue2, mock_issue3]

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        issues_map = cache._get_issues_map()

        assert len(issues_map) == 2
        assert issues_map["finding-1"].id == 1
        assert issues_map["finding-2"].id == 2
        assert None not in issues_map


class TestGetByImplementationId:
    """Test getting issues by implementation ID."""

    @patch(f"{PATH}.Application")
    def test_get_by_implementation_id_found(self, mock_app_class):
        """Test retrieving issues by implementation ID."""
        mock_issue = create_mock_issue(1)
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._existing_issues_map[101] = [mock_issue]

        result = cache.get_by_implementation_id(101)

        assert len(result) == 1
        assert result[0].id == 1

    @patch(f"{PATH}.Application")
    def test_get_by_implementation_id_not_found(self, mock_app_class):
        """Test retrieving issues by nonexistent implementation ID."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")

        result = cache.get_by_implementation_id(999)

        assert result == []


class TestGetOpenIssuesByImplementation:
    """Test getting open issues by implementation."""

    @patch(f"{PATH}.IssueCache._load_open_issues_by_implementation")
    @patch(f"{PATH}.Application")
    def test_get_open_issues_lazy_load(self, mock_app_class, mock_load):
        """Test lazy loading of open issues."""
        mock_open_issues = {101: [{"id": 1, "otherIdentifier": "oid1", "integrationFindingId": "fid1"}]}
        mock_load.side_effect = lambda: setattr(cache, "_open_issues_by_implementation", mock_open_issues)

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        result = cache.get_open_issues_by_implementation()

        mock_load.assert_called_once()
        assert result == mock_open_issues

    @patch(f"{PATH}.Application")
    def test_get_open_issues_already_loaded(self, mock_app_class):
        """Test getting open issues when already loaded."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._open_issues_by_implementation = {
            101: [{"id": 1, "otherIdentifier": "oid1", "integrationFindingId": "fid1"}]
        }

        result = cache.get_open_issues_by_implementation()

        assert result == cache._open_issues_by_implementation


class TestAdd:
    """Test adding issues to cache."""

    @patch(f"{PATH}.IssueCache._populate_issue_lookup_cache")
    @patch(f"{PATH}.Application")
    def test_add_issue_to_cache(self, mock_app_class, mock_populate):
        """Test adding an issue to the cache."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._integration_finding_id_cache = ThreadSafeDict()

        mock_issue = create_mock_issue(1, "finding-1")
        cache.add(mock_issue)

        assert "finding-1" in cache._integration_finding_id_cache
        assert len(cache._integration_finding_id_cache["finding-1"]) == 1
        assert cache._integration_finding_id_cache["finding-1"][0].id == 1

    @patch(f"{PATH}.IssueCache._populate_issue_lookup_cache")
    @patch(f"{PATH}.Application")
    def test_add_issue_without_finding_id(self, mock_app_class, mock_populate):
        """Test adding an issue without finding ID is ignored."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._integration_finding_id_cache = ThreadSafeDict()

        mock_issue = create_mock_issue(1, None)
        cache.add(mock_issue)

        assert len(cache._integration_finding_id_cache) == 0

    @patch(f"{PATH}.IssueCache._populate_issue_lookup_cache")
    @patch(f"{PATH}.Application")
    def test_add_duplicate_issue_ignored(self, mock_app_class, mock_populate):
        """Test adding the same issue twice is ignored."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._integration_finding_id_cache = ThreadSafeDict()

        mock_issue = create_mock_issue(1, "finding-1")
        cache.add(mock_issue)
        cache.add(mock_issue)

        assert len(cache._integration_finding_id_cache["finding-1"]) == 1

    @patch(f"{PATH}.IssueCache._populate_issue_lookup_cache")
    @patch(f"{PATH}.Application")
    def test_add_initializes_cache_if_needed(self, mock_app_class, mock_populate):
        """Test adding issue initializes cache if not already initialized."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        assert cache._integration_finding_id_cache is None

        mock_issue = create_mock_issue(1, "finding-1")
        cache.add(mock_issue)

        mock_populate.assert_called_once()


class TestFindExistingForFinding:
    """Test finding existing issues for findings."""

    @patch("regscale.integrations.variables.ScannerVariables.issueCreation", "perasset")
    @patch(f"{PATH}.IssueCache._get_existing_issues_for_finding")
    @patch(f"{PATH}.Application")
    def test_find_existing_per_asset_mode_returns_none(self, mock_app_class, mock_get_existing):
        """Test that per-asset mode always returns None."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        finding = MockIntegrationFinding()

        result = cache.find_existing_for_finding(finding, "finding-1")

        assert result is None
        mock_get_existing.assert_not_called()

    @patch("regscale.integrations.variables.ScannerVariables.issueCreation", "consolidated")
    @patch(f"{PATH}.IssueCache._find_issue_for_open_status")
    @patch(f"{PATH}.IssueCache._get_existing_issues_for_finding")
    @patch(f"{PATH}.Application")
    def test_find_existing_for_open_status(self, mock_app_class, mock_get_existing, mock_find_open):
        """Test finding existing issue for open status."""
        mock_issue = create_mock_issue(1, "finding-1", IssueStatus.Open)
        mock_get_existing.return_value = [mock_issue]
        mock_find_open.return_value = mock_issue

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        finding = MockIntegrationFinding()

        result = cache.find_existing_for_finding(finding, "finding-1", IssueStatus.Open)

        mock_find_open.assert_called_once_with([mock_issue], "finding-1")
        assert result == mock_issue

    @patch("regscale.integrations.variables.ScannerVariables.issueCreation", "consolidated")
    @patch(f"{PATH}.IssueCache._find_issue_for_closed_status")
    @patch(f"{PATH}.IssueCache._get_existing_issues_for_finding")
    @patch(f"{PATH}.Application")
    def test_find_existing_for_closed_status(self, mock_app_class, mock_get_existing, mock_find_closed):
        """Test finding existing issue for closed status."""
        mock_issue = create_mock_issue(1, "finding-1", IssueStatus.Closed)
        mock_get_existing.return_value = [mock_issue]
        mock_find_closed.return_value = mock_issue

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        finding = MockIntegrationFinding()

        result = cache.find_existing_for_finding(finding, "finding-1", IssueStatus.Closed)

        mock_find_closed.assert_called_once_with([mock_issue], finding, "finding-1")
        assert result == mock_issue

    @patch("regscale.integrations.variables.ScannerVariables.issueCreation", "consolidated")
    @patch(f"{PATH}.IssueCache._get_existing_issues_for_finding")
    @patch(f"{PATH}.Application")
    def test_find_existing_no_status_returns_first(self, mock_app_class, mock_get_existing):
        """Test finding existing issue with no status specified returns first match."""
        mock_issue = create_mock_issue(1, "finding-1")
        mock_get_existing.return_value = [mock_issue]

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        finding = MockIntegrationFinding()

        result = cache.find_existing_for_finding(finding, "finding-1")

        assert result == mock_issue

    @patch("regscale.integrations.variables.ScannerVariables.issueCreation", "consolidated")
    @patch(f"{PATH}.IssueCache._get_existing_issues_for_finding")
    @patch(f"{PATH}.Application")
    def test_find_existing_no_issues_returns_none(self, mock_app_class, mock_get_existing):
        """Test finding existing issue when no issues exist returns None."""
        mock_get_existing.return_value = []

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        finding = MockIntegrationFinding()

        result = cache.find_existing_for_finding(finding, "finding-1")

        assert result is None


class TestGetExistingIssuesForFinding:
    """Test getting existing issues for a finding."""

    @patch(f"{PATH}.IssueCache._populate_issue_lookup_cache")
    @patch(f"{PATH}.Application")
    def test_get_existing_cache_hit(self, mock_app_class, mock_populate):
        """Test cache hit scenario."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._integration_finding_id_cache = ThreadSafeDict()

        mock_issue = create_mock_issue(1, "finding-1")
        cache._integration_finding_id_cache["finding-1"] = [mock_issue]

        finding = MockIntegrationFinding()
        result = cache._get_existing_issues_for_finding("finding-1", finding)

        assert len(result) == 1
        assert result[0] == mock_issue
        assert cache._cache_hit_count == 1
        assert cache._cache_miss_count == 0

    @patch(f"{PATH}.IssueCache._populate_issue_lookup_cache")
    @patch(f"{PATH}.Application")
    def test_get_existing_cache_miss(self, mock_app_class, mock_populate):
        """Test cache miss scenario."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._integration_finding_id_cache = ThreadSafeDict()

        finding = MockIntegrationFinding()
        result = cache._get_existing_issues_for_finding("nonexistent", finding)

        assert len(result) == 0
        assert cache._cache_hit_count == 0
        assert cache._cache_miss_count == 1

    @patch(f"{PATH}.IssueCache._find_issues_by_identifier_fallback")
    @patch(f"{PATH}.IssueCache._populate_issue_lookup_cache")
    @patch(f"{PATH}.Application")
    def test_get_existing_fallback_on_miss(self, mock_app_class, mock_populate, mock_fallback):
        """Test fallback to identifier search on cache miss."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._integration_finding_id_cache = ThreadSafeDict()

        mock_issue = create_mock_issue(1, "finding-1", other_identifier="ext-123")
        mock_fallback.return_value = [mock_issue]

        finding = MockIntegrationFinding(external_id="ext-123")
        result = cache._get_existing_issues_for_finding("finding-1", finding)

        mock_fallback.assert_called_once_with("ext-123")
        assert len(result) == 1
        assert result[0] == mock_issue
        assert cache._cache_fallback_count == 1
        # Fallback result should be cached
        assert "finding-1" in cache._integration_finding_id_cache

    @patch(f"{PATH}.IssueCache._populate_issue_lookup_cache")
    @patch(f"{PATH}.Application")
    def test_get_existing_no_fallback_without_external_id(self, mock_app_class, mock_populate):
        """Test no fallback is attempted without external_id."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._integration_finding_id_cache = ThreadSafeDict()

        finding = MockIntegrationFinding(external_id=None)
        result = cache._get_existing_issues_for_finding("finding-1", finding)

        assert len(result) == 0
        assert cache._cache_fallback_count == 0

    @patch(f"{PATH}.IssueCache._populate_issue_lookup_cache")
    @patch(f"{PATH}.Application")
    def test_get_existing_initializes_cache_if_needed(self, mock_app_class, mock_populate):
        """Test cache initialization on first access."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        assert cache._integration_finding_id_cache is None

        finding = MockIntegrationFinding()
        cache._get_existing_issues_for_finding("finding-1", finding)

        mock_populate.assert_called_once()


class TestFindIssuesByIdentifierFallback:
    """Test fallback issue lookup by identifier."""

    @patch(f"{PATH}.Issue.get_all_by_parent")
    @patch(f"{PATH}.Application")
    def test_fallback_by_other_identifier(self, mock_app_class, mock_get_all):
        """Test fallback finds issue by otherIdentifier."""
        mock_issue = create_mock_issue(1, other_identifier="ext-123", source_report="Test Integration")
        mock_get_all.return_value = [mock_issue]

        cache = IssueCache(plan_id=123, parent_module="securityplans", title="Test Integration")
        result = cache._find_issues_by_identifier_fallback("ext-123")

        assert len(result) == 1
        assert result[0].id == 1

    @patch(f"{PATH}.Issue.get_all_by_parent")
    @patch(f"{PATH}.Application")
    def test_fallback_by_custom_field(self, mock_app_class, mock_get_all):
        """Test fallback finds issue by custom identifier field."""
        mock_issue = create_mock_issue(1, source_report="Test Integration")
        mock_issue.customField = "custom-123"
        mock_get_all.return_value = [mock_issue]

        cache = IssueCache(
            plan_id=123,
            parent_module="securityplans",
            title="Test Integration",
            issue_identifier_field="customField",
        )
        result = cache._find_issues_by_identifier_fallback("custom-123")

        assert len(result) == 1
        assert result[0].id == 1

    @patch(f"{PATH}.Issue.get_all_by_parent")
    @patch(f"{PATH}.Application")
    def test_fallback_filters_by_source_report(self, mock_app_class, mock_get_all):
        """Test fallback filters by source report."""
        mock_issue1 = create_mock_issue(1, other_identifier="ext-123", source_report="Test Integration")
        mock_issue2 = create_mock_issue(2, other_identifier="ext-123", source_report="Other Integration")
        mock_get_all.return_value = [mock_issue1, mock_issue2]

        cache = IssueCache(plan_id=123, parent_module="securityplans", title="Test Integration")
        result = cache._find_issues_by_identifier_fallback("ext-123")

        assert len(result) == 1
        assert result[0].id == 1

    @patch(f"{PATH}.Issue.get_all_by_parent")
    @patch(f"{PATH}.Application")
    def test_fallback_no_match(self, mock_app_class, mock_get_all):
        """Test fallback returns empty list when no match found."""
        mock_issue = create_mock_issue(1, other_identifier="different", source_report="Test Integration")
        mock_get_all.return_value = [mock_issue]

        cache = IssueCache(plan_id=123, parent_module="securityplans", title="Test Integration")
        result = cache._find_issues_by_identifier_fallback("ext-123")

        assert len(result) == 0

    @patch(f"{PATH}.Issue.get_all_by_parent")
    @patch(f"{PATH}.Application")
    def test_fallback_handles_exception(self, mock_app_class, mock_get_all):
        """Test fallback handles exceptions gracefully."""
        mock_get_all.side_effect = Exception("API Error")

        cache = IssueCache(plan_id=123, parent_module="securityplans", title="Test Integration")
        result = cache._find_issues_by_identifier_fallback("ext-123")

        assert len(result) == 0


class TestFindIssueForOpenStatus:
    """Test finding issues for open status."""

    @patch(f"{PATH}.Application")
    def test_find_open_issue(self, mock_app_class):
        """Test finding an open issue."""
        mock_open = create_mock_issue(1, "finding-1", IssueStatus.Open)
        mock_closed = create_mock_issue(2, "finding-1", IssueStatus.Closed)

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        result = cache._find_issue_for_open_status([mock_open, mock_closed], "finding-1")

        assert result == mock_open

    @patch(f"{PATH}.Application")
    def test_find_pending_issue(self, mock_app_class):
        """Test finding a pending issue when no open issue exists."""
        mock_pending = create_mock_issue(1, "finding-1", IssueStatus.PendingVerification)

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        result = cache._find_issue_for_open_status([mock_pending], "finding-1")

        assert result == mock_pending

    @patch(f"{PATH}.Application")
    def test_reopen_closed_issue(self, mock_app_class):
        """Test reopening a closed issue when no open issues exist."""
        mock_closed = create_mock_issue(1, "finding-1", IssueStatus.Closed)

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        result = cache._find_issue_for_open_status([mock_closed], "finding-1")

        assert result == mock_closed

    @patch(f"{PATH}.Application")
    def test_no_issues_returns_none(self, mock_app_class):
        """Test returns None when no issues provided."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        result = cache._find_issue_for_open_status([], "finding-1")

        assert result is None


class TestFindIssueForClosedStatus:
    """Test finding issues for closed status."""

    @patch("regscale.core.utils.date.date_str")
    @patch(f"{PATH}.Application")
    def test_find_closed_issue_matching_due_date(self, mock_app_class, mock_date_str):
        """Test finding a closed issue with matching due date."""
        mock_date_str.side_effect = lambda x: x

        mock_closed1 = create_mock_issue(1, "finding-1", IssueStatus.Closed, due_date="2024-12-31")
        mock_closed2 = create_mock_issue(2, "finding-1", IssueStatus.Closed, due_date="2024-11-30")

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        finding = MockIntegrationFinding(due_date="2024-12-31")
        result = cache._find_issue_for_closed_status([mock_closed1, mock_closed2], finding, "finding-1")

        assert result == mock_closed1

    @patch("regscale.core.utils.date.date_str")
    @patch(f"{PATH}.Application")
    def test_close_any_existing_issue(self, mock_app_class, mock_date_str):
        """Test closing any existing issue when no matching closed issue found."""
        mock_date_str.side_effect = lambda x: x

        mock_open = create_mock_issue(1, "finding-1", IssueStatus.Open)

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        finding = MockIntegrationFinding(due_date="2024-12-31")
        result = cache._find_issue_for_closed_status([mock_open], finding, "finding-1")

        assert result == mock_open

    @patch(f"{PATH}.Application")
    def test_no_issues_returns_none(self, mock_app_class):
        """Test returns None when no issues provided."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        finding = MockIntegrationFinding()
        result = cache._find_issue_for_closed_status([], finding, "finding-1")

        assert result is None


class TestLogCacheEffectiveness:
    """Test cache effectiveness logging."""

    @patch(f"{PATH}.Application")
    def test_log_effectiveness_with_hits_and_misses(self, mock_app_class):
        """Test logging with both hits and misses."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._cache_hit_count = 80
        cache._cache_miss_count = 20
        cache._cache_fallback_count = 5

        # Should not raise exception
        cache.log_cache_effectiveness()

    @patch(f"{PATH}.Application")
    def test_log_effectiveness_no_lookups(self, mock_app_class):
        """Test logging with no lookups returns early."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._cache_hit_count = 0
        cache._cache_miss_count = 0

        # Should not raise exception and returns early
        cache.log_cache_effectiveness()


class TestGetCacheStats:
    """Test getting cache statistics."""

    @patch(f"{PATH}.Application")
    def test_get_stats_with_activity(self, mock_app_class):
        """Test getting stats with cache activity."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._cache_hit_count = 75
        cache._cache_miss_count = 25
        cache._cache_fallback_count = 10
        cache._integration_finding_id_cache = ThreadSafeDict()
        cache._integration_finding_id_cache["finding-1"] = []
        cache._integration_finding_id_cache["finding-2"] = []

        stats = cache.get_cache_stats()

        assert stats["hit_count"] == 75
        assert stats["miss_count"] == 25
        assert stats["fallback_count"] == 10
        assert stats["total_lookups"] == 100
        assert stats["hit_rate"] == 75.0
        assert stats["cache_size"] == 2

    @patch(f"{PATH}.Application")
    def test_get_stats_no_activity(self, mock_app_class):
        """Test getting stats with no cache activity."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")

        stats = cache.get_cache_stats()

        assert stats["hit_count"] == 0
        assert stats["miss_count"] == 0
        assert stats["fallback_count"] == 0
        assert stats["total_lookups"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["cache_size"] == 0

    @patch(f"{PATH}.Application")
    def test_get_stats_with_cache_populated(self, mock_app_class):
        """Test getting stats with populated cache."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._integration_finding_id_cache = ThreadSafeDict()
        for i in range(50):
            cache._integration_finding_id_cache[f"finding-{i}"] = []

        stats = cache.get_cache_stats()

        assert stats["cache_size"] == 50


class TestClear:
    """Test cache clearing functionality."""

    @patch(f"{PATH}.Application")
    def test_clear_resets_all_state(self, mock_app_class):
        """Test clear resets all cache state."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")

        # Populate cache
        cache._integration_finding_id_cache = ThreadSafeDict()
        cache._integration_finding_id_cache["finding-1"] = []
        cache._existing_issues_map[101] = []
        cache._open_issues_by_implementation = {101: []}
        cache._cache_hit_count = 10
        cache._cache_miss_count = 5
        cache._cache_fallback_count = 2

        cache.clear()

        assert cache._integration_finding_id_cache is None
        assert len(cache._existing_issues_map) == 0
        assert cache._open_issues_by_implementation == {}
        assert cache._cache_hit_count == 0
        assert cache._cache_miss_count == 0
        assert cache._cache_fallback_count == 0

    @patch(f"{PATH}.Application")
    def test_clear_on_empty_cache(self, mock_app_class):
        """Test clear on empty cache doesn't raise exception."""
        cache = IssueCache(plan_id=123, parent_module="securityplans")

        # Should not raise exception
        cache.clear()

        assert cache._integration_finding_id_cache is None


class TestThreadSafety:
    """Test thread safety of cache operations."""

    @patch(f"{PATH}.IssueCache._populate_issue_lookup_cache")
    @patch(f"{PATH}.Application")
    def test_concurrent_add_operations(self, mock_app_class, mock_populate):
        """Test concurrent add operations are thread-safe."""
        import threading

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._integration_finding_id_cache = ThreadSafeDict()

        def add_issues(start_id, count):
            for i in range(count):
                issue_id = start_id + i
                mock_issue = create_mock_issue(issue_id, f"finding-{issue_id}")
                cache.add(mock_issue)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_issues, args=(i * 100, 10))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should have 50 unique issues
        total_issues = sum(len(issues) for issues in cache._integration_finding_id_cache.values())
        assert total_issues == 50

    @patch(f"{PATH}.Application")
    def test_concurrent_clear_operations(self, mock_app_class):
        """Test concurrent clear operations are thread-safe."""
        import threading

        cache = IssueCache(plan_id=123, parent_module="securityplans")
        cache._integration_finding_id_cache = ThreadSafeDict()

        def clear_cache():
            cache.clear()

        threads = []
        for i in range(10):
            thread = threading.Thread(target=clear_cache)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should not raise exception and cache should be clear
        assert cache._integration_finding_id_cache is None
